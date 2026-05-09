package com.yk.system.mapper;

import com.yk.system.entity.Disease;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface DiseaseMapper {
    List<Disease> list(@Param("diseaseName") String diseaseName,
                       @Param("diseaseType") String diseaseType);

    Disease getById(@Param("id") Long id);

    int insert(Disease disease);

    int update(Disease disease);

    int deleteById(@Param("id") Long id);
}
