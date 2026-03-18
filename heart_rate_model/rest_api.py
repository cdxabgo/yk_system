"""
REST API服务 - 心率监测系统对外接口
提供HTTP接口供Java等外部程序调用
数据来源：直接从 yk_demo.employee_heart_rate 表读取，
          ML检测结果写入 yk_demo.ml_detection_result 表
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import time
import json
import os
import urllib.request
from datetime import datetime
from db_monitor import DbHeartRateMonitor
from typing import Dict, List

app = Flask(__name__)
CORS(app)  # 允许跨域访问

import urllib.parse

# Java后端地址（可选：用于将ML检测结果实时推送给前端SSE通道）
_raw_java_url = os.environ.get('JAVA_BACKEND_URL', 'http://localhost:8081').rstrip('/')
_parsed = urllib.parse.urlparse(_raw_java_url)
if _parsed.scheme not in ('http', 'https') or not _parsed.netloc:
    raise ValueError(
        f"JAVA_BACKEND_URL 格式无效: {_raw_java_url!r}。"
        "请设置为合法的 HTTP/HTTPS 地址，例如 http://localhost:8081"
    )
JAVA_BACKEND_URL = _raw_java_url

# 全局变量
monitor_instance: DbHeartRateMonitor = None
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

def on_detection_result(result: dict):
    """DbHeartRateMonitor 检测结果回调"""
    global monitoring_data

    monitoring_data['total_records'] += 1

    is_abnormal = result.get('is_abnormal', False)
    anomaly_type = result.get('anomaly_type')

    # 构造推送给 Java 后端的实时数据包（可选推送）
    push_payload = {
        'userId': str(result.get('employee_id', 'unknown')),
        'heartRate': result.get('heart_rate'),
        'dataTime': result.get('detect_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        'isAbnormal': is_abnormal,
        'anomalyType': anomaly_type,
        'severity': 'high' if is_abnormal else 'normal'
    }
    notify_java_backend(push_payload)

    # 更新内存监控数据
    monitoring_data['latest_data'].append(push_payload)
    if len(monitoring_data['latest_data']) > 10:
        monitoring_data['latest_data'] = monitoring_data['latest_data'][-10:]

    if is_abnormal:
        anomaly_record = {
            'timestamp': datetime.now().isoformat(),
            'employee_id': result.get('employee_id'),
            'heart_rate': result.get('heart_rate'),
            'anomaly_type': anomaly_type,
        }
        monitoring_data['anomalies'].append(anomaly_record)
        monitoring_data['anomaly_count'] += 1
        # 只保留最近50条异常
        if len(monitoring_data['anomalies']) > 50:
            monitoring_data['anomalies'] = monitoring_data['anomalies'][-50:]


def monitor_worker(interval: int, window_size: int):
    """监测工作线程（基于数据库轮询）"""
    global monitor_instance, is_monitoring, monitoring_data

    try:
        from config import DB_MONITOR_CONFIG
        monitor_instance = DbHeartRateMonitor(
            interval=interval,
            window_size=window_size,
        )
        monitor_instance.set_result_callback(on_detection_result)
        monitor_instance.start()

        # 阻塞直到停止标志
        while is_monitoring:
            time.sleep(1)

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
        'service': '心率监测系统（数据库模式）',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/monitor/start', methods=['POST'])
def start_monitoring():
    """
    启动监测（从数据库读取心率数据，ML检测后写入 ml_detection_result）

    请求体（可选，覆盖默认配置）:
    {
        "interval": 10,
        "window_size": 30
    }
    """
    global monitor_thread, is_monitoring, monitoring_data

    if is_monitoring:
        return jsonify({
            'success': False,
            'message': '监测已在运行中'
        }), 400

    from config import DB_MONITOR_CONFIG
    data = request.get_json() or {}
    interval = data.get('interval', DB_MONITOR_CONFIG.get('interval', 10))
    window_size = data.get('window_size', DB_MONITOR_CONFIG.get('window_size', 30))

    # 重置监测数据
    monitoring_data = {
        'status': 'running',
        'start_time': datetime.now().isoformat(),
        'latest_data': [],
        'anomaly_count': 0,
        'total_records': 0,
        'anomalies': [],
        'config': {
            'interval': interval,
            'window_size': window_size,
        }
    }

    is_monitoring = True
    monitor_thread = threading.Thread(
        target=monitor_worker,
        args=(interval, window_size),
        daemon=True
    )
    monitor_thread.start()

    return jsonify({
        'success': True,
        'message': '监测已启动（数据库模式）',
        'config': {
            'interval': interval,
            'window_size': window_size,
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


@app.route('/api/monitor/detect-once', methods=['POST'])
def detect_once():
    """
    立即对所有职工执行一次检测（不需要启动持续监测）
    """
    try:
        from config import DB_MONITOR_CONFIG
        m = DbHeartRateMonitor(
            interval=DB_MONITOR_CONFIG.get('interval', 10),
            window_size=DB_MONITOR_CONFIG.get('window_size', 30),
        )
        m.run_once()
        m.db.close()
        return jsonify({'success': True, 'message': '单次检测完成，结果已写入 ml_detection_result 表'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'检测失败: {str(e)}'}), 500


@app.route('/api/data/latest', methods=['GET'])
def get_latest_data():
    """
    获取内存中的最新检测数据

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
    获取异常记录（内存缓存）

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
    from config import DB_MONITOR_CONFIG, MODEL_CONFIG, FILTER_CONFIG

    return jsonify({
        'success': True,
        'config': {
            'db_monitor': DB_MONITOR_CONFIG,
            'model': MODEL_CONFIG,
            'filter': FILTER_CONFIG
        }
    })


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
    print("🚀 心率监测系统 REST API 服务（数据库模式）")
    print("=" * 60)
    print(f"📡 服务地址: http://{host}:{port}")
    print(f"📖 API文档: http://{host}:{port}/api/health")
    print("=" * 60)
    print("\n可用接口:")
    print("  GET  /api/health                  - 健康检查")
    print("  POST /api/monitor/start           - 启动监测（DB模式）")
    print("  POST /api/monitor/stop            - 停止监测")
    print("  GET  /api/monitor/status          - 获取状态")
    print("  POST /api/monitor/detect-once     - 立即执行单次检测")
    print("  GET  /api/data/latest             - 获取最新数据（内存）")
    print("  GET  /api/anomalies               - 获取异常记录（内存）")
    print("  GET  /api/anomalies/latest        - 获取最新异常（内存）")
    print("  GET  /api/config                  - 获取配置")
    print("  GET  /api/statistics              - 获取统计信息")
    print("=" * 60 + "\n")

    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    start_api_server(host='0.0.0.0', port=5000, debug=True)

