package com.yk.system.controller;

import com.yk.system.common.PageResult;
import com.yk.system.common.Result;
import com.yk.system.entity.Employee;
import com.yk.system.service.EmployeeService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/employee")
public class EmployeeController {

    @Autowired
    private EmployeeService employeeService;

    @GetMapping("/list")
    public Result<PageResult<Employee>> list(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(required = false) String name,
            @RequestParam(required = false) String department,
            @RequestParam(required = false) String empNo) {
        return Result.success(employeeService.list(page, size, name, department, empNo));
    }

    @GetMapping("/{id}")
    public Result<Employee> getById(@PathVariable Long id) {
        return Result.success(employeeService.getById(id));
    }

    @PostMapping
    public Result<?> add(@RequestBody Employee employee) {
        employee.setId(null);
        employeeService.save(employee);
        return Result.success();
    }

    @PutMapping("/{id}")
    public Result<?> update(@PathVariable Long id, @RequestBody Employee employee) {
        employee.setId(id);
        employeeService.save(employee);
        return Result.success();
    }

    @DeleteMapping("/{id}")
    public Result<?> delete(@PathVariable Long id) {
        employeeService.deleteById(id);
        return Result.success();
    }
}
