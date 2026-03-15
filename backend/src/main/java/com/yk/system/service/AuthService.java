package com.yk.system.service;

import com.yk.system.entity.SysUser;
import com.yk.system.interceptor.AuthInterceptor;
import com.yk.system.mapper.SysUserMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

@Service
public class AuthService {

    @Autowired
    private SysUserMapper sysUserMapper;

    /**
     * 登录验证，成功则返回 token，失败返回 null
     */
    public Map<String, Object> login(String username, String password) {
        SysUser user = sysUserMapper.findByUsername(username);
        if (user == null || !user.getPassword().equals(password)) {
            return null;
        }
        String token = UUID.randomUUID().toString().replace("-", "");
        AuthInterceptor.TOKEN_MAP.put(token, username);
        Map<String, Object> data = new HashMap<>();
        data.put("token", token);
        data.put("username", username);
        data.put("realName", user.getRealName());
        return data;
    }

    /**
     * 登出，移除 token
     */
    public void logout(String token) {
        if (token != null) {
            AuthInterceptor.TOKEN_MAP.remove(token);
        }
    }
}
