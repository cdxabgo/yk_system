package com.yk.system.mapper;

import com.yk.system.entity.AbnormalHeartRate;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface AbnormalHeartRateMapper {
    List<AbnormalHeartRate> list(@Param("empId") Long empId,
                                  @Param("alertLevel") String alertLevel,
                                  @Param("handleStatus") String handleStatus);

    AbnormalHeartRate getById(@Param("id") Long id);

    int insert(AbnormalHeartRate abnormalHeartRate);

    int deleteById(@Param("id") Long id);
}
