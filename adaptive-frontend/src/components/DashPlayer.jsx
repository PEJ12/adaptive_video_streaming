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

    const logCurrentTrackInfo = (label) => {
      const currentTrack = player.getCurrentTrackFor('video')
      if (currentTrack) {
        // bitrateList가 존재하면 첫 번째 항목 가져오기
        const rep = currentTrack.bitrateList?.[0]  // 현재 해상도 하나만 존재하므로 0번
        console.log(`✅ [${label}]`)
        console.log(`   • ID        : ${currentTrack.id}`)
        console.log(`   • Height    : ${rep?.height ?? 'Unknown'}p`)
        console.log(`   • Bandwidth : ${rep?.bandwidth ?? 'Unknown'} bps`)
      } else {
        console.warn(`⚠️ [${label}] currentTrack를 찾을 수 없습니다.`)
      }
    }

    player.on(dashjs.MediaPlayer.events.STREAM_INITIALIZED, () => {
      logCurrentTrackInfo('STREAM_INITIALIZED')
    })

    player.on(dashjs.MediaPlayer.events.QUALITY_CHANGE_RENDERED, () => {
      logCurrentTrackInfo('QUALITY_CHANGE_RENDERED')
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
