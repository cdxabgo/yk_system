package com.yk.system.entity;

import lombok.Data;
import java.time.LocalDateTime;

/**
 * 职工心率实体
 */
@Data
public class EmployeeHeartRate {
    private Long id;
    private Long employeeId;
    private Integer heartRate;
    private LocalDateTime collectTime;
    private Integer isAbnormal;
    private String deviceId;
    // 联查扩展字段
    private String employeeName;
    private String job;
}
