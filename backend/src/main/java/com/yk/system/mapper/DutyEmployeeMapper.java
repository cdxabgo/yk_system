package com.yk.system.mapper;

import com.yk.system.entity.DutyEmployee;
import com.yk.system.entity.DutyEmployeeVO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface DutyEmployeeMapper {
    /**
     * 联查班中职工信息（JOIN 职工信息表、心率表、异常心率表）
     */
    List<DutyEmployeeVO> listDutyEmployeeVO(@Param("shiftDate") String shiftDate,
                                             @Param("shiftType") String shiftType,
                                             @Param("empName") String empName,
                                             @Param("department") String department);

    List<DutyEmployee> list(@Param("shiftDate") String shiftDate,
                             @Param("shiftType") String shiftType,
                             @Param("empId") Long empId);

    DutyEmployee getById(@Param("id") Long id);

    int insert(DutyEmployee dutyEmployee);

    int update(DutyEmployee dutyEmployee);

    int deleteById(@Param("id") Long id);
}
