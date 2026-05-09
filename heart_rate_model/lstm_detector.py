"""
LSTM-Autoencoder 无监督异常检测器
只用正常数据训练，重构误差大 = 异常
"""

import numpy as np
import pickle
import os
import warnings
warnings.filterwarnings('ignore')

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, Model
    HAS_TF = True
except ImportError:
    HAS_TF = False


class LSTMAutoencoderDetector:
    def __init__(self, sequence_length=30, latent_dim=8, threshold_percentile=95):
        if not HAS_TF:
            raise ImportError("pip install tensorflow")
        self.sequence_length = sequence_length
        self.latent_dim = latent_dim
        self.threshold_percentile = threshold_percentile
        self.threshold = None
        self.autoencoder = None
        self.history = None

    def _build_model(self, input_dim=1):
        inputs = layers.Input(shape=(self.sequence_length, input_dim))
        # Encoder
        x = layers.LSTM(32, return_sequences=True)(inputs)
        x = layers.LSTM(16, return_sequences=False)(x)
        latent = layers.Dense(self.latent_dim, activation='relu')(x)
        # Decoder
        x = layers.RepeatVector(self.sequence_length)(latent)
        x = layers.LSTM(16, return_sequences=True)(x)
        x = layers.LSTM(32, return_sequences=True)(x)
        outputs = layers.TimeDistributed(layers.Dense(input_dim, activation='linear'))(x)
        self.autoencoder = Model(inputs, outputs, name='lstm_ae')
        self.autoencoder.compile(optimizer='adam', loss='mse', metrics=['mae'])
        return self.autoencoder

    def _prepare_sequences(self, data):
        data = np.array(data)
        if len(data) < self.sequence_length:
            return np.array([]).reshape(0, self.sequence_length, 1)
        seqs = [data[i:i + self.sequence_length] for i in range(len(data) - self.sequence_length + 1)]
        return np.array(seqs).reshape(-1, self.sequence_length, 1)

    def fit(self, normal_data, epochs=50, batch_size=32, validation_split=0.1, verbose=0):
        if isinstance(normal_data, list):
            all_data = np.concatenate([np.array(d).flatten() for d in normal_data if len(np.array(d).flatten()) > 0])
        else:
            all_data = np.array(normal_data).flatten()

        X = self._prepare_sequences(all_data).astype(np.float32)
        if len(X) == 0:
            raise ValueError(f"数据不足 (需>{self.sequence_length})")
        print(f"训练序列数: {len(X)}, 序列长度: {self.sequence_length}")

        if self.autoencoder is None:
            self._build_model()

        split = int(len(X) * (1 - validation_split)) if validation_split > 0 and len(X) > 10 else len(X)
        self.history = self.autoencoder.fit(
            X[:split], X[:split], epochs=epochs, batch_size=batch_size,
            validation_data=(X[split:], X[split:]) if split < len(X) else None,
            verbose=verbose, shuffle=True
        )

        recon = self.autoencoder.predict(X, verbose=0)
        errors = np.mean(np.square(X - recon), axis=(1, 2))
        self.threshold = np.percentile(errors, self.threshold_percentile)
        print(f"[OK] LSTM-AE 训练完成, 损失={self.history.history['loss'][-1]:.4f}, 阈值={self.threshold:.4f}")

    def predict(self, data):
        if self.autoencoder is None:
            raise ValueError("模型未训练")
        data = np.array(data)
        if len(data) < self.sequence_length:
            return np.zeros(len(data), dtype=int)
        X = self._prepare_sequences(data).astype(np.float32)
        recon = self.autoencoder.predict(X, verbose=0)
        errors = np.mean(np.square(X - recon), axis=(1, 2))
        seq_preds = (errors > self.threshold).astype(int)
        point_preds = np.zeros(len(data), dtype=int)
        for i in range(len(seq_preds)):
            for j in range(self.sequence_length):
                point_preds[i + j] = max(point_preds[i + j], seq_preds[i])
        return point_preds

    def score(self, data):
        if self.autoencoder is None:
            return np.zeros(len(data))
        data = np.array(data)
        if len(data) < self.sequence_length:
            return np.zeros(len(data))
        X = self._prepare_sequences(data).astype(np.float32)
        recon = self.autoencoder.predict(X, verbose=0)
        errors = np.mean(np.square(X - recon), axis=(1, 2))
        scores = np.zeros(len(data))
        for i in range(len(errors)):
            for j in range(self.sequence_length):
                scores[i + j] = max(scores[i + j], errors[i])
        if self.threshold and self.threshold > 0:
            scores = np.clip(scores / (self.threshold * 3), 0, 1)
        return scores

    def save(self, filepath):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        keras_path = filepath.replace('.pkl', '.keras')
        if self.autoencoder:
            self.autoencoder.save(keras_path)
        with open(filepath, 'wb') as f:
            pickle.dump({
                'sequence_length': self.sequence_length, 'latent_dim': self.latent_dim,
                'threshold_percentile': self.threshold_percentile,
                'threshold': self.threshold, 'keras_path': keras_path
            }, f)
        print(f"[OK] LSTM-AE saved: {filepath}")

    @classmethod
    def load(cls, filepath):
        if not HAS_TF:
            raise ImportError("pip install tensorflow")
        with open(filepath, 'rb') as f:
            p = pickle.load(f)
        det = cls(sequence_length=p['sequence_length'], latent_dim=p['latent_dim'],
                   threshold_percentile=p['threshold_percentile'])
        det.threshold = p['threshold']
        kp = p.get('keras_path', filepath.replace('.pkl', '.keras'))
        if os.path.exists(kp):
            det.autoencoder = keras.models.load_model(kp)
        return det
