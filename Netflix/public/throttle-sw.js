/* public/throttle-sw.js  — m4s/mpd 스로틀링 SW (교체본) */
const PROFILES = {
  fast: { bps: 9_000_000, latencyMs: 40 },   // 9 Mbps / 40ms
  slow: { bps: 2_500_000, latencyMs: 120 },  // 2.5 Mbps / 120ms
  off:  { bps: Infinity,  latencyMs: 0 },
};

let current = PROFILES.off;

// ★변경: 더 부드러운 스로틀(50ms 단위) + 전환 직후 300ms 만큼 버스트
const TICK_MS    = 50;   // 50ms마다 일정 바이트를 흘림
const WARMUP_MS  = 300;  // 전환 직후 0.3초는 빠르게 버스트 전송

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()));

self.addEventListener('message', (e) => {
  if (e.data?.type === 'SET_PROFILE' && PROFILES[e.data.profile]) {
    current = PROFILES[e.data.profile];
    log(`[SW] profile=${e.data.profile} (bps=${current.bps}, latency=${current.latencyMs}ms)`);
  }
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  const isDash =
    /\.m4s($|\?)/.test(url.pathname) ||
    /\.mpd($|\?)/.test(url.pathname) ||
    /init-stream\.mp4$/.test(url.pathname);

  if (!isDash) return;
  event.respondWith(throttledFetch(event.request));
});

async function throttledFetch(request) {
  const res = await fetch(request, { cache: 'no-store' });

  if ((current.bps === Infinity && current.latencyMs === 0) || !res.body) {
    return res; // 제한 해제 또는 스트림 불가
  }

  // ★변경: 초기 지연 (짧게 튜닝)
  if (current.latencyMs > 0) await delay(current.latencyMs);

  const reader = res.body.getReader();
  const headers = new Headers(res.headers);
  headers.delete('content-length'); // 스트리밍 재계산을 위해 길이 제거

  const bytesPerSec = current.bps / 8;
  const bytesPerTick = Math.max(8 * 1024, Math.floor(bytesPerSec * (TICK_MS / 1000)));
  let warmupBudget = Math.floor(bytesPerSec * (WARMUP_MS / 1000)); // ★추가: 버스트 예산

  let firstChunk = true;

  const stream = new ReadableStream({
    async start(controller) {
      while (true) {
        const { value, done } = await reader.read();
        if (done) { controller.close(); break; }
        if (!value) continue;

        let offset = 0;

        // ★추가: 전환 직후 warm-up — 버퍼가 마르지 않도록 300ms치 예산까지는 지연 없이 빨리 흘림
        if (warmupBudget > 0) {
          const w = Math.min(warmupBudget, value.byteLength);
          controller.enqueue(value.subarray(offset, offset + w));
          warmupBudget -= w;
          offset += w;
          // 남은 데이터는 일반 스로틀로 처리
        }

        // 일반 스로틀: tick 단위로 잘라서 전송
        while (offset < value.byteLength) {
          const end = Math.min(offset + bytesPerTick, value.byteLength);
          controller.enqueue(value.subarray(offset, end));
          offset = end;
          await delay(TICK_MS);
        }

        firstChunk = false;
      }
    },
    cancel(reason) { try { reader.cancel(reason); } catch (_) {} }
  });

  return new Response(stream, { status: res.status, statusText: res.statusText, headers });
}

function delay(ms) { return new Promise(r => setTimeout(r, ms)); }
function log(msg) {
  self.clients.matchAll().then(cs => cs.forEach(c => c.postMessage({ type: 'LOG', msg })));
}
