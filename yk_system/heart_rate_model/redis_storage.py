"""
Redis数据存储模块 - 存储近10分钟心率历史数据
"""

import redis
import json
from typing import List, Dict, Optional
from datetime import datetime
from config import REDIS_CONFIG


class RedisStorage:
    """Redis数据存储管理器"""
    
    def __init__(self):
        """初始化Redis连接"""
        try:
            self.redis_client = redis.Redis(
                host=REDIS_CONFIG['host'],
                port=REDIS_CONFIG['port'],
                db=REDIS_CONFIG['db'],
                password=REDIS_CONFIG.get('password'),
                decode_responses=REDIS_CONFIG.get('decode_responses', True)
            )
            # 测试连接
            self.redis_client.ping()
            print("✅ Redis连接成功")
        except Exception as e:
            print(f"❌ Redis连接失败: {e}")
            self.redis_client = None
    
    def _get_key(self, device_id: str) -> str:
        """
        生成Redis key
        
        Args:
            device_id: 设备ID
            
        Returns:
            Redis key
        """
        return f"heart_rate:history:{device_id}"
    
    def add_heart_rate(self, device_id: str, heart_rate: float, timestamp: str = None) -> bool:
        """
        添加心率数据到Redis（使用列表存储，保持时间顺序）
        
        Args:
            device_id: 设备ID
            heart_rate: 心率值
            timestamp: 时间戳（可选，默认当前时间）
            
        Returns:
            是否添加成功
        """
        if not self.redis_client:
            return False
        
        try:
            key = self._get_key(device_id)
            
            if timestamp is None:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 构造数据
            data = {
                'heart_rate': heart_rate,
                'timestamp': timestamp
            }
            
            # 添加到列表尾部（右侧）
            self.redis_client.rpush(key, json.dumps(data))
            
            # 保持列表长度，只保留最近的N条数据
            max_count = REDIS_CONFIG.get('max_history_count', 60)
            self.redis_client.ltrim(key, -max_count, -1)
            
            # 设置过期时间（10分钟）
            expire_time = REDIS_CONFIG.get('history_expire', 600)
            self.redis_client.expire(key, expire_time)
            
            return True
            
        except Exception as e:
            print(f"❌ Redis添加数据失败: {e}")
            return False
    
    def get_recent_heart_rates(self, device_id: str, count: int = None) -> List[Dict]:
        """
        获取最近的心率数据
        
        Args:
            device_id: 设备ID
            count: 获取数量（None表示全部）
            
        Returns:
            心率数据列表，每项包含 heart_rate 和 timestamp
        """
        if not self.redis_client:
            return []
        
        try:
            key = self._get_key(device_id)
            
            if count is None:
                # 获取全部数据
                data_list = self.redis_client.lrange(key, 0, -1)
            else:
                # 获取最近的count条数据
                data_list = self.redis_client.lrange(key, -count, -1)
            
            # 解析JSON数据
            result = []
            for item in data_list:
                try:
                    result.append(json.loads(item))
                except:
                    continue
            
            return result
            
        except Exception as e:
            print(f"❌ Redis获取数据失败: {e}")
            return []
    
    def get_heart_rate_values(self, device_id: str, count: int = None) -> List[float]:
        """
        获取心率值列表（仅返回数值，不含时间戳）
        
        Args:
            device_id: 设备ID
            count: 获取数量（None表示全部）
            
        Returns:
            心率值列表
        """
        data_list = self.get_recent_heart_rates(device_id, count)
        return [item['heart_rate'] for item in data_list]
    
    def get_history_count(self, device_id: str) -> int:
        """
        获取存储的历史数据数量
        
        Args:
            device_id: 设备ID
            
        Returns:
            数据条数
        """
        if not self.redis_client:
            return 0
        
        try:
            key = self._get_key(device_id)
            return self.redis_client.llen(key)
        except Exception as e:
            print(f"❌ Redis获取数据量失败: {e}")
            return 0
    
    def clear_history(self, device_id: str) -> bool:
        """
        清除设备历史数据
        
        Args:
            device_id: 设备ID
            
        Returns:
            是否清除成功
        """
        if not self.redis_client:
            return False
        
        try:
            key = self._get_key(device_id)
            self.redis_client.delete(key)
            print(f"✅ 已清除设备 {device_id} 的历史数据")
            return True
        except Exception as e:
            print(f"❌ Redis清除数据失败: {e}")
            return False
    
    def batch_add_heart_rates(self, device_id: str, data_list: List[Dict]) -> bool:
        """
        批量添加心率数据
        
        Args:
            device_id: 设备ID
            data_list: 数据列表，每项包含 heart_rate 和 timestamp
            
        Returns:
            是否添加成功
        """
        if not self.redis_client:
            return False
        
        try:
            key = self._get_key(device_id)
            
            # 批量添加
            pipe = self.redis_client.pipeline()
            for data in data_list:
                if 'timestamp' not in data:
                    data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                pipe.rpush(key, json.dumps(data))
            
            # 保持列表长度
            max_count = REDIS_CONFIG.get('max_history_count', 60)
            pipe.ltrim(key, -max_count, -1)
            
            # 设置过期时间
            expire_time = REDIS_CONFIG.get('history_expire', 600)
            pipe.expire(key, expire_time)
            
            pipe.execute()
            
            print(f"✅ 批量添加 {len(data_list)} 条数据到Redis")
            return True
            
        except Exception as e:
            print(f"❌ Redis批量添加失败: {e}")
            return False
    
    def get_statistics(self, device_id: str) -> Optional[Dict]:
        """
        获取设备心率数据统计信息
        
        Args:
            device_id: 设备ID
            
        Returns:
            统计信息（平均值、最大值、最小值等）
        """
        values = self.get_heart_rate_values(device_id)
        
        if not values:
            return None
        
        import numpy as np
        
        return {
            'count': len(values),
            'mean': float(np.mean(values)),
            'std': float(np.std(values)),
            'min': float(np.min(values)),
            'max': float(np.max(values)),
            'latest': values[-1] if values else None
        }
    
    def close(self):
        """关闭Redis连接"""
        if self.redis_client:
            self.redis_client.close()
            print("📴 Redis连接已关闭")


if __name__ == "__main__":
    # 测试Redis存储
    storage = RedisStorage()
    
    # 测试添加数据
    device_id = "test_device_001"
    
    print("\n1. 添加单条数据:")
    storage.add_heart_rate(device_id, 75.0)
    storage.add_heart_rate(device_id, 78.0)
    storage.add_heart_rate(device_id, 82.0)
    
    print("\n2. 获取历史数据:")
    history = storage.get_recent_heart_rates(device_id)
    print(f"历史数据: {history}")
    
    print("\n3. 获取心率值:")
    values = storage.get_heart_rate_values(device_id)
    print(f"心率值: {values}")
    
    print("\n4. 数据统计:")
    stats = storage.get_statistics(device_id)
    print(f"统计信息: {stats}")
    
    print("\n5. 批量添加数据:")
    batch_data = [
        {'heart_rate': 85.0, 'timestamp': '2025-12-26 10:00:00'},
        {'heart_rate': 88.0, 'timestamp': '2025-12-26 10:00:10'},
        {'heart_rate': 90.0, 'timestamp': '2025-12-26 10:00:20'}
    ]
    storage.batch_add_heart_rates(device_id, batch_data)
    
    print("\n6. 获取数据量:")
    count = storage.get_history_count(device_id)
    print(f"数据总数: {count}")
    
    print("\n7. 清除数据:")
    storage.clear_history(device_id)
    
    storage.close()
