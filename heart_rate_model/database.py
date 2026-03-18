"""
数据库操作模块 - 支持设备状态和异常记录管理
"""

import pymysql
from datetime import datetime, date
from typing import Optional, Dict, List
from config import DATABASE_CONFIG


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        """初始化数据库连接"""
        self.config = DATABASE_CONFIG['mysql']
        self.connection = None
        self.connect()
    
    def connect(self):
        """建立数据库连接"""
        try:
            self.connection = pymysql.connect(
                host=self.config['host'],
                port=self.config['port'],
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['database'],
                charset=self.config['charset'],
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False
            )
            print("✅ 数据库连接成功")
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            self.connection = None
    
    def ensure_connection(self):
        """确保数据库连接有效"""
        try:
            if self.connection is None:
                self.connect()
            else:
                self.connection.ping(reconnect=True)
        except Exception as e:
            print(f"⚠️  数据库重连: {e}")
            self.connect()
    
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            print("📴 数据库连接已关闭")
    
    # ==================== 设备状态管理 ====================
    
    def update_device_status(self, device_id: str, client_id: str, is_online: bool) -> bool:
        """
        更新设备在线/离线状态
        
        Args:
            device_id: 设备ID（userId）
            client_id: MQTT客户端ID
            is_online: 是否在线
            
        Returns:
            是否更新成功
        """
        try:
            self.ensure_connection()
            
            with self.connection.cursor() as cursor:
                # 检查设备是否存在
                check_sql = """
                    SELECT id FROM device_status 
                    WHERE device_id = %s
                """
                cursor.execute(check_sql, (device_id,))
                existing = cursor.fetchone()
                
                now = datetime.now()
                
                if existing:
                    # 更新现有记录
                    update_sql = """
                        UPDATE device_status 
                        SET client_id = %s,
                            is_online = %s,
                            last_update_time = %s,
                            online_time = CASE WHEN %s = 1 THEN %s ELSE online_time END,
                            offline_time = CASE WHEN %s = 0 THEN %s ELSE offline_time END
                        WHERE device_id = %s
                    """
                    cursor.execute(update_sql, (
                        client_id, 
                        1 if is_online else 0, 
                        now,
                        1 if is_online else 0, now,  # online_time
                        1 if is_online else 0, now,  # offline_time
                        device_id
                    ))
                else:
                    # 插入新记录
                    insert_sql = """
                        INSERT INTO device_status 
                        (device_id, client_id, is_online, online_time, offline_time, last_update_time)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_sql, (
                        device_id,
                        client_id,
                        1 if is_online else 0,
                        now if is_online else None,
                        now if not is_online else None,
                        now
                    ))
                
                self.connection.commit()
                status_text = "在线" if is_online else "离线"
                print(f"✅ 设备状态已更新: {device_id} -> {status_text}")
                return True
                
        except Exception as e:
            print(f"❌ 更新设备状态失败: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def get_device_status(self, device_id: str) -> Optional[Dict]:
        """
        获取设备状态
        
        Args:
            device_id: 设备ID
            
        Returns:
            设备状态信息
        """
        try:
            self.ensure_connection()
            
            with self.connection.cursor() as cursor:
                sql = """
                    SELECT * FROM device_status 
                    WHERE device_id = %s
                """
                cursor.execute(sql, (device_id,))
                return cursor.fetchone()
                
        except Exception as e:
            print(f"❌ 查询设备状态失败: {e}")
            return None
    
    # ==================== 异常记录管理 ====================
    
    def insert_anomaly_record(self, 
                             device_id: str,
                             heart_rate: float,
                             anomaly_type: str,
                             severity: str = 'medium',
                             description: str = None) -> bool:
        """
        插入异常记录
        
        Args:
            device_id: 设备ID
            heart_rate: 心率值
            anomaly_type: 异常类型（instant_high/instant_low/continuous_high/continuous_low等）
            severity: 严重程度（low/medium/high）
            description: 描述信息
            
        Returns:
            是否插入成功
        """
        try:
            self.ensure_connection()
            
            with self.connection.cursor() as cursor:
                insert_sql = """
                    INSERT INTO anomaly_records 
                    (device_id, heart_rate, anomaly_type, severity, description, record_time)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_sql, (
                    device_id,
                    heart_rate,
                    anomaly_type,
                    severity,
                    description,
                    datetime.now()
                ))
                
                self.connection.commit()
                print(f"✅ 异常记录已插入: {device_id} - {anomaly_type}")
                return True
                
        except Exception as e:
            print(f"❌ 插入异常记录失败: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def update_daily_anomaly_count(self, device_id: str, anomaly_type: str = 'instant') -> bool:
        """
        更新设备今日瞬时异常总数
        
        Args:
            device_id: 设备ID
            anomaly_type: 异常类型（instant/continuous）
            
        Returns:
            是否更新成功
        """
        try:
            self.ensure_connection()
            
            with self.connection.cursor() as cursor:
                today = date.today()
                
                # 检查今日统计记录是否存在
                check_sql = """
                    SELECT id, instant_anomaly_count, continuous_anomaly_count 
                    FROM daily_anomaly_stats 
                    WHERE device_id = %s AND stat_date = %s
                """
                cursor.execute(check_sql, (device_id, today))
                existing = cursor.fetchone()
                
                if existing:
                    # 更新计数
                    if anomaly_type == 'instant':
                        update_sql = """
                            UPDATE daily_anomaly_stats 
                            SET instant_anomaly_count = instant_anomaly_count + 1,
                                last_update_time = %s
                            WHERE device_id = %s AND stat_date = %s
                        """
                    else:
                        update_sql = """
                            UPDATE daily_anomaly_stats 
                            SET continuous_anomaly_count = continuous_anomaly_count + 1,
                                last_update_time = %s
                            WHERE device_id = %s AND stat_date = %s
                        """
                    cursor.execute(update_sql, (datetime.now(), device_id, today))
                else:
                    # 创建新的统计记录
                    insert_sql = """
                        INSERT INTO daily_anomaly_stats 
                        (device_id, stat_date, instant_anomaly_count, continuous_anomaly_count, last_update_time)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_sql, (
                        device_id,
                        today,
                        1 if anomaly_type == 'instant' else 0,
                        1 if anomaly_type == 'continuous' else 0,
                        datetime.now()
                    ))
                
                self.connection.commit()
                print(f"✅ 今日异常统计已更新: {device_id}")
                return True
                
        except Exception as e:
            print(f"❌ 更新今日异常统计失败: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def get_daily_anomaly_stats(self, device_id: str, stat_date: date = None) -> Optional[Dict]:
        """
        获取设备指定日期的异常统计
        
        Args:
            device_id: 设备ID
            stat_date: 统计日期（默认今天）
            
        Returns:
            统计信息
        """
        try:
            self.ensure_connection()
            
            if stat_date is None:
                stat_date = date.today()
            
            with self.connection.cursor() as cursor:
                sql = """
                    SELECT * FROM daily_anomaly_stats 
                    WHERE device_id = %s AND stat_date = %s
                """
                cursor.execute(sql, (device_id, stat_date))
                return cursor.fetchone()
                
        except Exception as e:
            print(f"❌ 查询异常统计失败: {e}")
            return None
    
    def get_recent_anomalies(self, device_id: str, limit: int = 10) -> List[Dict]:
        """
        获取设备最近的异常记录
        
        Args:
            device_id: 设备ID
            limit: 返回条数
            
        Returns:
            异常记录列表
        """
        try:
            self.ensure_connection()
            
            with self.connection.cursor() as cursor:
                sql = """
                    SELECT * FROM anomaly_records 
                    WHERE device_id = %s 
                    ORDER BY record_time DESC 
                    LIMIT %s
                """
                cursor.execute(sql, (device_id, limit))
                return cursor.fetchall()
                
        except Exception as e:
            print(f"❌ 查询异常记录失败: {e}")
            return []

    # ==================== 心率数据读取（轮询模式） ====================

    def get_latest_heart_rate_id(self) -> int:
        """获取 employee_heart_rate 表中最新记录ID"""
        try:
            self.ensure_connection()
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT IFNULL(MAX(id), 0) AS max_id FROM employee_heart_rate")
                row = cursor.fetchone() or {}
                return int(row.get('max_id') or 0)
        except Exception as e:
            print(f"❌ 查询最新心率记录ID失败: {e}")
            return 0

    def get_new_heart_rate_records(self, last_id: int = 0, limit: int = 100) -> List[Dict]:
        """
        获取大于 last_id 的最新心率记录（按ID升序）

        Args:
            last_id: 上次处理的最大ID
            limit: 拉取条数上限
        """
        try:
            self.ensure_connection()
            with self.connection.cursor() as cursor:
                sql = """
                    SELECT id, employee_id, heart_rate, measure_time, is_abnormal, source
                    FROM employee_heart_rate
                    WHERE id > %s
                    ORDER BY id ASC
                    LIMIT %s
                """
                cursor.execute(sql, (last_id, limit))
                return cursor.fetchall()
        except Exception as e:
            print(f"❌ 查询增量心率记录失败: {e}")
            return []

    def get_recent_employee_heart_rates(self, employee_id: str, limit: int = 60) -> List[Dict]:
        """
        获取指定职工最近心率数据（按时间升序返回）

        Args:
            employee_id: 职工ID
            limit: 返回条数
        """
        try:
            self.ensure_connection()
            with self.connection.cursor() as cursor:
                sql = """
                    SELECT id, employee_id, heart_rate, measure_time, is_abnormal, source
                    FROM (
                        SELECT id, employee_id, heart_rate, measure_time, is_abnormal, source
                        FROM employee_heart_rate
                        WHERE employee_id = %s
                        ORDER BY measure_time DESC, id DESC
                        LIMIT %s
                    ) t
                    ORDER BY measure_time ASC, id ASC
                """
                cursor.execute(sql, (employee_id, limit))
                return cursor.fetchall()
        except Exception as e:
            print(f"❌ 查询职工最近心率数据失败: {e}")
            return []


# 创建数据库表的SQL语句（首次使用时执行）
CREATE_TABLES_SQL = """
-- 设备状态表
CREATE TABLE IF NOT EXISTS device_status (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL UNIQUE COMMENT '设备ID',
    client_id VARCHAR(100) COMMENT 'MQTT客户端ID',
    is_online TINYINT(1) DEFAULT 0 COMMENT '是否在线 0-离线 1-在线',
    online_time DATETIME COMMENT '上线时间',
    offline_time DATETIME COMMENT '离线时间',
    last_update_time DATETIME COMMENT '最后更新时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_device_id (device_id),
    INDEX idx_is_online (is_online)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='设备状态表';

-- 异常记录表
CREATE TABLE IF NOT EXISTS anomaly_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL COMMENT '设备ID',
    heart_rate FLOAT NOT NULL COMMENT '心率值',
    anomaly_type VARCHAR(50) NOT NULL COMMENT '异常类型',
    severity VARCHAR(20) DEFAULT 'medium' COMMENT '严重程度',
    description TEXT COMMENT '描述信息',
    record_time DATETIME NOT NULL COMMENT '记录时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_device_id (device_id),
    INDEX idx_record_time (record_time),
    INDEX idx_anomaly_type (anomaly_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='异常记录表';

-- 每日异常统计表
CREATE TABLE IF NOT EXISTS daily_anomaly_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL COMMENT '设备ID',
    stat_date DATE NOT NULL COMMENT '统计日期',
    instant_anomaly_count INT DEFAULT 0 COMMENT '瞬时异常总数',
    continuous_anomaly_count INT DEFAULT 0 COMMENT '连续异常总数',
    last_update_time DATETIME COMMENT '最后更新时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_device_date (device_id, stat_date),
    INDEX idx_stat_date (stat_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='每日异常统计表';
"""


def init_database():
    """初始化数据库表结构"""
    try:
        # 第一步：先创建数据库（不指定database参数）
        connection = pymysql.connect(
            host=DATABASE_CONFIG['mysql']['host'],
            port=DATABASE_CONFIG['mysql']['port'],
            user=DATABASE_CONFIG['mysql']['user'],
            password=DATABASE_CONFIG['mysql']['password'],
            charset=DATABASE_CONFIG['mysql']['charset']
        )
        
        with connection.cursor() as cursor:
            # 创建数据库（如果不存在）
            db_name = DATABASE_CONFIG['mysql']['database']
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci")
            print(f"✅ 数据库 '{db_name}' 已创建或已存在")
            cursor.execute(f"USE {db_name}")
            
            # 执行建表语句
            for statement in CREATE_TABLES_SQL.split(';'):
                if statement.strip():
                    cursor.execute(statement)
        
        connection.commit()
        connection.close()
        print("✅ 数据库表初始化成功")
        return True
        
    except Exception as e:
        print(f"❌ 数据库表初始化失败: {e}")
        return False


if __name__ == "__main__":
    # 测试数据库连接和初始化
    init_database()
    
    db = DatabaseManager()
    
    # 测试设备状态更新
    db.update_device_status("test_device_001", "client_001", True)
    status = db.get_device_status("test_device_001")
    print(f"设备状态: {status}")
    
    # 测试异常记录
    db.insert_anomaly_record("test_device_001", 180, "instant_high", "high", "心率过高")
    db.update_daily_anomaly_count("test_device_001", "instant")
    
    stats = db.get_daily_anomaly_stats("test_device_001")
    print(f"今日统计: {stats}")
    
    db.close()
