import io
import base64
import json
import torch
import cv2
import os
import warnings
from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1

# 忽略警告
warnings.filterwarnings("ignore")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# 设置为当前脚本目录下的 JSON 路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_LIBRARY_PATH = os.path.join(BASE_DIR, "face_library.json")

# 初始化设备
torch_device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# 初始化人脸检测与识别模型
mtcnn = MTCNN(image_size=160, keep_all=False, device=torch_device)
resnet = InceptionResnetV1(pretrained='vggface2').eval().to(torch_device)

def pil_to_datauri(pil_img, fmt="PNG"):
    buf = io.BytesIO()
    pil_img.save(buf, format=fmt)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/{fmt.lower()};base64,{b64}"

def get_embedding_and_face_from_frame(frame):
    """
    从 OpenCV 图像帧提取人脸和嵌入向量。
    """
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    face_tensor = mtcnn(img)
    if face_tensor is None:
        return None, None
    emb = resnet(face_tensor.unsqueeze(0).to(torch_device)).detach()
    return emb, face_tensor

def tensor_to_image(tensor):
    img = tensor.permute(1, 2, 0).cpu().numpy()
    img = (img - img.min()) / (img.max() - img.min())
    return (img * 255).astype('uint8')

def find_top_matches_facenet(tgt_emb, top_k=10):
    with open(JSON_LIBRARY_PATH, 'r', encoding='utf-8') as f:
        candidates = json.load(f)

    scored = []
    for c in candidates:
        emb = torch.tensor(c["embedding"]).unsqueeze(0).to(torch_device)
        sim = torch.nn.functional.cosine_similarity(tgt_emb.to(torch_device), emb).item()
        scored.append((sim, c))

    top_matches = sorted(scored, key=lambda x: x[0], reverse=True)[:top_k]
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

            emb, tgt_uri = get_embedding_and_face_from_frame(frame)
            if emb is None:
                print("⚠️ 未检测到人脸，请重试")
                continue

            print("🔍 正在识别，请稍候...")
            matches = find_top_matches_facenet(emb, top_k=10)

            print("\n✅ 匹配结果（Top 10）：")
            for rank, (score, match) in enumerate(matches, 1):
                print(f"{rank}. 姓名: {match['name']} | 学号: {match['student_id']} | 相似度: {score:.4f}")
        else:
            print("⚠️ 无效指令，请输入 's' 或 'q'")

    cap.release()

if __name__ == "__main__":
    capture_and_compare()
