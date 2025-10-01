import React, { useEffect, useState } from "react";
import { topRegions, listFlights } from "../api";
import MapView from "../components/MapView";
import FlightsList from "../components/FlightsList";

export default function UserDashboard(){
  const [regions, setRegions] = useState([]);
  const [flights, setFlights] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchTop();
    fetchFlights();
  }, []);

  async function fetchTop(){
    try {
      const r = await topRegions({ limit: 10 });
      setRegions(r.data);
    } catch (e) {
      console.error(e);
    }
  }

  async function fetchFlights(){
    setLoading(true);
    try {
      const r = await listFlights({ limit: 200 });
      setFlights(r.data);
    } catch (e) {
      console.error(e);
    } finally { setLoading(false); }
  }

  return (
    <div style={{ padding: 10 }}>
      <h2>Dashboard</h2>
      <div style={{ display: "flex", gap: 20 }}>
        <div style={{flex: 1, minWidth: 400}}>
          <MapView flights={flights} />
        </div>
        <div style={{width: 420}}>
          <h3>Top regions</h3>
          <ol>
            {regions.map(r => <li key={r.gid}>{r.name} — {r.count} flights</li>)}
          </ol>
          <h3>Recent flights</h3>
          <FlightsList flights={flights} loading={loading} />
        </div>
      </div>
    </div>
  );
}
