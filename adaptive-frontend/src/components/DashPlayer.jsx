// src/pages/PlayerPage.jsx
import React from 'react'
import { useParams } from 'react-router-dom'
import vids from '../assets/videos.js'
import DashPlayer from '../components/DashPlayer'
//import './PlayerPage.css'

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
import React, { useRef, useEffect } from 'react'
import dashjs from 'dashjs'
import './DashPlayer.css'

const DashPlayer = ({ manifestUrl }) => {
  const videoRef = useRef(null)

  useEffect(() => {
    if (!videoRef.current) return
    const player = dashjs.MediaPlayer().create()
    player.initialize(videoRef.current, manifestUrl, true)
    return () => player.reset()
  }, [manifestUrl])

  return (
    <div className={styles.container}>
      <video
        ref={videoRef}
        className={styles.video}
        controls
      />
    </div>
  )
}

export default DashPlayer
*/