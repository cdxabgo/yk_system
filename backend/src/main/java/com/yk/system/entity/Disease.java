package com.yk.system.entity;

import lombok.Data;
import java.time.LocalDateTime;

/**
 * 疾病信息实体
 */
@Data
public class Disease {
    private Long id;
    private String diseaseCode;
    private String diseaseName;
    private String description;
    private String level;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
