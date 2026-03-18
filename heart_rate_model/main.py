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
    print("\n【数据库轮询模式】🔥")
    print("  4. 数据库监测 - 定时从数据库读取心率并分析")
    print("  5. MQTT发送（已停用）")
    print("  6. MQTT演示（已停用）")
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
    """数据库轮询监测（保留函数名兼容旧菜单）"""
    from mqtt_handler import MQTTHeartRateMonitor
    
    print("\n" + "="*80)
    print("🗄️ 数据库轮询监测模式（v2.0）")
    print("="*80)
    
    poll_interval = input("\n请输入数据库轮询间隔（秒，默认5）: ").strip()
    poll_interval = int(poll_interval) if poll_interval else 5

    print(f"\n轮询间隔: {poll_interval} 秒")
    print("数据库: ✅ 已启用")
    print("\n💡 提示:")
    print("  - 本系统支持两种检测模式：")
    print("    1. 连续异常检测（数据充足时）")
    print("    2. 瞬时心率预警（数据较少时）")
    print("  - 每次从数据库 employee_heart_rate 读取新增数据")
    print("  - 异常记录自动写入 anomaly_records / daily_anomaly_stats")
    print("  - 按 Ctrl+C 停止监测\n")
    
    monitor = MQTTHeartRateMonitor(
        enable_redis=False,
        enable_db=True,
        poll_interval=poll_interval
    )
    print("按 Ctrl+C 停止监测\n")

    try:
        monitor.start()
    except KeyboardInterrupt:
        print("\n")
        monitor.stop()


def run_mqtt_sender():
    """MQTT发送（已停用）"""
    print("\n⚠️ MQTT模式已停用，请直接向数据库 employee_heart_rate 写入测试数据。")


def run_mqtt_demo():
    """MQTT演示（已停用）"""
    print("\n⚠️ MQTT模式已停用。请使用选项 4（数据库监测）并向数据库写入测试数据。")


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
