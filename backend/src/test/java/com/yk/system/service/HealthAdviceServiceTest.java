package com.yk.system.service;

import com.yk.system.entity.Employee;
import com.yk.system.entity.EmployeeHeartRate;
import org.junit.jupiter.api.Test;

import java.time.LocalDateTime;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class HealthAdviceServiceTest {

    @Test
    void shouldBuildPromptWithEmployeeAndTodayRates() {
        Employee employee = new Employee();
        employee.setName("张三");
        employee.setAge(35);
        employee.setJob("矿工");
        employee.setWorkingYears(5);
        employee.setContactInformation("13800000001");

        EmployeeHeartRate rate = new EmployeeHeartRate();
        rate.setCollectTime(LocalDateTime.of(2026, 3, 18, 9, 30));
        rate.setHeartRate(102);
        rate.setIsAbnormal(1);

        String prompt = HealthAdviceService.buildPrompt(employee, List.of(rate));

        assertTrue(prompt.contains("姓名: 张三"));
        assertTrue(prompt.contains("岗位: 矿工"));
        assertTrue(prompt.contains("心率=102"));
        assertTrue(prompt.contains("是否异常=是"));
    }

    @Test
    void shouldResolveDeepSeekApiUrlWhenConfiguredWithV1Base() {
        String resolved = HealthAdviceService.resolveDeepSeekApiUrl("https://api.deepseek.com/v1");
        assertEquals("https://api.deepseek.com/v1/chat/completions", resolved);
    }

    @Test
    void shouldKeepDeepSeekApiUrlWhenConfiguredWithCompletionsPath() {
        String resolved = HealthAdviceService.resolveDeepSeekApiUrl("https://api.deepseek.com/chat/completions");
        assertEquals("https://api.deepseek.com/chat/completions", resolved);
    }
}
