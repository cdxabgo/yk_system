package com.yk.system.service;

import com.yk.system.common.JwtUtil;
import com.yk.system.entity.SysUser;
import com.yk.system.mapper.SysUserMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HashMap;
import java.util.Map;

@Service
public class AuthService {

    @Autowired
    private SysUserMapper sysUserMapper;

    @Autowired
    private JwtUtil jwtUtil;

    /**
     * 登录验证，成功则返回包含 JWT token 的数据，失败返回 null
     */
    public Map<String, Object> login(String username, String password) {
        SysUser user = sysUserMapper.findByUsername(username);
        if (user == null || !matchesPassword(password, user.getPassword())) {
            return null;
        }
        String token = jwtUtil.generateToken(username);
        Map<String, Object> data = new HashMap<>();
        data.put("token", token);
        data.put("username", username);
        data.put("realName", user.getRealName());
        return data;
    }

    private boolean matchesPassword(String rawPassword, String storedPassword) {
        if (rawPassword == null || storedPassword == null) {
            return false;
        }
        return md5(rawPassword).equalsIgnoreCase(storedPassword) || rawPassword.equals(storedPassword);
    }

    private String md5(String text) {
        try {
            MessageDigest md = MessageDigest.getInstance("MD5");
            byte[] digest = md.digest(text.getBytes(StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder();
            for (byte b : digest) {
                sb.append(String.format("%02x", b));
            }
            return sb.toString();
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException("MD5算法不可用", e);
        }
    }

    /**
     * 登出（JWT 无状态，服务端无需处理；客户端清除 token 即可）
     */
    public void logout(String token) {
        // JWT 为无状态认证，登出由客户端清除 token 实现
    }
}

