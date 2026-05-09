package com.yk.system.service;

import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;
import com.yk.system.common.PageResult;
import com.yk.system.entity.Employee;
import com.yk.system.mapper.EmployeeDiseaseRelationMapper;
import com.yk.system.mapper.EmployeeMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class EmployeeService {

    @Autowired
    private EmployeeMapper employeeMapper;

    @Autowired
    private EmployeeDiseaseRelationMapper employeeDiseaseRelationMapper;

    public PageResult<Employee> list(int page, int size, String name, String job) {
        PageHelper.startPage(page, size);
        List<Employee> list = employeeMapper.list(name, job);
        PageInfo<Employee> pageInfo = new PageInfo<>(list);
        return new PageResult<>(pageInfo.getTotal(), pageInfo.getList());
    }

    public Employee getById(Long id) {
        return employeeMapper.getById(id);
    }

    public void save(Employee employee) {
        if (employee.getId() == null) {
            employeeMapper.insert(employee);
        } else {
            employeeMapper.update(employee);
        }
    }

    @Transactional
    public void deleteById(Long id) {
        employeeDiseaseRelationMapper.deleteByEmployeeId(id);
        employeeMapper.deleteById(id);
    }
}
