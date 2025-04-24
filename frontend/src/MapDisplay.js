// src/MapDisplay.js
import React from 'react';
import "./App.css";
import { GoogleMap, useJsApiLoader, Marker, Polyline } from '@react-google-maps/api';

const mapContainerStyle = {
  width: '100%',
  height: '400px'
};

export default function MapDisplay({ routeData, defaultCenter, zoom = 13 }) {
  const { isLoaded, loadError } = useJsApiLoader({
    googleMapsApiKey: process.env.REACT_APP_GOOGLE_MAPS_API_KEY,
  });

  if (loadError)  return <div style={{ padding: '1rem', color: 'red' }}>Error loading map</div>;
  if (!isLoaded) return <div style={{ padding: '1rem' }}>Loading map…</div>;

  // Turn [lat, lng] arrays into {lat, lng} objects
  const path = (routeData || []).map(([lat, lng]) => ({ lat, lng }));

  return (
    <GoogleMap
      mapContainerStyle={mapContainerStyle}
      center={{ lat: defaultCenter[0], lng: defaultCenter[1] }}
      zoom={zoom}
      options={{
        streetViewControl: false,
        mapTypeControl: false,
        fullscreenControl: false,
      }}
    >
      {path.map((pos, i) => (
        <Marker
          key={i}
          position={pos}
          label={{
            text: String(i + 1),
            color: '#fff',
            fontSize: '12px',
            fontWeight: 'bold',
          }}
          icon={{
            path: window.google.maps.SymbolPath.CIRCLE,
            fillColor: '#4285F4',
            fillOpacity: 1,
            strokeOpacity: 0,
            scale: 16,
          }}
        />
      ))}

      {path.length > 1 && (
        <Polyline
          path={path}
          options={{
            strokeColor: '#4285F4',
            strokeOpacity: 0.8,
            strokeWeight: 4,
            clickable: false,
            editable: false,
            geodesic: true,
          }}
        />
      )}
    </GoogleMap>
  );
}



// import React from 'react';
// import "./App.css";
// import 'leaflet/dist/leaflet.css';
// import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';

// function MapDisplay({ routeData, defaultCenter }) {
//   return (
//     <MapContainer
//       center={[10.776345751453743, 106.7011806321713]} // center of Ho Chi Minh City
//       zoom={11.5}
//       style={{ height: '400px', width: '100%' }}
//       dragging={true}
//       scrollWheelZoom={true}
//       doubleClickZoom={true}
//       zoomControl={true}
//     >
//       <TileLayer
//         attribution='&copy; <a href="https://openstreetmap.org">OpenStreetMap</a> contributors'
//         url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
//       />
//       {routeData && routeData.map((coord, index) => (
//         <Marker key={index} position={coord}>
//           <Popup>
//             Stop {index + 1}: [ {coord[0]}, {coord[1]} ]
//           </Popup>
//         </Marker>
//       ))}
//       {routeData && routeData.length > 0 && (
//         <Polyline positions={routeData} color="blue" />
//       )}
//     </MapContainer>
//   );
// }

// export default MapDisplay;
