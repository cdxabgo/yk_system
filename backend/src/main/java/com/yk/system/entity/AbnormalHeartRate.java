package com.yk.system.entity;

import lombok.Data;
import java.time.LocalDateTime;

/**
 * 异常心率实体
 */
@Data
public class AbnormalHeartRate {
    private Long id;
    private Long empId;
    private Integer heartRate;
    private LocalDateTime measureTime;
    private String alertLevel;
    private String handleStatus;
    private LocalDateTime createTime;
    // 联查字段
    private String empName;
    private String empNo;
}
