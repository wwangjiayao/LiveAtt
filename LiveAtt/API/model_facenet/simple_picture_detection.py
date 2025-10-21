import cv2
import numpy as np

def perform_liveness_detection_simple(img_path):
    img = cv2.imread(img_path)
    if img is None:
        return 0.0, 'spoof'  # 图像无法读取

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1. 模糊度（打印/屏幕图通常更模糊）
    lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    is_blurry = lap_var < 100

    # 2. 颜色偏差检测（伪造图可能偏蓝或偏红）
    b_mean = np.mean(img[:, :, 0])
    g_mean = np.mean(img[:, :, 1])
    r_mean = np.mean(img[:, :, 2])
    color_diff = abs(r_mean - g_mean) + abs(b_mean - g_mean)
    is_color_distorted = color_diff > 60

    # 3. 摩尔纹检测（高频纹理异常）
    fft = np.fft.fft2(gray)
    fft_shift = np.fft.fftshift(fft)
    magnitude_spectrum = 20 * np.log(np.abs(fft_shift) + 1e-6)
    h, w = gray.shape
    center_region = magnitude_spectrum[h//4:3*h//4, w//4:3*w//4]
    high_freq_energy = np.mean(center_region)
    is_moire = high_freq_energy > 150

    # 可疑项计数
    suspicious_score = sum([is_blurry, is_color_distorted, is_moire])
    label = 'spoof' if suspicious_score >= 2 else 'real'

    # 构造一个 0~1 的置信分数，越接近1表示越真实
    score = 1.0 - suspicious_score / 3.0

    return score, label
