package com.yk.system.mapper;

import com.yk.system.entity.EmployeeHeartRate;
import com.yk.system.entity.EmployeeMonitorVO;
import com.yk.system.entity.HeartRateLatestVO;
import com.yk.system.entity.HourlyTrendVO;
import com.yk.system.entity.TodayStatsVO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface EmployeeHeartRateMapper {
    List<EmployeeHeartRate> list(@Param("employeeId") Long employeeId,
                                  @Param("isAbnormal") Integer isAbnormal,
                                  @Param("startTime") String startTime,
                                  @Param("endTime") String endTime);

    EmployeeHeartRate getById(@Param("id") Long id);

    int insert(EmployeeHeartRate heartRate);

    int deleteById(@Param("id") Long id);

    /**
     * 班中职工监控查询：JOIN 职工信息表 + 心率表 + 异常心率统计
     */
    List<EmployeeMonitorVO> queryMonitor(@Param("name") String name,
                                          @Param("job") String job,
                                          @Param("isAbnormal") Integer isAbnormal);

    /**
     * 查询每位职工的最新一条心率记录（供前端10秒轮询使用）
     */
    List<HeartRateLatestVO> getLatestPerEmployee();

    /**
     * 查询某职工当天心率记录
     */
    List<EmployeeHeartRate> getTodayByEmployeeId(@Param("employeeId") Long employeeId);

    /**
     * 今日监测统计（总记录数、异常数、异常率、员工数、各类异常分布）
     */
    TodayStatsVO getTodayStats();

    /**
     * 按小时聚合的心率趋势（指定日期）
     */
    List<HourlyTrendVO> getHourlyTrend(@Param("date") String date);

    /**
     * 某职工指定日期的心率时序数据
     */
    List<EmployeeHeartRate> getEmployeeTimeSeries(@Param("employeeId") Long employeeId,
                                                   @Param("date") String date);
}
