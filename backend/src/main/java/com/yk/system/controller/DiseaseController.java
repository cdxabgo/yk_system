package com.yk.system.controller;

import com.yk.system.common.PageResult;
import com.yk.system.common.Result;
import com.yk.system.entity.Disease;
import com.yk.system.service.DiseaseService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/disease")
public class DiseaseController {

    @Autowired
    private DiseaseService diseaseService;

    @GetMapping("/list")
    public Result<PageResult<Disease>> list(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(required = false) String diseaseName,
            @RequestParam(required = false) String level) {
        return Result.success(diseaseService.list(page, size, diseaseName, level));
    }

    @GetMapping("/{id}")
    public Result<Disease> getById(@PathVariable Long id) {
        return Result.success(diseaseService.getById(id));
    }

    @PostMapping
    public Result<?> add(@RequestBody Disease disease) {
        disease.setId(null);
        diseaseService.save(disease);
        return Result.success();
    }

    @PutMapping("/{id}")
    public Result<?> update(@PathVariable Long id, @RequestBody Disease disease) {
        disease.setId(id);
        diseaseService.save(disease);
        return Result.success();
    }

    @DeleteMapping("/{id}")
    public Result<?> delete(@PathVariable Long id) {
        diseaseService.deleteById(id);
        return Result.success();
    }
}
