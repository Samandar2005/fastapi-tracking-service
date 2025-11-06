import React, { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

export default function MapView({ locations = [], selectedDevice = null, onSelectDevice = () => {} }) {
  const containerRef = useRef(null)
  const mapRef = useRef(null)
  const markersLayerRef = useRef(null)

  useEffect(() => {
    if (mapRef.current) return
    // initialize map
    const map = L.map(containerRef.current, { center: [41.3128, 69.2787], zoom: 12 })
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(map)
    markersLayerRef.current = L.layerGroup().addTo(map)
    mapRef.current = map
  }, [])

  useEffect(() => {
    const map = mapRef.current
    const layer = markersLayerRef.current
    if (!map || !layer) return

    layer.clearLayers()

    const markers = locations.map((loc) => {
      const marker = L.marker([loc.lat, loc.lng])
      marker.bindPopup(`<b>${loc.device_id}</b><br/>${new Date(loc.ts).toLocaleString()}`)
      marker.on('click', () => onSelectDevice(loc.device_id))
      marker.addTo(layer)
      return { id: loc.device_id, marker }
    })

    // Fit bounds if we have more than one marker
    if (markers.length === 1) {
      map.setView(markers[0].marker.getLatLng(), 14)
      if (selectedDevice === markers[0].id) markers[0].marker.openPopup()
    } else if (markers.length > 1) {
      const group = L.featureGroup(markers.map((m) => m.marker))
      map.fitBounds(group.getBounds().pad(0.2))
    }

    // If a device is selected, open its popup and center
    if (selectedDevice) {
      const found = markers.find((m) => m.id === selectedDevice)
      if (found) {
        map.setView(found.marker.getLatLng(), 15)
        found.marker.openPopup()
      }
    }
  }, [locations, selectedDevice, onSelectDevice])

  return <div ref={containerRef} id="map" style={{ height: '100%', width: '100%' }} />
}
