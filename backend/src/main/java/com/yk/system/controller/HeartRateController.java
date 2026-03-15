package com.yk.system.controller;

import com.yk.system.common.PageResult;
import com.yk.system.common.Result;
import com.yk.system.entity.HeartRate;
import com.yk.system.service.HeartRateService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/heartRate")
public class HeartRateController {

    @Autowired
    private HeartRateService heartRateService;

    @GetMapping("/list")
    public Result<PageResult<HeartRate>> list(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(required = false) Long empId,
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String startTime,
            @RequestParam(required = false) String endTime) {
        return Result.success(heartRateService.list(page, size, empId, status, startTime, endTime));
    }

    @GetMapping("/{id}")
    public Result<HeartRate> getById(@PathVariable Long id) {
        return Result.success(heartRateService.getById(id));
    }

    @PostMapping
    public Result<?> add(@RequestBody HeartRate heartRate) {
        heartRate.setId(null);
        heartRateService.add(heartRate);
        return Result.success();
    }

    @DeleteMapping("/{id}")
    public Result<?> delete(@PathVariable Long id) {
        heartRateService.deleteById(id);
        return Result.success();
    }
}
