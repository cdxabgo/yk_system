package com.yk.system.entity;

import lombok.Data;
import java.time.LocalDateTime;

/**
 * 心率实体
 */
@Data
public class HeartRate {
    private Long id;
    private Long empId;
    private Integer heartRate;
    private LocalDateTime measureTime;
    private String status;
    private LocalDateTime createTime;
    // 联查字段
    private String empName;
    private String empNo;
    private String department;
}
