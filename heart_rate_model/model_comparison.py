"""
三模型对比训练与评估框架

模型: LightGBM(有监督) + LSTM-Autoencoder(无监督) + Isolation Forest(基线)
数据: 生成器模拟数据 + MIT-BIH 真实数据
评估: Accuracy / Precision / Recall / F1 / AUC + 投票融合
"""

import numpy as np
import pandas as pd
import pickle
import os
import warnings
warnings.filterwarnings('ignore')

from data_generator import HeartRateDataGenerator
from data_filter import HeartRateFilter
from enhanced_detector import EnhancedAnomalyDetector
from lgbm_model import LGBMAnomalyDetector
from lstm_detector import LSTMAutoencoderDetector, HAS_TF
from isolation_forest_detector import IForestDetector
from mitbih_loader import MITBIHLoader

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix
)


class ModelComparison:
    """三模型对比评估框架"""

    def __init__(self, output_dir='output'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(f'{output_dir}/models', exist_ok=True)
        self.filter = HeartRateFilter()
        self.lgbm = LGBMAnomalyDetector(window_size=30)
        self.lstm_ae = None
        self.iforest = None
        self.results = {}

    # ---- 数据准备 ----
    def prepare_synthetic_data(self, num_batches=500):
        print(f"\n[数据] 生成模拟数据 ({num_batches} 批次)...")
        df = HeartRateDataGenerator().generate_mixed_dataset(num_batches=num_batches)
        print(f"  总数据点: {len(df)}, 异常: {df['is_abnormal'].sum()} ({df['is_abnormal'].mean()*100:.1f}%)")
        return df

    def prepare_mitbih_data(self, limit_records=None):
        print(f"\n[数据] 加载 MIT-BIH 数据...")
        loader = MITBIHLoader(data_dir='mitbih_data')
        loader.download_if_needed()
        return loader.load_as_training_data(limit_records=limit_records or 10)

    def filter_data(self, df, hr_col='heart_rate'):
        filtered = []
        if 'batch_id' in df.columns:
            for bid in df['batch_id'].unique():
                mask = df['batch_id'] == bid
                filtered.extend(self.filter.comprehensive_filter(df.loc[mask, hr_col].values))
        else:
            filtered = self.filter.comprehensive_filter(df[hr_col].values)
        df = df.copy()
        df['heart_rate_filtered'] = filtered
        return df

    # ---- 特征提取 ----
    def extract_lgbm_features(self, df, hr_col='heart_rate_filtered'):
        feats, labels = [], []
        if 'batch_id' in df.columns:
            for bid in df['batch_id'].unique():
                batch = df[df['batch_id'] == bid]
                feats.append(self.lgbm.extract_features(batch[hr_col].values))
                labels.append(batch['is_abnormal'].values)
        else:
            feats.append(self.lgbm.extract_features(df[hr_col].values))
            labels.append(df['is_abnormal'].values)
        return np.vstack(feats), np.concatenate(labels).astype(int)

    # ---- 训练 ----
    def train_lgbm(self, df, hr_col='heart_rate_filtered'):
        print("\n[LightGBM] 训练...")
        X, y = self.extract_lgbm_features(df, hr_col)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        self.lgbm.train(X_train, y_train, num_boost_round=100)
        y_pred = self.lgbm.predict(X_test)
        y_prob = self.lgbm.predict_proba(X_test)
        m = self._metrics(y_test, y_pred, y_prob)
        m['model'] = 'LightGBM'
        self.results['LightGBM'] = m
        self.lgbm.save_model(f'{self.output_dir}/models/lgbm_model.pkl')
        self._print_m(m)

    def train_lstm_ae(self, df, hr_col='heart_rate_filtered'):
        if not HAS_TF:
            print("[LSTM-AE] TensorFlow 未安装, 跳过")
            return
        print("\n[LSTM-AE] 训练...")
        normal_batches = [
            df[df['batch_id'] == bid][hr_col].values
            for bid in df['batch_id'].unique()
            if df[df['batch_id'] == bid]['is_abnormal'].sum() == 0
        ] if 'batch_id' in df.columns else [df[df['is_abnormal'] == 0][hr_col].values]

        self.lstm_ae = LSTMAutoencoderDetector(sequence_length=15, latent_dim=8)
        self.lstm_ae.fit(normal_batches, epochs=30, verbose=0)

        data = df[hr_col].values[:3000]
        y_pred = self.lstm_ae.predict(data)
        scores = self.lstm_ae.score(data)
        m = self._metrics(df['is_abnormal'].values[:3000], y_pred, scores)
        m['model'] = 'LSTM-Autoencoder'
        self.results['LSTM-Autoencoder'] = m
        self.lstm_ae.save(f'{self.output_dir}/models/lstm_ae.pkl')
        self._print_m(m)

    def train_isolation_forest(self, df, hr_col='heart_rate_filtered'):
        print("\n[Isolation Forest] 训练...")
        data = df[hr_col].values
        self.iforest = IForestDetector(
            contamination=max(df['is_abnormal'].mean(), 0.05), window_size=10)
        self.iforest.fit(data)
        y_pred = self.iforest.predict(data[:3000])
        scores = self.iforest.score(data[:3000])
        m = self._metrics(df['is_abnormal'].values[:3000], y_pred, scores)
        m['model'] = 'Isolation Forest'
        self.results['Isolation Forest'] = m
        self.iforest.save(f'{self.output_dir}/models/isolation_forest.pkl')
        self._print_m(m)

    def train_rule_based(self, df, hr_col='heart_rate_filtered'):
        print("\n[Rule-based] 评估...")
        detector = EnhancedAnomalyDetector()
        all_preds, all_labels = [], []
        for bid in df['batch_id'].unique():
            batch = df[df['batch_id'] == bid]
            rates = batch[hr_col].values
            res = detector.detect_all(rates)
            preds = np.zeros(len(rates), dtype=int)
            for idx in res['all']:
                preds[idx] = 1
            all_preds.append(preds)
            all_labels.append(batch['is_abnormal'].values)
        y_pred = np.concatenate(all_preds)
        y_true = np.concatenate(all_labels).astype(int)
        m = self._metrics(y_true, y_pred, y_pred.astype(float))
        m['model'] = 'Rule-based'
        self.results['Rule-based'] = m
        self._print_m(m)

    # ---- 融合 ----
    def evaluate_voting(self, df, hr_col='heart_rate_filtered', limit=3000):
        print("\n[融合] 投票评估...")
        data = df[hr_col].values[:limit]
        y_true = df['is_abnormal'].values[:limit]

        # LightGBM
        X, _ = self.extract_lgbm_features(df.head(limit), hr_col)
        lgbm_p = self.lgbm.predict(X) if self.lgbm.model else np.zeros(limit, dtype=int)
        lgbm_s = self.lgbm.predict_proba(X) if self.lgbm.model else np.zeros(limit)

        # LSTM-AE
        lstm_p = self.lstm_ae.predict(data) if self.lstm_ae else np.zeros(limit, dtype=int)
        lstm_s = self.lstm_ae.score(data) if self.lstm_ae else np.zeros(limit)

        # IForest
        if_p = self.iforest.predict(data) if self.iforest else np.zeros(limit, dtype=int)
        if_s = self.iforest.score(data) if self.iforest else np.zeros(limit)

        # Hard voting
        hard = (lgbm_p + lstm_p + if_p >= 2).astype(int)
        # Soft voting
        soft_scores = (lgbm_s + lstm_s + if_s) / 3.0
        soft = (soft_scores > np.percentile(soft_scores, 90)).astype(int)

        print("  硬投票 (>=2/3):")
        hm = self._metrics(y_true, hard, soft_scores)
        self._print_m(hm)
        self.results['Hard Voting'] = hm

        print("  软投票:")
        sm = self._metrics(y_true, soft, soft_scores)
        self._print_m(sm)
        self.results['Soft Voting'] = sm

    # ---- 工具 ----
    def _metrics(self, y_true, y_pred, y_scores=None):
        if len(np.unique(y_true)) < 2 or y_scores is None:
            auc = ap = 0.5
        else:
            try:    auc = roc_auc_score(y_true, y_scores)
            except: auc = 0.5
            try:    ap = average_precision_score(y_true, y_scores)
            except: ap = 0.5
        cm = confusion_matrix(y_true, y_pred)
        return {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, zero_division=0),
            'recall': recall_score(y_true, y_pred, zero_division=0),
            'f1': f1_score(y_true, y_pred, zero_division=0),
            'auc': auc, 'avg_precision': ap,
            'tp': int(cm[1, 1]) if cm.size == 4 else 0,
            'fp': int(cm[0, 1]) if cm.size == 4 else 0,
            'tn': int(cm[0, 0]) if cm.size == 4 else 0,
            'fn': int(cm[1, 0]) if cm.size == 4 else 0,
        }

    def _print_m(self, m):
        print(f"    Acc={m['accuracy']:.4f} Prec={m['precision']:.4f} "
              f"Recall={m['recall']:.4f} F1={m['f1']:.4f} AUC={m['auc']:.4f}")

    def print_report(self):
        if not self.results:
            return
        print("\n" + "=" * 90)
        print(f"{'Model':22s} {'Acc':>8s} {'Prec':>8s} {'Recall':>8s} {'F1':>8s} {'AUC':>8s}")
        print("-" * 90)
        for name, m in self.results.items():
            print(f"{name:22s} {m['accuracy']:8.4f} {m['precision']:8.4f} "
                  f"{m['recall']:8.4f} {m['f1']:8.4f} {m['auc']:8.4f}")
        print("-" * 90)
        df = pd.DataFrame(self.results).T
        df.to_csv(f'{self.output_dir}/comparison_results.csv', encoding='utf-8-sig')
        print(f"结果已保存: {self.output_dir}/comparison_results.csv")


def main():
    print("=" * 80)
    print("三模型对比训练与评估")
    print("=" * 80)

    comp = ModelComparison()

    # 实验一: 模拟数据
    print("\n" + "=" * 80)
    print("实验一: 模拟数据集")
    print("=" * 80)
    df_syn = comp.prepare_synthetic_data(num_batches=300)
    df_syn = comp.filter_data(df_syn)

    comp.train_rule_based(df_syn)
    comp.train_lgbm(df_syn)
    comp.train_isolation_forest(df_syn)
    if HAS_TF:
        comp.train_lstm_ae(df_syn)
    comp.evaluate_voting(df_syn)
    comp.print_report()

    # 实验二: MIT-BIH
    print("\n" + "=" * 80)
    print("实验二: MIT-BIH 真实数据验证")
    print("=" * 80)
    df_real = comp.prepare_mitbih_data(limit_records=5)
    df_real = comp.filter_data(df_real, hr_col='heart_rate')

    if comp.lgbm.model:
        X, y = comp.extract_lgbm_features(df_real, hr_col='heart_rate_filtered')
        y_pred = comp.lgbm.predict(X)
        m = comp._metrics(y, y_pred, comp.lgbm.predict_proba(X))
        comp.results['MITBIH-LGBM'] = m
        comp._print_m(m)

    if comp.lstm_ae:
        y_pred = comp.lstm_ae.predict(df_real['heart_rate_filtered'].values)
        m = comp._metrics(df_real['is_abnormal'].values, y_pred,
                          comp.lstm_ae.score(df_real['heart_rate_filtered'].values))
        comp.results['MITBIH-LSTM-AE'] = m
        comp._print_m(m)

    if comp.iforest and comp.iforest.model:
        y_pred = comp.iforest.predict(df_real['heart_rate_filtered'].values)
        m = comp._metrics(df_real['is_abnormal'].values, y_pred,
                          comp.iforest.score(df_real['heart_rate_filtered'].values))
        comp.results['MITBIH-IForest'] = m
        comp._print_m(m)

    comp.print_report()
    print("\n[DONE] 全部实验完成!")


if __name__ == '__main__':
    main()
