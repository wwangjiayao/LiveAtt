import cv2
import mediapipe as mp
import numpy as np

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1)

# EAR（眨眼）常量
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]
EAR_THRESHOLD = 0.21

# 张嘴检测常量
MOUTH_IDX = [13, 14, 78, 308]
MAR_THRESHOLD = 0.5

# 转头检测常量
MODEL_POINTS = np.array([
    (0.0, 0.0, 0.0),        # Nose tip
    (0.0, -63.6, -12.5),    # Chin
    (-43.3, 32.7, -26.0),   # Left eye
    (43.3, 32.7, -26.0),    # Right eye
    (-28.9, -28.9, -24.1),  # Left mouth
    (28.9, -28.9, -24.1)    # Right mouth
], dtype=np.float64)

LANDMARK_IDS = {
    "nose_tip": 1,
    "chin": 199,
    "left_eye": 33,
    "right_eye": 263,
    "left_mouth": 61,
    "right_mouth": 291
}

def get_camera_matrix(w, h):
    f = w
    return np.array([[f, 0, w / 2], [0, f, h / 2], [0, 0, 1]], dtype=np.float64)

def calculate_ear(lm, eye_indices, w, h):
    points = [(int(lm[i].x * w), int(lm[i].y * h)) for i in eye_indices]
    v1 = np.linalg.norm(np.array(points[1]) - np.array(points[5]))
    v2 = np.linalg.norm(np.array(points[2]) - np.array(points[4]))
    hlen = np.linalg.norm(np.array(points[0]) - np.array(points[3]))
    return (v1 + v2) / (2.0 * hlen)

def calculate_mar(lm, idx, w, h):
    top = np.array((lm[idx[0]].x * w, lm[idx[0]].y * h))
    bottom = np.array((lm[idx[1]].x * w, lm[idx[1]].y * h))
    left = np.array((lm[idx[2]].x * w, lm[idx[2]].y * h))
    right = np.array((lm[idx[3]].x * w, lm[idx[3]].y * h))
    return np.linalg.norm(top - bottom) / np.linalg.norm(left - right)

def detect_blink(frames, w, h):
    for frame in frames:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = face_mesh.process(rgb)
        if res.multi_face_landmarks:
            lm = res.multi_face_landmarks[0].landmark
            le = calculate_ear(lm, LEFT_EYE, w, h)
            re = calculate_ear(lm, RIGHT_EYE, w, h)
            if (le + re) / 2.0 < EAR_THRESHOLD:
                return True
    return False

def detect_mouth(frames, w, h):
    for frame in frames:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = face_mesh.process(rgb)
        if res.multi_face_landmarks:
            lm = res.multi_face_landmarks[0].landmark
            mar = calculate_mar(lm, MOUTH_IDX, w, h)
            if mar > MAR_THRESHOLD:
                return True
    return False

def detect_head(frames, w, h):
    for frame in frames:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = face_mesh.process(rgb)
        if res.multi_face_landmarks:
            lm = res.multi_face_landmarks[0].landmark
            image_points = np.array([
                (lm[LANDMARK_IDS["nose_tip"]].x * w, lm[LANDMARK_IDS["nose_tip"]].y * h),
                (lm[LANDMARK_IDS["chin"]].x * w, lm[LANDMARK_IDS["chin"]].y * h),
                (lm[LANDMARK_IDS["left_eye"]].x * w, lm[LANDMARK_IDS["left_eye"]].y * h),
                (lm[LANDMARK_IDS["right_eye"]].x * w, lm[LANDMARK_IDS["right_eye"]].y * h),
                (lm[LANDMARK_IDS["left_mouth"]].x * w, lm[LANDMARK_IDS["left_mouth"]].y * h),
                (lm[LANDMARK_IDS["right_mouth"]].x * w, lm[LANDMARK_IDS["right_mouth"]].y * h),
            ], dtype=np.float64)
            success, rot_vec, trans_vec = cv2.solvePnP(MODEL_POINTS, image_points, get_camera_matrix(w, h), np.zeros((4, 1)))
            if success:
                rmat, _ = cv2.Rodrigues(rot_vec)
                proj = np.hstack((rmat, trans_vec))
                _, _, _, _, _, _, euler = cv2.decomposeProjectionMatrix(proj)
                yaw = euler[1]
                if abs(yaw) > 15:  # 超过 15 度算成功
                    return True
    return False

def run_liveness_check(video_path, action):
    cap = cv2.VideoCapture(video_path)
    frames = []
    ret = True
    while ret:
        ret, frame = cap.read()
        if ret:
            frames.append(frame)
    cap.release()

    if not frames:
        return False

    h, w = frames[0].shape[:2]

    if action == 'blink':
        return detect_blink(frames, w, h)
    elif action == 'mouth':
        return detect_mouth(frames, w, h)
    elif action == 'head':
        return detect_head(frames, w, h)
    else:
        return False
