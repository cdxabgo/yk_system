package com.yk.system.mapper;

import com.yk.system.entity.EmployeeDiseaseRelation;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface EmployeeDiseaseRelationMapper {
    List<EmployeeDiseaseRelation> listByEmployeeId(@Param("employeeId") Long employeeId);

    List<EmployeeDiseaseRelation> listByDiseaseId(@Param("diseaseId") Long diseaseId);

    int insert(EmployeeDiseaseRelation relation);

    int deleteById(@Param("id") Long id);

    int deleteByEmployeeId(@Param("employeeId") Long employeeId);

    int deleteByDiseaseId(@Param("diseaseId") Long diseaseId);
}
