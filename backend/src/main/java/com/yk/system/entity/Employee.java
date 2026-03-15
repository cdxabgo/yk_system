package com.yk.system.entity;

import lombok.Data;
import java.time.LocalDateTime;

/**
 * 职工信息实体
 */
@Data
public class Employee {
    private Long id;
    private String name;
    private Integer age;
    private String job;
    private Integer workingYears;
    private String contactInformation;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
