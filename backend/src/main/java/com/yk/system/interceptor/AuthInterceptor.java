package com.yk.system.interceptor;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.yk.system.common.Result;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 登录认证拦截器（基于内存 token）
 */
@Component
public class AuthInterceptor implements HandlerInterceptor {

    /** token -> username 映射，存储已登录的 token */
    public static final Map<String, String> TOKEN_MAP = new ConcurrentHashMap<>();

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler)
            throws Exception {
        String token = request.getHeader("Authorization");
        if (token != null && TOKEN_MAP.containsKey(token)) {
            return true;
        }
        response.setContentType("application/json;charset=UTF-8");
        Result<?> result = Result.error("未登录或登录已过期，请重新登录");
        result.setCode(401);
        response.getWriter().write(new ObjectMapper().writeValueAsString(result));
        return false;
    }
}
