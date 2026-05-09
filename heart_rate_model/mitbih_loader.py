"""
MIT-BIH Arrhythmia Database 加载器
将 ECG 信号 + 专家标注 转换为 10 秒间隔心率序列
"""

import numpy as np
import pandas as pd
import wfdb
import os
from collections import Counter
from typing import List, Dict, Tuple

NORMAL_BEATS = {'N', 'e', 'j'}
ABNORMAL_BEATS = {
    'V': '室性早搏', 'A': '房性早搏', 'F': '融合心跳',
    'L': '左束支传导阻滞', 'R': '右束支传导阻滞', '/': '起搏心跳',
    'Q': '未分类异常', 'a': '异常房性早搏', 'J': '交界性早搏',
    'S': '室上性早搏', 'E': '室性逸搏', '!': '室颤'
}
ALL_RECORDS = list(range(100, 125)) + list(range(200, 235))


class MITBIHLoader:
    """MIT-BIH 数据加载与转换器"""

    def __init__(self, data_dir='mitbih_data', window_seconds=10):
        self.data_dir = data_dir
        self.window_seconds = window_seconds
        os.makedirs(data_dir, exist_ok=True)

    def download_if_needed(self):
        """检查并下载 MIT-BIH 数据"""
        if os.path.exists(os.path.join(self.data_dir, 'RECORDS')):
            print(f"[OK] 数据已存在: {self.data_dir}")
            return
        print("正在从 PhysioNet 下载 MIT-BIH Arrhythmia Database...")
        try:
            wfdb.dl_database('mitdb', dl_dir=self.data_dir)
            print("[OK] 下载完成")
        except Exception as e:
            print(f"[WARN] 自动下载失败: {e}，将使用在线读取")

    def load_record(self, record_num: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray, int]:
        """加载单条记录，返回 (r_peaks, beat_labels, rr_intervals, fs)"""
        try:
            record = wfdb.rdrecord(os.path.join(self.data_dir, str(record_num)))
            annotation = wfdb.rdann(os.path.join(self.data_dir, str(record_num)), 'atr')
        except Exception:
            record = wfdb.rdrecord(str(record_num), pn_dir='mitdb')
            annotation = wfdb.rdann(str(record_num), 'atr', pn_dir='mitdb')

        r_peaks = annotation.sample
        beat_labels = np.array(list(annotation.symbol))
        rr_intervals = np.diff(r_peaks) / record.fs
        return r_peaks, beat_labels, rr_intervals, record.fs

    def compute_instantaneous_hr(self, r_peaks, beat_labels, fs):
        """逐拍心率 + 异常标注"""
        rr = np.diff(r_peaks) / fs
        valid = (rr > 0.24) & (rr < 2.0)
        results = []
        for i in range(len(rr)):
            if not valid[i]:
                continue
            hr = 60.0 / rr[i]
            beat_time = r_peaks[i + 1] / fs
            label = beat_labels[i + 1] if i + 1 < len(beat_labels) else 'N'
            is_ab = 1 if label in ABNORMAL_BEATS else 0
            results.append({
                'beat_time': beat_time, 'heart_rate': round(hr, 1),
                'is_abnormal': is_ab,
                'anomaly_type': ABNORMAL_BEATS.get(label, '') if is_ab else '',
                'beat_label': label
            })
        return pd.DataFrame(results)

    def aggregate_to_windows(self, beat_df, record_num):
        """聚合为 10 秒窗口"""
        if len(beat_df) == 0:
            return pd.DataFrame()
        max_time = beat_df['beat_time'].max()
        ws = np.arange(0, max_time, self.window_seconds)
        rows = []
        for i, (w_start, w_end) in enumerate(zip(ws, ws + self.window_seconds)):
            wb = beat_df[(beat_df['beat_time'] >= w_start) & (beat_df['beat_time'] < w_end)]
            if len(wb) == 0:
                continue
            avg_hr = wb['heart_rate'].mean()
            ab_cnt = wb['is_abnormal'].sum()
            is_ab = 1 if ab_cnt > 0 else 0
            if is_ab:
                if avg_hr > 150 and ab_cnt >= 2:
                    mtype = 'high_rate'
                elif avg_hr < 60 and ab_cnt >= 2:
                    mtype = 'low_rate'
                elif avg_hr >= 200 or avg_hr <= 30:
                    mtype = 'extreme_value'
                else:
                    mtype = 'arrhythmia'
            else:
                mtype = 'normal'
            rows.append({
                'window_id': i, 'batch_id': record_num, 'heart_rate': round(avg_hr, 1),
                'is_abnormal': is_ab, 'anomaly_type': mtype,
                'abnormal_beat_count': ab_cnt, 'total_beat_count': len(wb),
                'record_num': record_num
            })
        return pd.DataFrame(rows)

    def load_as_training_data(self, record_nums=None, limit_records=None):
        """加载 MIT-BIH 数据为训练用 DataFrame"""
        if record_nums is None:
            record_nums = ALL_RECORDS
        if limit_records:
            record_nums = record_nums[:limit_records]

        all_windows = []
        stats = {'total_beats': 0, 'abnormal_beats': 0, 'total_windows': 0, 'abnormal_windows': 0}

        print(f"加载 MIT-BIH 数据 ({len(record_nums)} 条记录)...")
        for rec in record_nums:
            try:
                r_peaks, beat_labels, rr, fs = self.load_record(rec)
                beat_df = self.compute_instantaneous_hr(r_peaks, beat_labels, fs)
                windows = self.aggregate_to_windows(beat_df, rec)
                if len(windows) > 0:
                    all_windows.append(windows)
                stats['total_beats'] += len(beat_df)
                stats['abnormal_beats'] += beat_df['is_abnormal'].sum()
                stats['total_windows'] += len(windows)
                stats['abnormal_windows'] += windows['is_abnormal'].sum()
                print(f"  记录 {rec}: {len(beat_df)} 心跳 -> {len(windows)} 窗口, "
                      f"异常率 {windows['is_abnormal'].mean()*100:.1f}%")
            except Exception as e:
                print(f"  记录 {rec}: 加载失败 - {e}")

        if not all_windows:
            raise RuntimeError("未加载到任何记录")
        result = pd.concat(all_windows, ignore_index=True)
        print(f"\n{'='*60}")
        print(f"加载完成: {stats['total_beats']} 心跳, {stats['total_windows']} 窗口")
        print(f"异常窗口: {stats['abnormal_windows']} ({stats['abnormal_windows']/stats['total_windows']*100:.1f}%)")
        print(f"{'='*60}")
        return result

    def get_record_info(self, record_num):
        r_peaks, beat_labels, rr, fs = self.load_record(record_num)
        counts = Counter(beat_labels)
        total = len(beat_labels)
        ab = sum(counts.get(k, 0) for k in ABNORMAL_BEATS)
        return {
            'record_num': record_num, 'duration_min': len(r_peaks) / fs / 60,
            'total_beats': total, 'abnormal_beats': ab,
            'abnormal_rate': ab / total * 100 if total else 0,
            'distribution': {k: v for k, v in counts.most_common(10)}
        }


if __name__ == '__main__':
    loader = MITBIHLoader(data_dir='mitbih_data')
    loader.download_if_needed()
    print("\n=== 记录 100 信息 ===")
    info = loader.get_record_info(100)
    for k, v in info.items():
        print(f"  {k}: {v}")
    print("\n=== 加载训练数据 (5条记录) ===")
    df = loader.load_as_training_data(limit_records=5)
    print("\n前10条:")
    print(df.head(10))
    print("\n异常类型分布:")
    print(df['anomaly_type'].value_counts())
    os.makedirs('output', exist_ok=True)
    df.to_csv('output/mitbih_training_data.csv', index=False, encoding='utf-8-sig')
    print("\n[OK] 已保存: output/mitbih_training_data.csv")
