package com.yk.system.service;

import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;
import com.yk.system.common.PageResult;
import com.yk.system.entity.EmployeeHeartRate;
import com.yk.system.entity.EmployeeMonitorVO;
import com.yk.system.entity.HeartRateLatestVO;
import com.yk.system.mapper.EmployeeHeartRateMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class HeartRateService {

    @Autowired
    private EmployeeHeartRateMapper heartRateMapper;

    public PageResult<EmployeeHeartRate> list(int page, int size, Long employeeId,
                                               Integer isAbnormal, String startTime, String endTime) {
        PageHelper.startPage(page, size);
        List<EmployeeHeartRate> list = heartRateMapper.list(employeeId, isAbnormal, startTime, endTime);
        PageInfo<EmployeeHeartRate> pageInfo = new PageInfo<>(list);
        return new PageResult<>(pageInfo.getTotal(), pageInfo.getList());
    }

    public EmployeeHeartRate getById(Long id) {
        return heartRateMapper.getById(id);
    }

    public void add(EmployeeHeartRate heartRate) {
        heartRateMapper.insert(heartRate);
    }

    public void deleteById(Long id) {
        heartRateMapper.deleteById(id);
    }

    public PageResult<EmployeeMonitorVO> queryMonitor(int page, int size,
                                                       String name, String job, Integer isAbnormal) {
        PageHelper.startPage(page, size);
        List<EmployeeMonitorVO> list = heartRateMapper.queryMonitor(name, job, isAbnormal);
        PageInfo<EmployeeMonitorVO> pageInfo = new PageInfo<>(list);
        return new PageResult<>(pageInfo.getTotal(), pageInfo.getList());
    }

    /**
     * 查询每位职工的最新一条心率记录（供前端10秒轮询使用）
     */
    public List<HeartRateLatestVO> getLatestPerEmployee() {
        return heartRateMapper.getLatestPerEmployee();
    }
}
