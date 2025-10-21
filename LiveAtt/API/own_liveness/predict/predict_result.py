from tensorflow.keras.models import load_model
import numpy as np
import json
import cv2
from keras_facenet import FaceNet

embedder = FaceNet()

def extract_embedding(image_path):
    """提取128维FaceNet人脸向量"""
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    embeddings = embedder.embeddings([image])
    #print("Embedding shape:", embeddings[0].shape)  # 打印维度
    return embeddings[0]

def predict_image(image_path):
    MAPPING_PATH = "D:/cs-lastwork/LiveAtt/API/own_liveness/predict/data/filename_mapping.json"
    model = load_model("D:/cs-lastwork/LiveAtt/API/own_liveness/facenet_classifier.h5")

    with open("D:/cs-lastwork/LiveAtt/API/own_liveness/predict/label_encoder.json", "r") as f:
        class_names = json.load(f)

    embedding = extract_embedding(image_path)
    embedding = np.expand_dims(embedding, axis=0)

    prediction = model.predict(embedding)
    pred_index = np.argmax(prediction)

    with open(MAPPING_PATH, "r", encoding="utf-8") as f:
        id_to_name = json.load(f)

    id = class_names[pred_index]
    return id_to_name.get(id, "unknown")
