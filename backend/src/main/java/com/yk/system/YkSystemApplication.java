package com.yk.system;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@MapperScan("com.yk.system.mapper")
public class YkSystemApplication {
    public static void main(String[] args) {
        SpringApplication.run(YkSystemApplication.class, args);
    }
}
