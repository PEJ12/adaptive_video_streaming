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
      if (player) {
      player.reset()
      player = null              // Dash.js 인스턴스 해제
    }
    if (videoRef.current) {
      videoRef.current.removeAttribute('src')  
      videoRef.current.load()     // video 태그의 src 언로드
    }
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
