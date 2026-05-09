package com.yk.system.entity;

import lombok.Data;
import java.time.LocalDateTime;

/**
 * 疾病信息实体
 */
@Data
public class Disease {
    private Long id;
    private String diseaseName;
    private String diseaseType;
    private LocalDateTime createTime;
}
