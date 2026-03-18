"""
数据库监测模块 - 替代原 MQTT 监测模式
启动后定时从 employee_heart_rate 表读取最新心率数据，
经 ML 模型 + 规则检测判断是否异常，
将检测结果写入 ml_detection_result 表。
"""

import os
import time
import threading
import numpy as np
from datetime import datetime
from typing import Callable, Dict, List, Optional

from data_filter import HeartRateFilter
from enhanced_detector import EnhancedAnomalyDetector
from lgbm_model import LGBMAnomalyDetector
from database import DatabaseManager

# ── 心率分类阈值常量 ────────────────────────────────────────────────────────────
_HR_EXTREME_HIGH = 200   # 心率极高上限（bpm）
_HR_EXTREME_LOW  = 30    # 心率极低下限（bpm）
_HR_HIGH         = 150   # 心率过快阈值（bpm）
_HR_LOW          = 60    # 心率过慢阈值（bpm）


class DbHeartRateMonitor:
    """从数据库读取心率数据、运行ML检测并将结果写入检测结果表的监测器"""

    # 默认 ML 模型路径（相对于此文件所在目录）
    DEFAULT_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'output', 'models', 'lgbm_model.pkl')

    def __init__(self, interval: int = 10, window_size: int = 30):
        """
        Args:
            interval:    检测轮询间隔（秒），默认 10 秒
            window_size: 滑动窗口大小（每位职工取最近 N 条），默认 30 条
        """
        self.interval = interval
        self.window_size = window_size
        self.is_running = False
        self._thread: Optional[threading.Thread] = None

        # 子模块
        self.db = DatabaseManager()
        self.filter = HeartRateFilter()
        self.rule_detector = EnhancedAnomalyDetector()
        self.ml_detector = LGBMAnomalyDetector(window_size=window_size)
        self.model_loaded = self._load_model()

        # 已处理的最新记录 ID（避免同一条原始记录被重复写入结果表）
        self._last_processed: Dict[int, int] = {}  # employee_id -> heart_rate record id

        # 停止信号（比轮询 is_running 标志更高效）
        self._stop_event = threading.Event()

        # 可选回调：每条检测结果产生后调用 callback(result_dict)
        self._on_result: Optional[Callable[[Dict], None]] = None

    # ── 初始化 ────────────────────────────────────────────────────────────────

    def _load_model(self) -> bool:
        """加载已训练的 LightGBM 模型；若不存在则仅使用规则检测"""
        if os.path.exists(self.DEFAULT_MODEL_PATH):
            try:
                self.ml_detector.load_model(self.DEFAULT_MODEL_PATH)
                print(f"✅ ML 模型已加载: {self.DEFAULT_MODEL_PATH}")
                return True
            except Exception as e:
                print(f"⚠️  ML 模型加载失败: {e}，将仅使用规则检测")
        else:
            print("⚠️  ML 模型文件不存在，将仅使用规则检测")
            print(f"   路径: {self.DEFAULT_MODEL_PATH}")
            print("   可在主菜单选择「1. 训练模型」生成模型文件")
        return False

    def set_result_callback(self, callback: Callable[[Dict], None]):
        """设置检测结果回调函数，每次写入 ml_detection_result 后触发"""
        self._on_result = callback

    # ── 数据库读取 ─────────────────────────────────────────────────────────────

    def get_all_employee_ids(self) -> List[int]:
        """获取 employee 表中所有职工 ID"""
        try:
            self.db.ensure_connection()
            with self.db.connection.cursor() as cursor:
                cursor.execute("SELECT id FROM employee ORDER BY id")
                return [row['id'] for row in cursor.fetchall()]
        except Exception as e:
            print(f"❌ 获取职工列表失败: {e}")
            return []

    def get_employee_records(self, employee_id: int, limit: int = None) -> List[Dict]:
        """
        获取某位职工最近 limit 条心率记录（时间升序，最新数据在末尾）

        Returns:
            list of dict with keys: id, heart_rate, measure_time, is_abnormal
        """
        if limit is None:
            limit = self.window_size
        try:
            self.db.ensure_connection()
            with self.db.connection.cursor() as cursor:
                cursor.execute(
                    """SELECT id, heart_rate, measure_time, is_abnormal
                       FROM employee_heart_rate
                       WHERE employee_id = %s
                       ORDER BY measure_time DESC
                       LIMIT %s""",
                    (employee_id, limit)
                )
                # DESC 查出后反转，使最旧的排在前面（滑动窗口需要时序数据）
                return list(reversed(cursor.fetchall()))
        except Exception as e:
            print(f"❌ 获取心率记录失败 employee_id={employee_id}: {e}")
            return []

    # ── 数据库写入 ─────────────────────────────────────────────────────────────

    def save_detection_result(
        self,
        employee_id: int,
        heart_rate: int,
        is_abnormal: bool,
        anomaly_type: Optional[str],
        source_record_id: Optional[int],
    ) -> bool:
        """将一条检测结果插入 ml_detection_result 表"""
        try:
            self.db.ensure_connection()
            with self.db.connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO ml_detection_result
                       (employee_id, heart_rate, is_abnormal, anomaly_type,
                        source_record_id, detect_time)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (
                        employee_id,
                        heart_rate,
                        1 if is_abnormal else 0,
                        anomaly_type,
                        source_record_id,
                        datetime.now(),
                    ),
                )
            self.db.connection.commit()
            return True
        except Exception as e:
            print(f"❌ 保存检测结果失败 employee_id={employee_id}: {e}")
            if self.db.connection:
                self.db.connection.rollback()
            return False

    # ── 检测逻辑 ───────────────────────────────────────────────────────────────

    def _classify_by_rate(self, heart_rate: float) -> str:
        """根据心率值粗略分类（ML 检测到异常但规则未命中时使用）"""
        if heart_rate >= _HR_EXTREME_HIGH or heart_rate <= _HR_EXTREME_LOW:
            return '心率极值'
        if heart_rate > _HR_HIGH:
            return '心率过快'
        if heart_rate < _HR_LOW:
            return '心率过慢'
        return '心律不齐'

    def _detect_employee(self, employee_id: int):
        """对单个职工执行一轮检测并将结果写入 ml_detection_result"""
        records = self.get_employee_records(employee_id)
        if not records:
            return

        latest_record = records[-1]
        latest_id = latest_record['id']

        # 若最新记录与上次相同，说明无新数据，跳过
        if self._last_processed.get(employee_id) == latest_id:
            return

        heart_rates = np.array([r['heart_rate'] for r in records], dtype=float)

        # ── 数据滤波 ──────────────────────────────────────────────────────────
        filtered = self.filter.comprehensive_filter(heart_rates)
        last_idx = len(filtered) - 1

        is_abnormal = False
        anomaly_type_parts: List[str] = []

        # ── 规则检测 ──────────────────────────────────────────────────────────
        rule_results = self.rule_detector.detect_all(filtered)
        if last_idx in rule_results.get('high_rate', []):
            is_abnormal = True
            anomaly_type_parts.append('心率过快')
        if last_idx in rule_results.get('low_rate', []):
            is_abnormal = True
            anomaly_type_parts.append('心率过慢')
        if last_idx in rule_results.get('extreme_value', []):
            is_abnormal = True
            anomaly_type_parts.append('心率极值')
        if last_idx in rule_results.get('arrhythmia', []):
            is_abnormal = True
            anomaly_type_parts.append('心律不齐')

        # ── ML 模型检测（补充规则未捕捉到的异常） ─────────────────────────────
        if self.model_loaded and len(filtered) >= 2:
            try:
                features = self.ml_detector.extract_features(filtered)
                prediction = self.ml_detector.predict(features[-1:])
                if prediction[0] == 1 and not is_abnormal:
                    is_abnormal = True
                    anomaly_type_parts.append(self._classify_by_rate(filtered[-1]))
            except Exception as e:
                print(f"⚠️  ML 检测失败 employee_id={employee_id}: {e}")

        anomaly_type = ', '.join(anomaly_type_parts) if anomaly_type_parts else None

        # ── 写入结果表 ────────────────────────────────────────────────────────
        saved = self.save_detection_result(
            employee_id=employee_id,
            heart_rate=int(heart_rates[-1]),
            is_abnormal=is_abnormal,
            anomaly_type=anomaly_type,
            source_record_id=latest_id,
        )

        if saved:
            self._last_processed[employee_id] = latest_id

            result = {
                'employee_id': employee_id,
                'heart_rate': int(heart_rates[-1]),
                'is_abnormal': is_abnormal,
                'anomaly_type': anomaly_type,
                'detect_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            if self._on_result:
                self._on_result(result)

            if is_abnormal:
                print(
                    f"⚠️  [{datetime.now().strftime('%H:%M:%S')}] "
                    f"employee_id={employee_id} "
                    f"心率={int(heart_rates[-1])}bpm "
                    f"异常类型={anomaly_type}"
                )

    def run_once(self):
        """对数据库中所有职工执行一轮检测"""
        employee_ids = self.get_all_employee_ids()
        if not employee_ids:
            print("⚠️  employee 表为空，无职工数据可检测")
            return
        for emp_id in employee_ids:
            try:
                self._detect_employee(emp_id)
            except Exception as e:
                print(f"❌ 检测职工 {emp_id} 时出错: {e}")

    # ── 后台线程控制 ───────────────────────────────────────────────────────────

    def _worker(self):
        """后台检测循环（每 interval 秒执行一次 run_once）"""
        print(f"\n🔍 数据库心率检测已启动")
        print(f"   轮询间隔: {self.interval}s  |  滑动窗口: {self.window_size}条")
        print(f"   ML 模型: {'✅ 已加载' if self.model_loaded else '⚠️  未加载（仅规则检测）'}")
        while not self._stop_event.is_set():
            try:
                self.run_once()
            except Exception as e:
                print(f"❌ 检测循环出错: {e}")
            # 使用 Event.wait 代替 time.sleep，以便 stop() 可以立即唤醒循环
            self._stop_event.wait(timeout=self.interval)
        print("⏹️  数据库心率检测已停止")

    def start(self):
        """在后台线程中启动持续检测"""
        if self.is_running:
            return
        self._stop_event.clear()
        self.is_running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def stop(self):
        """停止后台检测"""
        self.is_running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=self.interval + 2)
        if self.db:
            self.db.close()
