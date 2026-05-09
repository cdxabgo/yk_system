package com.yk.system.entity;

import lombok.Data;
import java.time.LocalDateTime;

/**
 * 最新心率数据 VO（每位职工一条，供前端轮询使用）
 */
@Data
public class HeartRateLatestVO {
    /** 职工 ID（前端使用 userId 字段名） */
    private Long userId;
    /** 职工姓名 */
    private String employeeName;
    /** 最新心率（bpm） */
    private Integer heartRate;
    /** 是否异常（0 正常，1 异常） */
    private Integer isAbnormal;
    /** 采集时间 */
    private LocalDateTime dataTime;
    /** 异常类型描述（正常时为 null） */
    private String anomalyType;
}
