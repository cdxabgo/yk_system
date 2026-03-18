package com.yk.system.service;

import com.yk.system.entity.Employee;
import com.yk.system.entity.EmployeeHeartRate;
import com.yk.system.mapper.EmployeeHeartRateMapper;
import com.yk.system.mapper.EmployeeMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Random;

/**
 * 心率数据模拟器
 * <p>
 * 每 30 秒为数据库中所有职工自动插入一条随机心率记录，
 * 供前端以10秒为间隔轮询数据库，模拟实时心率监测效果。
 * 正常心率 60-100 bpm（92%），心率过高 150-200 bpm（5%），心率过低 30-59 bpm（3%）。
 */
@Service
public class HeartRateSimulatorService {

    @Autowired
    private EmployeeHeartRateMapper heartRateMapper;

    @Autowired
    private EmployeeMapper employeeMapper;

    private final Random random = new Random();

    @Scheduled(fixedDelay = 30000)
    public void generateSimulatedData() {
        List<Employee> employees = employeeMapper.list(null, null);
        if (employees == null || employees.isEmpty()) {
            return;
        }

        for (Employee emp : employees) {
            EmployeeHeartRate hr = new EmployeeHeartRate();
            hr.setEmployeeId(emp.getId());

            double rand = random.nextDouble();
            int heartRate;
            int isAbnormal;

            if (rand < 0.05) {
                // 心率过高（5% 概率）
                heartRate = 150 + random.nextInt(51); // 150–200
                isAbnormal = 1;
            } else if (rand < 0.08) {
                // 心率过低（3% 概率）
                heartRate = 30 + random.nextInt(30); // 30–59
                isAbnormal = 1;
            } else {
                // 正常心率（92% 概率）
                heartRate = 60 + random.nextInt(41); // 60–100
                isAbnormal = 0;
            }

            hr.setHeartRate(heartRate);
            hr.setIsAbnormal(isAbnormal);
            hr.setCollectTime(LocalDateTime.now());
            hr.setDeviceId("simulator");
            heartRateMapper.insert(hr);
        }
    }
}
