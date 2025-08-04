// DashPlayer.jsx


import React, { useRef, useEffect, useState } from 'react';
import Chart from 'chart.js/auto';
import Papa from 'papaparse';

export default function DashPlayer({ manifestUrl }) {
  const videoRef = useRef(null);
  const chartRef = useRef(null);
  const playerRef = useRef(null);
  const chartInstanceRef = useRef(null);

  const [bitrateLog, setBitrateLog] = useState([]);
  const [currentSegment, setCurrentSegment] = useState(null);
  const [segmentStartTime, setSegmentStartTime] = useState(Date.now());

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
            borderColor: 'orange',
            backgroundColor: 'orange',
            fill: false,
            tension: 0.1,
            pointRadius: 3,
            pointHoverRadius: 6,
          },
        ],
      },
      options: {
        responsive: true,
        animation: false,
        scales: {
          x: {
            title: { display: true, text: 'Time (s)' },
            beginAtZero: true,  // ✅ 필수
            min: 0,             // ✅ X축 0부터 강제
          },
          y: {
            title: { display: true, text: 'Bitrate (kbps)' },
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
        const globalSec = (segIdx-1) * 10 + localSec;
        const bitrate = parseFloat(row.bitrate_kbps);

        if (!isNaN(bitrate)) {
          const chart = chartInstanceRef.current;
          const globalSecStr = globalSec.toString(); // ✅ 문자열로 변환
          const idx = chart.data.labels.indexOf(globalSecStr); // ✅ 문자열 비교

          if (idx !== -1) {
            // 이미 label에 해당 초 있음 → 값 덮어쓰기
            chart.data.datasets[0].data[idx] = bitrate;
          } else {
            // 없으면 새로 추가
            chart.data.labels.push(globalSecStr);  // ✅ 문자열로 추가
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

  return (
    <div>
      <video ref={videoRef} controls width="800" />
      <canvas ref={chartRef} />
    </div>
  );
}



