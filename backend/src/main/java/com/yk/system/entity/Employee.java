package com.yk.system.entity;

import lombok.Data;
import java.time.LocalDateTime;

/**
 * 职工信息实体
 */
@Data
public class Employee {
    private Long id;
    private String empNo;
    private String name;
    private String gender;
    private Integer age;
    private String department;
    private String position;
    private String phone;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
