from flask import Flask, render_template, request, jsonify,session
import base64
import numpy as np
import cv2
import os
import uuid
import json

# --- 提取视频首帧保存为图片 ---
def extract_frame(video_path):
    cap = cv2.VideoCapture(video_path)
    success, frame = cap.read()
    cap.release()
    if success:
        frame_path = video_path.replace('.webm', '.jpg')
        cv2.imwrite(frame_path, frame)
        return frame_path
    return None

# --- 比对人脸 ---
# def compare_encoding_to_db(image_path):

#     return {
#         "matched": True,
#         "score": 0.99,
#         "name":"linda"
#     }
