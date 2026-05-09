"""
LSTM-Autoencoder 无监督异常检测器

原理：
- 只用正常心率数据训练自编码器，学习"正常心率波形"的重构
- 异常数据通过自编码器时，重构误差显著增大
- 重构误差超过阈值 → 判定为异常
- 优势：不需要异常标签，天然适合医疗场景（异常样本少且多样）
"""

import numpy as np
import pickle
import os
import warnings
warnings.filterwarnings('ignore')

# 尝试导入 TensorFlow / Keras
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, Model
    HAS_TF = True
except ImportError:
    HAS_TF = False
    print("⚠ TensorFlow 未安装，LSTM-Autoencoder 将不可用")
    print("  安装命令: pip install tensorflow")


class LSTMAutoencoderDetector:
    """
    LSTM-Autoencoder 无监督异常检测器

    训练：只用正常数据，最小化重构误差
    推理：重构误差超过阈值 → 异常
    """

    def __init__(self, sequence_length=30, latent_dim=8, threshold_percentile=95):
        """
        Args:
            sequence_length: 输入序列长度（默认 30 = 5 分钟数据）
            latent_dim: 潜在空间维度
            threshold_percentile: 异常阈值百分位（训练集重构误差的分布）
        """
        if not HAS_TF:
            raise ImportError("需要安装 TensorFlow: pip install tensorflow")

        self.sequence_length = sequence_length
        self.latent_dim = latent_dim
        self.threshold_percentile = threshold_percentile
        self.threshold = None
        self.autoencoder = None
        self.encoder = None
        self.history = None

    def _build_model(self, input_dim=1):
        """构建 LSTM-Autoencoder 网络（单模型方式，避免 graph 不匹配）"""
        inputs = layers.Input(shape=(self.sequence_length, input_dim), name='ae_input')

        # Encoder
        x = layers.LSTM(32, return_sequences=True, name='enc_lstm1')(inputs)
        x = layers.LSTM(16, return_sequences=False, name='enc_lstm2')(x)
        latent = layers.Dense(self.latent_dim, activation='relu', name='latent')(x)

        # Decoder
        x = layers.RepeatVector(self.sequence_length, name='dec_repeat')(latent)
        x = layers.LSTM(16, return_sequences=True, name='dec_lstm1')(x)
        x = layers.LSTM(32, return_sequences=True, name='dec_lstm2')(x)
        outputs = layers.TimeDistributed(
            layers.Dense(input_dim, activation='linear'), name='dec_output')(x)

        self.autoencoder = Model(inputs, outputs, name='lstm_autoencoder')
        self.autoencoder.compile(optimizer='adam', loss='mse', metrics=['mae'])

        return self.autoencoder

    def _prepare_sequences(self, data, sequence_length=None):
        """
        将一维心率序列转为滑动窗口输入

        Args:
            data: 1D array of heart rates
            sequence_length: 窗口长度

        Returns:
            (n_sequences, sequence_length, 1) array
        """
        if sequence_length is None:
            sequence_length = self.sequence_length

        if len(data) < sequence_length:
            return np.array([]).reshape(0, sequence_length, 1)

        sequences = []
        for i in range(len(data) - sequence_length + 1):
            seq = data[i:i + sequence_length]
            sequences.append(seq)

        return np.array(sequences).reshape(-1, sequence_length, 1)

    def fit(self, normal_data, epochs=50, batch_size=32, validation_split=0.1, verbose=0):
        """
        用正常心率数据训练自编码器

        Args:
            normal_data: 1D array of normal heart rates（或嵌套 list 的 batches）
            epochs: 训练轮数
            batch_size: 批大小
            validation_split: 验证集比例
            verbose: 0=静默, 1=进度条
        """
        # 处理输入：可能是 1D array 或 batches 列表
        if isinstance(normal_data, list):
            all_normal = np.concatenate([np.array(b) for b in normal_data])
        else:
            all_normal = np.array(normal_data)

        # 构建序列
        X_train = self._prepare_sequences(all_normal)
        if len(X_train) == 0:
            raise ValueError(f"数据长度 ({len(all_normal)}) 不足以构建序列 (需要 > {self.sequence_length})")

        X_train = X_train.astype(np.float32)

        print(f"训练序列数: {len(X_train)}, 序列长度: {self.sequence_length}")

        # 构建模型
        if self.autoencoder is None:
            self._build_model(input_dim=1)

        # 手动划分验证集
        if validation_split > 0 and len(X_train) > 10:
            split_idx = int(len(X_train) * (1 - validation_split))
            X_val = X_train[split_idx:]
            X_train_fit = X_train[:split_idx]
            validation_data = (X_val, X_val)
        else:
            X_train_fit = X_train
            validation_data = None

        # 训练
        self.history = self.autoencoder.fit(
            X_train_fit, X_train_fit,  # 输入=输出（重构任务）
            epochs=epochs,
            batch_size=batch_size,
            validation_data=validation_data,
            verbose=verbose,
            shuffle=True
        )

        # 计算异常阈值
        train_recon = self.autoencoder.predict(X_train, verbose=0)
        train_errors = np.mean(np.square(X_train - train_recon), axis=(1, 2))
        self.threshold = np.percentile(train_errors, self.threshold_percentile)

        print(f"[OK] LSTM-Autoencoder 训练完成")
        print(f"  训练损失: {self.history.history['loss'][-1]:.4f}")
        print(f"  异常阈值 ({self.threshold_percentile}%): {self.threshold:.4f}")

        return self.history

    def predict(self, data, return_scores=False):
        """
        预测异常（逐点）

        Args:
            data: 1D array of heart rates，长度 ≥ sequence_length
            return_scores: 是否返回异常分数

        Returns:
            predictions: (len(data),) binary array (0=正常, 1=异常)
            scores: 异常分数（只有 return_scores=True 时）
        """
        if self.autoencoder is None:
            raise ValueError("模型未训练，请先调用 fit()")

        data = np.array(data)
        if len(data) < self.sequence_length:
            # 数据不足，不做预测
            if return_scores:
                return np.zeros(len(data), dtype=int), np.zeros(len(data))
            return np.zeros(len(data), dtype=int)

        # 构建序列
        X = self._prepare_sequences(data).astype(np.float32)
        n_sequences = len(X)

        # 重构
        X_recon = self.autoencoder.predict(X, verbose=0)
        seq_errors = np.mean(np.square(X - X_recon), axis=(1, 2))  # (n_sequences,)

        # 序列级异常判定
        seq_predictions = (seq_errors > self.threshold).astype(int)

        # 映射回逐点预测
        point_predictions = np.zeros(len(data), dtype=int)
        point_scores = np.zeros(len(data))

        for i in range(n_sequences):
            for j in range(self.sequence_length):
                idx = i + j
                point_scores[idx] = max(point_scores[idx], seq_errors[i])
                point_predictions[idx] = max(point_predictions[idx], seq_predictions[i])

        if return_scores:
            return point_predictions, point_scores

        return point_predictions

    def score(self, data):
        """计算异常分数（0-1 之间，越高越异常）"""
        _, scores = self.predict(data, return_scores=True)
        # 归一化到 [0, 1]
        if self.threshold and self.threshold > 0:
            scores = np.clip(scores / (self.threshold * 3), 0, 1)
        return scores

    def save(self, filepath):
        """保存模型"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Keras 模型保存为 .keras 格式
        keras_path = filepath.replace('.pkl', '.keras')
        if self.autoencoder:
            self.autoencoder.save(keras_path)

        # 参数保存为 pickle
        params = {
            'sequence_length': self.sequence_length,
            'latent_dim': self.latent_dim,
            'threshold_percentile': self.threshold_percentile,
            'threshold': self.threshold,
            'keras_path': keras_path
        }
        with open(filepath, 'wb') as f:
            pickle.dump(params, f)
        print(f"[OK] LSTM-Autoencoder 已保存: {filepath}")

    @classmethod
    def load(cls, filepath):
        """加载模型"""
        if not HAS_TF:
            raise ImportError("需要安装 TensorFlow")

        with open(filepath, 'rb') as f:
            params = pickle.load(f)

        detector = cls(
            sequence_length=params['sequence_length'],
            latent_dim=params['latent_dim'],
            threshold_percentile=params['threshold_percentile']
        )
        detector.threshold = params['threshold']

        keras_path = params.get('keras_path', filepath.replace('.pkl', '.keras'))
        if os.path.exists(keras_path):
            detector.autoencoder = keras.models.load_model(keras_path)
        else:
            print(f"⚠ Keras 模型文件不存在: {keras_path}")

        return detector


if __name__ == '__main__':
    from data_generator import HeartRateDataGenerator
    from data_filter import HeartRateFilter
    import time

    if not HAS_TF:
        print("跳过测试：TensorFlow 未安装")
        exit(0)

    print("=" * 60)
    print("LSTM-Autoencoder 测试")
    print("=" * 60)

    # 生成训练数据（只用正常数据）
    print("\n[1] 生成训练数据...")
    generator = HeartRateDataGenerator()
    normal_sequences = []
    for _ in range(100):
        rates, labels, _ = generator.generate_normal_data(num_points=18)
        normal_sequences.append(rates)

    # 训练模型
    print("\n[2] 训练 LSTM-Autoencoder...")
    detector = LSTMAutoencoderDetector(sequence_length=10, latent_dim=4)
    detector.fit(normal_sequences, epochs=20, verbose=0)

    # 测试：生成包含异常的混合数据
    print("\n[3] 测试...")
    filter_obj = HeartRateFilter()

    # 正常数据
    normal, _, _ = generator.generate_normal_data(18)
    pred_normal = detector.predict(normal)
    score_normal = detector.score(normal)

    # 异常数据（高心率）
    abnormal, labels_true, types_true = generator.generate_high_rate_anomaly(18)
    filtered = filter_obj.comprehensive_filter(abnormal)
    pred_abnormal = detector.predict(filtered)
    score_abnormal = detector.score(filtered)

    print(f"\n正常数据重构分数: 均值={score_normal.mean():.4f}, 最大={score_normal.max():.4f}")
    print(f"异常数据重构分数: 均值={score_abnormal.mean():.4f}, 最大={score_abnormal.max():.4f}")

    print(f"正常数据误报: {pred_normal.sum()}/{len(pred_normal)}")
    print(f"异常数据检出: {pred_abnormal.sum()}/{len(pred_abnormal)}")
    print(f"真实异常标签: {sum(labels_true)}/{len(labels_true)}")

    # 保存
    print("\n[4] 保存模型...")
    os.makedirs('output/models', exist_ok=True)
    detector.save('output/models/lstm_ae.pkl')
    print("[OK] 完成")
