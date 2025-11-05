import React, { useEffect, useState, useRef } from 'react'

// 🔧 WebSocket URL (localhost uchun)
const WS_URL = (clientId) => `ws://localhost:8000/ws/${clientId}`

export default function App() {
  const [messages, setMessages] = useState([])
  const wsRef = useRef(null)
  const clientIdRef = useRef(`viewer-${Math.floor(Math.random() * 10000)}`)

  useEffect(() => {
    const ws = new WebSocket(WS_URL(clientIdRef.current))
    wsRef.current = ws

    ws.onopen = () => console.log('✅ WebSocket connected')
    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data)
        setMessages((prev) => [data, ...prev].slice(0, 50))
      } catch (e) {
        setMessages((prev) => [{ raw: ev.data }, ...prev].slice(0, 50))
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

    // WebSocket orqali ham yuborish mumkin:
    // wsRef.current?.send(JSON.stringify(payload))

    await fetch('http://localhost:8000/publish', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
  }

  return (
    <div style={{ padding: 20, fontFamily: 'sans-serif' }}>
      <h2>FastAPI Live GPS Tracker</h2>
      <p>
        Connected as <b>{clientIdRef.current}</b>
      </p>
      <button onClick={sendMock}>Send mock location (POST)</button>

      <h3>Latest messages</h3>
      <div
        style={{
          maxHeight: 400,
          overflow: 'auto',
          border: '1px solid #ddd',
          padding: 10,
        }}
      >
        {messages.map((m, i) => (
          <div key={i} style={{ padding: 6, borderBottom: '1px solid #eee' }}>
            <pre style={{ margin: 0 }}>{JSON.stringify(m, null, 2)}</pre>
          </div>
        ))}
      </div>
    </div>
  )
}
