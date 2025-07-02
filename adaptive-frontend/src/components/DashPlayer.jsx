import React, { useRef, useEffect } from 'react'
import './DashPlayer.css'

export default function DashPlayer({ manifestUrl }) {
  const videoRef = useRef(null)

  useEffect(() => {
    const dashjs = window.dashjs
    if (!dashjs || typeof dashjs.MediaPlayer !== 'function') {
      console.error('❌ dash.js 로딩 실패')
      return
    }

    const player = dashjs.MediaPlayer().create()
    player.initialize(videoRef.current, manifestUrl, true)

    // ✅ 초기화 시 현재 트랙 정보 직접 가져오기
    player.on(dashjs.MediaPlayer.events.STREAM_INITIALIZED, () => {
      const currentTrack = player.getCurrentTrackFor('video')
      if (currentTrack) {
        console.log('✅ [STREAM_INITIALIZED]')
        console.log(`   • ID        : ${currentTrack.id}`)
        console.log(`   • Height    : ${currentTrack.height}p`)
        console.log(`   • Bandwidth : ${currentTrack.bandwidth} bps`)
      }
    })

    // ✅ 화질 변경 시 getCurrentTrackFor 사용
    player.on(dashjs.MediaPlayer.events.QUALITY_CHANGE_RENDERED, () => {
      const currentTrack = player.getCurrentTrackFor('video')
      if (currentTrack) {
        console.log('🟢 [QUALITY_CHANGE_RENDERED]')
        console.log(`   • ID        : ${currentTrack.id}`)
        console.log(`   • Height    : ${currentTrack.height}p`)
        console.log(`   • Bandwidth : ${currentTrack.bandwidth} bps`)
      }
    })

    return () => {
      player.reset()
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
