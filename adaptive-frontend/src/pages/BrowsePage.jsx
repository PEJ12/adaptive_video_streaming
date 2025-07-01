
import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import DashPlayer from '../components/DashPlayer';
import vids from '../assets/videos.js'; // [{ id, title, manifest, thumbnail }, ...]

//import './BrowsePage.css';

export default function BrowsePage() {
  const { profileId } = useParams();
  const navigate = useNavigate();
  const [hero, setHero] = useState(vids[0]);
  

  return (
    <div className="browse-page">
      {/* Hero 배너 */}
      <section className="hero">
        {/* DashPlayer로 hero 비디오 렌더링 */}
        <DashPlayer manifestUrl={`http://localhost:8000${hero.manifest}`} />

        {/* 타이틀과 재생 버튼 오버레이 */}
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

      {/* 추천 콘텐츠 섹션 제목 */}
      <h2 className="section-title">
        프로필 {profileId}님을 위한 추천 콘텐츠
      </h2>

      {/* 썸네일 리스트 */}
      <div className="browse-row">
        {vids.map(v => (
          <div
            key={v.id}
            className={`browse-item ${v.id === hero.id ? 'active' : ''}`}
            onClick={() => setHero(v)}
          >
            {/* 이미지 태그로 변경하여 로딩 경량화 */}
            <img
              className="browse-thumb"
              src={v.thumbnail}
              alt={`${v.title} 썸네일`}
            />
            <p className="browse-label">{v.title}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

