import os
import cv2
import numpy as np
import json
from keras_facenet import FaceNet
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import Adam
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# 图像增强配置
datagen = ImageDataGenerator(
    rotation_range=40,  # 随机旋转角度
    width_shift_range=0.2,  # 水平平移
    height_shift_range=0.2,  # 垂直平移
    shear_range=0.2,  # 剪切变换
    zoom_range=0.2,  # 随机缩放
    horizontal_flip=True,  # 随机水平翻转
    fill_mode='nearest'  # 填充模式
)

# 初始化 FaceNet
embedder = FaceNet()

def extract_and_augment_image(image_path):
    """增强图像并提取嵌入向量"""
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = np.expand_dims(image, axis=0)  # 增加batch维度

    # 使用 ImageDataGenerator 进行增强
    augmented_images = datagen.flow(image, batch_size=1)

    # 只取一个增强后的图像并提取特征
    augmented_image = next(augmented_images)[0].astype(np.uint8)
    embeddings = embedder.embeddings([augmented_image])

    return embeddings[0]


def load_data_from_folder_with_augmentation(folder_path):
    X, y = [], []
    for fname in os.listdir(folder_path):
        if not fname.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue
        label = os.path.splitext(fname)[0]  # 使用文件名作为标签
        img_path = os.path.join(folder_path, fname)
        try:
            emb = extract_and_augment_image(img_path)
            X.append(emb)
            y.append(label)
        except Exception as e:
            print(f"跳过 {fname}：{e}")
    return np.array(X), np.array(y)

# 加载数据
data_dir = "D:/download/LiveAtt/LiveAtt/API/own_liveness/predict/data"
X, y = load_data_from_folder_with_augmentation(data_dir)

# 标签编码
le = LabelEncoder()
y_encoded = le.fit_transform(y)
with open("label_encoder.json", "w") as f:
    json.dump(le.classes_.tolist(), f)

X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

model = Sequential([
    Dense(128, activation='relu', input_shape=(512,)),
    Dropout(0.4),
    Dense(len(np.unique(y_encoded)), activation='softmax')
])

model.compile(optimizer=Adam(learning_rate=0.001),
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])

model.fit(X_train, y_train, epochs=30, batch_size=4, validation_data=(X_test, y_test))
model.save("facenet_classifier.h5")
