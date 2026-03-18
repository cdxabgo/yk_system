-- =====================================================================
-- yk_demo 数据库迁移脚本 v3.0
-- 适用场景：从旧版（SSE实时推送架构）升级到 v3.0（数据库轮询架构）
--
-- 执行前请先备份数据库：
--   mysqldump -u root -p yk_demo > yk_demo_backup.sql
--
-- 执行方式：
--   mysql -u root -p yk_demo < migration_v3.sql
-- =====================================================================

USE yk_demo;

-- ---------------------------------------------------------------------
-- 1. 确保 employee 表存在（含 position / phone 列）
-- ---------------------------------------------------------------------
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

-- ---------------------------------------------------------------------
-- 2. 确保 employee_heart_rate 表存在，并包含 source 列与所有必要索引
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `employee_heart_rate` (
    `id`           BIGINT     NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    `employee_id`  BIGINT     NOT NULL                           COMMENT '职工ID',
    `heart_rate`   INT        NOT NULL                           COMMENT '心率（次/分钟）',
    `measure_time` DATETIME   NOT NULL                           COMMENT '采集时间',
    `is_abnormal`  TINYINT(1) NOT NULL DEFAULT 0                 COMMENT '是否异常（0正常 1异常）',
    `source`       VARCHAR(64)                                   COMMENT '设备ID/数据来源'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='职工心率记录表';

-- 若表已存在但缺少 source 列，则补充添加
ALTER TABLE `employee_heart_rate`
    ADD COLUMN IF NOT EXISTS `source` VARCHAR(64) COMMENT '设备ID/数据来源';

-- 添加单列索引（已存在则跳过）
ALTER TABLE `employee_heart_rate`
    ADD INDEX IF NOT EXISTS `idx_employee_id`  (`employee_id`);

ALTER TABLE `employee_heart_rate`
    ADD INDEX IF NOT EXISTS `idx_measure_time` (`measure_time`);

-- 添加复合索引（v3.0 班中监控轮询 / 连续异常检测 必需）
ALTER TABLE `employee_heart_rate`
    ADD INDEX IF NOT EXISTS `idx_employee_abnormal_time` (`employee_id`, `is_abnormal`, `measure_time`);

-- ---------------------------------------------------------------------
-- 3. 确保 disease 表存在
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `disease` (
    `id`           BIGINT       NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    `disease_name` VARCHAR(128) NOT NULL                           COMMENT '疾病名称',
    `disease_type` VARCHAR(64)                                     COMMENT '疾病类型',
    `create_time`  DATETIME     DEFAULT CURRENT_TIMESTAMP          COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='疾病信息表';

-- ---------------------------------------------------------------------
-- 4. 确保 employee_disease_relation 表存在
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `employee_disease_relation` (
    `id`             BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    `employee_id`    BIGINT NOT NULL                           COMMENT '职工ID',
    `disease_id`     BIGINT NOT NULL                           COMMENT '疾病ID',
    `diagnosis_time` DATE                                      COMMENT '诊断时间',
    `create_time`    DATETIME DEFAULT CURRENT_TIMESTAMP        COMMENT '创建时间',
    INDEX `idx_employee_id` (`employee_id`),
    INDEX `idx_disease_id`  (`disease_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='职工疾病关联表';

-- ---------------------------------------------------------------------
-- 5. 确保 user 表存在，并插入默认管理员账户
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `user` (
    `id`          BIGINT      NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    `username`    VARCHAR(64) NOT NULL UNIQUE                     COMMENT '用户名',
    `password`    VARCHAR(128) NOT NULL                           COMMENT '密码（MD5或明文）',
    `real_name`   VARCHAR(64)                                     COMMENT '真实姓名',
    `create_time` DATETIME    DEFAULT CURRENT_TIMESTAMP           COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统用户表';

-- 默认管理员账户（用户名: admin，密码: admin123，已MD5加密）
INSERT IGNORE INTO `user` (`username`, `password`, `real_name`)
VALUES ('admin', '0192023a7bbd73250516f069df18b500', '系统管理员');

-- =====================================================================
-- 迁移完成！
-- 主要变更说明：
--   - employee_heart_rate 表新增了 source 列（设备ID/数据来源）
--   - 新增复合索引 idx_employee_abnormal_time，供班中监控轮询查询使用
--   - 旧版 SSE 推送无需数据库，升级到 v3.0 后心率数据改由数据库存储，
--     前端每10秒轮询 /api/realtime/latest 接口获取最新心率。
-- =====================================================================
