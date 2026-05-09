package com.yk.system.entity;

/**
 * 今日监测统计数据
 */
public class TodayStatsVO {
    private long totalRecords;
    private long abnormalCount;
    private double abnormalRate;
    private long employeeCount;
    private long highRateCount;
    private long lowRateCount;
    private long extremeCount;

    public long getTotalRecords() { return totalRecords; }
    public void setTotalRecords(long totalRecords) { this.totalRecords = totalRecords; }
    public long getAbnormalCount() { return abnormalCount; }
    public void setAbnormalCount(long abnormalCount) { this.abnormalCount = abnormalCount; }
    public double getAbnormalRate() { return abnormalRate; }
    public void setAbnormalRate(double abnormalRate) { this.abnormalRate = abnormalRate; }
    public long getEmployeeCount() { return employeeCount; }
    public void setEmployeeCount(long employeeCount) { this.employeeCount = employeeCount; }
    public long getHighRateCount() { return highRateCount; }
    public void setHighRateCount(long highRateCount) { this.highRateCount = highRateCount; }
    public long getLowRateCount() { return lowRateCount; }
    public void setLowRateCount(long lowRateCount) { this.lowRateCount = lowRateCount; }
    public long getExtremeCount() { return extremeCount; }
    public void setExtremeCount(long extremeCount) { this.extremeCount = extremeCount; }
}
