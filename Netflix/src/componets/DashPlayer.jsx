// DashPlayer.jsx

import React, { useRef, useEffect, useState } from 'react';
import Chart from 'chart.js/auto';
import Papa from 'papaparse';
import './DashPlayer.css';

export default function DashPlayer({ manifestUrl }) {
  const videoRef = useRef(null);
  const chartRef = useRef(null);
  const playerRef = useRef(null);
  const chartInstanceRef = useRef(null);

  const [bitrateLog, setBitrateLog] = useState([]);
  const [currentSegment, setCurrentSegment] = useState(null);
  const [segmentStartTime, setSegmentStartTime] = useState(Date.now());
  const [uiProfile, setUiProfile] = useState('off');
  const currentProfileRef = useRef('off');


  useEffect(() => {
  if (!bitrateLog.length) return;
  const seg1080 = bitrateLog.filter(row => row.segment_name === 'ai_seg_1_1080p.mp4');
  console.log("[🔍 ai_seg_1_1080p.mp4 비트레이트]", seg1080);
}, [bitrateLog]);

  // 📦 CSV 불러오기
  useEffect(() => {
    fetch('/husky/bitrate_logs/husky_bitrate_per_second.csv')
      .then((res) => res.text())
      .then((csvText) => {
        Papa.parse(csvText, {
          header: true,
          skipEmptyLines: true,
          dynamicTyping: true,
          transformHeader: (header) => header.trim(),
          complete: (result) => {
            console.log('✅ CSV 샘플 확인:', result.data.slice(0, 3));
            setBitrateLog(result.data);
          },
        });
      });
  }, []);

  // 📺 dash.js 초기화 및 차트 생성
  useEffect(() => {
    const dashjs = window.dashjs;
    if (!dashjs || typeof dashjs.MediaPlayer !== 'function') {
      console.error('❌ dash.js 로딩 실패');
      return;
    }

    const player = dashjs.MediaPlayer().create();
    playerRef.current = player;
    player.initialize(videoRef.current, manifestUrl, true);

    chartInstanceRef.current = new Chart(chartRef.current, {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          {
            label: 'Bitrate (kbps)',
            data: [],
            borderColor: '#ffb74d',             // 더 밝은 오렌지
            backgroundColor: 'rgba(255,183,77,0.4)', // 약간 투명한 배경
            fill: true,                         // 아래 면 채우기
            tension: 0.3,                       // 더 부드러운 곡선
            borderWidth: 2,
            pointRadius: 1.5,                   // 작고 깔끔한 점
            pointHoverRadius: 4,
            pointBackgroundColor: '#fff',
          },
        ],
      },
      options: {
        responsive: true,
        animation: false,
        devicePixelRatio: 2,
        plugins: {
          legend: {
            labels: {
              color: '#eee',
              font: { weight: 'bold' }
            }
          },
          tooltip: {
            backgroundColor: '#222',
            titleColor: '#ffb74d',
            bodyColor: '#fff'
          }
        },
        scales: {
          x: {
            title: { display: true, text: 'Time (s)', color: '#ccc' },
            ticks: { color: '#aaa' },
            grid: { color: 'rgba(255,255,255,0.05)' },
            beginAtZero: true,
            min: 0,
          },
          y: {
            title: { display: true, text: 'Bitrate (kbps)', color: '#ccc' },
            ticks: { color: '#aaa' },
            grid: { color: 'rgba(255,255,255,0.05)' },
            beginAtZero: false,
          },
        },
      },
    });


    return () => {
      player.reset();
      chartInstanceRef.current?.destroy();
    };
  }, [manifestUrl]);

  // 📊 bitrateLog가 준비된 후 이벤트 핸들러 등록
  useEffect(() => {
    if (!bitrateLog.length || !playerRef.current) return;

    const player = playerRef.current;

    const handleFragment = (e) => {
      const url = e.request?.url;
      const video = e.request?.mediaType === 'video';
      if (!url || !video) return;

      const match = url.match(/merged_ai_fixed_(\d+p)_dash(\d+)\.m4s/);
      if (!match) return;

      const resolution = match[1];
      const segIdx = parseInt(match[2], 10);
      const segmentName = `ai_seg_${segIdx}_${resolution}.mp4`;

      setCurrentSegment(segmentName);
      setSegmentStartTime(Date.now());

      console.log("🔍 현재 세그먼트 이름:", segmentName);
      console.log("📄 bitrateLog 샘플:", bitrateLog.slice(0, 3));

      const matched = bitrateLog.filter(
        (row) => row.segment_name?.trim() === segmentName
      );

      if (matched.length === 0) {
        console.warn(`[📉] ${segmentName} 에 대한 비트레이트 없음`);
        return;
      }

      const chart = chartInstanceRef.current;

      matched.forEach((row) => {
        const localSec = parseInt(row.time_second);
        const globalSec = (segIdx - 1) * 10 + localSec;
        const bitrate = parseFloat(row.bitrate_kbps);

        if (!isNaN(bitrate)) {
          const globalSecStr = globalSec.toString();
          const idx = chart.data.labels.indexOf(globalSecStr);

          if (idx !== -1) {
            chart.data.datasets[0].data[idx] = bitrate;
          } else {
            chart.data.labels.push(globalSecStr);
            chart.data.datasets[0].data.push(bitrate);
          }
        }
      });
      chart.update();
    };

    player.on(window.dashjs.MediaPlayer.events.FRAGMENT_LOADING_COMPLETED, handleFragment);

    return () => {
      player.off(window.dashjs.MediaPlayer.events.FRAGMENT_LOADING_COMPLETED, handleFragment);
    };
  }, [bitrateLog]);

  // 🔁 1초마다 현재 세그먼트 비트레이트 출력
  useEffect(() => {
    const interval = setInterval(() => {
      if (!currentSegment || bitrateLog.length === 0) return;

      const elapsedSec = Math.floor((Date.now() - segmentStartTime) / 1000);
      const row = bitrateLog.find(
        (r) =>
          r.segment_name?.trim() === currentSegment &&
          parseInt(r.time_second) === elapsedSec
      );

      if (row) {
        console.log(`📦 [${currentSegment}] ${elapsedSec}s → ${row.bitrate_kbps} kbps`);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [currentSegment, segmentStartTime, bitrateLog]);

  // ✅ SW 등록 + 프로파일 전송
  useEffect(() => {
    const onMsg = (e) => {
      if (e.data?.type === 'LOG') console.log(e.data.msg);
    };
    navigator.serviceWorker?.addEventListener('message', onMsg);

    (async () => {
      if ('serviceWorker' in navigator) {
        try {
          const reg = await navigator.serviceWorker.register('/throttle-sw.js', { scope: '/' });
          await navigator.serviceWorker.ready;

          if (!navigator.serviceWorker.controller) {
            navigator.serviceWorker.addEventListener('controllerchange', () => {
              sendProfile(currentProfileRef.current);
            });
          } else {
            sendProfile('off');
          }
        } catch (err) {
          console.warn('SW 등록 실패:', err);
        }
      }
    })();

    return () => navigator.serviceWorker?.removeEventListener('message', onMsg);
  }, []);

  const sendProfile = (p) => {
    currentProfileRef.current = p;
    setUiProfile(p);

    if (navigator.serviceWorker?.controller) {
      navigator.serviceWorker.controller.postMessage({
        type: 'SET_PROFILE',
        profile: p,
      });
      console.log(`[UI] Network profile → ${p}`);
    } else {
      console.warn('[SW] 아직 제어권 없음');
    }
  };

  return (
    <div className="dash-container">
      <div className="dash-video-wrapper">
        <video ref={videoRef} className="dash-video" controls />
      </div>

      <div className="throttle-controls">
        <span className="throttle-label">Network:</span>
        <button className={`throttle-btn ${uiProfile === 'fast' ? 'active' : ''}`} onClick={() => sendProfile('fast')}>Fast</button>
        <button className={`throttle-btn ${uiProfile === 'slow' ? 'active' : ''}`} onClick={() => sendProfile('slow')}>Slow</button>
        <button className={`throttle-btn ${uiProfile === 'off' ? 'active' : ''}`} onClick={() => sendProfile('off')}>Off</button>
      </div>

      <div className="dash-chart">
        <canvas ref={chartRef} />
      </div>
    </div>
  );
}
