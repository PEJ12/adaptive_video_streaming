# 자동화 인코딩 스크립트
#3개의 mp4 영상을 읽어서, 각각에 대해 4개 해상도(360p, 480p, 720p, 1080p)로
#인코딩을 하고, DASH 스트리밍용 MPD + 세그먼트들을 생성

import os
import subprocess

# ffmpeg 실행 경로 (환경에 맞게 수정)
ffmpeg_path = r"C:\ffmpeg-2025-06-04-git-a4c1a5b084-essentials_build\bin\ffmpeg.exe"

# 입력 및 출력 디렉토리
#input/ 폴더에 video1.mp4 ~ video3.mp4가 있어야 함
#결과물은 static/video1/, static/video2/ 등에 저장됨
input_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "input"))
output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))

# 인코딩할 영상 목록
video_files = ["video1.mp4", "video2.mp4", "video3.mp4"]

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

    print(f"\n[+] Encoding {file} → {name}/manifest.mpd")

    cmd = [ffmpeg_path, "-y", "-i", input_path]
    
    for i, (br, res) in enumerate(bitrates):
        w, h = res.split("x")
        cmd += [
            "-map", "0:v:0",
            f"-filter:v:{i}", f"scale={w}:{h}",
            f"-b:v:{i}", br
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
        "-seg_duration", "4",
        "-f", "dash",
        manifest_path
    ]

    try:
        subprocess.run(cmd, cwd=output_path, check=True)
    except subprocess.CalledProcessError as e:
        print(f" {file} 인코딩 실패: {e}")



subprocess.run(cmd, cwd=output_path)

print("\n 모든 영상 인코딩 완료!")
