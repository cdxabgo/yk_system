"""
REST API服务 - 心率监测系统对外接口
提供HTTP接口供Java等外部程序调用
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import time
import json
import os
from datetime import datetime
from mqtt_handler import MQTTHeartRateMonitor
from typing import Dict, List

app = Flask(__name__)
CORS(app)  # 允许跨域访问

# 全局变量
monitor_instance = None
monitor_thread = None
is_monitoring = False
monitoring_data = {
    'status': 'stopped',
    'start_time': None,
    'latest_data': [],
    'anomaly_count': 0,
    'total_records': 0,
    'anomalies': []  # 存储最近的异常记录
}

# ==================== 辅助函数 ====================

def monitor_worker(broker: str, port: int, topics: List[str]):
    """监测工作线程"""
    global monitor_instance, is_monitoring, monitoring_data
    
    try:
        monitor_instance = MQTTHeartRateMonitor(mqtt_broker=broker, mqtt_port=port)
        
        # 设置数据回调
        def on_data_callback(data_info):
            """数据回调处理"""
            monitoring_data['latest_data'] = data_info.get('filtered_data', [])[-10:]  # 保留最新10条
            monitoring_data['total_records'] += len(data_info.get('filtered_data', []))
            
            # 检测异常
            if data_info.get('ml_anomalies') or data_info.get('rule_anomalies'):
                anomaly_record = {
                    'timestamp': datetime.now().isoformat(),
                    'user_id': data_info.get('user_id', 'unknown'),
                    'ml_anomalies': data_info.get('ml_anomalies', []),
                    'rule_anomalies': data_info.get('rule_anomalies', [])
                }
                monitoring_data['anomalies'].append(anomaly_record)
                monitoring_data['anomaly_count'] += 1
                
                # 只保留最近50条异常
                if len(monitoring_data['anomalies']) > 50:
                    monitoring_data['anomalies'] = monitoring_data['anomalies'][-50:]
        
        monitor_instance.set_data_callback(on_data_callback)
        
        # 订阅主题
        for topic in topics:
            monitor_instance.subscribe(topic)
        
        # 启动监测
        monitor_instance.start()
        
    except Exception as e:
        monitoring_data['status'] = 'error'
        monitoring_data['error_message'] = str(e)
        is_monitoring = False


# ==================== API接口 ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'ok',
        'service': '心率监测系统',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/monitor/start', methods=['POST'])
def start_monitoring():
    """
    启动监测
    
    请求体:
    {
        "broker": "localhost",
        "port": 1883,
        "topics": ["/bdohs/data/#"]
    }
    """
    global monitor_thread, is_monitoring, monitoring_data
    
    if is_monitoring:
        return jsonify({
            'success': False,
            'message': '监测已在运行中'
        }), 400
    
    data = request.get_json()
    broker = data.get('broker', 'localhost')
    port = data.get('port', 1883)
    topics = data.get('topics', ['/bdohs/data/#'])
    
    # 重置监测数据
    monitoring_data = {
        'status': 'running',
        'start_time': datetime.now().isoformat(),
        'latest_data': [],
        'anomaly_count': 0,
        'total_records': 0,
        'anomalies': [],
        'config': {
            'broker': broker,
            'port': port,
            'topics': topics
        }
    }
    
    # 启动监测线程
    is_monitoring = True
    monitor_thread = threading.Thread(
        target=monitor_worker,
        args=(broker, port, topics),
        daemon=True
    )
    monitor_thread.start()
    
    return jsonify({
        'success': True,
        'message': '监测已启动',
        'config': {
            'broker': broker,
            'port': port,
            'topics': topics
        }
    })


@app.route('/api/monitor/stop', methods=['POST'])
def stop_monitoring():
    """停止监测"""
    global monitor_instance, is_monitoring, monitoring_data
    
    if not is_monitoring:
        return jsonify({
            'success': False,
            'message': '监测未运行'
        }), 400
    
    if monitor_instance:
        monitor_instance.stop()
    
    is_monitoring = False
    monitoring_data['status'] = 'stopped'
    
    return jsonify({
        'success': True,
        'message': '监测已停止'
    })


@app.route('/api/monitor/status', methods=['GET'])
def get_status():
    """获取监测状态"""
    return jsonify({
        'success': True,
        'data': {
            'status': monitoring_data.get('status'),
            'is_monitoring': is_monitoring,
            'start_time': monitoring_data.get('start_time'),
            'total_records': monitoring_data.get('total_records'),
            'anomaly_count': monitoring_data.get('anomaly_count'),
            'config': monitoring_data.get('config', {})
        }
    })


@app.route('/api/data/latest', methods=['GET'])
def get_latest_data():
    """
    获取最新数据
    
    查询参数:
    - limit: 返回数据条数（默认10）
    """
    limit = request.args.get('limit', 10, type=int)
    latest = monitoring_data.get('latest_data', [])[-limit:]
    
    return jsonify({
        'success': True,
        'data': latest,
        'count': len(latest),
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/anomalies', methods=['GET'])
def get_anomalies():
    """
    获取异常记录
    
    查询参数:
    - limit: 返回记录条数（默认20）
    """
    limit = request.args.get('limit', 20, type=int)
    anomalies = monitoring_data.get('anomalies', [])[-limit:]
    
    return jsonify({
        'success': True,
        'data': anomalies,
        'count': len(anomalies),
        'total_anomaly_count': monitoring_data.get('anomaly_count', 0)
    })


@app.route('/api/anomalies/latest', methods=['GET'])
def get_latest_anomaly():
    """获取最新的异常记录"""
    anomalies = monitoring_data.get('anomalies', [])
    
    if not anomalies:
        return jsonify({
            'success': True,
            'data': None,
            'message': '暂无异常记录'
        })
    
    return jsonify({
        'success': True,
        'data': anomalies[-1]
    })


@app.route('/api/config', methods=['GET'])
def get_config():
    """获取当前配置"""
    from config import MQTT_CONFIG, MODEL_CONFIG, FILTER_CONFIG
    
    return jsonify({
        'success': True,
        'config': {
            'mqtt': MQTT_CONFIG,
            'model': MODEL_CONFIG,
            'filter': FILTER_CONFIG
        }
    })


@app.route('/api/config/mqtt', methods=['POST'])
def update_mqtt_config():
    """
    更新MQTT配置（需要重启监测才生效）
    
    请求体:
    {
        "broker": "mqtt.example.com",
        "port": 1883,
        "username": "user",
        "password": "pass",
        "topics": ["/bdohs/data/#"]
    }
    """
    data = request.get_json()
    
    # 验证必要参数
    if 'broker' not in data:
        return jsonify({
            'success': False,
            'message': '缺少broker参数'
        }), 400
    
    # 更新配置文件
    try:
        from config import MQTT_CONFIG
        MQTT_CONFIG.update(data)
        
        return jsonify({
            'success': True,
            'message': '配置已更新，请重启监测使其生效',
            'config': MQTT_CONFIG
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'配置更新失败: {str(e)}'
        }), 500


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """获取统计信息"""
    start_time = monitoring_data.get('start_time')
    if start_time:
        start_dt = datetime.fromisoformat(start_time)
        running_time = (datetime.now() - start_dt).total_seconds()
    else:
        running_time = 0
    
    total_records = monitoring_data.get('total_records', 0)
    anomaly_count = monitoring_data.get('anomaly_count', 0)
    
    return jsonify({
        'success': True,
        'statistics': {
            'running_time_seconds': running_time,
            'total_records': total_records,
            'anomaly_count': anomaly_count,
            'anomaly_rate': (anomaly_count / total_records * 100) if total_records > 0 else 0,
            'records_per_minute': (total_records / running_time * 60) if running_time > 0 else 0
        }
    })


@app.route('/api/test/send', methods=['POST'])
def test_send_data():
    """
    测试接口：发送模拟数据到MQTT
    
    请求体:
    {
        "broker": "localhost",
        "port": 1883,
        "topic": "/bdohs/data/test",
        "user_id": "TEST001",
        "count": 18
    }
    """
    data = request.get_json()
    
    try:
        from mqtt_sender import send_test_data
        
        broker = data.get('broker', 'localhost')
        port = data.get('port', 1883)
        topic = data.get('topic', '/bdohs/data/test')
        user_id = data.get('user_id', 'TEST001')
        count = data.get('count', 18)
        
        # 发送测试数据
        send_test_data(
            broker=broker,
            port=port,
            topic=topic,
            user_id=user_id,
            data_count=count
        )
        
        return jsonify({
            'success': True,
            'message': f'已发送{count}条测试数据到主题{topic}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'发送失败: {str(e)}'
        }), 500


# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'API接口不存在'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': '服务器内部错误'
    }), 500


# ==================== 主函数 ====================

def start_api_server(host='0.0.0.0', port=5000, debug=False):
    """启动API服务器"""
    print("\n" + "=" * 60)
    print("🚀 心率监测系统 REST API 服务")
    print("=" * 60)
    print(f"📡 服务地址: http://{host}:{port}")
    print(f"📖 API文档: http://{host}:{port}/api/health")
    print("=" * 60)
    print("\n可用接口:")
    print("  GET  /api/health              - 健康检查")
    print("  POST /api/monitor/start       - 启动监测")
    print("  POST /api/monitor/stop        - 停止监测")
    print("  GET  /api/monitor/status      - 获取状态")
    print("  GET  /api/data/latest         - 获取最新数据")
    print("  GET  /api/anomalies           - 获取异常记录")
    print("  GET  /api/anomalies/latest    - 获取最新异常")
    print("  GET  /api/config              - 获取配置")
    print("  POST /api/config/mqtt         - 更新MQTT配置")
    print("  GET  /api/statistics          - 获取统计信息")
    print("  POST /api/test/send           - 发送测试数据")
    print("=" * 60 + "\n")
    
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    start_api_server(host='0.0.0.0', port=5000, debug=True)
