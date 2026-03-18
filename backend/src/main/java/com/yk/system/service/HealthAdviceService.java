package com.yk.system.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.yk.system.entity.Employee;
import com.yk.system.entity.EmployeeHeartRate;
import com.yk.system.entity.HealthAdviceResult;
import com.yk.system.mapper.EmployeeHeartRateMapper;
import com.yk.system.mapper.EmployeeMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class HealthAdviceService {

    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();
    private static final HttpClient HTTP_CLIENT = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .build();

    @Autowired
    private EmployeeMapper employeeMapper;

    @Autowired
    private EmployeeHeartRateMapper employeeHeartRateMapper;

    @Value("${deepseek.api-url:https://api.deepseek.com/chat/completions}")
    private String deepseekApiUrl;

    @Value("${deepseek.api-key:}")
    private String deepseekApiKey;

    @Value("${deepseek.model:deepseek-reasoner}")
    private String deepseekModel;

    public HealthAdviceResult generateByEmployeeId(Long employeeId) {
        if (employeeId == null) {
            throw new IllegalArgumentException("employeeId 不能为空");
        }
        if (deepseekApiKey == null || deepseekApiKey.trim().isEmpty()) {
            throw new IllegalStateException("未配置 DeepSeek API Key，请设置 DEEPSEEK_API_KEY");
        }

        Employee employee = employeeMapper.getById(employeeId);
        if (employee == null) {
            throw new IllegalArgumentException("职工不存在");
        }

        List<EmployeeHeartRate> todayRates = employeeHeartRateMapper.getTodayByEmployeeId(employeeId);
        if (todayRates == null || todayRates.isEmpty()) {
            throw new IllegalArgumentException("该职工今日暂无心率数据");
        }

        String prompt = buildPrompt(employee, todayRates);
        String advice = callDeepSeek(prompt);

        HealthAdviceResult result = new HealthAdviceResult();
        result.setEmployeeId(employeeId);
        result.setEmployeeName(employee.getName());
        result.setTodaySampleCount(todayRates.size());
        result.setGeneratedAt(LocalDateTime.now());
        result.setAdvice(advice);
        return result;
    }

    static String buildPrompt(Employee employee, List<EmployeeHeartRate> todayRates) {
        String rateText = todayRates.stream()
                .map(rate -> String.format("%s 心率=%d 是否异常=%s",
                        rate.getCollectTime(),
                        rate.getHeartRate(),
                        Integer.valueOf(1).equals(rate.getIsAbnormal()) ? "是" : "否"))
                .collect(Collectors.joining("\n"));

        return "请基于以下井下职工信息与当天心率数据，给出健康建议。\n"
                + "要求：\n"
                + "1) 输出中文；\n"
                + "2) 先给出总体风险判断（低/中/高）；\n"
                + "3) 给出3-5条可执行建议；\n"
                + "4) 如存在异常心率，给出就医与复测建议；\n"
                + "5) 内容面向非专业人员，简洁明确。\n\n"
                + "【职工基本信息】\n"
                + "姓名: " + employee.getName() + "\n"
                + "年龄: " + employee.getAge() + "\n"
                + "岗位: " + employee.getJob() + "\n"
                + "工龄: " + employee.getWorkingYears() + "\n"
                + "联系方式: " + employee.getContactInformation() + "\n\n"
                + "【当天心率数据（按时间升序）】\n"
                + rateText;
    }

    private String callDeepSeek(String prompt) {
        try {
            Map<String, Object> body = new HashMap<>();
            body.put("model", deepseekModel);
            body.put("messages", List.of(
                    Map.of("role", "system", "content", "你是一名严谨的职业健康顾问。"),
                    Map.of("role", "user", "content", prompt)
            ));
            body.put("temperature", 0.3);
            String requestJson = OBJECT_MAPPER.writeValueAsString(body);

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(deepseekApiUrl))
                    .timeout(Duration.ofSeconds(30))
                    .header(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                    .header(HttpHeaders.AUTHORIZATION, "Bearer " + deepseekApiKey.trim())
                    .POST(HttpRequest.BodyPublishers.ofString(requestJson, StandardCharsets.UTF_8))
                    .build();

            HttpResponse<String> response = HTTP_CLIENT.send(request, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
            if (response.statusCode() < 200 || response.statusCode() >= 300) {
                throw new IllegalStateException("DeepSeek 调用失败，状态码: " + response.statusCode());
            }

            JsonNode root = OBJECT_MAPPER.readTree(response.body());
            JsonNode contentNode = root.path("choices").path(0).path("message").path("content");
            if (contentNode.isMissingNode() || contentNode.asText().trim().isEmpty()) {
                throw new IllegalStateException("DeepSeek 返回内容为空");
            }
            return contentNode.asText().trim();
        } catch (IllegalStateException e) {
            throw e;
        } catch (Exception e) {
            throw new IllegalStateException("生成健康建议失败: " + e.getMessage(), e);
        }
    }
}
