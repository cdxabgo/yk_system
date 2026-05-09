package com.yk.system.interceptor;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.yk.system.common.JwtUtil;
import com.yk.system.common.Result;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

/**
 * 登录认证拦截器（基于 JWT）
 */
@Component
public class AuthInterceptor implements HandlerInterceptor {

    @Autowired
    private JwtUtil jwtUtil;

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler)
            throws Exception {
        String token = request.getHeader("Authorization");
        if (token != null) {
            if (token.startsWith("Bearer ")) {
                token = token.substring(7);
            }
            String username = jwtUtil.getUsernameFromToken(token);
            if (username != null) {
                request.setAttribute("username", username);
                return true;
            }
        }
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.setContentType("application/json;charset=UTF-8");
        Result<?> result = Result.error(401, "未登录或登录已过期，请重新登录");
        response.getWriter().write(new ObjectMapper().writeValueAsString(result));
        return false;
    }
}

