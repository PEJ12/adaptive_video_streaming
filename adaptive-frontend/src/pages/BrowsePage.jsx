// src/pages/BrowsePage.jsx
import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'

const videos = [
  { id: 1, title: '영상 1', thumb: '/assets/video1-thumb.jpg' },
  { id: 2, title: '영상 2', thumb: '/assets/video2-thumb.jpg' },
  { id: 3, title: '영상 3', thumb: '/assets/video3-thumb.jpg' },
]

export default function BrowsePage() {
  const { profileId } = useParams()
  const nav = useNavigate()

  // ① 현재 히어로 비디오 상태로 관리
  const [hero, setHero] = useState(videos[0])

  return (
    <div className="browse-page">
      {/* Hero 배너 */}
      <div className="hero">
        <video
          className="hero-video"
          src={`/assets/videos/video${hero.id}.mp4`}
          poster={hero.thumb}
          muted
          autoPlay
          loop
          playsInline
        />
        <div className="hero-title">
          {hero.title}
        </div>
        {/* Hero의 Play 버튼은 hero.id로 이동 */}
        <button
          className="play-btn"
          onClick={() => nav(`/player/${hero.id}`)}
        >
          ▶ 지금 재생
        </button>
      </div>

      <h2 className="section-title">
        프로필 {profileId}님을 위한 추천 콘텐츠
      </h2>

      <div className="browse-row">
        {videos.map(v => (
          <div
            key={v.id}
            className="browse-item"
            // ② 썸네일 클릭 시 히어로 상태를 해당 영상으로 교체
            onClick={() => setHero(v)}
          >
            <video
              className="browse-video-preview"
              src={`/assets/videos/video${v.id}.mp4`}
              poster={v.thumb}
              muted
              autoPlay
              loop
              playsInline
            />
            <span className="browse-label">{v.title}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
