// src/pages/BrowsePage.jsx
import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import DashPlayer from '../components/DashPlayer'
import vids from '../assets/videos.js'  // [{ id, title, manifest, thumbnail }, ...]


export default function BrowsePage() {
  const { profileId } = useParams()
  const navigate = useNavigate()

  const [hero, setHero] = useState(vids[0])
  // 아래 candidates를 vids.slice(1,4) 대신 원본 vids로 설정
  const candidates = vids  
  // or: const candidates = vids.slice(0, 3)

  return (
    <div className="browse-page">
      <section className="hero">
        <DashPlayer
          manifestUrl={`http://localhost:8000${hero.manifest}`}
          autoPlay
          poster={hero.thumbnail}
        />
        <div className="hero-overlay">
          <h1 className="hero-title">{hero.title}</h1>
          <button
            className="play-btn"
            onClick={() => navigate(`/browse/${profileId}/player/${hero.id}`)}
          >
            ▶ 지금 재생
          </button>
        </div>
      </section>

      <h2 className="section-title">
        프로필 {profileId}님을 위한 추천 콘텐츠
      </h2>

      <div className="browse-row">
        {candidates.map(v => (
          <div
            key={v.id}
            className="browse-item"
            onClick={() => setHero(v)}
          >
            <DashPlayer
              manifestUrl={`http://localhost:8000${v.manifest}`}
              autoPlay={false}
              poster={v.thumbnail}
            />
            <p className="browse-label">{v.title}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
