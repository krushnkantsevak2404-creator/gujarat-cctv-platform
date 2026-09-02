-- Gujarat CCTV Intelligence Platform
-- Database Initialization Script for PostgreSQL + PostGIS

-- Enable PostGIS extension for spatial/GIS operations
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Verify PostGIS installation
SELECT postgis_full_version();
