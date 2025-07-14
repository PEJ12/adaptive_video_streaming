#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="${SCRIPT_DIR}/static"

RES_LABELS=("360p" "480p" "720p" "1080p")
REP_IDS=(0 1 2 3)

for VIDEO_DIR in "$BASE_DIR"/*/; do
    SEGMENT_DIR="${VIDEO_DIR}encoded_segments"
    OUTPUT_DIR="${VIDEO_DIR}"

    if [ ! -d "$SEGMENT_DIR" ]; then
        echo "[⚠️] $SEGMENT_DIR 없음. 스킵함."
        continue
    fi

    echo "[▶️] $VIDEO_DIR 처리 중..."

    for i in "${!RES_LABELS[@]}"; do
        label="${RES_LABELS[$i]}"
        rep_id="${REP_IDS[$i]}"

        # 첫 번째 세그먼트로 init-stream 생성
        first_seg=$(find "$SEGMENT_DIR" -name "*_${label}.mp4" | head -n 1)
        if [ -f "$first_seg" ]; then
            ffmpeg -y -i "$first_seg" -c copy -f mp4 "${OUTPUT_DIR}/init-stream${rep_id}.mp4"
            echo "  [🎬] init-stream${rep_id}.mp4 생성 완료"
        fi

        # m4s 파일로 복사
        for seg_path in "$SEGMENT_DIR"/encoded_segment_*_"${label}".mp4; do
            seg_name=$(basename "$seg_path")
            seg_num=$(echo "$seg_name" | grep -oP 'encoded_segment_\K[0-9]+')
            cp "$seg_path" "${OUTPUT_DIR}/chunk-stream${rep_id}-${seg_num}.m4s"
        done
    done
done

echo "[✅] 모든 m4s 및 init-stream 생성 완료"
