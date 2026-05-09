/**
 * 心率监测系统 - Java客户端
 * 使用Java 11+ HttpClient调用REST API
 */

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import com.google.gson.Gson;
import com.google.gson.JsonObject;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

public class HeartRateMonitorClient {
    
    private static final String BASE_URL = "http://localhost:5000";
    private final HttpClient client;
    private final Gson gson;
    
    public HeartRateMonitorClient() {
        this.client = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .build();
        this.gson = new Gson();
    }
    
    /**
     * 健康检查
     */
    public ApiResponse healthCheck() throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(BASE_URL + "/api/health"))
            .GET()
            .build();
            
        HttpResponse<String> response = client.send(
            request, 
            HttpResponse.BodyHandlers.ofString()
        );
        
        return gson.fromJson(response.body(), ApiResponse.class);
    }
    
    /**
     * 启动监测
     */
    public ApiResponse startMonitoring(MonitorConfig config) throws Exception {
        String jsonBody = gson.toJson(config);
        
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(BASE_URL + "/api/monitor/start"))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(jsonBody))
            .build();
            
        HttpResponse<String> response = client.send(
            request, 
            HttpResponse.BodyHandlers.ofString()
        );
        
        return gson.fromJson(response.body(), ApiResponse.class);
    }
    
    /**
     * 停止监测
     */
    public ApiResponse stopMonitoring() throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(BASE_URL + "/api/monitor/stop"))
            .POST(HttpRequest.BodyPublishers.noBody())
            .build();
            
        HttpResponse<String> response = client.send(
            request, 
            HttpResponse.BodyHandlers.ofString()
        );
        
        return gson.fromJson(response.body(), ApiResponse.class);
    }
    
    /**
     * 获取监测状态
     */
    public StatusResponse getStatus() throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(BASE_URL + "/api/monitor/status"))
            .GET()
            .build();
            
        HttpResponse<String> response = client.send(
            request, 
            HttpResponse.BodyHandlers.ofString()
        );
        
        return gson.fromJson(response.body(), StatusResponse.class);
    }
    
    /**
     * 获取最新数据
     */
    public DataResponse getLatestData(int limit) throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(BASE_URL + "/api/data/latest?limit=" + limit))
            .GET()
            .build();
            
        HttpResponse<String> response = client.send(
            request, 
            HttpResponse.BodyHandlers.ofString()
        );
        
        return gson.fromJson(response.body(), DataResponse.class);
    }
    
    /**
     * 获取异常记录
     */
    public AnomalyResponse getAnomalies(int limit) throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(BASE_URL + "/api/anomalies?limit=" + limit))
            .GET()
            .build();
            
        HttpResponse<String> response = client.send(
            request, 
            HttpResponse.BodyHandlers.ofString()
        );
        
        return gson.fromJson(response.body(), AnomalyResponse.class);
    }
    
    /**
     * 获取最新异常
     */
    public AnomalyResponse getLatestAnomaly() throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(BASE_URL + "/api/anomalies/latest"))
            .GET()
            .build();
            
        HttpResponse<String> response = client.send(
            request, 
            HttpResponse.BodyHandlers.ofString()
        );
        
        return gson.fromJson(response.body(), AnomalyResponse.class);
    }
    
    /**
     * 获取统计信息
     */
    public StatisticsResponse getStatistics() throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(BASE_URL + "/api/statistics"))
            .GET()
            .build();
            
        HttpResponse<String> response = client.send(
            request, 
            HttpResponse.BodyHandlers.ofString()
        );
        
        return gson.fromJson(response.body(), StatisticsResponse.class);
    }
    
    /**
     * 定时轮询异常数据
     */
    public void startAnomalyPolling(int intervalSeconds, AnomalyCallback callback) {
        ScheduledExecutorService executor = Executors.newScheduledThreadPool(1);
        
        executor.scheduleAtFixedRate(() -> {
            try {
                AnomalyResponse response = getLatestAnomaly();
                if (response.success && response.data != null) {
                    callback.onAnomalyDetected(response.data);
                }
            } catch (Exception e) {
                callback.onError(e);
            }
        }, 0, intervalSeconds, TimeUnit.SECONDS);
    }
    
    // ========== 数据模型 ==========
    
    public static class MonitorConfig {
        public String broker;
        public int port;
        public String[] topics;
        
        public MonitorConfig(String broker, int port, String[] topics) {
            this.broker = broker;
            this.port = port;
            this.topics = topics;
        }
    }
    
    public static class ApiResponse {
        public boolean success;
        public String message;
        public JsonObject config;
    }
    
    public static class StatusResponse {
        public boolean success;
        public StatusData data;
        
        public static class StatusData {
            public String status;
            public boolean is_monitoring;
            public String start_time;
            public int total_records;
            public int anomaly_count;
            public JsonObject config;
        }
    }
    
    public static class DataResponse {
        public boolean success;
        public HeartRateData[] data;
        public int count;
        public String timestamp;
        
        public static class HeartRateData {
            public double heart_rate;
            public String timestamp;
        }
    }
    
    public static class AnomalyResponse {
        public boolean success;
        public AnomalyData data;
        public int total_anomaly_count;
        
        public static class AnomalyData {
            public String timestamp;
            public String user_id;
            public int[] ml_anomalies;
            public RuleAnomaly[] rule_anomalies;
        }
        
        public static class RuleAnomaly {
            public String type;
            public String description;
        }
    }
    
    public static class StatisticsResponse {
        public boolean success;
        public Statistics statistics;
        
        public static class Statistics {
            public double running_time_seconds;
            public int total_records;
            public int anomaly_count;
            public double anomaly_rate;
            public double records_per_minute;
        }
    }
    
    // ========== 回调接口 ==========
    
    public interface AnomalyCallback {
        void onAnomalyDetected(AnomalyResponse.AnomalyData anomaly);
        void onError(Exception e);
    }
    
    // ========== 使用示例 ==========
    
    public static void main(String[] args) {
        try {
            HeartRateMonitorClient client = new HeartRateMonitorClient();
            
            System.out.println("========== 心率监测系统 Java客户端 ==========");
            
            // 1. 健康检查
            System.out.println("\n1. 健康检查...");
            ApiResponse healthResponse = client.healthCheck();
            System.out.println("状态: " + (healthResponse.success ? "正常" : "异常"));
            
            // 2. 启动监测
            System.out.println("\n2. 启动监测...");
            MonitorConfig config = new MonitorConfig(
                "localhost", 
                1883, 
                new String[]{"/bdohs/data/#"}
            );
            ApiResponse startResponse = client.startMonitoring(config);
            System.out.println("结果: " + startResponse.message);
            
            // 3. 等待数据收集
            System.out.println("\n3. 等待数据收集（10秒）...");
            Thread.sleep(10000);
            
            // 4. 获取监测状态
            System.out.println("\n4. 获取监测状态...");
            StatusResponse statusResponse = client.getStatus();
            if (statusResponse.success) {
                System.out.println("状态: " + statusResponse.data.status);
                System.out.println("总记录数: " + statusResponse.data.total_records);
                System.out.println("异常数: " + statusResponse.data.anomaly_count);
            }
            
            // 5. 获取最新数据
            System.out.println("\n5. 获取最新数据...");
            DataResponse dataResponse = client.getLatestData(5);
            if (dataResponse.success && dataResponse.data != null) {
                System.out.println("最新" + dataResponse.count + "条数据:");
                for (DataResponse.HeartRateData data : dataResponse.data) {
                    System.out.println("  心率: " + data.heart_rate + " 次/分钟");
                }
            }
            
            // 6. 获取统计信息
            System.out.println("\n6. 获取统计信息...");
            StatisticsResponse statsResponse = client.getStatistics();
            if (statsResponse.success) {
                System.out.println("运行时间: " + 
                    statsResponse.statistics.running_time_seconds + " 秒");
                System.out.println("异常率: " + 
                    String.format("%.2f%%", statsResponse.statistics.anomaly_rate));
                System.out.println("数据速率: " + 
                    String.format("%.2f", statsResponse.statistics.records_per_minute) + 
                    " 条/分钟");
            }
            
            // 7. 获取异常记录
            System.out.println("\n7. 获取异常记录...");
            AnomalyResponse anomalyResponse = client.getAnomalies(5);
            if (anomalyResponse.success && anomalyResponse.data != null) {
                System.out.println("发现异常:");
                System.out.println("  用户: " + anomalyResponse.data.user_id);
                System.out.println("  时间: " + anomalyResponse.data.timestamp);
                if (anomalyResponse.data.rule_anomalies != null) {
                    for (AnomalyResponse.RuleAnomaly rule : anomalyResponse.data.rule_anomalies) {
                        System.out.println("  类型: " + rule.type);
                        System.out.println("  描述: " + rule.description);
                    }
                }
            } else {
                System.out.println("暂无异常");
            }
            
            // 8. 启动异常轮询（可选）
            System.out.println("\n8. 启动异常轮询（每5秒检查一次）...");
            client.startAnomalyPolling(5, new AnomalyCallback() {
                @Override
                public void onAnomalyDetected(AnomalyResponse.AnomalyData anomaly) {
                    System.out.println("⚠️  检测到异常 - 用户: " + anomaly.user_id + 
                        ", 时间: " + anomaly.timestamp);
                }
                
                @Override
                public void onError(Exception e) {
                    System.err.println("轮询错误: " + e.getMessage());
                }
            });
            
            // 等待一段时间观察轮询
            Thread.sleep(30000);
            
            // 9. 停止监测
            System.out.println("\n9. 停止监测...");
            ApiResponse stopResponse = client.stopMonitoring();
            System.out.println("结果: " + stopResponse.message);
            
            System.out.println("\n========== 测试完成 ==========");
            
        } catch (Exception e) {
            System.err.println("错误: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
