package com.yk.system.entity;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class HealthAdviceResult {
    private Long employeeId;
    private String employeeName;
    private Integer todaySampleCount;
    private LocalDateTime generatedAt;
    private String advice;
}
