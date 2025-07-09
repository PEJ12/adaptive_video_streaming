import React, { useRef, useEffect } from 'react'
import './DashPlayer.css'

export default function DashPlayer({ manifestUrl }) {
  const videoRef = useRef(null)

  console.log("📼 manifestUrl", manifestUrl)

  useEffect(() => {
    const dashjs = window.dashjs
    if (!dashjs || typeof dashjs.MediaPlayer !== 'function') {
      console.error('❌ dash.js 로딩 실패')
      return
    }

    const player = dashjs.MediaPlayer().create()
    player.initialize(videoRef.current, manifestUrl, true)

    player.updateSettings({
      streaming: {
        abr: {
          autoSwitchBitrate: {
            video: true
          }
        }
      }
    })

    let lastTrackId = null

    const logCurrentTrackInfo = (label) => {
      const currentTrack = player.getCurrentTrackFor('video')
      const rep = currentTrack?.bitrateList?.[0]

      if (label === 'QUALITY_CHANGE_RENDERED' && currentTrack?.id === lastTrackId) return
      lastTrackId = currentTrack?.id

      if (currentTrack && rep) {
        console.log(`✅ [${label}]`)
        console.log(`   • ID        : ${currentTrack.id}`)
        console.log(`   • Height    : ${rep.height ?? 'Unknown'}p`)
        console.log(`   • Bandwidth : ${rep.bandwidth ?? 'Unknown'} bps`)
      } else {
        console.warn(`⚠️ [${label}] 트랙 정보를 찾을 수 없습니다.`)
      }
    }

    player.on(dashjs.MediaPlayer.events.QUALITY_CHANGE_REQUESTED, (e) => {
      if (e.mediaType !== 'video') return

      const fromHeight = e.oldRepresentation?.height ?? 'unknown'
      const toHeight = e.newRepresentation?.height ?? 'unknown'
      const fromBw = e.oldRepresentation?.bandwidth ?? 'unknown'
      const toBw = e.newRepresentation?.bandwidth ?? 'unknown'

      console.log(`🟡 [QUALITY_CHANGE_REQUESTED] From ${fromHeight}p (${fromBw}bps) → ${toHeight}p (${toBw}bps)`)
    })

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
