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
import urllib.request
from datetime import datetime
from mqtt_handler import MQTTHeartRateMonitor
from typing import Dict

app = Flask(__name__)
CORS(app)  # 允许跨域访问

import urllib.parse

# Java后端地址（用于将ML检测结果实时推送给前端）
_raw_java_url = os.environ.get('JAVA_BACKEND_URL', 'http://localhost:8081').rstrip('/')
_parsed = urllib.parse.urlparse(_raw_java_url)
if _parsed.scheme not in ('http', 'https') or not _parsed.netloc:
    raise ValueError(
        f"JAVA_BACKEND_URL 格式无效: {_raw_java_url!r}。"
        "请设置为合法的 HTTP/HTTPS 地址，例如 http://localhost:8081"
    )
JAVA_BACKEND_URL = _raw_java_url

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


def notify_java_backend(payload: dict):
    """
    将心率检测结果推送至 Java 后端（/api/realtime/push），
    Java 后端再通过 SSE 广播给所有在线前端客户端。
    推送失败时静默忽略，不影响主监测流程。
    """
    try:
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        req = urllib.request.Request(
            f"{JAVA_BACKEND_URL}/api/realtime/push",
            data=data,
            headers={'Content-Type': 'application/json; charset=utf-8'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=2):
            pass
    except Exception:
        pass  # 推送失败不影响主流程


# ==================== 辅助函数 ====================

def monitor_worker(poll_interval: int):
    """监测工作线程"""
    global monitor_instance, is_monitoring, monitoring_data
    
    try:
        monitor_instance = MQTTHeartRateMonitor(
            enable_redis=False,
            enable_db=True,
            poll_interval=poll_interval
        )
        
        # 设置数据回调
        def on_data_callback(data_info):
            """数据回调处理"""
            monitoring_data['latest_data'] = data_info.get('filtered_data', [])[-10:]  # 保留最新10条
            monitoring_data['total_records'] += len(data_info.get('filtered_data', []))

            ml_anomalies = data_info.get('ml_anomalies') or []
            rule_anomalies = data_info.get('rule_anomalies') or {}
            is_abnormal = bool(ml_anomalies or rule_anomalies)

            # 构造异常类型描述
            anomaly_type = None
            if is_abnormal:
                parts = []
                if ml_anomalies:
                    parts.append(', '.join(str(a) for a in ml_anomalies))
                if rule_anomalies and isinstance(rule_anomalies, dict):
                    rule_keys = [k for k, v in rule_anomalies.items() if v]
                    if rule_keys:
                        parts.append(', '.join(rule_keys))
                elif rule_anomalies:
                    parts.append(str(rule_anomalies))
                anomaly_type = '; '.join(parts) if parts else '异常'

            # 构造推送给 Java 后端的实时数据包
            push_payload = {
                'userId': data_info.get('user_id', 'unknown'),
                'heartRate': data_info.get('heart_rate'),
                'dataTime': data_info.get('data_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                'isAbnormal': is_abnormal,
                'anomalyType': anomaly_type,
                'severity': 'high' if is_abnormal else 'normal'
            }
            notify_java_backend(push_payload)

            # 检测异常
            if is_abnormal:
                anomaly_record = {
                    'timestamp': datetime.now().isoformat(),
                    'user_id': data_info.get('user_id', 'unknown'),
                    'ml_anomalies': ml_anomalies,
                    'rule_anomalies': rule_anomalies
                }
                monitoring_data['anomalies'].append(anomaly_record)
                monitoring_data['anomaly_count'] += 1

                # 只保留最近50条异常
                if len(monitoring_data['anomalies']) > 50:
                    monitoring_data['anomalies'] = monitoring_data['anomalies'][-50:]
        
        monitor_instance.set_data_callback(on_data_callback)
        
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
        "poll_interval": 5
    }
    """
    global monitor_thread, is_monitoring, monitoring_data
    
    if is_monitoring:
        return jsonify({
            'success': False,
            'message': '监测已在运行中'
        }), 400
    
    from config import MONITOR_CONFIG
    data = request.get_json() or {}
    poll_interval = data.get('poll_interval', MONITOR_CONFIG.get('poll_interval', 5))
    
    # 重置监测数据
    monitoring_data = {
        'status': 'running',
        'start_time': datetime.now().isoformat(),
        'latest_data': [],
        'anomaly_count': 0,
        'total_records': 0,
        'anomalies': [],
        'config': {
            'poll_interval': poll_interval
        }
    }
    
    # 启动监测线程
    is_monitoring = True
    monitor_thread = threading.Thread(
        target=monitor_worker,
        args=(poll_interval,),
        daemon=True
    )
    monitor_thread.start()
    
    return jsonify({
        'success': True,
        'message': '监测已启动',
        'config': {
            'poll_interval': poll_interval
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
    from config import MONITOR_CONFIG, MODEL_CONFIG, FILTER_CONFIG
    
    return jsonify({
        'success': True,
        'config': {
            'monitor': MONITOR_CONFIG,
            'model': MODEL_CONFIG,
            'filter': FILTER_CONFIG
        }
    })


@app.route('/api/config/mqtt', methods=['POST'])
def update_mqtt_config():
    """
    更新轮询配置（兼容旧接口路径，需重启监测生效）
    
    请求体:
    {
        "poll_interval": 5,
        "poll_batch_size": 100
    }
    """
    data = request.get_json()
    
    # 验证必要参数
    if not data:
        return jsonify({
            'success': False,
            'message': '缺少配置参数'
        }), 400
    
    # 更新配置文件
    try:
        from config import MONITOR_CONFIG
        MONITOR_CONFIG.update(data)
        
        return jsonify({
            'success': True,
            'message': '配置已更新，请重启监测使其生效',
            'config': MONITOR_CONFIG
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
    测试接口（兼容保留）：MQTT模式已停用
    """
    return jsonify({
        'success': False,
        'message': 'MQTT模式已停用，请直接向数据库 employee_heart_rate 写入测试数据'
    }), 400


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
    print("  POST /api/config/mqtt         - 更新轮询配置（兼容路径）")
    print("  GET  /api/statistics          - 获取统计信息")
    print("  POST /api/test/send           - 测试接口（MQTT已停用）")
    print("=" * 60 + "\n")
    
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    start_api_server(host='0.0.0.0', port=5000, debug=True)
