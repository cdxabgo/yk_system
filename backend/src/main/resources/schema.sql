-- 职工健康监测系统数据库初始化脚本

CREATE DATABASE IF NOT EXISTS yk_system DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE yk_system;

-- 职工信息表
CREATE TABLE IF NOT EXISTS employee (
    id         BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    emp_no     VARCHAR(20)  NOT NULL UNIQUE COMMENT '工号',
    name       VARCHAR(50)  NOT NULL COMMENT '姓名',
    gender     VARCHAR(10)  NOT NULL COMMENT '性别：男/女',
    age        INT          NOT NULL COMMENT '年龄',
    department VARCHAR(50)  NOT NULL COMMENT '部门',
    position   VARCHAR(50)  NOT NULL COMMENT '职位',
    phone      VARCHAR(20)  COMMENT '联系电话',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='职工信息表';

-- 疾病信息表
CREATE TABLE IF NOT EXISTS disease (
    id           BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    disease_code VARCHAR(20)  NOT NULL UNIQUE COMMENT '疾病编码',
    disease_name VARCHAR(100) NOT NULL COMMENT '疾病名称',
    description  TEXT COMMENT '疾病描述',
    level        VARCHAR(20)  NOT NULL DEFAULT '普通' COMMENT '等级：轻微/普通/严重',
    create_time  DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='疾病信息表';

-- 心率表
CREATE TABLE IF NOT EXISTS heart_rate (
    id           BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    emp_id       BIGINT      NOT NULL COMMENT '职工ID',
    heart_rate   INT         NOT NULL COMMENT '心率值（次/分钟）',
    measure_time DATETIME    NOT NULL COMMENT '测量时间',
    status       VARCHAR(20) NOT NULL DEFAULT '正常' COMMENT '状态：正常/异常',
    create_time  DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (emp_id) REFERENCES employee(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='心率表';

-- 异常心率表
CREATE TABLE IF NOT EXISTS abnormal_heart_rate (
    id            BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    emp_id        BIGINT      NOT NULL COMMENT '职工ID',
    heart_rate    INT         NOT NULL COMMENT '异常心率值（次/分钟）',
    measure_time  DATETIME    NOT NULL COMMENT '测量时间',
    alert_level   VARCHAR(20) NOT NULL DEFAULT '警告' COMMENT '告警等级：警告/危险',
    handle_status VARCHAR(20) NOT NULL DEFAULT '未处理' COMMENT '处理状态：未处理/已处理',
    create_time   DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (emp_id) REFERENCES employee(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='异常心率表';

-- 班中职工表
CREATE TABLE IF NOT EXISTS duty_employee (
    id         BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    emp_id     BIGINT      NOT NULL COMMENT '职工ID',
    shift_date DATE        NOT NULL COMMENT '班次日期',
    shift_type VARCHAR(20) NOT NULL DEFAULT '早班' COMMENT '班次类型：早班/中班/晚班',
    start_time DATETIME    NOT NULL COMMENT '开始时间',
    end_time   DATETIME    COMMENT '结束时间',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (emp_id) REFERENCES employee(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='班中职工表';

-- 初始化示例数据
INSERT INTO employee (emp_no, name, gender, age, department, position, phone) VALUES
('E001', '张三', '男', 32, '生产部', '操作员', '13800000001'),
('E002', '李四', '男', 28, '生产部', '操作员', '13800000002'),
('E003', '王五', '女', 35, '技术部', '工程师', '13800000003'),
('E004', '赵六', '男', 45, '管理部', '主管', '13800000004'),
('E005', '孙七', '女', 26, '生产部', '操作员', '13800000005');

INSERT INTO disease (disease_code, disease_name, description, level) VALUES
('D001', '高血压', '血压持续偏高，需定期监测', '严重'),
('D002', '心律不齐', '心跳节律异常', '严重'),
('D003', '冠心病', '冠状动脉供血不足', '严重'),
('D004', '贫血', '血液中红细胞或血红蛋白不足', '普通'),
('D005', '头晕', '偶发性头晕症状', '轻微');

INSERT INTO heart_rate (emp_id, heart_rate, measure_time, status) VALUES
(1, 75, NOW() - INTERVAL 1 HOUR, '正常'),
(1, 82, NOW() - INTERVAL 30 MINUTE, '正常'),
(2, 68, NOW() - INTERVAL 2 HOUR, '正常'),
(2, 115, NOW() - INTERVAL 1 HOUR, '异常'),
(3, 72, NOW() - INTERVAL 3 HOUR, '正常'),
(4, 65, NOW() - INTERVAL 4 HOUR, '正常'),
(5, 88, NOW() - INTERVAL 2 HOUR, '正常');

INSERT INTO abnormal_heart_rate (emp_id, heart_rate, measure_time, alert_level, handle_status) VALUES
(2, 115, NOW() - INTERVAL 1 HOUR, '警告', '未处理'),
(2, 125, NOW() - INTERVAL 30 MINUTE, '危险', '未处理');

INSERT INTO duty_employee (emp_id, shift_date, shift_type, start_time, end_time) VALUES
(1, CURDATE(), '早班', CONCAT(CURDATE(), ' 08:00:00'), CONCAT(CURDATE(), ' 16:00:00')),
(2, CURDATE(), '早班', CONCAT(CURDATE(), ' 08:00:00'), CONCAT(CURDATE(), ' 16:00:00')),
(3, CURDATE(), '中班', CONCAT(CURDATE(), ' 16:00:00'), CONCAT(CURDATE(), ' 00:00:00')),
(4, CURDATE(), '早班', CONCAT(CURDATE(), ' 08:00:00'), CONCAT(CURDATE(), ' 16:00:00')),
(5, CURDATE(), '中班', CONCAT(CURDATE(), ' 16:00:00'), CONCAT(CURDATE(), ' 00:00:00'));
