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
import cv2
import pandas as pd
import glob
from collections import Counter
import re

def split_video_to_segments(input_path, segment_dir, segment_length=10):
    segment_pattern = os.path.join(segment_dir, "segment_%04d.mp4")
    cmd = [
        "ffmpeg", "-i", input_path, 
        "-c", "copy", 
        "-map", "0", 
        "-f", "segment",
        "-segment_time", str(segment_length), 
        "-reset_timestamps", "1", 
        segment_pattern
    ]
    subprocess.run(cmd, check=True)
    return sorted([os.path.join(segment_dir, f) for f in os.listdir(segment_dir) if f.endswith(".mp4")])

def extract_features(input_path, segment_motion_vector_dir):
    # 모션벡터 추출
    # !python extract_mvs.py "{input_path}" -d "{segment_motion_vector_dir}"
    extract_script = "./mv_extractor/extract_mvs.py"
    cmd = [
        "python3", extract_script,
        input_path,
        "-d", segment_motion_vector_dir
    ]
    subprocess.run(cmd)
    
    # 모션 벡터 통계
    csv_dir = os.path.join(segment_motion_vector_dir, "motion_vectors")
    npy_files = glob.glob(os.path.join(csv_dir, '*.npy'))
    if not npy_files:
        print(f"No .npy files found in {csv_dir}")
        return
    for npy_file in npy_files:
        data = np.load(npy_file)
        csv_file = npy_file.replace('.npy', '.csv')
        np.savetxt(csv_file, data, delimiter=",")
    
    csv_files = glob.glob(os.path.join(csv_dir, '*.csv'))
    
    all_motion_x = []
    all_motion_y = []
    all_magnitudes = []

    for csv_file in csv_files:
        if os.path.getsize(csv_file) == 0:
          print(f"빈 파일: {csv_file}")
          continue
        df = pd.read_csv(csv_file)
        df.columns = ['ref_offset', 'block_w', 'block_h', 'ref_x', 'ref_y', 'cur_x', 'cur_y', 'mv_x', 'mv_y', 'mv_scale']
        df['motion_x'] = df['mv_x'] / df['mv_scale']
        df['motion_y'] = df['mv_y'] / df['mv_scale']
        df['magnitude'] = np.sqrt(df['motion_x']**2 + df['motion_y']**2)
        all_motion_x.extend(df['motion_x'])
        all_motion_y.extend(df['motion_y'])
        all_magnitudes.extend(df['magnitude'])
        
    motion_x_arr = np.array(all_motion_x)
    motion_y_arr = np.array(all_motion_y)
    magnitude_arr = np.array(all_magnitudes)
    
    segment_stats = {
        #'mean_motion_x': np.mean(motion_x_arr),
        #'mean_motion_y': np.mean(motion_y_arr),
        'mean_magnitude': np.mean(magnitude_arr),
        'max_magnitude': np.max(magnitude_arr),
        'std_magnitude': np.std(magnitude_arr),
        'motion_vector_count': len(magnitude_arr)
    }
    
    # 프레임 비율 분석
    frame_types_file = os.path.join(segment_motion_vector_dir, "frame_types.txt")
    with open(frame_types_file, 'r') as f:
        frame_types = [line.strip() for line in f if line.strip()]
    counts = Counter(frame_types)
    total = len(frame_types)
    ratios = {k: round(v / total, 3) for k, v in counts.items()}
    for k, v in ratios.items():
        segment_stats[k + '_ratio'] = v
    
    # 매크로 블록 비율 분석
    cmd = [
        'ffmpeg',
        '-debug', 'mb_type',
        '-i', input_path,
        '-f', 'null',
        '-'
    ]
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stderr = process.stderr

    symbol_map = {
        'Intra': ['I', 'i'], # 'A', 'i', "I"
        'Inter': ['d', '<', '>', 'X'], # 'd', '<' ,'>', 'X', 'D'
        'Skip': ['S'] # 'S', 'd'
    }
    # 정규표현식: 기호가 10개 이상 반복되는 라인만 추출(환경에 따라 숫자 조정)
    mb_lines = [line for line in stderr.splitlines() if re.search(r'([dI<SX>iS]\s*){10,}', line)]

    # 전체 심볼 카운트
    total_counts = {'Intra': 0, 'Inter': 0, 'Skip': 0}

    for line in mb_lines:
        symbols = re.findall(r'[dI<SX>iS]', line)
        for k, v in symbol_map.items():
            total_counts[k] += sum(symbols.count(s) for s in v)

    total_blocks = sum(total_counts.values())
    if total_blocks == 0:
        return {k: 0.0 for k in total_counts}
    ratios = {k: round(total_counts[k] / total_blocks, 3) for k in total_counts}
    
    for k, v in ratios.items():
        segment_stats[k] = v
        
    return segment_stats
    
def encode_segment(input_path, crf, max_rate, encoded_path):
    """
    하나의 영상 세그먼트를 지정된 CRF와 Max Rate로 인코딩
    """
    # bufsize는 일반적으로 maxrate의 1.5 ~ 2배 정도로 설정합니다.
    # max_rate가 'k'나 'M' 단위로 올 수 있으므로, 숫자만 파싱하여 계산
    if max_rate.endswith('k'):
        rate_val = int(max_rate[:-1]) * 1000
    elif max_rate.endswith('M'):
        rate_val = int(max_rate[:-1]) * 1000000
    else:
        rate_val = int(max_rate) # 기본은 bps
    bufsize_val = rate_val * 2
    bufsize = f"{int(bufsize_val / 1000)}k" if bufsize_val >= 1000 else f"{bufsize_val}"

    # ffmpeg -i [입력 파일] -c:v [인코더] -crf [CRF] -maxrate [MaxRate] -bufsize [BufferSize] -y [출력 파일]
    cmd = [
        "ffmpeg",
        "-i", input_path,
        "-c:v", "libx264", # config에서 설정한 인코더 사용
        "-preset", "medium",  # 인코딩 속도 vs 압축률 조절 (GPU 인코더에도 적용 가능)
        "-crf", str(crf), # NVENC의 CQP 매핑
        "-maxrate", max_rate,
        "-bufsize", bufsize,
        "-threads", "0",  # CPU 멀티스레드 자동 사용
        "-y",  # 덮어쓰기 허용
        encoded_path
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, errors='ignore')
        #subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return encoded_path
    except subprocess.CalledProcessError as e:
        print(f"인코딩 실패: {input_path} (CRF: {crf}, Max Rate: {max_rate})")
        print(f"FFmpeg 에러 메시지:\n{e.stderr}")
        return None    
    
def encode_segment_per_resolution(input_path, crf, max_rate, output_base_path):
    """
    하나의 세그먼트를 해상도별로 CRF 및 MaxRate로 인코딩
    ex: segment_0000_360p.mp4, segment_0000_480p.mp4 ...
    """
    resolutions = {
        "360p":  "640x360",
        "480p":  "854x480",
        "720p":  "1280x720",
        "1080p": "1920x1080"
    }
    
    # bufsize는 일반적으로 maxrate의 1.5 ~ 2배 정도로 설정합니다.
    # max_rate가 'k'나 'M' 단위로 올 수 있으므로, 숫자만 파싱하여 계산
    if max_rate.endswith('k'):
        rate_val = int(max_rate[:-1]) * 1000
    elif max_rate.endswith('M'):
        rate_val = int(max_rate[:-1]) * 1000000
    else:
        rate_val = int(max_rate) # 기본은 bps
    bufsize_val = rate_val * 2
    bufsize = f"{int(bufsize_val / 1000)}k" if bufsize_val >= 1000 else f"{bufsize_val}"

    output_paths = {}
    
    # ffmpeg -i [입력 파일] -c:v [인코더] -crf [CRF] -maxrate [MaxRate] -bufsize [BufferSize] -y [출력 파일]
    for label, res in resolutions.items():
        output_path = f"{output_base_path}_{label}.mp4"
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-vf", f"scale={res}", # 해상도별 인코딩
            "-c:v", "libx264", # config에서 설정한 인코더 사용
            "-preset", "medium",  # 인코딩 속도 vs 압축률 조절 (GPU 인코더에도 적용 가능)
            "-crf", str(crf), # NVENC의 CQP 매핑
            "-maxrate", max_rate,
            "-bufsize", bufsize,
            "-threads", "0",  # CPU 멀티스레드 자동 사용
            "-y",  # 덮어쓰기 허용
            output_path
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, errors='ignore')
            output_paths[label] = output_path
        except subprocess.CalledProcessError as e:
            print(f"인코딩 실패: {input_path} (CRF: {crf}, Max Rate: {max_rate})")
            print(f"FFmpeg 에러 메시지:\n{e.stderr}")
    
    return output_paths

# Max Rate를 다시 문자열 형태로 변환
def convert_numeric_to_max_rate_str(max_rate_num):
    if max_rate_num >= 950000: # 1M에 가까우면 M으로 표시
        return f"{round(max_rate_num / 1000000)}M"
    elif max_rate_num >= 950: # 1k에 가까우면 k로 표시
        return f"{round(max_rate_num / 1000)}k"
    return str(round(max_rate_num))

def run_dash_generation(sh_path):
    print("[⚙️] dash_generate.sh 실행 중...")
    result = subprocess.run(["bash", sh_path], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[❌] 실행 실패\n{result.stderr}")
    else:
        print("[✅] DASH 세그먼트 생성 완료")

def generate_single_mpd(output_dir, num_segments):
    print("[📄] MPD 파일 생성 중...")
    rep_ids = [0, 1, 2, 3]
    with open(os.path.join(output_dir, "manifest.mpd"), "w") as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>\n')
        f.write('<MPD xmlns="urn:mpeg:dash:schema:mpd:2011" type="static">\n')
        f.write('  <Period>\n')
        f.write('    <AdaptationSet>\n')
        for rep_id in rep_ids:
            f.write(f'      <Representation id="{rep_id}" bandwidth="1000000">\n')
            f.write(f'        <BaseURL>chunk-stream{rep_id}-</BaseURL>\n')
            f.write('      </Representation>\n')
        f.write('    </AdaptationSet>\n')
        f.write('  </Period>\n')
        f.write('</MPD>\n')
    print("[✅] manifest.mpd 생성 완료!")

# ffmpeg 실행 경로 (환경에 맞게 수정)
# Window에서 실행 시
# ffmpeg_path = r"C:\ffmpeg-2025-06-04-git-a4c1a5b084-essentials_build\bin\ffmpeg.exe"
# WSL Ubuntu에서 실행 시
ffmpeg_path = r"/mnt/c/ffmpeg-2025-06-04-git-a4c1a5b084-essentials_build/bin/ffmpeg.exe"

# 입력 및 출력 디렉토리
#input/ 폴더에 video1.mp4 ~ video3.mp4가 있어야 함
#결과물은 static/video1/, static/video2/ 등에 저장됨
current_dir = os.path.dirname(os.path.abspath(__file__))
input_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "input"))
output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))
if not os.path.exists(output_dir):
    os.makedirs(output_dir, exist_ok=True)

# 모델 로드
model = joblib.load(os.path.join(current_dir, 'v3_rf_model.pkl'))
scaler_X = joblib.load(os.path.join(current_dir, 'v3_scaler_X.pkl'))
scaler_y = joblib.load(os.path.join(current_dir, 'v3_scaler_y.pkl'))

# 비트레이트 및 해상도 설정 [(bitrate, resolution)]
resolution = ["640x360", "854x480", "1280x720", "1920x1080"]
# 세그먼트 길이(초)
segment_length = 10

#video_files = os.listdir(input_dir)
video_files = ["husky.mp4"]

for file in video_files:
    input_path = os.path.join(input_dir, file)
    name = os.path.splitext(file)[0]
    
    # server/static/video1
    video_dir = os.path.join(output_dir, name)
    os.makedirs(video_dir, exist_ok=True)
    # server/static/video1/segments
    segment_dir = os.path.join(video_dir, "segments")
    os.makedirs(segment_dir, exist_ok=True)
    # server/static/video1/encoded_segments
    encoded_segment_dir = os.path.join(video_dir, "encoded_segments")
    os.makedirs(encoded_segment_dir, exist_ok=True)
    # server/static/video1/motion_vectotr
    motion_vector_dir = os.path.join(video_dir, "motion_vector")
    os.makedirs(motion_vector_dir, exist_ok=True)
    
    # 원본 영상을 10초 단위의 세그먼트(mp4)로 분할
    segments = split_video_to_segments(input_path, segment_dir, segment_length=10)
    encoded_segments = []
    
    for idx, segment_path in enumerate(segments):
        # 세그먼트별 특성 추출 및 전처리
        segment_name = os.path.basename(segment_path).split('.')[0]
        segment_motion_vector_dir = os.path.join(motion_vector_dir, segment_name)
        X_raw_dict = extract_features(segment_path, segment_motion_vector_dir)
        X_raw_list = list(X_raw_dict.values())
        X_scaled = scaler_X.transform([X_raw_list])
        
        # 모델 예측
        pred_scaled = model.predict(X_scaled)
        pred_scaled = pred_scaled.reshape(1, -1)
        pred_y = scaler_y.inverse_transform(pred_scaled)
        
        crf = round(pred_y[0, 0])
        max_rate = pred_y[0, 1]
        max_rate_str = convert_numeric_to_max_rate_str(max_rate)

        # 세그먼트 인코딩
        print(f"{segment_name}에 대하여 CRF : {crf}, Max rate : {max_rate_str}로 인코딩합니다.")
        encoded_path = os.path.join(encoded_segment_dir, f"encoded_{segment_name}")
        encoded_paths = encode_segment_per_resolution(segment_path, crf, max_rate_str, encoded_path)
    
    run_dash_generation(os.path.join(current_dir, 'dash_generate.sh'))
    num_segments = len([f for f in os.listdir(os.path.join(video_dir, "segments"))])
    generate_single_mpd(video_dir, num_segments)
    '''
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