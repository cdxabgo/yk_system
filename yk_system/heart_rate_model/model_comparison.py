"""
三模型对比训练与评估框架

模型:
  1. LightGBM        - 有监督主线模型（23维手工特征）
  2. LSTM-Autoencoder - 无监督深度学习（时序重构）
  3. Isolation Forest  - 无监督传统方法（基线）

训练数据源:
  - 生成器模拟数据（逐点标签）
  - MIT-BIH 真实心律失常数据（专家标注）

评估指标:
  - Accuracy, Precision, Recall, F1-Score
  - ROC-AUC, PR-AUC
  - 各类异常检出率
  - 混淆矩阵

融合策略:
  - 硬投票：>=2 票同意 → 最终异常
  - 软投票：分数加权平均
"""

import numpy as np
import pandas as pd
import pickle
import os
import time
import warnings
warnings.filterwarnings('ignore')

from data_generator import HeartRateDataGenerator
from data_filter import HeartRateFilter
from enhanced_detector import EnhancedAnomalyDetector
from lgbm_model import LGBMAnomalyDetector
from lstm_detector import LSTMAutoencoderDetector, HAS_TF
from isolation_forest_detector import IForestDetector
from mitbih_loader import MITBIHLoader

from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix,
    classification_report, roc_curve, precision_recall_curve
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

    # ================================================================
    # 数据准备
    # ================================================================

    def prepare_synthetic_data(self, num_batches=500):
        """准备生成器数据（带逐点标签）"""
        print(f"\n[数据] 生成模拟数据 ({num_batches} 批次)...")
        generator = HeartRateDataGenerator()
        df = generator.generate_mixed_dataset(num_batches=num_batches)
        print(f"  总数据点: {len(df)}")
        print(f"  异常点: {df['is_abnormal'].sum()} ({df['is_abnormal'].mean()*100:.1f}%)")
        return df

    def prepare_mitbih_data(self, limit_records=None):
        """准备 MIT-BIH 真实数据"""
        print(f"\n[数据] 加载 MIT-BIH 数据...")
        loader = MITBIHLoader(data_dir='mitbih_data')
        loader.download_if_needed()
        df = loader.load_as_training_data(limit_records=limit_records or 10)
        return df

    def filter_data(self, df, hr_col='heart_rate'):
        """对数据中每个 batch 进行滤波"""
        filtered_rates = []
        if 'batch_id' in df.columns:
            for bid in df['batch_id'].unique():
                mask = df['batch_id'] == bid
                rates = df.loc[mask, hr_col].values
                filtered = self.filter.comprehensive_filter(rates)
                filtered_rates.extend(filtered)
        else:
            filtered_rates = self.filter.comprehensive_filter(df[hr_col].values)
        df = df.copy()
        df['heart_rate_filtered'] = filtered_rates
        return df

    # ================================================================
    # 特征提取（统一接口）
    # ================================================================

    def extract_lgbm_features(self, df, hr_col='heart_rate_filtered'):
        """为 LightGBM 提取 23 维特征"""
        features_list = []
        labels_list = []

        if 'batch_id' in df.columns:
            for bid in df['batch_id'].unique():
                batch = df[df['batch_id'] == bid]
                rates = batch[hr_col].values
                feats = self.lgbm.extract_features(rates)
                features_list.append(feats)
                labels_list.append(batch['is_abnormal'].values)
        else:
            rates = df[hr_col].values
            feats = self.lgbm.extract_features(rates)
            features_list.append(feats)
            labels_list.append(df['is_abnormal'].values)

        X = np.vstack(features_list)
        y = np.concatenate(labels_list).astype(int)
        return X, y

    def get_sequences_by_batch(self, df, hr_col='heart_rate_filtered'):
        """按 batch 提取滤波后的心率序列"""
        sequences = []
        labels = []
        if 'batch_id' in df.columns:
            for bid in df['batch_id'].unique():
                batch = df[df['batch_id'] == bid]
                sequences.append(batch[hr_col].values)
                labels.extend(batch['is_abnormal'].values)
        else:
            sequences.append(df[hr_col].values)
            labels = df['is_abnormal'].values
        return sequences, np.array(labels)

    # ================================================================
    # 模型训练
    # ================================================================

    def train_lgbm(self, df, hr_col='heart_rate_filtered'):
        """训练 LightGBM"""
        print("\n[LightGBM] 提取特征并训练...")
        X, y = self.extract_lgbm_features(df, hr_col)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        self.lgbm.train(X_train, y_train, num_boost_round=100)

        # 评估
        y_pred = self.lgbm.predict(X_test)
        y_prob = self.lgbm.predict_proba(X_test)

        metrics = self._compute_metrics(y_test, y_pred, y_prob)
        metrics['model'] = 'LightGBM'
        metrics['train_samples'] = len(X_train)
        metrics['test_samples'] = len(X_test)

        self.results['LightGBM'] = metrics
        self._print_metrics(metrics)

        # 保存
        self.lgbm.save_model(f'{self.output_dir}/models/lgbm_model.pkl')

    def train_lstm_ae(self, df, hr_col='heart_rate_filtered'):
        """训练 LSTM-Autoencoder"""
        if not HAS_TF:
            print("[LSTM-AE] TensorFlow 未安装，跳过")
            return

        print("\n[LSTM-AE] 准备训练...")
        sequences, all_labels = self.get_sequences_by_batch(df, hr_col)

        # 只用正常数据训练 AE
        normal_seqs = [seq for seq, lab in zip(sequences, df.groupby('batch_id')['is_abnormal'].max()) if lab == 0]
        # 如果按 batch_id 分组获取正常 batch
        normal_batches = []
        if 'batch_id' in df.columns:
            for bid in df['batch_id'].unique():
                batch_labels = df[df['batch_id'] == bid]['is_abnormal']
                if batch_labels.sum() == 0:  # 全部正常的 batch
                    normal_batches.append(df[df['batch_id'] == bid][hr_col].values)

        if len(normal_batches) < 3:
            # 如果纯正常 batch 不够，使用所有 batch 但只用其中的正常点
            normal_data = df[df['is_abnormal'] == 0][hr_col].values
            normal_batches = [normal_data]

        self.lstm_ae = LSTMAutoencoderDetector(sequence_length=15, latent_dim=8)
        self.lstm_ae.fit(normal_batches, epochs=30, batch_size=32, verbose=0)

        # 评估：用所有数据测试
        all_data = df[hr_col].values
        y_pred = self.lstm_ae.predict(all_data[:5000])  # 限制长度
        y_true = df['is_abnormal'].values[:5000]

        # 用 LSTM-AE 的异常分数计算 AUC
        scores = self.lstm_ae.score(all_data[:5000])

        metrics = self._compute_metrics(y_true, y_pred, scores)
        metrics['model'] = 'LSTM-Autoencoder'
        metrics['train_samples'] = sum(len(b) for b in normal_batches)
        metrics['test_samples'] = len(y_true)

        self.results['LSTM-Autoencoder'] = metrics
        self._print_metrics(metrics)

        self.lstm_ae.save(f'{self.output_dir}/models/lstm_ae.pkl')

    def train_isolation_forest(self, df, hr_col='heart_rate_filtered'):
        """训练 Isolation Forest"""
        print("\n[Isolation Forest] 训练...")
        all_data = df[hr_col].values

        self.iforest = IForestDetector(
            contamination=df['is_abnormal'].mean() or 0.1,
            window_size=10
        )
        self.iforest.fit(all_data)

        # 评估
        y_pred = self.iforest.predict(all_data[:5000])
        y_true = df['is_abnormal'].values[:5000]
        scores = self.iforest.score(all_data[:5000])

        metrics = self._compute_metrics(y_true, y_pred, scores)
        metrics['model'] = 'Isolation Forest'
        metrics['train_samples'] = len(all_data)
        metrics['test_samples'] = len(y_true)

        self.results['Isolation Forest'] = metrics
        self._print_metrics(metrics)

        self.iforest.save(f'{self.output_dir}/models/isolation_forest.pkl')

    def train_rule_based(self, df, hr_col='heart_rate_filtered'):
        """评估纯规则检测（作为对比基线）"""
        print("\n[Rule-based] 规则检测评估...")
        detector = EnhancedAnomalyDetector()

        all_preds = []
        all_labels = []
        if 'batch_id' in df.columns:
            for bid in df['batch_id'].unique():
                batch = df[df['batch_id'] == bid]
                rates = batch[hr_col].values
                results = detector.detect_all(rates)
                preds = np.zeros(len(rates), dtype=int)
                for idx in results['all']:
                    preds[idx] = 1
                all_preds.append(preds)
                all_labels.append(batch['is_abnormal'].values)

        y_pred = np.concatenate(all_preds)
        y_true = np.concatenate(all_labels).astype(int)

        metrics = self._compute_metrics(y_true, y_pred, y_pred.astype(float))
        metrics['model'] = 'Rule-based (baseline)'

        self.results['Rule-based'] = metrics
        self._print_metrics(metrics)

    # ================================================================
    # 融合策略
    # ================================================================

    def evaluate_voting_fusion(self, df, hr_col='heart_rate_filtered', sample_limit=3000):
        """评估投票融合效果"""
        print("\n[融合] 投票融合评估...")

        all_data = df[hr_col].values[:sample_limit]
        y_true = df['is_abnormal'].values[:sample_limit]

        # 获取各模型预测
        # LightGBM
        lgbm_preds = np.zeros(len(all_data), dtype=int)
        lgbm_scores = np.zeros(len(all_data))
        X, _ = self.extract_lgbm_features(df.head(sample_limit), hr_col)
        lgbm_preds = self.lgbm.predict(X)
        lgbm_scores = self.lgbm.predict_proba(X)

        # LSTM-AE
        lstm_preds = np.zeros(len(all_data), dtype=int)
        lstm_scores = np.zeros(len(all_data))
        if self.lstm_ae is not None:
            lstm_preds = self.lstm_ae.predict(all_data)
            lstm_scores = self.lstm_ae.score(all_data)

        # Isolation Forest
        if_preds = np.zeros(len(all_data), dtype=int)
        if_scores = np.zeros(len(all_data))
        if self.iforest is not None:
            if_preds = self.iforest.predict(all_data)
            if_scores = self.iforest.score(all_data)

        # 硬投票（>=2 同意）
        hard_votes = lgbm_preds + lstm_preds + if_preds
        hard_voting_preds = (hard_votes >= 2).astype(int)

        # 软投票（分数加权平均）
        soft_scores = (lgbm_scores + lstm_scores + if_scores) / 3.0
        soft_threshold = np.percentile(soft_scores, 90)
        soft_voting_preds = (soft_scores > soft_threshold).astype(int)

        # 评估
        print("\n  硬投票（>=2/3）:")
        hard_metrics = self._compute_metrics(y_true, hard_voting_preds, soft_scores)
        self._print_metrics(hard_metrics)

        print("\n  软投票（分数融合）:")
        soft_metrics = self._compute_metrics(y_true, soft_voting_preds, soft_scores)
        self._print_metrics(soft_metrics)

        self.results['Hard Voting Fusion'] = hard_metrics
        self.results['Soft Voting Fusion'] = soft_metrics

    # ================================================================
    # 评估工具
    # ================================================================

    def _compute_metrics(self, y_true, y_pred, y_scores=None):
        """计算所有评估指标"""
        # 处理可能为空的情况
        if len(np.unique(y_true)) < 2:
            auc = 0.5
            ap = 0.5
        elif y_scores is not None:
            try:
                auc = roc_auc_score(y_true, y_scores)
            except Exception:
                auc = 0.5
            try:
                ap = average_precision_score(y_true, y_scores)
            except Exception:
                ap = 0.5
        else:
            auc = 0.5
            ap = 0.5

        return {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, zero_division=0),
            'recall': recall_score(y_true, y_pred, zero_division=0),
            'f1': f1_score(y_true, y_pred, zero_division=0),
            'auc': auc,
            'avg_precision': ap,
            'tn': int(confusion_matrix(y_true, y_pred).ravel()[0]) if confusion_matrix(y_true, y_pred).size == 4 else 0,
            'fp': int(confusion_matrix(y_true, y_pred).ravel()[1]) if confusion_matrix(y_true, y_pred).size == 4 else 0,
            'fn': int(confusion_matrix(y_true, y_pred).ravel()[2]) if confusion_matrix(y_true, y_pred).size == 4 else 0,
            'tp': int(confusion_matrix(y_true, y_pred).ravel()[3]) if confusion_matrix(y_true, y_pred).size == 4 else 0,
        }

    def _print_metrics(self, metrics):
        """打印指标"""
        print(f"    Acc={metrics['accuracy']:.4f}  "
              f"Prec={metrics['precision']:.4f}  "
              f"Recall={metrics['recall']:.4f}  "
              f"F1={metrics['f1']:.4f}  "
              f"AUC={metrics['auc']:.4f}")

    # ================================================================
    # 综合报告
    # ================================================================

    def print_summary_report(self):
        """打印汇总对比报告"""
        if not self.results:
            print("暂无可用的评估结果")
            return

        print("\n" + "=" * 90)
        print("模型评估汇总报告")
        print("=" * 90)

        header = f"{'模型':22s} {'Acc':>8s} {'Prec':>8s} {'Recall':>8s} {'F1':>8s} {'AUC':>8s}"
        print(header)
        print("-" * 90)

        for model_name, m in self.results.items():
            print(f"{model_name:22s} {m['accuracy']:8.4f} {m['precision']:8.4f} "
                  f"{m['recall']:8.4f} {m['f1']:8.4f} {m['auc']:8.4f}")

        print("-" * 90)

        # 保存为 CSV
        df = pd.DataFrame(self.results).T
        df.index.name = 'model'
        csv_path = f'{self.output_dir}/model_comparison_results.csv'
        df.to_csv(csv_path, encoding='utf-8-sig')
        print(f"\n结果已保存: {csv_path}")

    def save_results(self):
        """保存完整结果"""
        path = f'{self.output_dir}/comparison_results.pkl'
        with open(path, 'wb') as f:
            pickle.dump(self.results, f)


def main():
    """完整训练+评估流程"""
    print("=" * 80)
    print("三模型对比训练与评估")
    print("=" * 80)

    comparison = ModelComparison(output_dir='output')

    # ====== 实验一：模拟数据上对比 ======
    print("\n" + "=" * 80)
    print("实验一：模拟数据集评估")
    print("=" * 80)

    # 准备数据
    df_syn = comparison.prepare_synthetic_data(num_batches=300)
    df_syn = comparison.filter_data(df_syn)

    # 训练所有模型
    comparison.train_rule_based(df_syn)       # 纯规则基线
    comparison.train_lgbm(df_syn)             # LightGBM
    comparison.train_isolation_forest(df_syn)  # Isolation Forest
    comparison.train_lstm_ae(df_syn)          # LSTM-Autoencoder

    # 融合评估
    comparison.evaluate_voting_fusion(df_syn)

    # 打印报告
    comparison.print_summary_report()
    comparison.save_results()

    # ====== 实验二：MIT-BIH 真实数据验证 ======
    print("\n" + "=" * 80)
    print("实验二：MIT-BIH 真实数据验证")
    print("=" * 80)

    df_real = comparison.prepare_mitbih_data(limit_records=5)
    df_real = comparison.filter_data(df_real, hr_col='heart_rate')

    # 用真实数据评估各模型（使用已训练模型）
    if comparison.lgbm.model:
        print("\n[MIT-BIH] LightGBM 评估...")
        X, y = comparison.extract_lgbm_features(df_real, hr_col='heart_rate_filtered')
        y_pred = comparison.lgbm.predict(X)
        y_prob = comparison.lgbm.predict_proba(X)
        m = comparison._compute_metrics(y, y_pred, y_prob)
        comparison.results['MITBIH-LightGBM'] = m
        comparison._print_metrics(m)

    if comparison.lstm_ae is not None:
        print("\n[MIT-BIH] LSTM-AE 评估...")
        data = df_real['heart_rate_filtered'].values
        y_pred = comparison.lstm_ae.predict(data)
        scores = comparison.lstm_ae.score(data)
        m = comparison._compute_metrics(
            df_real['is_abnormal'].values, y_pred, scores)
        comparison.results['MITBIH-LSTM-AE'] = m
        comparison._print_metrics(m)

    if comparison.iforest and comparison.iforest.model:
        print("\n[MIT-BIH] Isolation Forest 评估...")
        data = df_real['heart_rate_filtered'].values
        y_pred = comparison.iforest.predict(data)
        scores = comparison.iforest.score(data)
        m = comparison._compute_metrics(
            df_real['is_abnormal'].values, y_pred, scores)
        comparison.results['MITBIH-IForest'] = m
        comparison._print_metrics(m)

    # 最终汇总
    comparison.print_summary_report()
    comparison.save_results()

    print("\n[DONE] 全部实验完成！")


if __name__ == '__main__':
    main()
