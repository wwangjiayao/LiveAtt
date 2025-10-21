import os
import cv2
import numpy as np
import time
from .src.anti_spoof_predict import AntiSpoofPredict
from .src.generate_patches import CropImage
from .src.utility import parse_model_name

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # test.py 的目录
model_dir = os.path.normpath(os.path.join(BASE_DIR, 'resources', 'anti_spoof_models'))

def perform_liveness_detection(image_path, device_id=0):
    model_test = AntiSpoofPredict(device_id)
    image_cropper = CropImage()
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"无法读取图像: {image_path}")
    image_bbox = model_test.get_bbox(image)
    prediction = np.zeros((1, 3))
    test_speed = 0
    for model_name in os.listdir(model_dir):
        h_input, w_input, model_type, scale = parse_model_name(model_name)
        param = {
            "org_img": image,
            "bbox": image_bbox,
            "scale": scale,
            "out_w": w_input,
            "out_h": h_input,
            "crop": True,
        }
        if scale is None:
            param["crop"] = False
        img = image_cropper.crop(**param)
        start = time.time()
        prediction += model_test.predict(img, os.path.join(model_dir, model_name))
        test_speed += time.time() - start
    label = np.argmax(prediction)
    value = prediction[0][label] / 2
    if label == 1:
        return value, 'real'
    else:
        return value, 'fake'


    for model_name in os.listdir(model_dir):
        # 解析模型参数并预处理图像
        h_input, w_input, model_type, scale = parse_model_name(model_name)
        img = image_cropper.crop(...)  # 根据模型要求裁剪人脸区域
        
        # 关键预测代码：多模型结果累加
        prediction += model_test.predict(img, os.path.join(model_dir, model_name))

    label = np.argmax(prediction)  # 取概率最高的类别
    value = prediction[0][label] / 2  # 归一化置信度
    return value, 'real' if label == 1 else 'fake'