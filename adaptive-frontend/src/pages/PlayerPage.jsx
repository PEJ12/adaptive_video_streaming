import { useParams } from 'react-router-dom';
import { useEffect } from 'react';
import dashjs from 'dashjs';

export default function PlayerPage() {
  const { id } = useParams();
  useEffect(()=>{
    const player = dashjs.MediaPlayer().create();
    player.initialize(document.getElementById('videoPlayer'),
                      'http://localhost:8000/video3/manifest.mpd',
                      true);
  }, []);
  return (
    <div className="player-container">
      <header className="player-header">
        <img src="/assets/pnu-logo.jpg" alt="부산대 로고" className="logo small"/>
        <img src="/assets/sanjini.jpg" alt="산지니" className="mascot-small"/>
      </header>
      <div className="video-wrapper">
        <video id="videoPlayer" controls className="video-element"/>
      </div>
    </div>
  );
}
