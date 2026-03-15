package com.yk.system.mapper;

import com.yk.system.entity.SysUser;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface SysUserMapper {
    SysUser findByUsername(@Param("username") String username);
}
