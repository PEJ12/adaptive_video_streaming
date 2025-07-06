import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import './index.css';            // ← 전역 CSS 딱 1번만

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>          
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
