import io, base64
import json
import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
from PIL import Image

# Initialize face detector & embedder
torch_device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
mtcnn = MTCNN(image_size=160, keep_all=True, device=torch_device)
resnet = InceptionResnetV1(pretrained='vggface2').eval().to(torch_device)
JSON_LIBRARY_PATH = r"D:/cs-lastwork/LiveAtt/API/model_facenet/face_library.json"
torch_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def pil_to_datauri(pil_img, fmt="PNG"):
    """
    将PIL图像转换为`data:image/...;base64,`格式的字符串。
    """
    buf = io.BytesIO()
    pil_img.save(buf, format=fmt)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/{fmt.lower()};base64,{b64}"

def get_embedding_and_face(image_path):
    """
    Load a local image, detect the first face, and return (embedding_tensor, face_tensor).
    """
    img = Image.open(image_path).convert("RGB")
    faces, _ = mtcnn(img, return_prob=True)
    if faces is None or len(faces) == 0:
        return None, None

    emb = resnet(faces[0].unsqueeze(0).to(torch_device))
    return emb.detach(), faces[0]


def tensor_to_image(tensor):
    """Convert a normalized face-tensor to uint8 image for plotting."""
    img = tensor.permute(1,2,0).cpu().numpy()
    img = (img - img.min()) / (img.max() - img.min())
    return (img * 255).astype('uint8')

def find_most_similar_facenet(target_image_path):
    """
    给定目标图像路径和JSON库，返回：
      - user_id（姓名）,
      - student_id（学号）,
      - 相似度得分,
      - 裁剪后的目标人脸（数据URI格式）,
      - 裁剪后的匹配人脸（数据URI格式）。
    """
    # 加载目标图像
    tgt_emb, tgt_face = get_embedding_and_face(target_image_path)
    if tgt_emb is None:
        raise ValueError("目标图像中未检测到人脸。")

    # 将目标人脸张量转换为PIL图像，再转为数据URI
    tgt_pil = Image.fromarray(tensor_to_image(tgt_face))
    tgt_uri = pil_to_datauri(tgt_pil)

    # 加载JSON库
    with open(JSON_LIBRARY_PATH, 'r', encoding='utf-8') as f:
        candidates = json.load(f)

    # 寻找最佳匹配
    best_score = -1.0
    best_match = None
    for c in candidates:
        emb = torch.tensor(c["embedding"]).unsqueeze(0).to(torch_device)
        sim = torch.nn.functional.cosine_similarity(tgt_emb.to(torch_device), emb).item()
        if sim > best_score:
            best_score = sim
            best_match = c

    if best_match is None:
        raise ValueError("未找到有效候选。")

    # 重新加载最佳匹配的人脸裁剪张量
    _, best_face = get_embedding_and_face(best_match["image_path"])
    if best_face is None:
        raise ValueError(f"最佳匹配图像中未检测到人脸：{best_match['image_path']}")

    # 将最佳匹配人脸转换为数据URI
    best_pil = Image.fromarray(tensor_to_image(best_face))
    best_uri = pil_to_datauri(best_pil)

    return {
        "student_id": best_match["student_id"],
        "user_id":    best_match["name"],
        "score":      best_score,
        "target_face": tgt_uri,
        "match_face":  best_uri
    }