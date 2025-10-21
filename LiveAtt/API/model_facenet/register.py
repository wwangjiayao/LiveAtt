import os
import json
import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
from PIL import Image

# 初始化模型
torch_device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
mtcnn = MTCNN(image_size=160, keep_all=False, device=torch_device)
resnet = InceptionResnetV1(pretrained='vggface2').eval().to(torch_device)

def get_augmented_embeddings(image_path):
    """
    对输入图像进行原图 + 翻转增强，返回平均后的人脸嵌入向量。
    """
    try:
        img = Image.open(image_path).convert("RGB")
    except Exception as e:
        print(f"[Error] cannot open {image_path}: {e}")
        return None

    embeddings = []

    # 原图
    face = mtcnn(img)
    if face is not None:
        emb = resnet(face.unsqueeze(0).to(torch_device))
        embeddings.append(emb.detach().cpu())

    # 翻转图
    flipped = img.transpose(Image.FLIP_LEFT_RIGHT)
    face_flipped = mtcnn(flipped)
    if face_flipped is not None:
        emb_flipped = resnet(face_flipped.unsqueeze(0).to(torch_device))
        embeddings.append(emb_flipped.detach().cpu())

    if len(embeddings) == 0:
        return None

    # 平均合并特征向量
    emb_avg = torch.stack(embeddings).mean(dim=0)
    return emb_avg.squeeze(0).tolist()

def register_faces(picture_dir, json_out_path):
    """
    遍历文件夹，提取人脸嵌入并保存至JSON文件。
    """
    library = []
    for fname in os.listdir(picture_dir):
        if not fname.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue
        core, _ = os.path.splitext(fname)
        if '-' not in core:
            print(f"[Skip] filename does not match 学号-姓名: {fname}")
            continue
        student_id, name = core.split('-', 1)
        img_path = os.path.join(picture_dir, fname)

        emb_list = get_augmented_embeddings(img_path)
        if emb_list is None:
            print(f"[Warn] no face in {fname}, skipping")
            continue

        library.append({
            "student_id": student_id,
            "name": name,
            "image_path": img_path,
            "embedding": emb_list
        })
        print(f"[Registered] {student_id} - {name}")

    with open(json_out_path, 'w', encoding='utf-8') as f:
        json.dump(library, f, ensure_ascii=False, indent=2)
    print(f"[Done] saved {len(library)} entries to {json_out_path}")


if __name__ == "__main__":
    register_faces(
        picture_dir=r"D:/cs-lastwork/LiveAtt/picture",
        json_out_path=r"D:/cs-lastwork/LiveAtt/API/model_facenet/face_library.json"
    )
