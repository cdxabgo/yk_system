"""
井下实时心率监测系统 - 主程序入口
整合所有功能的统一启动脚本
"""

import sys
import os

def show_menu():
    """显示主菜单"""
    print("\n" + "="*80)
    print("🏥 井下实时心率监测系统 v3.0")
    print("="*80)
    print("\n请选择运行模式:")
    print("\n【数据库监测模式】🔥 （推荐）")
    print("  1. 训练模型 - 生成模拟数据并训练LightGBM模型")
    print("  2. 数据库监测 - 从 employee_heart_rate 表读取数据，ML检测后写入 ml_detection_result 表")
    print("  3. 完整流程 - 训练模型 + 启动数据库监测")
    print("  4. 单次检测 - 立即对所有职工执行一次检测（不持续运行）")
    print("\n【模拟数据模式】")
    print("  5. 模拟监测 - 随机生成心率数据模拟实时监测（无需数据库）")
    print("\n【REST API服务】🆕")
    print("  6. 启动API服务 - 提供HTTP接口供Java等程序调用")
    print("\n【系统管理】⚙️")
    print("  D. 初始化数据库 - 创建 ml_detection_result 等表结构")
    print("  9. 查看使用说明")
    print("  0. 退出")
    print("="*80)


def run_train():
    """训练模型"""
    from integrated_system import IntegratedHeartRateMonitor

    print("\n" + "="*80)
    print("🤖 模型训练模式")
    print("="*80)

    batches = input("\n请输入训练批次数 (默认200): ").strip()
    batches = int(batches) if batches else 200

    system = IntegratedHeartRateMonitor()
    system.train_model(num_batches=batches)


def run_db_monitor():
    """数据库监测 - 从 employee_heart_rate 读取，写入 ml_detection_result"""
    from db_monitor import DbHeartRateMonitor
    from config import DB_MONITOR_CONFIG
    import time

    print("\n" + "="*80)
    print("🔍 数据库监测模式")
    print("="*80)
    print("\n数据流: employee_heart_rate → ML检测 → ml_detection_result → 前端")

    interval_str = input(f"\n请输入轮询间隔（秒，默认{DB_MONITOR_CONFIG['interval']}）: ").strip()
    interval = int(interval_str) if interval_str else DB_MONITOR_CONFIG['interval']

    window_str = input(f"请输入滑动窗口大小（默认{DB_MONITOR_CONFIG['window_size']}）: ").strip()
    window_size = int(window_str) if window_str else DB_MONITOR_CONFIG['window_size']

    monitor = DbHeartRateMonitor(interval=interval, window_size=window_size)

    def on_result(result):
        if result.get('is_abnormal'):
            print(f"  ⚠️  employee_id={result['employee_id']} "
                  f"心率={result['heart_rate']}bpm "
                  f"异常={result['anomaly_type']}")

    monitor.set_result_callback(on_result)

    print(f"\n✅ 监测已启动（间隔={interval}s，窗口={window_size}条）")
    print("   检测结果将实时写入 ml_detection_result 表")
    print("   按 Ctrl+C 停止监测\n")

    try:
        monitor.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n")
        monitor.stop()


def run_complete():
    """完整流程：训练模型 + 启动数据库监测"""
    from integrated_system import IntegratedHeartRateMonitor
    from db_monitor import DbHeartRateMonitor
    import time

    print("\n" + "="*80)
    print("🔄 完整流程模式")
    print("="*80)

    system = IntegratedHeartRateMonitor()

    # Step 1: 训练模型
    print("\n" + "="*80)
    print("Step 1: 模型训练")
    print("="*80)
    system.train_model(num_batches=50)

    input("\n✓ 训练完成！按 Enter 键启动数据库监测...")

    # Step 2: 数据库监测
    print("\n" + "="*80)
    print("Step 2: 数据库监测")
    print("="*80)
    monitor = DbHeartRateMonitor()
    print("   按 Ctrl+C 停止监测\n")

    try:
        monitor.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n")
        monitor.stop()


def run_detect_once():
    """单次检测：对所有职工立即执行一次检测"""
    from db_monitor import DbHeartRateMonitor

    print("\n" + "="*80)
    print("🎯 单次检测模式")
    print("="*80)
    print("\n对数据库中所有职工执行一次心率检测，结果写入 ml_detection_result 表...\n")

    monitor = DbHeartRateMonitor()
    monitor.run_once()
    monitor.db.close()

    print("\n✅ 单次检测完成！")
    print("   检测结果已写入 yk_demo.ml_detection_result 表")
    print("   可通过 Java 后端 /api/heartRate/latest 接口查看前端实时监测结果")


def run_simulate_monitor():
    """模拟数据实时监测"""
    from integrated_system import IntegratedHeartRateMonitor

    print("\n" + "="*80)
    print("🔍 模拟数据监测模式")
    print("="*80)

    interval = input("\n请输入监测间隔（秒，默认10）: ").strip()
    interval = int(interval) if interval else 10

    system = IntegratedHeartRateMonitor()

    if not os.path.exists("output/models/lgbm_model.pkl"):
        print("\n⚠️  未发现训练好的模型")
        if input("是否先训练模型? (y/n): ").lower() == 'y':
            system.train_model(num_batches=100)
        else:
            print("将仅使用规则检测")
    else:
        system.ml_detector.load_model("output/models/lgbm_model.pkl")

    system.real_time_monitor(interval=interval)


def run_api_server():
    """启动REST API服务"""
    from rest_api import start_api_server

    print("\n" + "="*80)
    print("🚀 REST API服务启动（数据库模式）")
    print("="*80)
    print("\n💡 提示:")
    print("  - 服务地址: http://localhost:5000")
    print("  - 启动监测: POST http://localhost:5000/api/monitor/start")
    print("  - 单次检测: POST http://localhost:5000/api/monitor/detect-once")
    print("  - 按 Ctrl+C 停止服务")
    print("\n" + "="*80 + "\n")

    start_api_server(host='0.0.0.0', port=5000, debug=False)


def show_help():
    """显示使用说明"""
    print("\n" + "="*80)
    print("📖 使用说明")
    print("="*80)
    print("""
系统架构（数据库模式）:
  1. 心率传感器/模拟器 → 写入 yk_demo.employee_heart_rate 表
  2. Python ML模型     → 读取 employee_heart_rate，经模型检测
  3.                   → 将结果写入 yk_demo.ml_detection_result 表
  4. Java 后端         → 读取 ml_detection_result，通过 /api/heartRate/latest 暴露
  5. Vue 前端          → 每10秒轮询 /api/heartRate/latest，展示实时状态与异常

快速开始:
  第一步: 选择 D 初始化数据库（创建 ml_detection_result 表）
  第二步: 选择 1 训练模型（可选，有模型效果更好）
  第三步: 选择 2 启动数据库监测
  或者:   选择 3 一步完成训练+监测

数据库表说明:
  - employee_heart_rate  : 原始心率数据表（输入源）
  - ml_detection_result  : ML检测结果表（输出，前端读取此表）

更新数据库 SQL:
  执行 backend/src/main/resources/sql/migration_v4.sql
""")
    print("="*80)


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
        print("\n创建/确认的表:")
        print("  - device_status       (设备状态表)")
        print("  - anomaly_records     (异常记录表)")
        print("  - daily_anomaly_stats (每日异常统计表)")
        print("  - ml_detection_result (ML检测结果表) ← 新增")
    except Exception as e:
        print(f"\n❌ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    while True:
        show_menu()
        choice = input("\n请输入选项 (0-9/D): ").strip().upper()

        try:
            if choice == '1':
                run_train()
            elif choice == '2':
                run_db_monitor()
            elif choice == '3':
                run_complete()
            elif choice == '4':
                run_detect_once()
            elif choice == '5':
                run_simulate_monitor()
            elif choice == '6':
                run_api_server()
            elif choice == 'D':
                init_database()
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

