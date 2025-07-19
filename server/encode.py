# 자동화 인코딩 스크립트
#3개의 mp4 영상을 읽어서, 각각에 대해 4개 해상도(360p, 480p, 720p, 1080p)로
#인코딩을 하고, DASH 스트리밍용 MPD + 세그먼트들을 생성

#huskey 영상만 인코딩 하게 되어있음 
#video_files = ["husky.mp4"]

#실행순서
#python3 encode.py 로 실행. F5 말고, 터미널로 하기
#cd server
#python3 -m uvicorn main:app --reload
#Netflix 폴더에서 npm run dev 실행

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
from xml.etree.ElementTree import Element, SubElement, ElementTree

# 함수 추가(은재)
def get_valid_segments(segment_dir, min_duration=1.0):
    segments = sorted([os.path.join(segment_dir, f) for f in os.listdir(segment_dir) if f.endswith(".mp4")], key=extract_number)
    valid_segments = []
    for seg in segments:
        # ffprobe로 길이 측정
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            seg
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        duration = float(result.stdout.strip())
        if duration >= min_duration:
            valid_segments.append(seg)
        else:
            print(f"[SKIP] {os.path.basename(seg)} 너무 짧음({duration:.2f}s) → 제외")
    return valid_segments

def split_video_to_segments(input_path, segment_dir, segment_length=10):
    segment_pattern = os.path.join(segment_dir, "segment_%d.mp4")
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

def split_video_to_segments_reencode(input_path, segment_dir, segment_length=10):
    """
    정확히 segment_length(초) 단위로 영상을 재인코딩하여 세그먼트 분할
    - CRF 23, libx264 인코딩
    - 10초마다 키프레임 삽입
    - 오디오도 인코딩 포함
    """
    os.makedirs(segment_dir, exist_ok=True)
    segment_pattern = os.path.join(segment_dir, "segment_%d.mp4")

    cmd = [
        "ffmpeg", "-i", input_path,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-g", str(segment_length * 24),  # GOP 사이즈 (FPS=24 가정)
        "-keyint_min", str(segment_length * 24),
        "-force_key_frames", f"expr:gte(t,n_forced*{segment_length})",
        "-c:a", "aac", "-b:a", "128k",
        "-f", "segment",
        "-segment_time", str(segment_length),
        "-reset_timestamps", "1",
        "-y",
        segment_pattern
    ]

    print("[🎬] FFmpeg 세그먼트 재인코딩 중...")
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
    
def generate_init_stream(input_path, crf, max_rate, output_dir):
    """
    하나의 영상 세그먼트를 지정된 CRF와 Max Rate로 인코딩
    """
    resolutions = {
        "360p":  ("640x360", 0),
        "480p":  ("854x480", 1),
        "720p":  ("1280x720", 2),
        "1080p": ("1920x1080", 3)
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

    for label, (res, rep_id) in resolutions.items():
        output_path = os.path.join(output_dir, f"init-stream{rep_id}.mp4")

        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-vf", f"scale={res}",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", str(crf),
            "-maxrate", max_rate,
            "-bufsize", bufsize,
            "-an",
            "-threads", "0",
            "-movflags", "+frag_keyframe+empty_moov+default_base_moof",
            "-f", "mp4",
            "-y",
            output_path
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"[🎬] init-stream{rep_id}.mp4 생성 완료")
        except subprocess.CalledProcessError as e:
            print(f"[❌] init-stream{rep_id}.mp4 생성 실패")
            print(e.stderr)
    
def encode_segment_per_resolution(input_path, crf, max_rate, video_dir):
    """
    하나의 세그먼트를 해상도별로 CRF 및 MaxRate로 인코딩
    ex: segment_0_360p.mp4, segment_0_480p.mp4 ...
    """
    resolutions = {
        "360p":  ("640x360", 0),
        "480p":  ("854x480", 1),
        "720p":  ("1280x720", 2),
        "1080p": ("1920x1080", 3)
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
    for label, (res, rep_id) in resolutions.items():
        segment_name = os.path.basename(input_path).split('.')[0]
        segment_id = segment_name.split('_')[-1]  # 예: 0
        #output_path = f"{output_base_path}_{label}.mp4"
        output_path = os.path.join(video_dir, f"chunk-stream{rep_id}-{segment_id}.m4s")
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-vf", f"scale={res}", # 해상도별 인코딩
            "-c:v", "libx264", # config에서 설정한 인코더 사용
            "-preset", "medium",  # 인코딩 속도 vs 압축률 조절 (GPU 인코더에도 적용 가능)
            "-crf", str(crf), # NVENC의 CQP 매핑
            "-maxrate", max_rate,
            "-bufsize", bufsize,
            "-an",  # ✅ 오디오 제거
            "-threads", "0",  # CPU 멀티스레드 자동 
            "-movflags", "+frag_keyframe+empty_moov+default_base_moof",
            "-f", "mp4",
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

def get_last_segment_duration(last_segment_path):
    """
    마지막 세그먼트의 길이를 초 단위로 반환합니다.
    """
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        last_segment_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        duration = float(result.stdout.strip())
        return duration
    except ValueError:
        print(f"[⚠️] 마지막 세그먼트 길이 추출 실패: {last_segment_path}")
        return None

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

#매개변수 수정함!!(은재)
def generate_single_mpd(output_dir, num_segments, last_segment_duration, segment_duration=10, timescale=24000):
    print("[📄] MPD 파일 생성 중...")

    rep_settings = [
        {"id": 0, "width": 640,  "height": 360,  "bandwidth": 500000,  "codecs": "avc1.64001e", "sar": "1:1"},
        {"id": 1, "width": 854,  "height": 480,  "bandwidth": 1000000, "codecs": "avc1.64001e", "sar": "1280:1281"},
        {"id": 2, "width": 1280, "height": 720,  "bandwidth": 2000000, "codecs": "avc1.64001f", "sar": "1:1"},
        {"id": 3, "width": 1920, "height": 1080, "bandwidth": 3000000, "codecs": "avc1.640028", "sar": "1:1"}
    ]

    segment_duration_ticks = int(segment_duration * timescale)
    last_seg_ticks = int(last_segment_duration * timescale)
    total_ticks = (num_segments - 1) * segment_duration_ticks + last_seg_ticks

    mpd = Element("MPD", {
        "xmlns": "urn:mpeg:dash:schema:mpd:2011",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xmlns:xlink": "http://www.w3.org/1999/xlink",
        "xsi:schemaLocation": "urn:mpeg:DASH:schema:MPD:2011 http://standards.iso.org/ittf/PubliclyAvailableStandards/MPEG-DASH_schema_files/DASH-MPD.xsd",
        "profiles": "urn:mpeg:dash:profile:isoff-live:2011",
        "type": "static",
        "mediaPresentationDuration": f"PT{round(total_ticks / timescale, 3)}S",
        "maxSegmentDuration": f"PT{segment_duration:.3f}S",
        "minBufferTime": "PT8.3S"
    })

    SubElement(mpd, "ProgramInformation")
    SubElement(mpd, "ServiceDescription", {"id": "0"})

    period = SubElement(mpd, "Period", {"id": "0", "start": "PT0.0S"})

    adaptation_set = SubElement(period, "AdaptationSet", {
        "id": "0",
        "contentType": "video",
        "startWithSAP": "1",
        "segmentAlignment": "true",
        "bitstreamSwitching": "true",
        "frameRate": "24000/1001",
        "maxWidth": "1920",
        "maxHeight": "1080",
        "par": "16:9",
        "lang": "und"
    })

    for rep in rep_settings:
        representation = SubElement(adaptation_set, "Representation", {
            "id": str(rep["id"]),
            "mimeType": "video/mp4",
            "codecs": rep["codecs"],
            "bandwidth": str(rep["bandwidth"]),
            "width": str(rep["width"]),
            "height": str(rep["height"]),
            "sar": rep["sar"]
        })

        segment_template = SubElement(representation, "SegmentTemplate", {
            "timescale": str(timescale),
            "initialization": f"init-stream{rep['id']}.mp4",
            "media": f"chunk-stream{rep['id']}-$Number$.m4s",
            "startNumber": "0"  # 1 -> 0 으로 수정
        })

        timeline = SubElement(segment_template, "SegmentTimeline")
        
        # 일반 세그먼트
        for i in range(num_segments - 1):
            SubElement(timeline, "S", {
                "t": str(i * segment_duration_ticks),
                "d": str(segment_duration_ticks),
            })
        # 마지막 세그먼트 (길이가 짧을 수 있음)
        last_ticks = int(last_segment_duration * timescale)
        SubElement(timeline, "S", {
            "t": str((num_segments - 1) * segment_duration_ticks),
            "d": str(last_ticks)
        })

    # 저장
    output_path = os.path.join(output_dir, "manifest.mpd")
    ElementTree(mpd).write(output_path, encoding="utf-8", xml_declaration=True)
    print(f"[✅] manifest.mpd 생성 완료! → {output_path}")

def v2_generate_single_mpd(output_dir, num_segments, segment_duration, timescale=24000):
    print("[📄] MPD 파일 생성 중...")

    rep_settings = [
        {"id": 0, "width": 640,  "height": 360,  "bandwidth": 500000,  "codecs": "avc1.64001e", "sar": "1:1"},
        {"id": 1, "width": 854,  "height": 480,  "bandwidth": 1000000, "codecs": "avc1.64001e", "sar": "1280:1281"},
        {"id": 2, "width": 1280, "height": 720,  "bandwidth": 2000000, "codecs": "avc1.64001f", "sar": "1:1"},
        {"id": 3, "width": 1920, "height": 1080, "bandwidth": 3000000, "codecs": "avc1.640028", "sar": "1:1"}
    ]

    segment_duration_ticks = int(segment_duration * timescale)
    total_ticks = num_segments * segment_duration_ticks

    mpd = Element("MPD", {
        "xmlns": "urn:mpeg:dash:schema:mpd:2011",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xmlns:xlink": "http://www.w3.org/1999/xlink",
        "xsi:schemaLocation": "urn:mpeg:DASH:schema:MPD:2011 http://standards.iso.org/ittf/PubliclyAvailableStandards/MPEG-DASH_schema_files/DASH-MPD.xsd",
        "profiles": "urn:mpeg:dash:profile:isoff-live:2011",
        "type": "static",
        "mediaPresentationDuration": f"PT{round(total_ticks / timescale, 1)}S",
        "maxSegmentDuration": f"PT{segment_duration:.1f}S",
        "minBufferTime": "PT8.3S"
    })

    SubElement(mpd, "ProgramInformation")
    SubElement(mpd, "ServiceDescription", {"id": "0"})

    period = SubElement(mpd, "Period", {"id": "0", "start": "PT0.0S"})

    adaptation_set = SubElement(period, "AdaptationSet", {
        "id": "0",
        "contentType": "video",
        "startWithSAP": "1",
        "segmentAlignment": "true",
        "bitstreamSwitching": "true",
        "frameRate": "24000/1001",
        "maxWidth": "1920",
        "maxHeight": "1080",
        "par": "16:9",
        "lang": "und"
    })

    for rep in rep_settings:
        representation = SubElement(adaptation_set, "Representation", {
            "id": str(rep["id"]),
            "mimeType": "video/mp4",
            "codecs": rep["codecs"],
            "bandwidth": str(rep["bandwidth"]),
            "width": str(rep["width"]),
            "height": str(rep["height"]),
            "sar": rep["sar"]
        })

        segment_template = SubElement(representation, "SegmentTemplate", {
            "timescale": str(timescale),
            "initialization": f"init-stream{rep['id']}.mp4",
            "media": f"chunk-stream{rep['id']}-$Number$.m4s",
            "startNumber": "0"
        })

        timeline = SubElement(segment_template, "SegmentTimeline")
        SubElement(timeline, "S", {
            "d": str(segment_duration_ticks),
            "r": str(num_segments - 1)
        })

    # 저장
    output_path = os.path.join(output_dir, "manifest.mpd")
    ElementTree(mpd).write(output_path, encoding="utf-8", xml_declaration=True)
    print(f"[✅] manifest.mpd 생성 완료! → {output_path}")

def extract_number(filename):
    """파일 이름에서 숫자 추출 (예: segment_12.mp4 → 12)"""
    match = re.search(r"segment_(\d+)\.mp4", filename)
    return int(match.group(1)) if match else -1

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
#huskey 영상만 인코딩 하게 되어있음
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
    segments = split_video_to_segments_reencode(input_path, segment_dir, segment_length=10)
    #segments = split_video_to_segments(input_path, segment_dir, segment_length=10)
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

        # segment_0000에 대해서 init-stream 생성
        if segment_name=='segment_0':
            print(f"{segment_name}에 대하여 init-stream을 생성합니다.")
            generate_init_stream(segment_path, crf, max_rate_str, video_dir)

        # 세그먼트를 4개의 해상도로 m4s 파일 생성
        print(f"{segment_name}에 대하여 CRF : {crf}, Max rate : {max_rate_str}로 인코딩합니다.")
        encoded_paths = encode_segment_per_resolution(segment_path, crf, max_rate_str, video_dir)
    
    # 마지막 세그먼트 (segment_12.mp4) 길이 계산
    segment_files = [f for f in os.listdir(segment_dir) if f.endswith(".mp4")]
    segment_files.sort(key=extract_number)
    
    last_segment = segment_files[-1]
    last_segment_path = os.path.join(segment_dir, last_segment)
    last_duration = get_last_segment_duration(last_segment_path)
    print(f"마지막 세그먼트({last_segment}) 길이: {last_duration:.2f}초")
    
    num_segments = len([f for f in os.listdir(os.path.join(video_dir, "segments"))])
    generate_single_mpd(video_dir, num_segments, last_duration, segment_length)