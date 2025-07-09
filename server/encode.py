# 자동화 인코딩 스크립트
#3개의 mp4 영상을 읽어서, 각각에 대해 4개 해상도(360p, 480p, 720p, 1080p)로
#인코딩을 하고, DASH 스트리밍용 MPD + 세그먼트들을 생성

#실행순서
#encode.py 실행 후 
#cd server
#python -m uvicorn main:app --reload
#index.html 을 live server로 실행

# -*- coding: utf-8 -*-

import os
import subprocess
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import load_model
from tensorflow.keras.losses import mse
import joblib

# 모델 로드
model_path = r"optimal_param_prediction_model.h5"
print("모델 경로:", model_path)
model = load_model(model_path, custom_objects={'mse': mse})
scaler_X = joblib.load("scaler_X.pkl")
scaler_y = joblib.load("scaler_y.pkl")

# ffmpeg 실행 경로 (환경에 맞게 수정)
ffmpeg_path = r"C:\ffmpeg-2025-06-04-git-a4c1a5b084-essentials_build\bin\ffmpeg.exe"

# 입력 및 출력 디렉토리
#input/ 폴더에 video1.mp4 ~ video3.mp4가 있어야 함
#결과물은 static/video1/, static/video2/ 등에 저장됨
input_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "input"))
output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))

#####################################################################
# 인코딩 파라미터 최적화 모델
# input - motion-x, motion-y, i-ratio, p-ratio, b-ratio
# output - optimal_crf, optimal_max_rate

# 인코딩할 영상 목록
valid_extensions = ('.mp4', 'avi')
video_files = []
if os.path.exists(input_dir):
    for file in os.listdir(input_dir):
        if file.lower().endswith(valid_extensions):
            video_files.append(file)
#################################################################

# 비트레이트 및 해상도 설정 [(bitrate, resolution)]
bitrates = [
    ("500k",  "640x360"),
    ("1000k", "854x480"),
    ("2000k", "1280x720"),
    ("3000k", "1920x1080"),
]

os.makedirs(output_dir, exist_ok=True)

for file in video_files:
    input_path = os.path.join(input_dir, file)
    name = os.path.splitext(file)[0]
    output_path = os.path.join(output_dir, name)
    os.makedirs(output_path, exist_ok=True)
    manifest_path = os.path.join(output_path, "manifest.mpd")

    #########################################################
    # 최적 인코딩 파라미터 예측
    # 추후 모션 벡터 및 매크로블록 비율 분석하여 제대로 된 예측 수행

    # 예시 입력 데이터 (스케일링 전)
    sample_X_raw = np.array([[0.5, 1.2, 0.05, 0.7, 0.25]]) # 임의의 예시 값
    
    # 입력 데이터 정규화
    sample_X_scaled = scaler_X.transform(sample_X_raw)
    
    # 예측
    predicted_scaled_outputs = model.predict(sample_X_scaled)
    
    # 예측된 값을 원래 스케일로 역변환
    predicted_y_scaled = np.hstack(predicted_scaled_outputs)
    predicted_y_original = scaler_y.inverse_transform(predicted_y_scaled)
    
    predicted_crf = predicted_y_original[0, 0]
    predicted_max_rate_numeric = predicted_y_original[0, 1]
    
    # Max Rate를 다시 문자열 형태로 변환
    def convert_numeric_to_max_rate_str(max_rate_num):
        if max_rate_num >= 950000: # 1M에 가까우면 M으로 표시
            return f"{round(max_rate_num / 1000000)}M"
        elif max_rate_num >= 950: # 1k에 가까우면 k로 표시
            return f"{round(max_rate_num / 1000)}k"
        return str(round(max_rate_num))
    
    predicted_max_rate_str = convert_numeric_to_max_rate_str(predicted_max_rate_numeric)

    print(f"{file}에 대한 최적 인코딩 옵션 -> crf={predicted_crf}, max_rate={predicted_max_rate_str}")
    #########################################################

    print(f"\n[+] Encoding {file} → {name}/manifest.mpd")
    
    cmd = [ffmpeg_path, "-y", "-i", input_path]
    
    for i, (_, res) in enumerate(bitrates):
        w, h = res.split("x")
        cmd += [
            "-map", "0:v:0",
            f"-filter:v:{i}", f"scale={w}:{h}",
            f"-crf:{i}", str(int(predicted_crf)),
            f"-maxrate:{i}", predicted_max_rate_str,
            f"-bufsize:{i}", f"{int(int(predicted_max_rate_numeric) * 2)}"  # 버퍼는 관례상 maxrate의 2배 정도
        ]

    cmd += [
        "-c:v", "libx264",
        "-c:a", "aac",
        "-g", "100",
        "-keyint_min", "100",
        "-sc_threshold", "0",
        "-use_timeline", "1",
        "-use_template", "1",
        "-init_seg_name", "init-stream$RepresentationID$.mp4",
        "-media_seg_name", "chunk-stream$RepresentationID$-$Number$.m4s",
        "-adaptation_sets", "id=0,streams=v",
        "-seg_duration", "10",
        "-f", "dash",
        manifest_path
    ]

    try:
        subprocess.run(cmd, cwd=output_path, check=True)
    except subprocess.CalledProcessError as e:
        print(f" {file} 인코딩 실패: {e}")



subprocess.run(cmd, cwd=output_path)

print("\n 모든 영상 인코딩 완료!")
