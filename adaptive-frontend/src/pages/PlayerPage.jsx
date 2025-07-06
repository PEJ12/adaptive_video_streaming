// src/pages/PlayerPage.jsx
import React from 'react'
import { useParams } from 'react-router-dom'
import vids from '../assets/videos.js'
import DashPlayer from '../components/DashPlayer'


export default function PlayerPage() {
  const { profileId, videoId } = useParams()

  // videoId는 문자열이니까 숫자로 바꿔서 조회
  const video = vids.find(v => v.id === parseInt(videoId, 10))

  if (!video) {
    return <div className="player-page--error">⚠️ 해당 영상을 찾을 수 없습니다.</div>
  }

  return (
    <div className="player-page">
      <h2 className="player-page__title">
        {video.title} — Profile {profileId}님을 위한 스트리밍
      </h2>

      {/* DashPlayer에 manifest URL만 넘겨주면 dash.js가 adaptive streaming 해줍니다. */}
      <div className="player-page__player">
        <DashPlayer manifestUrl={video.manifest} />
      </div>
    </div>
  )
}


/*
import { useParams } from 'react-router-dom';
import { useEffect } from 'react';
import dashjs from 'dashjs';

export default function PlayerPage() {
  const { id } = useParams();
  useEffect(()=>{
    const player = dashjs.MediaPlayer().create();
    player.initialize(document.getElementById('videoPlayer'),
                      'http://localhost:8000/video3/manifest.mpd',
                      true);
  }, []);
  return (
    <div className="player-container">
      <header className="player-header">
        <img src="/assets/pnu-logo.jpg" alt="부산대 로고" className="logo small"/>
        <img src="/assets/sanjini.jpg" alt="산지니" className="mascot-small"/>
      </header>
      <div className="video-wrapper">
        <video id="videoPlayer" controls className="video-element"/>
      </div>
    </div>
  );
}
*/