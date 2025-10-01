import React from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";

// fix for default icon images when using CRA
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

function parseWKTPoint(wkt){
  // expects "POINT(lon lat)"
  if (!wkt) return null;
  const m = wkt.match(/POINT\(([-\d\.]+)\s+([-\d\.]+)\)/);
  if (!m) return null;
  const lon = parseFloat(m[1]), lat = parseFloat(m[2]);
  return [lat, lon];
}

export default function MapView({ flights }) {
  // find center from first flight with coords
  let center = [55.75, 37.61]; // fallback Moscow
  const markers = [];
  for (const f of flights) {
    if (f.start_geom_wkt) {
      const p = parseWKTPoint(f.start_geom_wkt);
      if (p) {
        markers.push({ id: f.id, pos: p, title: f.flight_id });
      }
    }
  }
  if (markers.length) center = markers[0].pos;

  return (
    <MapContainer center={center} zoom={6} style={{ height: "600px", width: "100%" }}>
      <TileLayer
        attribution='&copy; OpenStreetMap'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {markers.map(m => (
        <Marker key={m.id} position={m.pos}>
          <Popup>{m.title}</Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
