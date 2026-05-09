package com.yk.system.entity;

import lombok.Data;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 疾病职工关联实体
 */
@Data
public class EmployeeDiseaseRelation {
    private Long id;
    private Long employeeId;
    private Long diseaseId;
    private LocalDate diagnosisTime;
    private LocalDateTime createTime;
    // 联查扩展字段
    private String employeeName;
    private String diseaseName;
    private String diseaseType;
}
