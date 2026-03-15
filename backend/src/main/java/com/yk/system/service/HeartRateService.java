package com.yk.system.service;

import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;
import com.yk.system.common.PageResult;
import com.yk.system.entity.HeartRate;
import com.yk.system.mapper.HeartRateMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class HeartRateService {

    @Autowired
    private HeartRateMapper heartRateMapper;

    public PageResult<HeartRate> list(int page, int size, Long empId, String status,
                                       String startTime, String endTime) {
        PageHelper.startPage(page, size);
        List<HeartRate> list = heartRateMapper.list(empId, status, startTime, endTime);
        PageInfo<HeartRate> pageInfo = new PageInfo<>(list);
        return new PageResult<>(pageInfo.getTotal(), pageInfo.getList());
    }

    public HeartRate getById(Long id) {
        return heartRateMapper.getById(id);
    }

    public void add(HeartRate heartRate) {
        heartRateMapper.insert(heartRate);
    }

    public void deleteById(Long id) {
        heartRateMapper.deleteById(id);
    }
}
