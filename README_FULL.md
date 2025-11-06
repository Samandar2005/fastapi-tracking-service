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
