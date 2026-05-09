package com.yk.system.entity;

import lombok.Data;
import java.time.LocalDateTime;

/**
 * 班中职工监控视图 VO
 * JOIN 职工信息表 + 心率表 + 异常心率统计
 */
@Data
public class EmployeeMonitorVO {
    // 职工信息
    private Long employeeId;
    private String name;
    private Integer age;
    private String job;
    private Integer workingYears;
    private String contactInformation;
    // 最新心率
    private Integer latestHeartRate;
    private LocalDateTime latestCollectTime;
    private Integer latestIsAbnormal;
    private String latestDeviceId;
    // 异常心率统计
    private Integer totalRecords;
    private Integer abnormalCount;
    // 疾病数量
    private Integer diseaseCount;
    // 当前连续异常开始时间（null 表示最新记录正常，无连续异常）
    private LocalDateTime streakStartTime;
}
