#FastAPI 서버
#pip install fastapi uvicorn 로 설치 먼저 하세요!!
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
from fastapi.responses import FileResponse, Response
app = FastAPI()

# 클라이언트에서 접근 가능하도록 CORS 허용 (다른 포트에서 접근 가능하게)
app.add_middleware(
    CORSMiddleware,
    #allow_origins=["http://localhost:5173"], # 배포시에 수정
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)



app.mount(
    "/stream",
    StaticFiles(directory="static"),
    name="stream",
)

# (2) manifest.mpd만 별도 라우팅
@app.get("/stream/{video}/manifest.mpd")
async def get_mpd(video: str):
    print(f"manifest.mpd 요청됨: video={video}")  
    mpd_path = os.path.join("static", video, "manifest.mpd")
    if not os.path.exists(mpd_path):
        return Response(status_code=404)
    return FileResponse(mpd_path, media_type="application/dash+xml")


@app.get("/api/bitrate_csv")
def get_bitrate_csv():
    file_path = "./static/husky/bitrate_logs/husky_bitrate_per_second.csv"  # 절대경로 필요 시 수정
    if os.path.exists(file_path):
        return FileResponse(path=file_path, media_type='text/csv', filename="bitrate.csv")
    else:
        return {"error": "CSV not found"}

# 절대 경로 기준으로 static 마운트
#위에 코드 안되면 이 경로 사용
'''
base_dir = os.path.dirname(os.path.abspath(__file__))
static_path = os.path.join(base_dir, "static")

app.mount("/", StaticFiles(directory=static_path), name="static")
'''