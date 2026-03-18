-- migration_v4.sql
-- 新增 ML 心率检测结果表
-- 适用于从 v3 升级的现有 yk_demo 数据库
-- 执行方式: mysql -u root -p yk_demo < migration_v4.sql

USE yk_demo;

-- 创建 ML 检测结果表（Python 模型写入，Java 后端读取，前端展示异常）
CREATE TABLE IF NOT EXISTS `ml_detection_result` (
    `id`               BIGINT       NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    `employee_id`      BIGINT       NOT NULL                           COMMENT '职工ID（关联employee表）',
    `heart_rate`       INT          NOT NULL                           COMMENT '检测时使用的心率值（次/分钟）',
    `is_abnormal`      TINYINT(1)   NOT NULL DEFAULT 0                 COMMENT '是否异常 0正常 1异常',
    `anomaly_type`     VARCHAR(128)                                    COMMENT '异常类型（由ML+规则联合判断，如：心率过快、心率过慢、心率极值、心律不齐）',
    `source_record_id` BIGINT                                          COMMENT '来源心率记录ID（关联employee_heart_rate.id）',
    `detect_time`      DATETIME     NOT NULL                           COMMENT '检测时间',
    `created_at`       DATETIME     DEFAULT CURRENT_TIMESTAMP          COMMENT '记录创建时间',
    INDEX `idx_employee_id`          (`employee_id`),
    INDEX `idx_detect_time`          (`detect_time`),
    INDEX `idx_employee_detect_time` (`employee_id`, `detect_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ML模型心率检测结果表';

-- 写入初始样本数据（对应 employee_heart_rate 中各职工的最新一条记录）
-- 正式部署后此数据会被 Python ML 模型的检测结果覆盖
INSERT INTO `ml_detection_result` (`employee_id`, `heart_rate`, `is_abnormal`, `anomaly_type`, `source_record_id`, `detect_time`)
SELECT
    e.id,
    COALESCE(hr.heart_rate, 75)  AS heart_rate,
    COALESCE(hr.is_abnormal, 0)  AS is_abnormal,
    CASE
        WHEN hr.is_abnormal = 1 AND hr.heart_rate > 150 THEN '心率过快'
        WHEN hr.is_abnormal = 1 AND hr.heart_rate < 60  THEN '心率过慢'
        WHEN hr.is_abnormal = 1                          THEN '心律异常'
        ELSE NULL
    END                          AS anomaly_type,
    hr.id                        AS source_record_id,
    NOW()                        AS detect_time
FROM employee e
LEFT JOIN (
    SELECT hr1.*
    FROM employee_heart_rate hr1
    INNER JOIN (
        SELECT employee_id, MAX(measure_time) AS max_time
        FROM employee_heart_rate
        GROUP BY employee_id
    ) hr2 ON hr1.employee_id = hr2.employee_id AND hr1.measure_time = hr2.max_time
) hr ON e.id = hr.employee_id
-- 仅为尚无检测结果的职工写入初始记录
WHERE NOT EXISTS (
    SELECT 1 FROM ml_detection_result mr WHERE mr.employee_id = e.id
);
