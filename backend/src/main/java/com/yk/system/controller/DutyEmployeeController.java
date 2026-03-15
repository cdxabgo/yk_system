package com.yk.system.controller;

import com.yk.system.common.PageResult;
import com.yk.system.common.Result;
import com.yk.system.entity.DutyEmployee;
import com.yk.system.entity.DutyEmployeeVO;
import com.yk.system.service.DutyEmployeeService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/duty")
public class DutyEmployeeController {

    @Autowired
    private DutyEmployeeService dutyEmployeeService;

    /**
     * 联查班中职工信息（JOIN 职工信息表、心率表、异常心率表）
     */
    @GetMapping("/query")
    public Result<PageResult<DutyEmployeeVO>> query(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(required = false) String shiftDate,
            @RequestParam(required = false) String shiftType,
            @RequestParam(required = false) String empName,
            @RequestParam(required = false) String department) {
        return Result.success(dutyEmployeeService.listDutyEmployeeVO(page, size, shiftDate, shiftType, empName, department));
    }

    @GetMapping("/list")
    public Result<PageResult<DutyEmployee>> list(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(required = false) String shiftDate,
            @RequestParam(required = false) String shiftType,
            @RequestParam(required = false) Long empId) {
        return Result.success(dutyEmployeeService.list(page, size, shiftDate, shiftType, empId));
    }

    @GetMapping("/{id}")
    public Result<DutyEmployee> getById(@PathVariable Long id) {
        return Result.success(dutyEmployeeService.getById(id));
    }

    @PostMapping
    public Result<?> add(@RequestBody DutyEmployee dutyEmployee) {
        dutyEmployee.setId(null);
        dutyEmployeeService.save(dutyEmployee);
        return Result.success();
    }

    @PutMapping("/{id}")
    public Result<?> update(@PathVariable Long id, @RequestBody DutyEmployee dutyEmployee) {
        dutyEmployee.setId(id);
        dutyEmployeeService.save(dutyEmployee);
        return Result.success();
    }

    @DeleteMapping("/{id}")
    public Result<?> delete(@PathVariable Long id) {
        dutyEmployeeService.deleteById(id);
        return Result.success();
    }
}
