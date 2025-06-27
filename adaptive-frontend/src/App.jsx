// src/App.jsx
import { Routes, Route } from 'react-router-dom';
import LoginPage   from './pages/LoginPage';
import ProfilePage from './pages/ProfilePage';
import BrowsePage  from './pages/BrowsePage';
import PlayerPage  from './pages/PlayerPage';

export default function App() {
  return (
    <Routes>
      <Route path="/"           element={<LoginPage />} />
      <Route path="/profiles"   element={<ProfilePage />} />
      <Route path="/browse/:profileId" element={<BrowsePage />} />
      <Route path="/player/:id" element={<PlayerPage />} />
    </Routes>
  );
}
