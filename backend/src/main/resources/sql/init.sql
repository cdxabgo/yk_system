-- yk_demo 数据库初始化脚本
-- 请在执行前确保已创建数据库：CREATE DATABASE IF NOT EXISTS yk_demo DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE yk_demo;

-- 系统用户表
CREATE TABLE IF NOT EXISTS `user` (
    `id`          BIGINT      NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    `username`    VARCHAR(64) NOT NULL UNIQUE                     COMMENT '用户名',
    `password`    VARCHAR(128) NOT NULL                           COMMENT '密码（MD5或明文）',
    `real_name`   VARCHAR(64)                                     COMMENT '真实姓名',
    `create_time` DATETIME    DEFAULT CURRENT_TIMESTAMP           COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统用户表';

-- 职工信息表
CREATE TABLE IF NOT EXISTS `employee` (
    `id`            BIGINT      NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    `name`          VARCHAR(64) NOT NULL                           COMMENT '姓名',
    `age`           INT                                            COMMENT '年龄',
    `position`      VARCHAR(64)                                    COMMENT '岗位/职位',
    `working_years` INT         DEFAULT 0                          COMMENT '工龄（年）',
    `phone`         VARCHAR(64)                                    COMMENT '联系方式',
    `create_time`   DATETIME    DEFAULT CURRENT_TIMESTAMP          COMMENT '创建时间',
    `update_time`   DATETIME    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='职工信息表';

-- 心率记录表
CREATE TABLE IF NOT EXISTS `employee_heart_rate` (
    `id`          BIGINT   NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    `employee_id` BIGINT   NOT NULL                           COMMENT '职工ID',
    `heart_rate`  INT      NOT NULL                           COMMENT '心率（次/分钟）',
    `measure_time` DATETIME NOT NULL                          COMMENT '采集时间',
    `is_abnormal` TINYINT(1) NOT NULL DEFAULT 0               COMMENT '是否异常（0正常 1异常）',
    `source`      VARCHAR(64)                                 COMMENT '设备ID/数据来源',
    INDEX `idx_employee_id`            (`employee_id`),
    INDEX `idx_measure_time`           (`measure_time`),
    INDEX `idx_employee_abnormal_time` (`employee_id`, `is_abnormal`, `measure_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='职工心率记录表';

-- 疾病信息表
CREATE TABLE IF NOT EXISTS `disease` (
    `id`           BIGINT       NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    `disease_name` VARCHAR(128) NOT NULL                           COMMENT '疾病名称',
    `disease_type` VARCHAR(64)                                     COMMENT '疾病类型',
    `create_time`  DATETIME     DEFAULT CURRENT_TIMESTAMP          COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='疾病信息表';

-- ML模型心率检测结果表（由 Python ML 模型写入，Java 后端读取供前端展示）
CREATE TABLE IF NOT EXISTS `ml_detection_result` (
    `id`               BIGINT       NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    `employee_id`      BIGINT       NOT NULL                           COMMENT '职工ID（关联employee表）',
    `heart_rate`       INT          NOT NULL                           COMMENT '检测时使用的心率值（次/分钟）',
    `is_abnormal`      TINYINT(1)   NOT NULL DEFAULT 0                 COMMENT '是否异常 0正常 1异常',
    `anomaly_type`     VARCHAR(128)                                    COMMENT '异常类型（由ML+规则联合判断）',
    `source_record_id` BIGINT                                          COMMENT '来源心率记录ID（关联employee_heart_rate.id）',
    `detect_time`      DATETIME     NOT NULL                           COMMENT '检测时间',
    `created_at`       DATETIME     DEFAULT CURRENT_TIMESTAMP          COMMENT '记录创建时间',
    INDEX `idx_employee_id`          (`employee_id`),
    INDEX `idx_detect_time`          (`detect_time`),
    INDEX `idx_employee_detect_time` (`employee_id`, `detect_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ML模型心率检测结果表';

-- 职工疾病关联表
CREATE TABLE IF NOT EXISTS `employee_disease_relation` (
    `id`             BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    `employee_id`    BIGINT NOT NULL                           COMMENT '职工ID',
    `disease_id`     BIGINT NOT NULL                           COMMENT '疾病ID',
    `diagnosis_time` DATE                                      COMMENT '诊断时间',
    `create_time`    DATETIME DEFAULT CURRENT_TIMESTAMP        COMMENT '创建时间',
    INDEX `idx_employee_id` (`employee_id`),
    INDEX `idx_disease_id`  (`disease_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='职工疾病关联表';

-- 初始管理员账户（用户名: admin，密码: admin123，已MD5加密）
INSERT IGNORE INTO `user` (`username`, `password`, `real_name`)
VALUES ('admin', '0192023a7bbd73250516f069df18b500', '系统管理员');

-- 样本职工数据（用于模拟心率监测演示）
INSERT IGNORE INTO `employee` (`id`, `name`, `age`, `position`, `working_years`, `phone`) VALUES
(1, '张三',  35, '矿工',   5,  '13800000001'),
(2, '李四',  42, '班长',   10, '13800000002'),
(3, '王五',  28, '矿工',   3,  '13800000003'),
(4, '赵六',  50, '安全员', 20, '13800000004'),
(5, '陈七',  38, '技术员',  8, '13800000005'),
(6, '刘八',  45, '矿工',   15, '13800000006'),
(7, '周九',  32, '操作员',  6, '13800000007'),
(8, '吴十',  55, '班长',   25, '13800000008');

-- 初始心率记录（为各职工生成最近10分钟的历史数据，供轮询演示）
INSERT INTO `employee_heart_rate` (`employee_id`, `heart_rate`, `measure_time`, `is_abnormal`, `source`) VALUES
(1, 72, DATE_SUB(NOW(), INTERVAL 9 MINUTE), 0, 'simulator'),
(1, 75, DATE_SUB(NOW(), INTERVAL 6 MINUTE), 0, 'simulator'),
(1, 78, DATE_SUB(NOW(), INTERVAL 3 MINUTE), 0, 'simulator'),
(2, 85, DATE_SUB(NOW(), INTERVAL 9 MINUTE), 0, 'simulator'),
(2, 88, DATE_SUB(NOW(), INTERVAL 6 MINUTE), 0, 'simulator'),
(2, 91, DATE_SUB(NOW(), INTERVAL 3 MINUTE), 0, 'simulator'),
(3, 68, DATE_SUB(NOW(), INTERVAL 9 MINUTE), 0, 'simulator'),
(3, 65, DATE_SUB(NOW(), INTERVAL 6 MINUTE), 0, 'simulator'),
(3, 70, DATE_SUB(NOW(), INTERVAL 3 MINUTE), 0, 'simulator'),
(4, 95, DATE_SUB(NOW(), INTERVAL 9 MINUTE), 0, 'simulator'),
(4, 98, DATE_SUB(NOW(), INTERVAL 6 MINUTE), 0, 'simulator'),
(4, 160,DATE_SUB(NOW(), INTERVAL 3 MINUTE), 1, 'simulator'),
(5, 76, DATE_SUB(NOW(), INTERVAL 9 MINUTE), 0, 'simulator'),
(5, 79, DATE_SUB(NOW(), INTERVAL 6 MINUTE), 0, 'simulator'),
(5, 82, DATE_SUB(NOW(), INTERVAL 3 MINUTE), 0, 'simulator'),
(6, 88, DATE_SUB(NOW(), INTERVAL 9 MINUTE), 0, 'simulator'),
(6, 92, DATE_SUB(NOW(), INTERVAL 6 MINUTE), 0, 'simulator'),
(6, 45, DATE_SUB(NOW(), INTERVAL 3 MINUTE), 1, 'simulator'),
(7, 73, DATE_SUB(NOW(), INTERVAL 9 MINUTE), 0, 'simulator'),
(7, 76, DATE_SUB(NOW(), INTERVAL 6 MINUTE), 0, 'simulator'),
(7, 74, DATE_SUB(NOW(), INTERVAL 3 MINUTE), 0, 'simulator'),
(8, 80, DATE_SUB(NOW(), INTERVAL 9 MINUTE), 0, 'simulator'),
(8, 83, DATE_SUB(NOW(), INTERVAL 6 MINUTE), 0, 'simulator'),
(8, 86, DATE_SUB(NOW(), INTERVAL 3 MINUTE), 0, 'simulator');

-- 初始 ML 检测结果（对应上方心率记录的最新一条，供前端初次加载时展示）
INSERT INTO `ml_detection_result` (`employee_id`, `heart_rate`, `is_abnormal`, `anomaly_type`, `source_record_id`, `detect_time`) VALUES
(1, 78,  0, NULL,       NULL, DATE_SUB(NOW(), INTERVAL 2 MINUTE)),
(2, 91,  0, NULL,       NULL, DATE_SUB(NOW(), INTERVAL 2 MINUTE)),
(3, 70,  0, NULL,       NULL, DATE_SUB(NOW(), INTERVAL 2 MINUTE)),
(4, 160, 1, '心率过快', NULL, DATE_SUB(NOW(), INTERVAL 2 MINUTE)),
(5, 82,  0, NULL,       NULL, DATE_SUB(NOW(), INTERVAL 2 MINUTE)),
(6, 45,  1, '心率过慢', NULL, DATE_SUB(NOW(), INTERVAL 2 MINUTE)),
(7, 74,  0, NULL,       NULL, DATE_SUB(NOW(), INTERVAL 2 MINUTE)),
(8, 86,  0, NULL,       NULL, DATE_SUB(NOW(), INTERVAL 2 MINUTE));
