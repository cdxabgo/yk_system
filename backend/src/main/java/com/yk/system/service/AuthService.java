package com.yk.system.service;

import com.yk.system.common.JwtUtil;
import com.yk.system.entity.SysUser;
import com.yk.system.mapper.SysUserMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;

@Service
public class AuthService {

    @Autowired
    private SysUserMapper sysUserMapper;

    @Autowired
    private JwtUtil jwtUtil;

    private final BCryptPasswordEncoder passwordEncoder = new BCryptPasswordEncoder();

    /**
     * 登录验证，成功则返回包含 JWT token 的数据，失败返回 null
     */
    public Map<String, Object> login(String username, String password) {
        SysUser user = sysUserMapper.findByUsername(username);
        if (user == null || !passwordEncoder.matches(password, user.getPassword())) {
            return null;
        }
        String token = jwtUtil.generateToken(username);
        Map<String, Object> data = new HashMap<>();
        data.put("token", token);
        data.put("username", username);
        data.put("realName", user.getRealName());
        return data;
    }

    /**
     * 使用 BCrypt 对密码进行哈希（用于初始化/重置密码时生成密文）
     */
    public String encodePassword(String rawPassword) {
        return passwordEncoder.encode(rawPassword);
    }

    /**
     * 登出（JWT 无状态，服务端无需处理；客户端清除 token 即可）
     */
    public void logout(String token) {
        // JWT 为无状态认证，登出由客户端清除 token 实现
    }
}
