"""
MIT-BIH Arrhythmia Database 加载器
将 ECG 信号 + 专家标注 转换为 10 秒间隔心率序列，用于异常检测模型训练和评估
"""

import numpy as np
import pandas as pd
import wfdb
import os
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from collections import Counter


# 正常心跳类型 vs 异常心跳类型
NORMAL_BEATS = {'N', 'e', 'j'}  # 正常、逸搏、交界性逸搏
ABNORMAL_BEATS = {
    'V': '室性早搏',
    'A': '房性早搏',
    'F': '融合心跳',
    'L': '左束支传导阻滞',
    'R': '右束支传导阻滞',
    '/': '起搏心跳',
    'Q': '未分类异常',
    'a': '异常房性早搏',
    'J': '交界性早搏',
    'S': '室上性早搏',
    'E': '室性逸搏',
    '!': '室颤'
}

# MIT-BIH 48条记录列表
RECORDS_100 = list(range(100, 125))   # 23条（100-124）
RECORDS_200 = list(range(200, 235))   # 25条（200-234）
ALL_RECORDS = RECORDS_100 + RECORDS_200


class MITBIHLoader:
    """MIT-BIH 数据加载与转换器"""

    def __init__(self, data_dir='mitbih_data', window_seconds=10):
        """
        Args:
            data_dir: 本地数据存储目录
            window_seconds: 心率聚合窗口（秒），默认 10 秒匹配系统采样间隔
        """
        self.data_dir = data_dir
        self.window_seconds = window_seconds
        os.makedirs(data_dir, exist_ok=True)

    def download_if_needed(self):
        """检查并下载 MIT-BIH 数据"""
        if os.path.exists(os.path.join(self.data_dir, 'mitdb_dir')):
            print(f"✓ 数据已存在于 {self.data_dir}")
            return

        print(f"正在从 PhysioNet 下载 MIT-BIH Arrhythmia Database...")
        print(f"保存路径: {self.data_dir}")

        os.makedirs(self.data_dir, exist_ok=True)

        # 使用 wfdb 下载（它会自动缓存到当前目录）
        # 先下载一条测试
        try:
            wfdb.dl_database('mitdb', dl_dir=self.data_dir)
            print("✓ 下载完成")
        except Exception as e:
            print(f"⚠ 自动下载失败: {e}")
            print("尝试使用 wfdb 在线读取（首次会较慢）...")

    def load_record(self, record_num: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, int]:
        """
        加载单条记录

        Returns:
            signal: ECG 信号 (samples, channels)
            r_peaks: R 波峰样本索引
            beat_labels: 每个心跳的标注符号
            rr_intervals: RR 间期（秒）
            fs: 采样率
        """
        # 尝试本地读取，失败则在线读取
        try:
            record = wfdb.rdrecord(os.path.join(self.data_dir, str(record_num)))
            annotation = wfdb.rdann(os.path.join(self.data_dir, str(record_num)), 'atr')
        except Exception:
            try:
                record = wfdb.rdrecord(str(record_num), pn_dir=f'mitdb/{self.data_dir}')
                annotation = wfdb.rdann(str(record_num), 'atr', pn_dir=f'mitdb/{self.data_dir}')
            except Exception:
                record = wfdb.rdrecord(str(record_num), pn_dir='mitdb')
                annotation = wfdb.rdann(str(record_num), 'atr', pn_dir='mitdb')

        fs = record.fs
        signal = record.p_signal[:, 0]  # 第一通道（通常是 MLII）
        r_peaks = annotation.sample
        beat_labels = np.array(list(annotation.symbol))

        # 计算 RR 间期
        rr_intervals = np.diff(r_peaks) / fs  # 秒

        return signal, r_peaks, beat_labels, rr_intervals, fs

    def compute_instantaneous_hr(self, r_peaks: np.ndarray, beat_labels: np.ndarray,
                                  fs: int) -> pd.DataFrame:
        """
        计算逐拍心率，并标注每个心跳是否异常

        Returns:
            DataFrame with columns: beat_time, heart_rate, is_abnormal, anomaly_type, beat_label
        """
        rr_intervals = np.diff(r_peaks) / fs

        # 过滤生理上不可能的 RR 间期 (HR 30-250 bpm)
        valid = (rr_intervals > 0.24) & (rr_intervals < 2.0)

        results = []
        for i in range(len(rr_intervals)):
            if not valid[i]:
                continue

            hr = 60.0 / rr_intervals[i]
            beat_time = r_peaks[i + 1] / fs  # 秒

            # 标注当前心跳（使用 R 峰之后的标注）
            label = beat_labels[i + 1] if i + 1 < len(beat_labels) else 'N'

            is_abnormal = 1 if label in ABNORMAL_BEATS else 0
            anomaly_type = ABNORMAL_BEATS.get(label, '') if is_abnormal else ''

            results.append({
                'beat_time': beat_time,
                'heart_rate': round(hr, 1),
                'is_abnormal': is_abnormal,
                'anomaly_type': anomaly_type,
                'beat_label': label
            })

        return pd.DataFrame(results)

    def aggregate_to_windows(self, beat_df: pd.DataFrame, record_num: int) -> pd.DataFrame:
        """
        将逐拍心率聚合为固定时间窗口（模拟 10 秒间隔采样）

        每个窗口内：
        - 心率 = 窗口内所有心跳心率的平均值
        - 异常标记 = 窗口内任一心跳异常则窗口异常
        - 异常类型 = 窗口内出现最多的异常类型
        """
        if len(beat_df) == 0:
            return pd.DataFrame()

        max_time = beat_df['beat_time'].max()
        window_start = np.arange(0, max_time, self.window_seconds)
        window_end = window_start + self.window_seconds

        rows = []
        for i, (w_start, w_end) in enumerate(zip(window_start, window_end)):
            mask = (beat_df['beat_time'] >= w_start) & (beat_df['beat_time'] < w_end)
            window_beats = beat_df[mask]

            if len(window_beats) == 0:
                continue

            avg_hr = window_beats['heart_rate'].mean()
            abnormal_count = window_beats['is_abnormal'].sum()
            is_abnormal = 1 if abnormal_count > 0 else 0

            # 确定异常类型
            if is_abnormal:
                abnormal_types = window_beats[window_beats['is_abnormal'] == 1]['anomaly_type']
                # 分类到四大类型
                types_count = Counter(abnormal_types)
                # 映射到我们系统的异常类型
                hr_val = avg_hr
                if hr_val > 150 and abnormal_count >= 2:
                    mapped_type = 'high_rate'
                elif hr_val < 60 and abnormal_count >= 2:
                    mapped_type = 'low_rate'
                elif hr_val >= 200 or hr_val <= 30:
                    mapped_type = 'extreme_value'
                elif len(window_beats) >= 2:
                    # 检测心律不齐
                    diffs = abs(window_beats['heart_rate'].diff()).dropna()
                    if (diffs >= 30).any():
                        mapped_type = 'arrhythmia'
                    else:
                        mapped_type = 'arrhythmia'  # 其他心律失常归入心律不齐
                else:
                    mapped_type = 'arrhythmia'
            else:
                mapped_type = 'normal'

            rows.append({
                'window_id': i,
                'batch_id': record_num,
                'heart_rate': round(avg_hr, 1),
                'is_abnormal': is_abnormal,
                'anomaly_type': mapped_type,
                'abnormal_beat_count': abnormal_count,
                'total_beat_count': len(window_beats),
                'window_start_sec': w_start,
                'window_end_sec': w_end,
                'record_num': record_num
            })

        return pd.DataFrame(rows)

    def load_as_training_data(self, record_nums: List[int] = None,
                               limit_records: int = None) -> pd.DataFrame:
        """
        加载 MIT-BIH 数据并转换为训练用 DataFrame

        Args:
            record_nums: 要加载的记录编号列表，默认全部 48 条
            limit_records: 限制加载记录数（方便快速测试）

        Returns:
            DataFrame with columns: heart_rate, is_abnormal, anomaly_type, batch_id, record_num
        """
        if record_nums is None:
            record_nums = ALL_RECORDS
        if limit_records:
            record_nums = record_nums[:limit_records]

        all_windows = []
        stats = {'total_beats': 0, 'abnormal_beats': 0, 'normal_beats': 0,
                 'total_windows': 0, 'abnormal_windows': 0}

        print(f"加载 MIT-BIH 数据（{len(record_nums)} 条记录）...")
        for rec_num in record_nums:
            try:
                signal, r_peaks, beat_labels, rr_intervals, fs = self.load_record(rec_num)
                beat_df = self.compute_instantaneous_hr(r_peaks, beat_labels, fs)
                windows_df = self.aggregate_to_windows(beat_df, rec_num)

                if len(windows_df) > 0:
                    all_windows.append(windows_df)

                stats['total_beats'] += len(beat_df)
                stats['abnormal_beats'] += beat_df['is_abnormal'].sum()
                stats['normal_beats'] += (beat_df['is_abnormal'] == 0).sum()
                stats['total_windows'] += len(windows_df)
                stats['abnormal_windows'] += windows_df['is_abnormal'].sum()

                print(f"  记录 {rec_num}: {len(beat_df)} 心跳 → {len(windows_df)} 窗口, "
                      f"异常率 {windows_df['is_abnormal'].mean()*100:.1f}%")

            except Exception as e:
                print(f"  记录 {rec_num}: 加载失败 - {e}")

        if not all_windows:
            raise RuntimeError("未能加载任何记录，请检查网络连接或数据文件")

        result_df = pd.concat(all_windows, ignore_index=True)

        print(f"\n{'='*60}")
        print(f"数据加载完成:")
        print(f"  总记录数: {len(record_nums)} 条")
        print(f"  总心跳数: {stats['total_beats']}")
        print(f"  正常心跳: {stats['normal_beats']}")
        print(f"  异常心跳: {stats['abnormal_beats']}")
        print(f"  总窗口数: {stats['total_windows']}")
        print(f"  异常窗口: {stats['abnormal_windows']} "
              f"({stats['abnormal_windows']/stats['total_windows']*100:.1f}%)")
        print(f"  异常类型分布:")
        for t in result_df[result_df['is_abnormal'] == 1]['anomaly_type'].value_counts().items():
            print(f"    {t[0]}: {t[1]}")
        print(f"{'='*60}")

        return result_df

    def get_record_info(self, record_num: int) -> Dict:
        """获取记录的基本信息"""
        signal, r_peaks, beat_labels, rr_intervals, fs = self.load_record(record_num)

        label_counts = Counter(beat_labels)
        total = len(beat_labels)
        abnormal = sum(label_counts.get(k, 0) for k in ABNORMAL_BEATS)

        return {
            'record_num': record_num,
            'duration_minutes': len(signal) / fs / 60,
            'sampling_rate': fs,
            'total_beats': total,
            'normal_beats': total - abnormal,
            'abnormal_beats': abnormal,
            'abnormal_rate': abnormal / total * 100 if total > 0 else 0,
            'beat_distribution': {k: v for k, v in label_counts.most_common(10)}
        }


if __name__ == '__main__':
    loader = MITBIHLoader(data_dir='mitbih_data')

    # 先下载数据
    loader.download_if_needed()

    # 测试：加载单条记录的信息
    print("\n=== 单条记录信息 ===\n")
    info = loader.get_record_info(100)
    for k, v in info.items():
        if k == 'beat_distribution':
            print(f"心跳类型分布: {v}")
        else:
            print(f"{k}: {v}")

    # 测试：加载少量数据训练用
    print("\n=== 加载训练数据 ===\n")
    df = loader.load_as_training_data(limit_records=5)

    print("\n前10条数据预览:")
    print(df.head(10))

    print("\n数据类型分布:")
    print(df['anomaly_type'].value_counts())

    # 保存数据
    output_path = 'output/mitbih_training_data.csv'
    os.makedirs('output', exist_ok=True)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\n✓ 数据已保存: {output_path}")
