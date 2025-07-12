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
import joblib

def split_video_to_segments(input_path, segment_dir, segment_length=10):
    os.makedirs(segment_dir, exist_ok=True)
    segment_pattern = os.path.join(segment_dir, "segment_%04d.mp4")
    cmd = [
        ffmpeg_path, "-i", input_path, 
        "-c", "copy", 
        "-map", "0", 
        "-f", "segment",
        "-segment_time", str(segment_length), 
        "-reset_timestamps", "1", 
        segment_pattern
    ]
    subprocess.run(cmd, check=True)
    return sorted([os.path.join(segment_dir, f) for f in os.listdir(segment_dir) if f.endswith(".mp4")])

def extract_features(input_path):
    pass

def encode_segment(input_path, crf, max_rate, encoded_path):
    pass

# Max Rate를 다시 문자열 형태로 변환
def convert_numeric_to_max_rate_str(max_rate_num):
    if max_rate_num >= 950000: # 1M에 가까우면 M으로 표시
        return f"{round(max_rate_num / 1000000)}M"
    elif max_rate_num >= 950: # 1k에 가까우면 k로 표시
        return f"{round(max_rate_num / 1000)}k"
    return str(round(max_rate_num))

# 모델 로드
model = joblib.load('v3_rf_model.pkl')
scaler_X = joblib.load("v3_scaler_X.pkl")
scaler_y = joblib.load("v3_scaler_y.pkl")

# ffmpeg 실행 경로 (환경에 맞게 수정)
ffmpeg_path = r"C:\ffmpeg-2025-06-04-git-a4c1a5b084-essentials_build\bin\ffmpeg.exe"

# 입력 및 출력 디렉토리
#input/ 폴더에 video1.mp4 ~ video3.mp4가 있어야 함
#결과물은 static/video1/, static/video2/ 등에 저장됨
input_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "input"))
output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))
if not os.exists(output_dir):
    os.makedirs(output_dir, exist_ok=True)

# 비트레이트 및 해상도 설정 [(bitrate, resolution)]
resolution = ["640x360", "854x480", "1280x720", "1920x1080"]
# 세그먼트 길이(초)
segment_length = 10

#video_files = os.listdir(input_dir)
video_files = ["input/Anne-Marie - 2002 (Live At Brighton Music Hall 2018) (1).mp4", "input/Russian minister Roman Starovoit sacked by Putin found dead _ BBC News.mp4"]

for file in video_files:
    input_path = os.path.join(input_dir, file)
    name = os.path.splitext(file)[0]
    
    video_dir = os.path.join(output_dir, name)
    os.makedirs(video_dir, exist_ok=True)
    segment_dir = os.path.join(output_dir, name, "segments")
    os.makedirs(segment_dir, exist_ok=True)
    encoded_segment_dir = os.path.join(output_dir, name, "encoded_segments")
    os.makedirs(encoded_segment_dir, exist_ok=True)
    
    # 원본 영상을 10초 단위의 세그먼트(mp4)로 분할
    segments = split_video_to_segments(input_path, segment_dir, segment_length=10)
    encoded_segments = []
    
    for idx, segment_path in enumerate(segments):
        # 세그먼트별 특성 추출 및 전처리
        X_raw = extract_features(segment_path)
        X_scaled = scaler_X.transform(X_raw)
        
        # 모델 예측
        pred_scaled = model.predict(X_scaled)
        pred_scaled = pred_scaled.reshape(1, -1)
        pred_y = scaler_y.inverse_transform(pred_scaled)
        
        crf = pred_y[0, 0]
        max_rate = pred_y[0, 1]
        max_rate_str = convert_numeric_to_max_rate_str(max_rate)

        # 세그먼트 인코딩
        encoded_path = os.path.join(encoded_segment_dir, f"encoded_{idx:03d}.mp4")
        encode_segment(segment_path, crf, max_rate, encoded_path)
        encoded_segments.append(encoded_path)
    
    # DASH 패키징
    manifest_path = os.path.join(output_dir, name, "manifest.mpd")
    dash_cmd = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", "<(for f in {}/*.mp4; do echo \"file '$f'\"; done)".format(segment_dir),
        "-c", "copy",
        "-f", "dash",
        "-init_seg_name", "init-stream$RepresentationID$.mp4",
        "-media_seg_name", "chunk-stream$RepresentationID$-$Number$.m4s",
        "-seg_duration", str(segment_length),
        "-use_timeline", "1",
        "-use_template", "1",
        manifest_path
    ]
    subprocess.run(" ".join(dash_cmd), shell=True, check=True)
    
'''
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
    
    for i, res in enumerate(resolution):
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
'''