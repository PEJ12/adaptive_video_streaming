window.addEventListener("DOMContentLoaded", function () {
  const url = "http://localhost:8000/video3/manifest.mpd";  // 또는 video1, video2
  const video = document.getElementById("videoPlayer");

  const player = dashjs.MediaPlayer().create();
  player.initialize(video, url, true);

  // ——— 로그 찍기 시작 ———
  player.on(dashjs.MediaPlayer.events.STREAM_INITIALIZED, () => {
    console.log("[DASH] 스트림 초기화 완료");
  });

  player.on(dashjs.MediaPlayer.events.PLAYBACK_STARTED, () => {
    console.log("[DASH] 재생 시작");
  });

  player.on(dashjs.MediaPlayer.events.PLAYBACK_PAUSED, () => {
    console.log("[DASH] 재생 일시정지");
  });

  player.on(dashjs.MediaPlayer.events.BUFFER_LEVEL_UPDATED, (e) => {
    console.log(`[DASH] 버퍼 레벨: ${e.bufferLevel.toFixed(2)}초`);
  });

  player.on(dashjs.MediaPlayer.events.BUFFER_EMPTY, () => {
    console.warn("[DASH] 버퍼 비어있음");
  });

  player.on(dashjs.MediaPlayer.events.QUALITY_CHANGE_REQUESTED, (e) => {
    console.log(`[DASH] 품질 변경 요청: ${e.oldQuality} → ${e.newQuality}`);
  });

  player.on(dashjs.MediaPlayer.events.QUALITY_CHANGE_RENDERED, (e) => {
    console.log(`[DASH] 품질 변경 적용: ${e.oldQuality} → ${e.newQuality}`);
  });

  // HTTP 요청 완료 이벤트를 활용하면 각 세그먼트 로딩도 찍을 수 있습니다.
  player.on(dashjs.MediaPlayer.events.HTTP_REQUEST_COMPLETED, (e) => {
    if (e.type === "MediaSegment") {
      console.log(`[Segment] ${e.request.url.split("/").pop()} 수신 (duration: ${e.duration.toFixed(2)}s)`);
    }
  });

  player.on(dashjs.MediaPlayer.events.ERROR, (e) => {
    console.error("[DASH] 에러 발생:", e);
  });

  // ——— 추가 로그 ———

  // 비트레이트와 화질 변경 정보 출력
  setInterval(() => {
    const qualityIdx = player.getQualityFor("video");
    const bitrateInfo = player.getBitrateInfoListFor("video")[qualityIdx];
    console.log(`[DASH] 비트레이트: ${Math.round(bitrateInfo.bitrate / 1000)} kbps, 화질: ${bitrateInfo.height}p`);
  }, 5000);  // 5초마다 비트레이트 출력

  // 비디오 프레임 정보 출력
  video.addEventListener("timeupdate", () => {
    if (video.getVideoPlaybackQuality) {
      const quality = video.getVideoPlaybackQuality();
      console.log(`[FRAME] currentTime=${video.currentTime.toFixed(2)}s, totalFrames=${quality.totalVideoFrames}, droppedFrames=${quality.droppedVideoFrames}`);
    }
  });

  // ——— 로그 끝 ———
});




/*
window.addEventListener("DOMContentLoaded", function () {
  //const url = "http://127.0.0.1:8000/video1/manifest.mpd";
  const url = "http://localhost:8000/video3/manifest.mpd";  // 또는 video2, video3
 //서버에서 넘겨주는 MPD 주소
  const video = document.getElementById("videoPlayer");

  const player = dashjs.MediaPlayer().create();
  player.initialize(video, url, true);

  // 이벤트 로그 보기
  player.on(dashjs.MediaPlayer.events.STREAM_INITIALIZED, () => {
    console.log("DASH 스트림 초기화 완료");
  });

  player.on(dashjs.MediaPlayer.events.ERROR, (e) => {
    console.error("에러 발생:", e);
  });
});
*/