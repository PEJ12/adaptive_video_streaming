window.addEventListener("DOMContentLoaded", function () {
  //const url = "http://127.0.0.1:8000/video1/manifest.mpd";
  const url = "http://localhost:8000/video1/manifest.mpd";  // 또는 video2, video3
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
