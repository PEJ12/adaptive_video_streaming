// src/components/DashPlayer.jsx
// src/components/DashPlayer.jsx
import React, { useRef, useEffect } from 'react'
import './DashPlayer.css'

export default function DashPlayer({ manifestUrl }) {
  const videoRef = useRef(null)

  useEffect(() => {
    let player

    // 런타임에 CDN에서 ESM 모듈을 불러옵니다.
    import('https://cdn.dashjs.org/latest/modern/esm/dash.all.min.js')
      .then((dashjs) => {
        console.log('DashPlayer init with URL:', manifestUrl)
        if (!videoRef.current) return

        // CDN 모듈에서 MediaPlayer를 꺼내서 플레이어 생성
        player = dashjs.MediaPlayer().create()
        player.initialize(videoRef.current, manifestUrl, true)
      })
      .catch(err => {
        console.error('dash.js 모듈 로딩 실패:', err)
      })

    return () => {
      if (player) player.reset()
    }
  }, [manifestUrl])

  return (
    <div className="dash-player-container">
      <video
        ref={videoRef}
        className="dash-player-video"
        controls
      />
    </div>
  )
}

/*
import React, { useRef, useEffect } from 'react'
//import dashjs from 'dashjs'
import dashjs from 'dashjs/dist/modern/esm/dash.all.min.js'
import './DashPlayer.css'           // CSS는 여기서 import

export default function DashPlayer({ manifestUrl }) {
  const videoRef = useRef(null)

  useEffect(() => {
    // ← 여기에 꼭 로그를 남겨서 초기화가 호출되는지 봅니다.
    console.log('DashPlayer init with URL:', manifestUrl)

    if (!videoRef.current) return
    const player = dashjs.MediaPlayer().create()
    player.initialize(videoRef.current, manifestUrl, true)
    return () => player.reset()
  }, [manifestUrl])

  return (
    <div className="dash-player-container">
      <video
        ref={videoRef}
        className="dash-player-video"
        controls
      />
    </div>
  )
}
*/


/*
import React from 'react'
import { useParams } from 'react-router-dom'
import vids from '../assets/videos.js'
import DashPlayer from '../components/DashPlayer'
//import './PlayerPage.css'
import './DashPlayer.css'

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

      { DashPlayer에 manifest URL만 넘겨주면 dash.js가 adaptive streaming 해줍니다.*}
      <div className="player-page__player">
        <DashPlayer manifestUrl={video.manifest} />
      </div>
    </div>
  )
}
*/
