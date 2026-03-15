package com.yk.system.entity;

import lombok.Data;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

/**
 * 班中职工查询结果VO（联查职工信息、心率、异常心率）
 */
@Data
public class DutyEmployeeVO {
    // 班次信息
    private Long dutyId;
    private LocalDate shiftDate;
    private String shiftType;
    private LocalDateTime startTime;
    private LocalDateTime endTime;
    // 职工信息
    private Long empId;
    private String empNo;
    private String empName;
    private String gender;
    private Integer age;
    private String department;
    private String position;
    private String phone;
    // 最新心率
    private Integer latestHeartRate;
    private LocalDateTime latestMeasureTime;
    private String heartRateStatus;
    // 异常心率汇总
    private Integer abnormalCount;
    private String latestAlertLevel;
    private String latestHandleStatus;
}
