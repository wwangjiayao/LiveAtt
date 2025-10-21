from .baidu.api import search_baidu

from .own_liveness.action_match import run_liveness_check
from .own_liveness.face_match import extract_frame
from .own_liveness.predict.predict_result import predict_image

# 引入在 API/baidu/register.py 中的两个函数
from .baidu.register import register_users, get_all_members


# 引入在model_arcface中的函数
from .model_arcface.detect import find_most_similar

# 引入在model_facenet中的函数
from .model_facenet.detect import find_most_similar_facenet
from .model_facenet.simple_picture_detection import perform_liveness_detection_simple

# 引入SilentFace_AntiSpoofing
from .SilentFace_AntiSpoofing.test import perform_liveness_detection