# fastapi-tracking-service

FastAPI Tracking Service — oddiy, konteynerizatsiyalangan loyiha bo'lib, real vaqtda GPS ma'lumotlarini qabul qilish, saqlash va veb interfeys orqali xaritada ko'rsatishni ta'minlaydi.

Ushbu repo quyidagi xizmatlardan iborat:

- backend/: FastAPI ilovasi (Uvicorn) — REST endpoint `/publish` orqali GPS ma'lumotlarini qabul qiladi va WebSocket orqali mijozlarga yuboradi.
- frontend/: React + Vite ilovasi — Leaflet xaritasi yordamida qurilmalar joylashuvini vizualizatsiya qiladi.
- redis: qatorlarni va pub/sub uchun konteyner (docker-compose ichida).

## Tez boshlash (mahalliy, Docker yordamida)

Talablar:

- Docker Desktop yoki Docker Engine
- (Agar frontendi mahalliy ravishda ishga tushirsangiz) Node.js va npm/yarn

1) Hammasini ishga tushirish (konteynerlar yordamida):

```powershell
docker compose up --build
```

Bu quyidagi portlarni ochadi:

- Backend: http://localhost:8000
- Frontend (Vite dev server): http://localhost:5173
- Redis: 6379

2) Frontendni mahalliy ravishda ishga tushirish (agar Docker ishlatmasangiz yoki tez o'zgartirishlar qilmoqchi bo'lsangiz):

```powershell
cd frontend
npm install
npm run dev -- --host
```

## Loyihaning tuzilishi

- backend/
  - `main.py` — FastAPI ilovasi, WebSocket endpoint va `/publish` REST endpoint
  - `requirements.txt` — Python dependency
- frontend/
  - `src/` — React kod: `index.jsx`, `App.jsx`, `MapView.jsx`, `style.css`
  - `package.json`, `vite.config.js`
- `docker-compose.yml` — xizmatlar (backend, frontend, redis)

## API va ma'lumotlar shakli

- REST publish (test ma'lumot yuborish):

  POST http://localhost:8000/publish

  JSON misol:

```json
{
  "device_id": "dev-1",
  "lat": 41.3128,
  "lng": 69.2787,
  "ts": 1699190400000
}
```

- WebSocket: backend WebSocket serveriga ulanish `ws://<host>:8000/ws/{client_id}`. Server real vaqtda kelayotgan GPS ma'lumotlarini JSON shaklida yuboradi.

Frontend kutadi: har xabarda `device_id`, `lat`, `lng` (raqam) va ixtiyoriy `ts` bo'lishi kerak.

## Sending real device locations

You can send real GPS coordinates from any device (IoT unit, mobile phone, browser) to the backend REST endpoint `/publish` or publish directly to WebSocket if needed. Below are examples for several platforms.

Note: the backend may be configured with an optional API key via the `API_KEY` environment variable. If `API_KEY` is set, include the header `X-API-Key: <your-key>` in your requests.

1) curl (HTTP POST)

```bash
curl -X POST http://<SERVER_HOST>:8000/publish \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \ # optional header when API_KEY is used
  -d '{"device_id":"device-123","lat":41.3128,"lng":69.2787,"ts":1700000000000}'
```

2) Python (requests)

```python
import requests

payload = {
    "device_id": "device-123",
    "lat": 41.3128,
    "lng": 69.2787,
    "ts": 1700000000000,
}
headers = {"Content-Type": "application/json"}
# If you enabled API_KEY, add:
# headers["X-API-Key"] = "YOUR_API_KEY"

resp = requests.post("http://<SERVER_HOST>:8000/publish", json=payload, headers=headers)
print(resp.json())
```

3) Browser / mobile (JavaScript) — using Geolocation API

```javascript
function sendPosition(position) {
  const payload = {
    device_id: 'phone-1',
    lat: position.coords.latitude,
    lng: position.coords.longitude,
    ts: Date.now()
  }

  fetch('http://<SERVER_HOST>:8000/publish', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      // 'X-API-Key': 'YOUR_API_KEY' // if required
    },
    body: JSON.stringify(payload)
  })
}

if (navigator.geolocation) {
  navigator.geolocation.watchPosition(sendPosition, (err) => console.error(err), { enableHighAccuracy: true })
} else {
  console.error('Geolocation not supported')
}
```

4) Direct WebSocket publish (optional)

If you prefer to send via WebSocket, connect to `ws://<SERVER_HOST>:8000/ws/<client_id>` and send JSON messages. Note: server echoes/broadcasts messages received over websocket to other clients.

```javascript
const ws = new WebSocket('ws://<SERVER_HOST>:8000/ws/my-device')
ws.onopen = () => {
  ws.send(JSON.stringify({ device_id: 'device-123', lat: 41.3128, lng: 69.2787, ts: Date.now() }))
}
```

Important network notes

- Replace `<SERVER_HOST>` with the address reachable by your device (localhost for local testing; public IP or domain for real devices). If you run backend inside Docker on the same machine as the device, use the host IP that devices can reach.
- For devices on mobile networks, expose the backend securely (use HTTPS, set up firewall rules, or a tunnel like ngrok for testing).
 - For devices on mobile networks, expose the backend securely (use HTTPS, set up firewall rules, or a tunnel like ngrok for testing).
 - Note: Browser Geolocation API requires a secure context (HTTPS) on non-localhost origins. If you open the frontend from a phone using an IP (http://192.168.x.y:5173) the browser may block geolocation; use HTTPS or test from localhost.
- Use `API_KEY` environment variable for a simple auth layer. For production, prefer stronger auth (JWT, mTLS, OAuth).


## Frontend funktsional imkoniyatlari

- Xarita (Leaflet) ustida markerlar: har bir qurilma uchun oxirgi joylashuv ko'rsatiladi.
- Chap panelda qurilmalar ro'yxati, oxirgi xabar va `Send mock location` tugmasi mavjud — bu tugma backendga sinov ma'lumotlarini yuboradi.
- Markerga bosilganda yoki chap ro'yxatdan qurilmani tanlaganda xarita markerni markazlashtiradi va pop-up ochadi.

## Muammolar va tezkor yechimlar

- `sh: vite: not found` — bu muammo hostdagi bind-mount tufayli konteyner ichidagi `node_modules` yashirilganda yuz beradi. Repo `docker-compose.yml` faylida frontend uchun `command` yoki `.dockerignore` bilan hal qilindi. Agar siz dev uchun `node_modules` ga bog'liq bo'lsangiz, `npm install` ni konteyner ichida ishga tushiring yoki `.dockerignore` va nomlangan volume qo'shing.
- Docker Desktop ishlamay qolsa: Windows-da Docker Desktop-ni ishga tushiring (Start menu), so'ng `docker compose up --build` ni qayta bajaring.

## Rivojlantirish bo'yicha tavsiyalar (keyingi qadamlar)

- Marker clustering (ko'p markerlar bo'lsa) uchun `leaflet.markercluster` qo'shish.
- GPS tarixini saqlash va qurilma trayektoriya (trail) ni chizish.
- Autentifikatsiya va ruxsatlarni qo'shish (agar qurilmalar xavfsiz ulanishni talab qilsa).

## Hissa qo'shish

1. Fork qiling
2. Yangi branch yarating: `git checkout -b feature/your-feature`
3. O'zgartiring, test qiling
4. Pull request yuboring

## Litsenziya

Loyiha README-ga oid umumiy ma'lumot. Loyihani ochiq manba sifatida ishlatish va o'zgartirish mumkin.

---

Commit message uchun taklif (git commit -m):

```
feat(frontend): add MapView, sidebar UI and styles; integrate websocket location handling

- new MapView.jsx (Leaflet) to render markers and popups
- revamped App.jsx with sidebar, device list and mock sender
- improved styles in src/style.css
```

Yoki qisqaroq komment:

```
Add interactive map UI (MapView), sidebar and styling; wire websocket locations
```

---

Agar READMEni boshqa tilda (inglizcha) yoki qisqargan versiyasini xohlasangiz, ayting — men uni moslab yozib beraman va siz uchun `git add/commit/push` uchun kerakli buyruqlarni ham yozib beraman.
