package com.yk.system.entity;

import lombok.Data;
import java.time.LocalDateTime;

/**
 * 系统用户实体
 */
@Data
public class SysUser {
    private Long id;
    private String username;
    private String password;
    private String realName;
    private LocalDateTime createTime;
}
