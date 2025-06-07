#FastAPI 서버
#pip install fastapi uvicorn 로 설치 먼저 하세요!!
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# 클라이언트에서 접근 가능하도록 CORS 허용 (다른 포트에서 접근 가능하게)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# 현재 디렉토리의 static 폴더를 웹 루트 경로(/)로 마운트
#예를 들어, static/index.html이 있으면 브라우저에서
#http://localhost:8000/index.html로 접근할 수 있게 됩니다.
#.mpd, m4s 같은 MPD 파일이랑 세그먼트들이 static 폴더에 저장돼있음
app.mount("/", StaticFiles(directory="static"), name="static")


# 절대 경로 기준으로 static 마운트
#위에 코드 안되면 이 경로 사용
'''
base_dir = os.path.dirname(os.path.abspath(__file__))
static_path = os.path.join(base_dir, "static")

app.mount("/", StaticFiles(directory=static_path), name="static")
'''