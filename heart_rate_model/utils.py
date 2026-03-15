"""
工具模块 - 辅助功能集合
包含系统检查、模型验证、API测试等常用功能
"""

import os
import sys
import importlib


class SystemChecker:
    """系统检查工具"""
    
    @staticmethod
    def check_dependencies():
        """检查依赖包"""
        print("\n" + "=" * 60)
        print("📦 检查依赖包")
        print("=" * 60)
        
        required = {
            'flask': 'Flask',
            'flask_cors': 'Flask-CORS',
            'numpy': 'NumPy',
            'pandas': 'Pandas',
            'scipy': 'SciPy',
            'sklearn': 'Scikit-learn',
            'lightgbm': 'LightGBM',
            'paho.mqtt': 'Paho-MQTT',
            'matplotlib': 'Matplotlib'
        }
        
        missing = []
        for module, name in required.items():
            try:
                importlib.import_module(module)
                print(f"✅ {name:20s} - 已安装")
            except ImportError:
                print(f"❌ {name:20s} - 未安装")
                missing.append(name)
        
        if missing:
            print(f"\n⚠️  缺少以下依赖包: {', '.join(missing)}")
            print("请运行: pip install -r requirements.txt")
            return False
        
        print("\n✅ 所有依赖包已安装")
        return True
    
    @staticmethod
    def check_files():
        """检查必要文件"""
        print("\n" + "=" * 60)
        print("📄 检查必要文件")
        print("=" * 60)
        
        required_files = [
            'rest_api.py',
            'mqtt_handler.py',
            'config.py',
            'data_filter.py',
            'enhanced_detector.py',
            'lgbm_model.py',
            'requirements.txt'
        ]
        
        missing = []
        for filename in required_files:
            if os.path.exists(filename):
                print(f"✅ {filename:30s} - 存在")
            else:
                print(f"❌ {filename:30s} - 缺失")
                missing.append(filename)
        
        if missing:
            print(f"\n⚠️  缺少以下文件: {', '.join(missing)}")
            return False
        
        print("\n✅ 所有必要文件存在")
        return True
    
    @staticmethod
    def check_configuration():
        """检查配置"""
        print("\n" + "=" * 60)
        print("⚙️  检查配置")
        print("=" * 60)
        
        try:
            from config import MQTT_CONFIG, MODEL_CONFIG, FILTER_CONFIG
            
            print(f"✅ MQTT配置:")
            print(f"   Broker: {MQTT_CONFIG.get('broker')}")
            print(f"   Port: {MQTT_CONFIG.get('port')}")
            
            print(f"\n✅ 模型配置:")
            print(f"   启用ML检测: {MODEL_CONFIG.get('enable_ml_detection')}")
            print(f"   启用规则检测: {MODEL_CONFIG.get('enable_rule_detection')}")
            
            print(f"\n✅ 滤波配置:")
            print(f"   心率范围: {FILTER_CONFIG.get('lower_bound')} - {FILTER_CONFIG.get('upper_bound')}")
            
            return True
        except Exception as e:
            print(f"❌ 配置检查失败: {e}")
            return False
    
    @staticmethod
    def check_model():
        """检查模型文件"""
        model_path = "output/models/lgbm_model.pkl"
        
        if os.path.exists(model_path):
            print(f"✅ 发现训练好的模型: {model_path}")
            return True
        
        print(f"⚠️  未发现模型文件: {model_path}")
        print("   将仅使用规则检测")
        return False
    
    @staticmethod
    def verify_all():
        """完整系统验证"""
        print("\n" + "=" * 80)
        print("🔍 井下心率监测系统 - 完整验证")
        print("=" * 80)
        
        checks = [
            ("依赖包", SystemChecker.check_dependencies),
            ("必要文件", SystemChecker.check_files),
            ("配置", SystemChecker.check_configuration),
            ("模型文件", SystemChecker.check_model)
        ]
        
        results = []
        for name, check_func in checks:
            try:
                result = check_func()
                results.append((name, result))
            except Exception as e:
                print(f"\n❌ {name}检查出错: {e}")
                results.append((name, False))
        
        # 总结
        print("\n" + "=" * 60)
        print("📊 验证总结")
        print("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{status} - {name}")
        
        print("\n" + "=" * 60)
        print(f"总计: {passed}/{total} 项通过")
        print("=" * 60)
        
        return passed == total


class APITester:
    """API测试工具"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        
    def test_all(self):
        """测试所有API接口"""
        import requests
        import time
        
        print("\n" + "=" * 80)
        print("🧪 REST API 测试")
        print("=" * 80)
        
        tests = [
            ("健康检查", "GET", "/api/health", None),
            ("获取配置", "GET", "/api/config", None),
            ("启动监测", "POST", "/api/monitor/start", {
                "broker": "localhost", 
                "port": 1883,
                "topics": ["/bdohs/data/#"]
            }),
            ("获取状态", "GET", "/api/monitor/status", None),
            ("获取最新数据", "GET", "/api/data/latest?limit=5", None),
            ("获取异常记录", "GET", "/api/anomalies?limit=5", None),
        ]
        
        results = []
        
        for i, (name, method, endpoint, data) in enumerate(tests, 1):
            print(f"\n{i}️⃣  测试{name}...")
            try:
                url = f"{self.base_url}{endpoint}"
                
                if method == "GET":
                    response = requests.get(url, timeout=5)
                else:
                    response = requests.post(url, json=data, timeout=5)
                
                print(f"   状态码: {response.status_code}")
                result = response.json()
                
                if 'message' in result:
                    print(f"   响应: {result['message']}")
                elif 'count' in result:
                    print(f"   数据条数: {result['count']}")
                
                success = response.status_code in [200, 400]  # 400可能是已在运行
                results.append((name, success))
                print("   ✅ 通过" if success else "   ❌ 失败")
                
                # 等待一下
                if i == 3:
                    time.sleep(2)
                    
            except Exception as e:
                print(f"   ❌ 失败: {e}")
                results.append((name, False))
        
        # 总结
        print("\n" + "=" * 80)
        print("📊 测试总结")
        print("=" * 80)
        
        passed = sum(1 for _, success in results if success)
        total = len(results)
        
        for name, success in results:
            status = "✅ 通过" if success else "❌ 失败"
            print(f"{status} - {name}")
        
        print(f"\n总计: {passed}/{total} 项通过")
        print("=" * 80)
        
        return passed == total


def show_help():
    """显示使用说明"""
    help_text = """
╔════════════════════════════════════════════════════════════════════════════╗
║                     井下实时心率监测系统 - 使用说明                        ║
╚════════════════════════════════════════════════════════════════════════════╝

【快速开始】

  1. 验证系统环境:
     python utils.py verify

  2. 测试API接口:
     python utils.py test

  3. 运行主程序:
     python main.py

【目录结构】

  核心模块:
    - config.py              配置管理
    - data_generator.py      数据生成器
    - data_filter.py         数据滤波器
    - enhanced_detector.py   规则检测器
    - lgbm_model.py          机器学习模型
    - mqtt_handler.py        MQTT处理器
    - integrated_system.py   集成系统
    - rest_api.py            REST API服务
    - main.py                主程序入口
    - utils.py               工具模块

  辅助文件:
    - mqtt_sender.py         MQTT数据发送器
    - requirements.txt       依赖清单

【配置文件】

  config.py 包含:
    - MQTT_CONFIG: MQTT服务器配置
    - MODEL_CONFIG: 模型参数配置
    - FILTER_CONFIG: 滤波器配置
    - RULE_CONFIG: 异常检测规则

【常见问题】

  Q: 如何训练模型?
  A: python main.py → 选择选项1

  Q: 如何启动MQTT监测?
  A: python main.py → 选择选项4

  Q: 如何启动API服务?
  A: python main.py → 选择选项7
     或 python rest_api.py

  Q: 缺少依赖包?
  A: pip install -r requirements.txt

  Q: 模型文件不存在?
  A: 先训练模型或使用规则检测模式

【技术支持】

  详细文档: README.md
  API文档: REST_API使用说明.md
  MQTT文档: MQTT使用说明.md
  项目结构: PROJECT_STRUCTURE.md

╚════════════════════════════════════════════════════════════════════════════╝
"""
    print(help_text)


if __name__ == '__main__':
    """命令行工具入口"""
    if len(sys.argv) < 2:
        print("用法: python utils.py [verify|test|help]")
        print("  verify - 验证系统环境")
        print("  test   - 测试API接口")
        print("  help   - 显示帮助信息")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'verify':
        success = SystemChecker.verify_all()
        sys.exit(0 if success else 1)
    
    elif command == 'test':
        tester = APITester()
        success = tester.test_all()
        sys.exit(0 if success else 1)
    
    elif command == 'help':
        show_help()
        sys.exit(0)
    
    else:
        print(f"未知命令: {command}")
        print("用法: python utils.py [verify|test|help]")
        sys.exit(1)
