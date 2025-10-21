import time
import base64
from flask import Flask, jsonify
from tabulate import tabulate
from aip import AipFace
import json
import os

# ———— 配置区域 ————
APP_ID = "6824119"
API_KEY = "ByxUCiePRcASHdERl76ynkPx"
SECRET_KEY = 'PSN7EHur485OsxtJ2rQ4yPz94vfC0t2u'
client = AipFace(APP_ID, API_KEY, SECRET_KEY)

image_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', 'picture'))
group_id = 'class1'

# ———— 工具函数 ————
def parse_filename(filename):
    user_id, name_part = filename.rsplit('-', 1)
    user_name = name_part.rsplit('.', 1)[0].strip()
    return user_id.strip(), user_name

def validate_image(image_path):
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    result = client.detect(image_data, 'BASE64')
    if result.get('error_code') != 0:
        raise RuntimeError(result.get('error_msg'))
    if result['result']['face_num'] == 0:
        raise RuntimeError("未检测到人脸")
    return image_data

# ———— 核心逻辑 ————
def register_users():
    """批量注册/更新用户，返回注册成功数"""
    success_count = 0
    for filename in os.listdir(image_folder):
        if not filename.lower().endswith(('.jpg', '.png')):
            continue
        user_id, user_name = parse_filename(filename)
        image_path = os.path.join(image_folder, filename)
        # 检查是否已存在
        check = client.getUser(user_id, group_id)
        if check.get('error_code') == 0 and check.get('result', {}).get('user_list'):
            continue
        # 验证并注册
        image_data = validate_image(image_path)
        res = client.addUser(
            image_data, 'BASE64', group_id, user_id,
            options={'user_info': user_name, 'action_type': 'REPLACE',
                     'quality_control': 'NORMAL', 'liveness_control': 'LOW'}
        )
        if res.get('error_code') == 0:
            success_count += 1
        time.sleep(3)

        #注册有成功时清除旧缓存
        if success_count > 0:
            if os.path.exists(cache_path):
                os.remove(cache_path)

    return success_count

def find_avatar_file(user_id, user_name):
    base_name = f"{user_id}-{user_name}"
    for ext in ['.jpg', '.png']:
        avatar_path = os.path.join(image_folder, base_name + ext)
        if os.path.exists(avatar_path):
            return f'/static/picture/{base_name}{ext}'
    return '/static/default-avatar.jpg'  # 默认头像


current_dir = os.path.dirname(os.path.abspath(__file__))
cache_path = os.path.join(current_dir, 'members_cache.json')  # 缓存文件与脚本同目录
def get_all_members():
    """返回当前组所有成员的列表(dict)"""

    # 如果缓存文件存在，直接读取
    if os.path.exists(cache_path):
        with open(cache_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    members = []
    grp = client.getGroupUsers(group_id)
    if grp.get('error_code') != 0:
        return members
    for uid in grp['result']['user_id_list']:
        usr = client.getUser(uid, group_id)
        for item in usr.get('result', {}).get('user_list', []):
            members.append({
                'studentId': uid,
                'name': item.get('user_info', ''),

                # 修改 get_all_members() 中 avatar 字段：
                'avatar': find_avatar_file(uid, item.get("user_info", "")),
            })
        time.sleep(0.5)

    # 保存到缓存
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(members, f, ensure_ascii=False, indent=2)

    return members

