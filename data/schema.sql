CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE regions (
  id SERIAL PRIMARY KEY,
  name TEXT,
  geom geometry(MultiPolygon, 4326)
);

CREATE TABLE flights (
  id SERIAL PRIMARY KEY,
  flight_id TEXT,
  uav_type TEXT,
  start_time TIMESTAMP WITH TIME ZONE,
  end_time TIMESTAMP WITH TIME ZONE,
  duration_seconds INTEGER,
  start_geom geometry(Point, 4326),
  end_geom geometry(Point, 4326),
  start_region_id INTEGER,
  end_region_id INTEGER,
  fingerprint TEXT,
  raw_payload JSONB,
  created_at TIMESTAMP DEFAULT now()
);

CREATE INDEX idx_flights_start_geom ON flights USING GIST (start_geom);
CREATE INDEX idx_flights_end_geom ON flights USING GIST (end_geom);
CREATE INDEX idx_regions_geom ON regions USING GIST (geom);

CREATE UNIQUE INDEX IF NOT EXISTS uq_flight_flightid_time ON flights (flight_id, start_time);
