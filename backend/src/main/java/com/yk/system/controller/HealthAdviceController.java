package com.yk.system.controller;

import com.yk.system.common.Result;
import com.yk.system.entity.HealthAdviceResult;
import com.yk.system.service.HealthAdviceService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/healthAdvice")
public class HealthAdviceController {

    @Autowired
    private HealthAdviceService healthAdviceService;

    @GetMapping("/generate")
    public Result<HealthAdviceResult> generate(@RequestParam Long employeeId) {
        try {
            return Result.success(healthAdviceService.generateByEmployeeId(employeeId));
        } catch (IllegalArgumentException | IllegalStateException e) {
            return Result.error(e.getMessage());
        }
    }
}
