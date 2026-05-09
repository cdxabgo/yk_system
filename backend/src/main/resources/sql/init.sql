-- yk_demo 数据库初始化脚本
-- 请在执行前确保已创建数据库：CREATE DATABASE IF NOT EXISTS yk_demo DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE yk_demo;

-- 系统用户表
CREATE TABLE IF NOT EXISTS `user` (
    `id`          BIGINT      NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    `username`    VARCHAR(64) NOT NULL UNIQUE                     COMMENT '用户名',
    `password`    VARCHAR(128) NOT NULL                           COMMENT '密码（BCrypt加密）',
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

-- 初始管理员账户（用户名: admin，密码: admin123，BCrypt加密）
-- 如需重置密码，调用 AuthService.encodePassword("新密码") 生成密文
INSERT IGNORE INTO `user` (`username`, `password`, `real_name`)
VALUES ('admin', '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '系统管理员');

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
