# MQTT测试数据发送程序
# 模拟发送心率数据到MQTT服务器


import json
import time
import random
from datetime import datetime, timedelta
import paho.mqtt.client as mqtt


class MQTTDataSender:
    """MQTT测试数据发送器"""
    
    def __init__(self, mqtt_broker="localhost", mqtt_port=1883):
        """
        初始化MQTT发送器
        
        Args:
            mqtt_broker: MQTT服务器地址
            mqtt_port: MQTT服务器端口
        """
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        
        # MQTT客户端
        self.client = mqtt.Client(client_id="HeartRateSender_" + str(int(time.time())))
        
        # 用户配置
        self.users = [
            {'userId': 1830, 'deptId': 160, 'deviceId': 237},
            {'userId': 1831, 'deptId': 160, 'deviceId': 238},
        ]
    
    def connect(self):
        """连接到MQTT服务器"""
        try:
            self.client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.client.loop_start()
            print(f"✅ 已连接到MQTT服务器: {self.mqtt_broker}:{self.mqtt_port}")
            return True
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False
    
    def generate_heart_rate(self, base_rate=75, anomaly_prob=0.1):
        """
        生成心率数据
        
        Args:
            base_rate: 基础心率
            anomaly_prob: 异常概率
        
        Returns:
            心率值
        """
        if random.random() < anomaly_prob:
            # 生成异常数据
            anomaly_type = random.choice(['high', 'low', 'extreme'])
            if anomaly_type == 'high':
                return random.randint(150, 180)
            elif anomaly_type == 'low':
                return random.randint(45, 58)
            else:  # extreme
                return random.choice([random.randint(30, 40), random.randint(200, 220)])
        else:
            # 正常数据
            return int(random.gauss(base_rate, 10))
    
    def send_realtime_data(self, user_info, heart_rate):
        """
        发送实时数据（单条）
        
        Args:
            user_info: 用户信息
            heart_rate: 心率值
        """
        data = {
            "count": 0,
            "dataState": 1,
            "dataTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "dataVal": str(heart_rate),
            "deptId": user_info['deptId'],
            "deviceId": user_info['deviceId'],
            "params": {},
            "size": 0,
            "sortType": "DESC",
            "step": 0,
            "typeCode": "1001",
            "typeName": "心率",
            "typeUtil": "bpm",
            "userId": user_info['userId']
        }
        
        topic = f"/bdohs/data/{user_info['userId']}"
        payload = json.dumps(data, ensure_ascii=False)
        
        self.client.publish(topic, payload)
        print(f"📤 发送实时数据 -> {topic}: {heart_rate} bpm")
    
    def send_batch_data(self, user_info, count=18):
        """
        发送批量历史数据
        
        Args:
            user_info: 用户信息
            count: 数据条数
        """
        data_list = []
        base_time = datetime.now() - timedelta(minutes=3)
        
        for i in range(count):
            heart_rate = self.generate_heart_rate()
            data_time = (base_time + timedelta(seconds=i*10)).strftime("%Y-%m-%d %H:%M:%S")
            
            data = {
                "count": i,
                "dataState": 1,
                "dataTime": data_time,
                "dataVal": str(heart_rate),
                "deptId": user_info['deptId'],
                "deviceId": user_info['deviceId'],
                "params": {},
                "size": 0,
                "sortType": "DESC",
                "step": i,
                "typeCode": "1001",
                "typeName": "心率",
                "typeUtil": "bpm",
                "userId": user_info['userId']
            }
            data_list.append(data)
        
        topic = f"/bdohs/datalist/{user_info['userId']}"
        payload = json.dumps(data_list, ensure_ascii=False)
        
        self.client.publish(topic, payload)
        print(f"📦 发送批量数据 -> {topic}: {count} 条")
    
    def send_continuous_realtime(self, interval=10, duration=180):
        """
        持续发送实时数据
        
        Args:
            interval: 发送间隔（秒）
            duration: 持续时间（秒）
        """
        print(f"\n🔄 开始发送实时数据（间隔{interval}秒，持续{duration}秒）\n")
        
        start_time = time.time()
        count = 0
        
        while time.time() - start_time < duration:
            for user_info in self.users:
                heart_rate = self.generate_heart_rate()
                self.send_realtime_data(user_info, heart_rate)
                count += 1
            
            time.sleep(interval)
        
        print(f"\n✅ 已发送 {count} 条实时数据\n")
    
    def disconnect(self):
        """断开连接"""
        self.client.loop_stop()
        self.client.disconnect()
        print("✅ 已断开MQTT连接")


def main():
    """主函数"""
    print("\n" + "="*80)
    print("📡 MQTT心率数据发送测试程序")
    print("="*80 + "\n")
    
    # 配置MQTT服务器
    MQTT_BROKER = "localhost"  # 修改为实际的MQTT服务器地址
    MQTT_PORT = 1883
    
    sender = MQTTDataSender(mqtt_broker=MQTT_BROKER, mqtt_port=MQTT_PORT)
    
    # 连接到服务器
    if not sender.connect():
        return
    
    print("\n选择测试模式:")
    print("1. 发送批量历史数据（18条/批）")
    print("2. 发送实时数据（持续3分钟）")
    print("3. 混合模式（先批量后实时）")
    
    try:
        choice = input("\n请选择 (1/2/3): ").strip()
        
        if choice == '1':
            # 批量数据测试
            for user_info in sender.users:
                sender.send_batch_data(user_info, count=18)
                time.sleep(1)
        
        elif choice == '2':
            # 实时数据测试
            sender.send_continuous_realtime(interval=10, duration=180)
        
        elif choice == '3':
            # 混合模式
            print("\n第1阶段: 发送批量历史数据")
            for user_info in sender.users:
                sender.send_batch_data(user_info, count=18)
                time.sleep(1)
            
            print("\n第2阶段: 发送实时数据")
            sender.send_continuous_realtime(interval=10, duration=180)
        
        else:
            print("❌ 无效选择")
    
    except KeyboardInterrupt:
        print("\n\n⏹️  收到停止信号")
    
    finally:
        sender.disconnect()


if __name__ == "__main__":
    main()
