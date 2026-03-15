package com.yk.system.entity;

import lombok.Data;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 班中职工实体
 */
@Data
public class DutyEmployee {
    private Long id;
    private Long empId;
    private LocalDate shiftDate;
    private String shiftType;
    private LocalDateTime startTime;
    private LocalDateTime endTime;
    private LocalDateTime createTime;
}
