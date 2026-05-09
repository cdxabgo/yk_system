package com.yk.system.entity;

/**
 * 按小时聚合的心率趋势数据
 */
public class HourlyTrendVO {
    private int hour;
    private double avgHeartRate;
    private long abnormalCount;
    private long totalCount;

    public int getHour() { return hour; }
    public void setHour(int hour) { this.hour = hour; }
    public double getAvgHeartRate() { return avgHeartRate; }
    public void setAvgHeartRate(double avgHeartRate) { this.avgHeartRate = avgHeartRate; }
    public long getAbnormalCount() { return abnormalCount; }
    public void setAbnormalCount(long abnormalCount) { this.abnormalCount = abnormalCount; }
    public long getTotalCount() { return totalCount; }
    public void setTotalCount(long totalCount) { this.totalCount = totalCount; }
}
