package com.yk.system.mapper;

import com.yk.system.entity.HeartRate;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface HeartRateMapper {
    List<HeartRate> list(@Param("empId") Long empId,
                         @Param("status") String status,
                         @Param("startTime") String startTime,
                         @Param("endTime") String endTime);

    HeartRate getById(@Param("id") Long id);

    int insert(HeartRate heartRate);

    int deleteById(@Param("id") Long id);

    int deleteByEmpId(@Param("empId") Long empId);
}
