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
