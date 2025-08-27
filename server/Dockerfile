# server/Dockerfile
FROM python:3.11-slim

# [선택] ffmpeg/mp4box가 컨테이너에서도 필요하면 주석 해제
# RUN apt-get update && apt-get install -y ffmpeg gpac && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# (1) 의존성 먼저 복사/설치 → 캐시 활용
COPY server/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# (2) 앱 소스 복사
COPY server/ /app/

# (3) 컨테이너 내부 포트 노출
EXPOSE 8000

# (4) Uvicorn 실행
#  └─ NOTE: main:app 에서 app은 main.py 내부의 FastAPI 객체 이름이어야 함
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
#                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#                                  (수정 포인트 주석)
