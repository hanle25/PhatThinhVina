// src/MapDisplay.js
import React from 'react';
import "./App.css";
import 'leaflet/dist/leaflet.css';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';

function MapDisplay({ routeData, defaultCenter }) {
  // Center on the first coordinate of routeData if available or fallback to defaultCenter.
  const center = routeData && routeData.length > 0 ? routeData[0] : defaultCenter || [0, 0];

  return (
    <MapContainer
      center={[39.8283, -98.5795]} // approximate center of the US
      zoom={4}
      style={{ height: '400px', width: '100%' }}
      dragging={true}
      scrollWheelZoom={true}
      doubleClickZoom={true}
      zoomControl={true}
    >
      <TileLayer
        attribution='&copy; <a href="https://openstreetmap.org">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {routeData && routeData.map((coord, index) => (
        <Marker key={index} position={coord}>
          <Popup>
            Stop {index + 1}: [ {coord[0]}, {coord[1]} ]
          </Popup>
        </Marker>
      ))}
      {routeData && routeData.length > 0 && (
        <Polyline positions={routeData} color="blue" />
      )}
    </MapContainer>
  );
}

export default MapDisplay;
