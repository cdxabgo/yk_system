package com.yk.system.common;

import org.springframework.dao.DataAccessException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(DataAccessException.class)
    public Result<?> handleDataAccessException(DataAccessException e) {
        return Result.error(500, "数据库访问异常，请检查 yk_demo 数据库表结构是否已初始化");
    }

    @ExceptionHandler(Exception.class)
    public Result<?> handleException(Exception e) {
        return Result.error(500, e.getMessage() == null || e.getMessage().isBlank() ? "服务器内部错误" : e.getMessage());
    }
}
