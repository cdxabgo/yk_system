"""
井下实时心率监测系统 - 主程序入口
整合所有功能的统一启动脚本
"""

import sys
import os

def show_menu():
    """显示主菜单"""
    print("\n" + "="*80)
    print("🏥 井下实时心率监测系统 v2.0")
    print("="*80)
    print("\n请选择运行模式:")
    print("\n【模拟数据模式】")
    print("  1. 训练模型 - 生成模拟数据并训练LightGBM模型")
    print("  2. 实时监测 - 模拟数据实时监测演示")
    print("  3. 完整流程 - 训练 + 监测一体化")
    print("\n【MQTT数据模式】🔥")
    print("  4. MQTT监测 - 接收MQTT数据并分析（支持Redis+MySQL）")
    print("  5. MQTT发送 - 模拟发送MQTT测试数据")
    print("  6. MQTT演示 - 自动化完整演示")
    print("\n【REST API服务】🆕")
    print("  7. 启动API服务 - 提供HTTP接口供Java等程序调用")
    print("  8. 测试API - 测试API接口功能")
    print("\n【系统管理】⚙️")
    print("  D. 初始化数据库 - 创建数据库表结构")
    print("  R. 测试Redis连接")
    print("  9. 查看使用说明")
    print("  0. 退出")
    print("="*80)


def run_train():
    """训练模型"""
    from integrated_system import IntegratedHeartRateMonitor
    import argparse
    
    print("\n" + "="*80)
    print("🤖 模型训练模式")
    print("="*80)
    
    batches = input("\n请输入训练批次数 (默认200): ").strip()
    batches = int(batches) if batches else 200
    
    system = IntegratedHeartRateMonitor()
    system.train_model(num_batches=batches)


def run_monitor():
    """实时监测"""
    from integrated_system import IntegratedHeartRateMonitor
    
    print("\n" + "="*80)
    print("🔍 实时监测模式")
    print("="*80)
    
    interval = input("\n请输入监测间隔（秒，默认180）: ").strip()
    interval = int(interval) if interval else 180
    
    system = IntegratedHeartRateMonitor()
    
    # 检查模型
    if not os.path.exists("output/models/lgbm_model.pkl"):
        print("\n⚠️  未发现训练好的模型")
        if input("是否先训练模型? (y/n): ").lower() == 'y':
            system.train_model(num_batches=100)
        else:
            print("将仅使用规则检测")
    else:
        system.ml_detector.load_model("output/models/lgbm_model.pkl")
    
    system.real_time_monitor(interval=interval)


def run_complete():
    """完整流程"""
    from integrated_system import IntegratedHeartRateMonitor
    
    print("\n" + "="*80)
    print("🔄 完整流程模式")
    print("="*80)
    
    system = IntegratedHeartRateMonitor()
    
    # Step 1: 训练模型
    print("\n" + "="*80)
    print("Step 1: 模型训练")
    print("="*80)
    system.train_model(num_batches=50)
    
    input("\n✓ 训练完成！按 Enter 键开始实时监测...")
    
    # Step 2: 实时监测
    print("\n" + "="*80)
    print("Step 2: 实时监测")
    print("="*80)
    system.real_time_monitor(interval=10)


def run_mqtt_monitor():
    """MQTT监测"""
    from mqtt_handler import MQTTHeartRateMonitor
    
    print("\n" + "="*80)
    print("📡 MQTT监测模式（v2.0 - 支持Redis+MySQL）")
    print("="*80)
    
    broker = input("\n请输入MQTT服务器地址 (默认test.mosquitto.org): ").strip()
    broker = broker if broker else "test.mosquitto.org"
    
    port = input("请输入端口 (默认1883): ").strip()
    port = int(port) if port else 1883
    
    # 询问是否启用Redis和数据库
    enable_redis = input("\n是否启用Redis存储? (y/n, 默认y): ").strip().lower() != 'n'
    enable_db = input("是否启用数据库记录? (y/n, 默认y): ").strip().lower() != 'n'
    
    print(f"\n连接到: {broker}:{port}")
    print(f"Redis: {'✅ 已启用' if enable_redis else '❌ 未启用'}")
    print(f"数据库: {'✅ 已启用' if enable_db else '❌ 未启用'}")
    print("\n💡 提示:")
    print("  - 本系统支持两种检测模式：")
    print("    1. 连续异常检测（数据充足时）")
    print("    2. 瞬时心率预警（数据较少时）")
    print("  - 设备上线/离线状态会自动记录到数据库")
    print("  - 历史数据自动存储到Redis（近10分钟）")
    print("  - 按 Ctrl+C 停止监测\n")
    
    monitor = MQTTHeartRateMonitor(mqtt_broker=broker, mqtt_port=port, 
                                   enable_redis=enable_redis, enable_db=enable_db)
    print("按 Ctrl+C 停止监测\n")
    
    monitor = MQTTHeartRateMonitor(mqtt_broker=broker, mqtt_port=port)
    
    try:
        monitor.start()
    except KeyboardInterrupt:
        print("\n")
        monitor.stop()


def run_mqtt_sender():
    """MQTT发送"""
    import mqtt_sender
    mqtt_sender.main()


def run_mqtt_demo():
    """MQTT自动演示"""
    import threading
    import time
    from mqtt_handler import MQTTHeartRateMonitor
    from mqtt_sender import MQTTDataSender
    
    broker = "test.mosquitto.org"
    port = 1883
    
    print("\n" + "="*80)
    print("🎬 MQTT完整演示")
    print("="*80)
    print(f"\n📡 使用公共测试服务器: {broker}:{port}")
    print("💡 演示将自动启动监测和发送数据\n")
    
    # 检查模型
    from utils import SystemChecker
    SystemChecker.check_model()
    
    # 启动监测线程
    def start_monitor():
        time.sleep(2)
        print("\n🔍 启动监测系统...\n")
        monitor = MQTTHeartRateMonitor(mqtt_broker=broker, mqtt_port=port, 
                                       enable_redis=False, enable_db=False)
        try:
            monitor.start()
        except:
            pass
    
    # 启动发送线程
    def start_sender():
        time.sleep(4)
        print("\n📡 启动数据发送...\n")
        sender = MQTTDataSender(mqtt_broker=broker, mqtt_port=port)
        sender.connect()
        
        # 为每个用户发送数据
        for i in range(10):
            for user in sender.users:
                sender.send_batch_data(user, count=18)
            print(f"✅ 已发送第 {i+1}/10 批数据")
            time.sleep(5)
        
        sender.disconnect()
    
    # 启动线程
    monitor_thread = threading.Thread(target=start_monitor, daemon=True)
    sender_thread = threading.Thread(target=start_sender, daemon=True)
    
    monitor_thread.start()
    sender_thread.start()
    
    try:
        sender_thread.join()
        print("\n✅ 演示完成！")
        time.sleep(2)
    except KeyboardInterrupt:
        print("\n⏹️  演示已停止")


def show_help():
    """显示使用说明"""
    from utils import show_help
    show_help()


def run_api_server():
    """启动REST API服务"""
    from rest_api import start_api_server
    
    print("\n" + "="*80)
    print("🚀 REST API服务启动")
    print("="*80)
    print("\n💡 提示:")
    print("  - 服务地址: http://localhost:5000")
    print("  - API文档: http://localhost:5000/api/health")
    print("  - Java示例: 查看 Java调用示例/")
    print("  - 按 Ctrl+C 停止服务")
    print("\n" + "="*80 + "\n")
    
    start_api_server(host='0.0.0.0', port=5000, debug=False)


def run_api_test():
    """测试API"""
    from utils import APITester
    
    print("\n" + "="*80)
    print("🧪 API测试")
    print("="*80)
    print("\n💡 请确保API服务已启动")
    input("按回车键继续...\n")
    
    tester = APITester()
    tester.test_all()


def init_database():
    """初始化数据库"""
    print("\n" + "="*80)
    print("💾 数据库初始化")
    print("="*80)
    
    try:
        from database import init_database as db_init
        print("\n开始初始化数据库表...")
        db_init()
        print("\n✅ 数据库初始化成功！")
        print("\n创建的表:")
        print("  - device_status (设备状态表)")
        print("  - anomaly_records (异常记录表)")
        print("  - daily_anomaly_stats (每日异常统计表)")
    except Exception as e:
        print(f"\n❌ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()


def test_redis():
    """测试Redis连接"""
    print("\n" + "="*80)
    print("🔴 Redis连接测试")
    print("="*80)
    
    try:
        from redis_storage import RedisStorage
        print("\n正在连接Redis...")
        storage = RedisStorage()
        
        # 测试写入
        test_device = "test_device_001"
        storage.add_heart_rate(test_device, 75.0)
        
        # 测试读取
        values = storage.get_heart_rate_values(test_device)
        print(f"\n✅ Redis连接成功！")
        print(f"测试数据: {values}")
        
        # 清理测试数据
        storage.clear_history(test_device)
        storage.close()
        
    except Exception as e:
        print(f"\n❌ Redis连接失败: {e}")
        print("\n请确保:")
        print("  1. Redis服务已启动")
        print("  2. config.py 中配置正确")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    while True:
        show_menu()
        choice = input("\n请输入选项 (0-9/D/R): ").strip().upper()
        
        try:
            if choice == '1':
                run_train()
            elif choice == '2':
                run_monitor()
            elif choice == '3':
                run_complete()
            elif choice == '4':
                run_mqtt_monitor()
            elif choice == '5':
                run_mqtt_sender()
            elif choice == '6':
                run_mqtt_demo()
            elif choice == '7':
                run_api_server()
            elif choice == '8':
                run_api_test()
            elif choice == 'D':
                init_database()
            elif choice == 'R':
                test_redis()
            elif choice == '9':
                show_help()
            elif choice == '0':
                print("\n👋 感谢使用！再见！\n")
                sys.exit(0)
            else:
                print("\n❌ 无效选项，请重新选择")
        
        except KeyboardInterrupt:
            print("\n\n⏹️  操作已取消")
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            import traceback
            traceback.print_exc()
        
        input("\n按回车键继续...")


if __name__ == "__main__":
    main()
