// src/pages/BrowsePage.jsx
import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';

const videos = [
  { id: 1, title: '영상 1', thumb: '/assets/video1-thumb.jpg' },
  { id: 2, title: '영상 2', thumb: '/assets/video2-thumb.jpg' },
  { id: 3, title: '영상 3', thumb: '/assets/video3-thumb.jpg' },
];

export default function BrowsePage() {
  const { profileId } = useParams();
  const nav = useNavigate();
  const hero = videos[0];

  return (
    <div className="browse-page">
      {/* 히어로 배너 */}
      <div
        className="hero"
        style={{ backgroundImage: `url(${hero.thumb})` }}
        onClick={() => nav(`/player/${hero.id}`)}
      >
        <button className="play-btn">▶ 지금 재생</button>
      </div>

      {/* 추천 콘텐츠 타이틀 */}
      <h2 className="section-title">
        프로필 {profileId}님을 위한 추천 콘텐츠
      </h2>

      {/* 한 줄 가로 스크롤 썸네일 */}
      <div className="browse-row">
        {videos.map(v => (
          <div
            key={v.id}
            className="browse-item"
            onClick={() => nav(`/player/${v.id}`)}
          >
            <img src={v.thumb} alt={v.title} className="browse-thumb" />
            <span className="browse-label">{v.title}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
