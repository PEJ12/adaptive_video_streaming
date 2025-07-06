import { useNavigate } from 'react-router-dom';
import { useState } from 'react';

export default function LoginPage() {
  const [id, setId]         = useState('');
  const [pwd, setPwd]       = useState('');
  const [error, setError]   = useState('');
  const navigate            = useNavigate();

  const handleLogin = () => {
    if (id === '111' && pwd === '222') {
      // 로그인 성공 시 /profiles 로 이동
      navigate('/profiles');
    } else {
      setError('아이디 또는 비밀번호가 일치하지 않습니다.');
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        {/* 카드 내부에 로고 */}
        <img
          src="/assets/pnu.jpg"
          alt="부산대 로고"
          className="card-logo"
        />

        <h1>Adaptive Streaming</h1>

        <input
          type="text"
          placeholder="아이디"
          value={id}
          onChange={e => setId(e.target.value)}
          className="login-input"
        />
        <input
          type="password"
          placeholder="비밀번호"
          value={pwd}
          onChange={e => setPwd(e.target.value)}
          className="login-input"
        />

        <button onClick={handleLogin} className="login-btn">
          로그인
        </button>

        {error && <p className="error-text">{error}</p>}
      </div>
    </div>
  );
}
