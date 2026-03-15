package com.yk.system.mapper;

import com.yk.system.entity.Employee;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface EmployeeMapper {
    List<Employee> list(@Param("name") String name,
                        @Param("department") String department,
                        @Param("empNo") String empNo);

    Employee getById(@Param("id") Long id);

    int insert(Employee employee);

    int update(Employee employee);

    int deleteById(@Param("id") Long id);

    Employee getByEmpNo(@Param("empNo") String empNo);
}
