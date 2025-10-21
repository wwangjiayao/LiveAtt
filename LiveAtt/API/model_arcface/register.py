# register_arcface.py
import os
import json
import numpy as np
import cv2
from insightface.app import FaceAnalysis
import warnings

warnings.filterwarnings("ignore")

def imread_unicode(path):
    with open(path, "rb") as f:
        byte_data = bytearray(f.read())
    np_arr = np.asarray(byte_data, dtype=np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return img

# 初始化人脸分析器（检测 + 对齐 + embedding）
app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])  # 有 GPU 可加 CUDAExecutionProvider
app.prepare(ctx_id=0, det_size=(640, 640))

def get_embedding(img_path):
    img = imread_unicode(img_path)
    if img is None:
        return None
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    faces = app.get(rgb)
    if len(faces) == 0:
        return None
    return faces[0].normed_embedding  # 使用归一化的 embedding

def register_faces(image_dir, save_path="API/model_arcface/face_library_arcface.json"):
    facebank = []
    for filename in os.listdir(image_dir):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            full_path = os.path.join(image_dir, filename)
            name = os.path.splitext(filename)[0]
            emb = get_embedding(full_path)
            if emb is not None:
                facebank.append({
                    "student_id": name.split("-")[0],
                    "name": name,
                    "embedding": emb.tolist(),
                    "image_path": full_path.replace("\\", "/")  # 兼容跨平台路径
                })
                print(f"[OK] 注册成功: {name}")
            else:
                print(f"[FAIL] 跳过（无检测到人脸）: {name}")

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(facebank, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 注册完成，共 {len(facebank)} 人脸，保存至 {save_path}")

if __name__ == "__main__":
    register_faces("picture")  # 替换人脸图片文件夹
