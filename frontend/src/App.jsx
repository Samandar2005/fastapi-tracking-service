import React, { useEffect, useState, useRef } from 'react'
import MapView from './MapView'

// Determine backend URL dynamically so devices/browsers don't try to use `localhost`.
// You can override by setting VITE_BACKEND_URL in the frontend environment (example: VITE_BACKEND_URL="http://192.168.1.10:8000")
const ENV_BACKEND = import.meta.env.VITE_BACKEND_URL
const BACKEND = ENV_BACKEND || `${window.location.protocol}//${window.location.hostname}:8000`
const WS_URL = (clientId) => {
  const wsScheme = BACKEND.startsWith('https') ? 'wss' : 'ws'
  const host = BACKEND.replace(/^https?:\/\//, '')
  return `${wsScheme}://${host}/ws/${clientId}`
}

export default function App() {
  const [messages, setMessages] = useState([])
  const [locations, setLocations] = useState({}) // device_id -> latest location
  const [selectedDevice, setSelectedDevice] = useState(null)
  const wsRef = useRef(null)
  const clientIdRef = useRef(`viewer-${Math.floor(Math.random() * 10000)}`)

  useEffect(() => {
    const ws = new WebSocket(WS_URL(clientIdRef.current))
    wsRef.current = ws

    ws.onopen = () => console.log('✅ WebSocket connected')
    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data)
        setMessages((prev) => [data, ...prev].slice(0, 200))

        // Expecting data to contain device_id, lat, lng, ts
        if (data?.device_id && typeof data.lat === 'number' && typeof data.lng === 'number') {
          setLocations((prev) => ({
            ...prev,
            [data.device_id]: {
              device_id: data.device_id,
              lat: data.lat,
              lng: data.lng,
              ts: data.ts || Date.now(),
            },
          }))
        }
      } catch (e) {
        setMessages((prev) => [{ raw: ev.data }, ...prev].slice(0, 200))
      }
    }
    ws.onclose = () => console.log('❌ WebSocket disconnected')

    return () => ws.close()
  }, [])

  // 🔁 Test uchun mock GPS ma’lumot yuborish (REST orqali)
  const sendMock = async () => {
    const payload = {
      device_id: `dev-${Math.floor(Math.random() * 10)}`,
      lat: 41 + Math.random() * 0.1,
      lng: 69 + Math.random() * 0.1,
      ts: Date.now(),
    }

    await fetch(`${BACKEND}/publish`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
  }

  const devices = Object.values(locations)

  return (
    <div className="app-container">
      <aside className="sidebar">
        <header className="sidebar-header">
          <h2>FastAPI Tracker</h2>
          <div className="connected">Connected as <b>{clientIdRef.current}</b></div>
        </header>

        <div className="controls">
          <button onClick={sendMock} className="btn">Send mock location</button>
        </div>

        <section className="device-list">
          <h3>Devices ({devices.length})</h3>
          {devices.length === 0 && <div className="empty">No locations yet</div>}
          <ul>
            {devices.map((d) => (
              <li key={d.device_id} className={selectedDevice === d.device_id ? 'active' : ''} onClick={() => setSelectedDevice(d.device_id)}>
                <div className="device-id">{d.device_id}</div>
                <div className="device-meta">{new Date(d.ts).toLocaleString()}</div>
              </li>
            ))}
          </ul>
        </section>

        <section className="messages">
          <h4>Recent messages</h4>
          <div className="msgs">
            {messages.slice(0, 10).map((m, i) => (
              <pre key={i} className="msg">{JSON.stringify(m, null, 2)}</pre>
            ))}
          </div>
        </section>
      </aside>

      <main className="map-container">
        <MapView locations={devices} selectedDevice={selectedDevice} onSelectDevice={(id) => setSelectedDevice(id)} />
      </main>
    </div>
  )
}
