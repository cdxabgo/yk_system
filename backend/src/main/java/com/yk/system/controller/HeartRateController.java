package com.yk.system.controller;

import com.yk.system.common.PageResult;
import com.yk.system.common.Result;
import com.yk.system.entity.EmployeeHeartRate;
import com.yk.system.entity.EmployeeMonitorVO;
import com.yk.system.service.HeartRateService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/heartRate")
public class HeartRateController {

    @Autowired
    private HeartRateService heartRateService;

    @GetMapping("/list")
    public Result<PageResult<EmployeeHeartRate>> list(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(required = false) Long employeeId,
            @RequestParam(required = false) Integer isAbnormal,
            @RequestParam(required = false) String startTime,
            @RequestParam(required = false) String endTime) {
        return Result.success(heartRateService.list(page, size, employeeId, isAbnormal, startTime, endTime));
    }

    @GetMapping("/{id}")
    public Result<EmployeeHeartRate> getById(@PathVariable Long id) {
        return Result.success(heartRateService.getById(id));
    }

    @PostMapping
    public Result<?> add(@RequestBody EmployeeHeartRate heartRate) {
        heartRate.setId(null);
        heartRateService.add(heartRate);
        return Result.success();
    }

    @DeleteMapping("/{id}")
    public Result<?> delete(@PathVariable Long id) {
        heartRateService.deleteById(id);
        return Result.success();
    }

    /**
     * 班中职工监控查询：JOIN 职工信息表 + 心率表 + 异常心率统计
     */
    @GetMapping("/monitor")
    public Result<PageResult<EmployeeMonitorVO>> monitor(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(required = false) String name,
            @RequestParam(required = false) String job,
            @RequestParam(required = false) Integer isAbnormal) {
        return Result.success(heartRateService.queryMonitor(page, size, name, job, isAbnormal));
    }
}
