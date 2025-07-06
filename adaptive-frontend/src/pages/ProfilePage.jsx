// src/pages/ProfilePage.jsx
import React from 'react';
import { useNavigate } from 'react-router-dom';

const profiles = [
  { id: 1, name: '프로필 A', avatar: '/assets/sanjini.jpg' },
  { id: 2, name: '프로필 B', avatar: '/assets/sjn2.png' },
  { id: 3, name: '프로필 C', avatar: '/assets/sanjini.jpg' },
  { id: 4, name: '프로필 D', avatar: '/assets/sjn2.png' },
];

export default function ProfilePage() {
  const nav = useNavigate();
  return (
    <div className="profile-page">
      {/* 상단 로고 */}

      <h2 className="profile-title">누가 시청하시나요?</h2>

      <div className="profile-grid">
        {profiles.map(p => (
          <button
            key={p.id}
            className="profile-card"
            onClick={() => nav(`/browse/${p.id}`)}
          >
            <div className="profile-avatar">
              <img src={p.avatar} alt={p.name} />
            </div>
            <span className="profile-name">{p.name}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

