import json
import numpy as np
import cv2
import io
import base64
from PIL import Image
from insightface.app import FaceAnalysis
from insightface.utils.face_align import norm_crop
import warnings
import os

# 忽略警告信息
warnings.filterwarnings("ignore")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# 本地人脸库路径
JSON_LIBRARY_PATH = "API/model_arcface/face_library_arcface.json"


# 初始化人脸分析模型（ArcFace用的）
app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
app.prepare(ctx_id=0, det_size=(640, 640))


# 读取支持中文路径的图像
def imread_unicode(path):
    with open(path, "rb") as f:
        byte_data = bytearray(f.read())
    np_arr = np.asarray(byte_data, dtype=np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return img


# PIL 图转 Base64 数据 URI
def pil_to_datauri(pil_img, fmt="PNG"):
    buf = io.BytesIO()
    pil_img.save(buf, format=fmt)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/{fmt.lower()};base64,{b64}"


# 获取人脸特征和对齐图像
def get_embedding_and_crop(image_path):
    img = imread_unicode(image_path)
    if img is None:
        return None, None
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    faces = app.get(rgb)
    if len(faces) == 0:
        return None, None

    face = faces[0]
    emb = face.normed_embedding
    aligned_face = norm_crop(rgb, face.kps)
    pil_img = Image.fromarray(aligned_face)
    return emb, pil_to_datauri(pil_img)

# 寻找最相似的人脸
def find_most_similar(target_image_path):
    tgt_emb, tgt_uri = get_embedding_and_crop(target_image_path)
    if tgt_emb is None:
        raise ValueError("目标图像中未检测到人脸。")

    with open(JSON_LIBRARY_PATH, 'r', encoding='utf-8') as f:
        candidates = json.load(f)

    best_score = -1.0
    best_match = None

    for c in candidates:
        emb = np.array(c["embedding"])
        score = np.dot(tgt_emb, emb) / (np.linalg.norm(tgt_emb) * np.linalg.norm(emb))  # 余弦相似度
        if score > best_score:
            best_score = score
            best_match = c

    if best_match is None:
        raise ValueError("未找到匹配人脸。")

    _, match_uri = get_embedding_and_crop(best_match["image_path"])

    print(f"匹配到用户：{best_match['name']}，相似度：{best_score:.4f}")

    return {
        "student_id": best_match["student_id"],
        "user_id": best_match["name"],
        "score": float(best_score),
        "target_face": tgt_uri,
        "match_face": match_uri
    }


# 调试运行
if __name__ == "__main__":
    result = find_most_similar("D:/cs-lastwork/LiveAtt/picture/2022302181129-王佳瑶.jpg")
    print(json.dumps(result, indent=2, ensure_ascii=False))
