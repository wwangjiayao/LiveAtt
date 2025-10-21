from flask import Flask, render_template, request, jsonify,session
from pathlib import Path
import torch
import traceback
import base64, os, uuid, json, threading
from API.tools import *


app = Flask(__name__,
            static_folder="static",
            template_folder="templates")
app.secret_key = 'a_strong_random_secret_key'
face_result = {"matched": False, "score": None, "name": None, "face_in_process": True}

# 动态获取项目根目录
PROJECT_ROOT = Path(__file__).parent  # 获取app.py所在目录（即LiveAtt）
DATA_DIR = PROJECT_ROOT / "data"  # 对应 D:\cs-lastwork\LiveAtt\data
UPLOAD_DIR = DATA_DIR / "uploads"  # 完整路径：D:\cs-lastwork\LiveAtt\data\uploads


def convert_to_dict(res):
    res_dict = {}
    for key, value in res.items():
        if isinstance(value, torch.Tensor):
            # 如果是 Tensor 对象，则转换为 Python 的列表
            res_dict[key] = value.tolist()
        else:
            res_dict[key] = value
    return res_dict

# 第一种方法
@app.route('/')
def index():
    # return render_template('index.html')
    return render_template('index.html')

# —— 新增：成员注册与查询 —— #
@app.route('/api/members/register', methods=['POST'])
def api_register_members():
    try:
        cnt = register_users()   # 批量注册或更新用户
        return jsonify(success=True, count=cnt)
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

@app.route('/api/members', methods=['GET'])
def api_get_members():
    try:
        members = get_all_members()  # [{'studentId', 'name', 'avatar', 'registerTime'}, …]
        return jsonify(success=True, count=len(members), data=members)
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500


@app.route('/API_1', methods=['POST'])
def API_1():
    # save the img
    data = request.json['image']
    header, encoded = data.split(",", 1)
    binary = base64.b64decode(encoded)
    # img_path = "/home/ns/Homework/Face/data/received_image.png"
    # 生成唯一文件名
    filename = f"face_{os.urandom(4).hex()}.png"
    img_path = UPLOAD_DIR / filename

    with open(img_path, "wb") as image_file:
        image_file.write(binary)

    # get results
    res = search_baidu(img_path)
    res['score'] = round(res['score'] / 100, 2)

    # pass or not
    if float(res['score']) > 0.6 and res['livepass'] == "PASS":
        res['pass'] = "PASS"
    else:
        res['unpass'] = "UNPASS"
    return jsonify(res)

# 第二种方法
@app.route('/API_2', methods=['POST'])
def API_2():
    try:
        data = request.json.get('image', '')
        if not data:
            return jsonify({"status": "fail", "reason": "未提供图像数据"}), 400

        header, encoded = data.split(",", 1)
        binary = base64.b64decode(encoded)
        filename = f"face_{os.urandom(4).hex()}.png"
        img_path = UPLOAD_DIR / filename

        with open(img_path, "wb") as image_file:
            image_file.write(binary)

        # Step 1: 活体检测
        liveness_score, liveness_label = perform_liveness_detection(img_path)
        print(liveness_score, liveness_label)

        if liveness_label != 'real':
            # 活体检测未通过，提前返回
            return jsonify({
                "status": "fail",
                "reason": "活体检测未通过",
                "liveness_score": round(liveness_score, 2)
            }), 200

        # Step 2: 人脸匹配
        try:
            res = find_most_similar(img_path)
        except ValueError as e:
            return jsonify({
                "status": "fail",
                "reason": str(e),
                "liveness_pass": True,
                "liveness_score": round(liveness_score, 2)
            }), 200

        score = round(res['score'], 2)
        pass_status = "PASS" if score > 0.45 else "UNPASS"

        # Step 3: 返回完整结果
        return jsonify({
            "status": "success",
            "user_id": res["user_id"],
            "student_id": res["student_id"],
            "score": score,
            "pass": pass_status,
            "target_face": res["target_face"],
            "match_face": res["match_face"],
            "liveness_pass": True,
            "liveness_score": round(liveness_score, 2)
        }), 200

    except Exception as e:
        print("发生异常：", e)
        traceback.print_exc()  # 打印完整堆栈
        return jsonify({"status": "error", "reason": str(e)}), 500

# 第三种方法
ACTIONS = ['blink', 'mouth', 'head']
STATE_FILE = './API/temp/state.json'


def async_face_recognition(video_path, session_id):
    frame_path = extract_frame(video_path)
    # compare_encoding_to_db(frame_path)

    global face_result
    face_result["name"] = predict_image(frame_path)
    if face_result["name"] != "unknown":
        face_result["matched"] = True
    with open(STATE_FILE, 'r') as f:
        state_data = json.load(f)
    if session_id in state_data:
        print("now in progress,session_id:", session_id)
        face_result["face_in_process"] = False


@app.route('/API_3', methods=['POST'])
def API_3():
    data = request.json['video']
    header, encoded = data.split(',', 1)
    binary = base64.b64decode(encoded)

    session_id = session.get('session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id

    video_path = f'./API/temp/{session_id}.webm'
    with open(video_path, 'wb') as f:
        f.write(binary)

    if not os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'w') as f:
            json.dump({}, f)

    with open(STATE_FILE, 'r') as f:
        state_data = json.load(f)

    # 初始化 session 状态
    if session_id not in state_data:
        state_data[session_id] = {
            "current_idx": 0,
            "face_in_progress": True,
            "face_result": None
        }
        with open(STATE_FILE, 'w') as f:
            json.dump(state_data, f)
        # 首次动作时，启动异步线程做人脸识别
        thread = threading.Thread(target=async_face_recognition, args=(video_path, session_id))
        thread.start()

    current_idx = state_data[session_id]["current_idx"]
    if current_idx >= len(ACTIONS):
        return jsonify({"pass": True, "message": "已完成全部动作", "is_final": True})

    current_action = ACTIONS[current_idx]
    passed = run_liveness_check(video_path, current_action)

    if passed:
        current_idx += 1
        state_data[session_id]["current_idx"] = current_idx
        with open(STATE_FILE, 'w') as f:
            json.dump(state_data, f)

        # 如果是最后一个动作，检查人脸识别是否完成
        if current_idx == len(ACTIONS):
            while True:
                if face_result["face_in_process"] is False:
                    break
            print("now in final check and return")
            session.pop('session_id', None)
            return jsonify({
                "pass": True,
                "message": f"{current_action} 检测通过",
                "is_final": True,
                "face_match": face_result["matched"],
                "matched_name": face_result["name"],
                "match_score": face_result["score"]
            })

        return jsonify({
            "pass": True,
            "message": f"{current_action} 检测通过",
            "is_final": False,
            "face_match": True,  # 中途都显示 face_match = True，前端会等到最后一帧展示真正结果
            "matched_name": None,
            "match_score": None
        })
    else:
        session.pop('session_id', None)
        state_data.pop(session_id, None)
        with open(STATE_FILE, 'w') as f:
            json.dump(state_data, f)

        return jsonify({
            "pass": False,
            "message": f"{current_action} 检测未通过",
            "is_final": True,
            "face_match": False,
            "matched_name": None,
            "match_score": None
        })

@app.route('/API_Reset', methods=['POST'])
def api_reset():
    session.clear()  # 清空 session
    return jsonify({"message": "Session reset successful"}), 200



# 第四种方法
@app.route('/API_4', methods=['POST'])
def API_4():
    try:
        data = request.json.get('image', '')
        if not data:
            return jsonify({"status": "fail", "reason": "未提供图像数据"}), 400

        header, encoded = data.split(",", 1)
        binary = base64.b64decode(encoded)
        filename = f"face_{os.urandom(4).hex()}.png"
        img_path = UPLOAD_DIR / filename

        with open(img_path, "wb") as image_file:
            image_file.write(binary)

        # Step 1: 活体检测
        liveness_score, liveness_label = perform_liveness_detection(img_path)
        print(liveness_score, liveness_label)

        if liveness_label != 'real':
            # 活体检测未通过，提前返回
            return jsonify({
                "status": "fail",
                "reason": "活体检测未通过",
                "liveness_score": round(liveness_score, 2)
            }), 200

        # Step 2: 人脸匹配
        try:
            res = find_most_similar_facenet(img_path)
        except ValueError as e:
            return jsonify({
                "status": "fail",
                "reason": str(e),
                "liveness_pass": True,
                "liveness_score": round(liveness_score, 2)
            }), 200

        score = round(res['score'], 2)
        pass_status = "PASS" if score > 0.45 else "UNPASS"

        # Step 3: 返回完整结果
        return jsonify({
            "status": "success",
            "user_id": res["user_id"],
            "student_id": res["student_id"],
            "score": score,
            "pass": pass_status,
            "target_face": res["target_face"],
            "match_face": res["match_face"],
            "liveness_pass": True,
            "liveness_score": round(liveness_score, 2)
        }), 200

    except Exception as e:
        print("发生异常：", e)
        traceback.print_exc()  # 打印完整堆栈
        return jsonify({"status": "error", "reason": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
