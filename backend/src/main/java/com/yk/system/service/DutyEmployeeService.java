package com.yk.system.service;

import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;
import com.yk.system.common.PageResult;
import com.yk.system.entity.DutyEmployee;
import com.yk.system.entity.DutyEmployeeVO;
import com.yk.system.mapper.DutyEmployeeMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class DutyEmployeeService {

    @Autowired
    private DutyEmployeeMapper dutyEmployeeMapper;

    /**
     * 联查班中职工信息（JOIN 职工信息表、心率表、异常心率表）
     */
    public PageResult<DutyEmployeeVO> listDutyEmployeeVO(int page, int size, String shiftDate,
                                                          String shiftType, String empName, String department) {
        PageHelper.startPage(page, size);
        List<DutyEmployeeVO> list = dutyEmployeeMapper.listDutyEmployeeVO(shiftDate, shiftType, empName, department);
        PageInfo<DutyEmployeeVO> pageInfo = new PageInfo<>(list);
        return new PageResult<>(pageInfo.getTotal(), pageInfo.getList());
    }

    public PageResult<DutyEmployee> list(int page, int size, String shiftDate, String shiftType, Long empId) {
        PageHelper.startPage(page, size);
        List<DutyEmployee> list = dutyEmployeeMapper.list(shiftDate, shiftType, empId);
        PageInfo<DutyEmployee> pageInfo = new PageInfo<>(list);
        return new PageResult<>(pageInfo.getTotal(), pageInfo.getList());
    }

    public DutyEmployee getById(Long id) {
        return dutyEmployeeMapper.getById(id);
    }

    public void save(DutyEmployee dutyEmployee) {
        if (dutyEmployee.getId() == null) {
            dutyEmployeeMapper.insert(dutyEmployee);
        } else {
            dutyEmployeeMapper.update(dutyEmployee);
        }
    }

    public void deleteById(Long id) {
        dutyEmployeeMapper.deleteById(id);
    }
}
