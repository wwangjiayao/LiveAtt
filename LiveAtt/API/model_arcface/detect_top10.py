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


warnings.filterwarnings("ignore")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# 放在文件开头
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_LIBRARY_PATH = os.path.join(BASE_DIR, "face_library_arcface.json")

# 初始化人脸分析模型（ArcFace用的）
app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
app.prepare(ctx_id=0, det_size=(640, 640))

def pil_to_datauri(pil_img, fmt="PNG"):
    buf = io.BytesIO()
    pil_img.save(buf, format=fmt)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/{fmt.lower()};base64,{b64}"

def get_embedding_and_crop_from_img(img):
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    faces = app.get(rgb)
    if len(faces) == 0:
        return None, None
    face = faces[0]
    emb = face.normed_embedding
    aligned_face = norm_crop(rgb, face.kps)
    pil_img = Image.fromarray(aligned_face)
    return emb, pil_to_datauri(pil_img)

def find_top_matches_by_embedding(tgt_emb, top_k=10):
    with open(JSON_LIBRARY_PATH, 'r', encoding='utf-8') as f:
        candidates = json.load(f)

    scored_candidates = []
    for c in candidates:
        emb = np.array(c["embedding"])
        score = np.dot(tgt_emb, emb) / (np.linalg.norm(tgt_emb) * np.linalg.norm(emb))  # 余弦相似度
        scored_candidates.append((score, c))

    # 降序排列取前 top_k
    top_matches = sorted(scored_candidates, key=lambda x: x[0], reverse=True)[:top_k]
    return top_matches

def capture_and_compare():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ 无法打开摄像头")
        return

    print("📷 打开摄像头成功！请输入命令：\n  s - 拍照识别\n  q - 退出程序")
    while True:
        cmd = input("\n请输入操作指令（s/q）：").strip().lower()
        if cmd == 'q':
            print("👋 已退出摄像头识别")
            break
        elif cmd == 's':
            ret, frame = cap.read()
            if not ret:
                print("❌ 无法读取摄像头帧")
                continue

            # 保存当前帧
            cv2.imwrite("temp_frame.jpg", frame)
            print("📸 图像已保存为 temp_frame.jpg，正在处理人脸...")

            emb, tgt_uri = get_embedding_and_crop_from_img(frame)
            if emb is None:
                print("⚠️ 未检测到人脸，请重试")
                continue

            print("🔍 正在识别，请稍候...")
            matches = find_top_matches_by_embedding(emb, top_k=10)

            print("\n✅ 匹配结果（Top 10）：")
            for rank, (score, match) in enumerate(matches, 1):
                print(f"{rank}. 姓名: {match['name']} | 学号: {match['student_id']} | 相似度: {score:.4f}")
        else:
            print("⚠️ 无效指令，请输入 's' 或 'q'")

    cap.release()

if __name__ == "__main__":
    capture_and_compare()
