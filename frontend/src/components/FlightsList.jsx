import React from "react";

export default function FlightsList({ flights, loading }) {
  if (loading) return <div>Loading flights...</div>;
  return (
    <div style={{ maxHeight: 500, overflow: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr><th>ID</th><th>Flight ID</th><th>Type</th><th>Start</th><th>Duration s</th></tr>
        </thead>
        <tbody>
          {flights.map(f => (
            <tr key={f.id}>
              <td>{f.id}</td>
              <td>{f.flight_id}</td>
              <td>{f.uav_type}</td>
              <td>{f.start_time}</td>
              <td>{f.duration_seconds}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
