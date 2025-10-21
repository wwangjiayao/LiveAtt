import os
import re
import json

# 设置图片所在文件夹路径
folder_path = "./data"  # 修改为你的实际路径
mapping = {}

# 遍历文件夹中的所有文件
for filename in os.listdir(folder_path):
    match = re.match(r"(\d+)-(.+)\.(jpg|jpeg|png)", filename, re.IGNORECASE)
    if match:
        number = match.group(1)
        name = match.group(2)
        ext = match.group(3)
        new_filename = f"{number}.{ext}"
        
        # 记录映射关系
        mapping[number] = name

        # 获取完整路径并重命名
        old_path = os.path.join(folder_path, filename)
        new_path = os.path.join(folder_path, new_filename)
        os.rename(old_path, new_path)
        print(f"Renamed: {filename} -> {new_filename}")

# 保存映射为 JSON 文件
json_path = os.path.join(folder_path, "filename_mapping.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(mapping, f, ensure_ascii=False, indent=4)

print(f"\n映射文件已保存为: {json_path}")
