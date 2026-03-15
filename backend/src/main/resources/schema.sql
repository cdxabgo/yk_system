-- 井下职工心率监测系统数据库初始化脚本

CREATE DATABASE IF NOT EXISTS yk_system DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE yk_system;

-- 1. 职工信息表（核心主表）
CREATE TABLE IF NOT EXISTS `employee` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '职工唯一主键ID',
  `name` VARCHAR(50) NOT NULL COMMENT '职工姓名',
  `age` TINYINT UNSIGNED DEFAULT NULL COMMENT '年龄（0-255，满足实际年龄范围）',
  `job` VARCHAR(100) DEFAULT NULL COMMENT '岗位',
  `working_years` TINYINT UNSIGNED DEFAULT 0 COMMENT '工龄（年）',
  `contact_information` VARCHAR(200) DEFAULT NULL COMMENT '联系方式（手机号/邮箱等）',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '数据录入时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '数据更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_name` (`name`) COMMENT '姓名索引，便于快速查询职工'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='职工信息表';

-- 2. 疾病表（基础字典表）
CREATE TABLE IF NOT EXISTS `disease` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '疾病唯一主键ID',
  `disease_name` VARCHAR(100) NOT NULL COMMENT '疾病名称（如：高血压、糖尿病）',
  `disease_type` VARCHAR(50) DEFAULT NULL COMMENT '疾病类型（如：慢性病、心血管疾病）',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '录入时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_disease_name` (`disease_name`) COMMENT '疾病名称唯一，避免重复'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='疾病表';

-- 3. 疾病职工关联表（多对多关联）
CREATE TABLE IF NOT EXISTS `employee_disease_relation` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '关联记录主键ID',
  `employee_id` BIGINT UNSIGNED NOT NULL COMMENT '职工ID（外键）',
  `disease_id` BIGINT UNSIGNED NOT NULL COMMENT '疾病ID（外键）',
  `diagnosis_time` DATE DEFAULT NULL COMMENT '确诊时间（可选）',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '关联录入时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_emp_disease` (`employee_id`, `disease_id`),
  KEY `idx_disease_id` (`disease_id`),
  CONSTRAINT `fk_relation_employee` FOREIGN KEY (`employee_id`) REFERENCES `employee` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_relation_disease` FOREIGN KEY (`disease_id`) REFERENCES `disease` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='疾病职工关联表';

-- 4. 心率表（职工实时心率数据）
CREATE TABLE IF NOT EXISTS `employee_heart_rate` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '心率记录主键ID',
  `employee_id` BIGINT UNSIGNED NOT NULL COMMENT '职工ID（外键）',
  `heart_rate` TINYINT UNSIGNED NOT NULL COMMENT '心率值（次/分钟，0-255）',
  `collect_time` DATETIME NOT NULL COMMENT '采集时间',
  `is_abnormal` TINYINT NOT NULL DEFAULT 0 COMMENT '是否异常：0-正常 1-异常',
  `device_id` VARCHAR(50) DEFAULT NULL COMMENT '采集设备ID（如手环编号）',
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_emp_collect_time` (`employee_id`, `collect_time`),
  KEY `idx_is_abnormal` (`is_abnormal`),
  CONSTRAINT `fk_heart_rate_employee` FOREIGN KEY (`employee_id`) REFERENCES `employee` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='职工心率表';

-- 5. 系统用户表（登录使用）
CREATE TABLE IF NOT EXISTS `sys_user` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '用户主键ID',
  `username` VARCHAR(50) NOT NULL COMMENT '登录用户名',
  `password` VARCHAR(100) NOT NULL COMMENT '登录密码（明文存储，生产环境应加密）',
  `real_name` VARCHAR(50) DEFAULT NULL COMMENT '真实姓名',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统用户表';

-- 初始化示例数据
INSERT IGNORE INTO `sys_user` (username, password, real_name) VALUES ('admin', 'admin123', '系统管理员');

INSERT IGNORE INTO `employee` (name, age, job, working_years, contact_information) VALUES
('张三', 32, '采煤工', 8, '13800000001'),
('李四', 28, '掘进工', 4, '13800000002'),
('王五', 45, '支护工', 15, '13800000003'),
('赵六', 35, '机电工', 10, '13800000004'),
('孙七', 26, '通风工', 2, '13800000005');

INSERT IGNORE INTO `disease` (disease_name, disease_type) VALUES
('高血压', '心血管疾病'),
('心律不齐', '心血管疾病'),
('冠心病', '心血管疾病'),
('矽肺病', '职业病'),
('糖尿病', '慢性病');

INSERT IGNORE INTO `employee_heart_rate` (employee_id, heart_rate, collect_time, is_abnormal, device_id) VALUES
(1, 75, NOW() - INTERVAL 2 HOUR, 0, 'HB-001'),
(1, 82, NOW() - INTERVAL 1 HOUR, 0, 'HB-001'),
(2, 68, NOW() - INTERVAL 3 HOUR, 0, 'HB-002'),
(2, 118, NOW() - INTERVAL 1 HOUR, 1, 'HB-002'),
(3, 72, NOW() - INTERVAL 4 HOUR, 0, 'HB-003'),
(3, 65, NOW() - INTERVAL 2 HOUR, 0, 'HB-003'),
(4, 88, NOW() - INTERVAL 1 HOUR, 0, 'HB-004'),
(5, 130, NOW() - INTERVAL 30 MINUTE, 1, 'HB-005');
