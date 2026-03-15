package com.yk.system.service;

import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;
import com.yk.system.common.PageResult;
import com.yk.system.entity.Disease;
import com.yk.system.mapper.DiseaseMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class DiseaseService {

    @Autowired
    private DiseaseMapper diseaseMapper;

    public PageResult<Disease> list(int page, int size, String diseaseName, String diseaseType) {
        PageHelper.startPage(page, size);
        List<Disease> list = diseaseMapper.list(diseaseName, diseaseType);
        PageInfo<Disease> pageInfo = new PageInfo<>(list);
        return new PageResult<>(pageInfo.getTotal(), pageInfo.getList());
    }

    public Disease getById(Long id) {
        return diseaseMapper.getById(id);
    }

    public void save(Disease disease) {
        if (disease.getId() == null) {
            diseaseMapper.insert(disease);
        } else {
            diseaseMapper.update(disease);
        }
    }

    public void deleteById(Long id) {
        diseaseMapper.deleteById(id);
    }
}
