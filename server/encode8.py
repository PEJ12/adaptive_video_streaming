#29일 수정 
# 세그먼트별 AI 파라미터 적용 → concat → mp4box-dash 분할


# ai_dash_mp4box_pipeline.py
import os
import subprocess
import shutil
import numpy as np
import pandas as pd
import joblib
from collections import Counter
import glob
import re

# === (1) 설정 ===
INPUT_MP4 = "../input/husky.mp4"            # 원본 영상
TMP_SEG_DIR = "./static/husky/segments"     # 임시 세그먼트 mp4 폴더
AI_SEG_DIR = "./ai_encoded_segs"            # AI 파라미터 인코딩된 세그먼트 mp4 폴더
OUT_DIR = "./static/husky"                  # 최종 결과 폴더
MODEL_PATH = "./v3_rf_model.pkl"            # TODO: 네 AI 모델 파일
SCALER_X_PATH = "./v3_scaler_X.pkl"
SCALER_Y_PATH = "./v3_scaler_y.pkl"
MV_EXTRACT_PY = "./mv_extractor/extract_mvs.py"  # 모션벡터 추출 스크립트 경로
RESOLUTION = "1280x720"                    # 해상도(하나만 예시. 여러개는 for문)
SEG_LEN = 10
resolutions = {
    "360p":  ("640x360", 0),
    "480p":  ("854x480", 1),
    "720p":  ("1280x720", 2),
    "1080p": ("1920x1080", 3)
}

os.makedirs(TMP_SEG_DIR, exist_ok=True)
os.makedirs(AI_SEG_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

# === (2) 세그먼트 분할 함수 ===
def split_video(input_path, segment_dir, segment_length=10):
    import os
    from math import ceil
    duration_cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
        "default=noprint_wrappers=1:nokey=1", input_path
    ]
    duration = float(subprocess.check_output(duration_cmd).decode().strip())
    num_segments = ceil(duration / segment_length)
    seg_paths = []
    os.makedirs(segment_dir, exist_ok=True)
    # 기존 파일 모두 삭제
    for f in os.listdir(segment_dir):
        if f.startswith("segment_") and f.endswith(".mp4"):
            os.remove(os.path.join(segment_dir, f))
    for i in range(num_segments):
        out = os.path.join(segment_dir, f"segment_{i}.mp4")
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(i * segment_length),
            "-i", input_path,
            "-t", str(segment_length),
            "-an",
            "-c:v", "copy",
            out
        ]
        subprocess.run(cmd, check=True)
        seg_paths.append(out)
        print(f"[분할] {out} → 존재: {os.path.exists(out)}")
    print("== segments에 실제로 생성된 파일:", os.listdir(segment_dir))
    return seg_paths

# === (3) 세그먼트별 모션벡터/AI 특성 추출 ===
def extract_features(input_path, segment_motion_vector_dir):
    # 1. 모션벡터 추출
    extract_script = "./mv_extractor/extract_mvs.py"
    cmd = [
        "python3", extract_script,
        input_path,
        "-d", segment_motion_vector_dir
    ]
    subprocess.run(cmd)

    # 2. 모션 벡터 통계
    csv_dir = os.path.join(segment_motion_vector_dir, "motion_vectors")
    npy_files = glob.glob(os.path.join(csv_dir, '*.npy'))
    for npy_file in npy_files:
        data = np.load(npy_file)
        csv_file = npy_file.replace('.npy', '.csv')
        np.savetxt(csv_file, data, delimiter=",")
    csv_files = glob.glob(os.path.join(csv_dir, '*.csv'))
    all_magnitudes = []
    for csv_file in csv_files:
        if os.path.getsize(csv_file) == 0:
            continue
        df = pd.read_csv(csv_file)
        df.columns = ['ref_offset', 'block_w', 'block_h', 'ref_x', 'ref_y', 'cur_x', 'cur_y', 'mv_x', 'mv_y', 'mv_scale']
        df['motion_x'] = df['mv_x'] / df['mv_scale']
        df['motion_y'] = df['mv_y'] / df['mv_scale']
        df['magnitude'] = np.sqrt(df['motion_x']**2 + df['motion_y']**2)
        all_magnitudes.extend(df['magnitude'])
    if len(all_magnitudes) == 0:
        # 세그먼트가 너무 짧아서 벡터 없음
        return [0.0]*10

    motion_x_arr = np.array(all_magnitudes)
    # 3. 프레임 비율 분석 (I/P/B)
    frame_types_file = os.path.join(segment_motion_vector_dir, "frame_types.txt")
    I_ratio = P_ratio = B_ratio = 0.0
    if os.path.exists(frame_types_file):
        with open(frame_types_file, 'r') as f:
            frame_types = [line.strip() for line in f if line.strip()]
        counts = Counter(frame_types)
        total = len(frame_types)
        if total > 0:
            I_ratio = round(counts.get('I', 0)/total, 3)
            P_ratio = round(counts.get('P', 0)/total, 3)
            B_ratio = round(counts.get('B', 0)/total, 3)
    
    # 4. 매크로블록 비율 분석 (Intra/Inter/Skip)
    cmd = [
        'ffmpeg',
        '-debug', 'mb_type',
        '-i', input_path,
        '-f', 'null',
        '-'
    ]
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stderr = process.stderr
    symbol_map = {'Intra': ['I', 'i'], 'Inter': ['d', '<', '>', 'X'], 'Skip': ['S']}
    mb_lines = [line for line in stderr.splitlines() if re.search(r'([dI<SX>iS]\s*){10,}', line)]
    total_counts = {'Intra': 0, 'Inter': 0, 'Skip': 0}
    for line in mb_lines:
        symbols = re.findall(r'[dI<SX>iS]', line)
        for k, v in symbol_map.items():
            total_counts[k] += sum(symbols.count(s) for s in v)
    total_blocks = sum(total_counts.values())
    Intra_ratio = Inter_ratio = Skip_ratio = 0.0
    if total_blocks > 0:
        Intra_ratio = round(total_counts['Intra'] / total_blocks, 3)
        Inter_ratio = round(total_counts['Inter'] / total_blocks, 3)
        Skip_ratio = round(total_counts['Skip'] / total_blocks, 3)

    # 5. 반환 (항상 10개)
    features = [
        float(np.mean(motion_x_arr)),   # mean_magnitude
        float(np.max(motion_x_arr)),    # max_magnitude
        float(np.std(motion_x_arr)),    # std_magnitude
        float(len(motion_x_arr)),       # motion_vector_count
        I_ratio,                        # I_ratio
        P_ratio,                        # P_ratio
        B_ratio,                        # B_ratio
        Intra_ratio,                    # Intra
        Inter_ratio,                    # Inter
        Skip_ratio                      # Skip
    ]
    return features


# === (4) AI 파라미터 예측 ===
def ai_predict(feature_list, scaler_X, scaler_y, model):
    """
    feature_list : [mean_mag, max_mag, std_mag, count, I, P, B, Intra, Inter, Skip]
    """
    # feature_list는 이미 10개 특성이 정해진 순서로 담긴 리스트
    X_scaled = scaler_X.transform([feature_list])
    pred_scaled = model.predict(X_scaled)
    pred_scaled = pred_scaled.reshape(1, -1)
    pred_y = scaler_y.inverse_transform(pred_scaled)
    crf = round(pred_y[0, 0])
    maxrate = pred_y[0, 1]
    return crf, maxrate


# === (5) AI 인코딩 ===
def ai_encode_segments(seg_paths, out_dir, scaler_X, scaler_y, model, resolution):
    ai_segs = []
    for i, seg_path in enumerate(seg_paths):
        seg_name = f"ai_seg_{i}.mp4"
        out_mp4 = os.path.join(out_dir, seg_name)
        mv_dir = os.path.join(out_dir, f"mv_{i}")
        os.makedirs(mv_dir, exist_ok=True)
        # --- 특징 추출
        features = extract_features(seg_path, mv_dir)
        crf, maxrate = ai_predict(features, scaler_X, scaler_y, model)
        print(f"[AI인코딩] segment_{i}: CRF={crf}, maxrate={maxrate}")
        # --- 인코딩
        cmd = [
            "ffmpeg", "-y", "-i", seg_path,
            "-vf", f"scale={resolution}",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", str(crf),
            "-maxrate", str(maxrate),
            "-bufsize", "4000k",
            "-an", out_mp4
        ]
        subprocess.run(cmd, check=True)
        ai_segs.append(out_mp4)
    return ai_segs

# === (6) concat.txt & 병합 ===
def make_concat_txt(segment_paths, concat_txt_path):
    with open(concat_txt_path, "w") as f:
        for p in segment_paths:
            f.write(f"file '{os.path.abspath(p)}'\n")

def concat_segments(concat_txt_path, out_mp4_path):
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_txt_path,
        "-c", "copy",
        out_mp4_path
    ]
    subprocess.run(cmd, check=True)

# === (7) mp4box dash ===
def mp4box_dash(input_mp4, dash_dir, segment_ms=10000):
    os.makedirs(dash_dir, exist_ok=True)
    mpd_path = os.path.join(dash_dir, "manifest.mpd")
    cmd = [
        "MP4Box", "-dash", str(segment_ms), "-frag", str(segment_ms), "-rap",
        "-profile", "dashavc264:live",
        "-out", mpd_path,
        input_mp4
    ]
    subprocess.run(cmd, check=True)
    print(f"[완료] DASH mpd/m4s 생성: {mpd_path}")


def reencode_mp4(input_mp4, output_mp4):
    """
    병합된 mp4를 스트림 복사(copy) 말고, 실제 인코딩으로 다시 만듭니다.
    """
    cmd = [
        "ffmpeg", "-y", "-i", input_mp4,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-movflags", "+faststart",
        "-an",  # 오디오 필요시 이 줄 삭제
        output_mp4
    ]
    subprocess.run(cmd, check=True)
    print(f"[ffmpeg] 재인코딩 완료: {output_mp4}")

# === (8) 전체 실행 ===
if __name__ == "__main__":
    # 모델 로드
    model = joblib.load(MODEL_PATH)
    scaler_X = joblib.load(SCALER_X_PATH)
    scaler_y = joblib.load(SCALER_Y_PATH)

    print("1. 영상 세그먼트 분할")
    seg_paths = split_video(INPUT_MP4, TMP_SEG_DIR, SEG_LEN)
    print(f"총 {len(seg_paths)}개 세그먼트 생성됨.")

    print("2. 세그먼트별 AI 인코딩")
    ai_segs = ai_encode_segments(seg_paths, AI_SEG_DIR, scaler_X, scaler_y, model, RESOLUTION)

    print("3. concat.txt 작성 및 병합")
    concat_txt = os.path.join(OUT_DIR, "concat.txt")
    merged_mp4 = os.path.join(OUT_DIR, "merged_ai.mp4")
    make_concat_txt(ai_segs, concat_txt)
    concat_segments(concat_txt, merged_mp4)

    print("4. 병합 mp4 재인코딩")
    fixed_mp4 = os.path.join(OUT_DIR, "merged_ai_fixed.mp4")
    reencode_mp4(merged_mp4, fixed_mp4)

    print("5. mp4box dash로 분할 및 mpd생성")
    mp4box_dash(fixed_mp4, os.path.join(OUT_DIR), segment_ms=SEG_LEN*1000)