import React, { useEffect, useRef, useMemo, useState } from 'react';
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  useMap,
  ZoomControl,
} from 'react-leaflet';
import L from 'leaflet';
import {
  MapPin,
  Film,
  Radio,
  Eye,
  Play,
  HardDrive,
  Layers,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  XCircle,
  ExternalLink,
  RotateCcw,
} from 'lucide-react';

// Geographic Center & Initial Zoom for Gujarat State View
const GUJARAT_CENTER = [22.30, 71.80];
const GUJARAT_ZOOM = 7.5;

// Controller component to handle programmatic map pan/zoom and reset
function MapController({ focusedCamera, resetViewTrigger }) {
  const map = useMap();

  // Reset to full Gujarat state view
  useEffect(() => {
    if (resetViewTrigger) {
      map.setView(GUJARAT_CENTER, GUJARAT_ZOOM, {
        animate: true,
        duration: 1.0,
      });
    }
  }, [resetViewTrigger, map]);

  // Fly to focused camera when selected
  useEffect(() => {
    if (
      focusedCamera &&
      typeof focusedCamera.latitude === 'number' &&
      typeof focusedCamera.longitude === 'number' &&
      !isNaN(focusedCamera.latitude) &&
      !isNaN(focusedCamera.longitude) &&
      (focusedCamera.latitude !== 0 || focusedCamera.longitude !== 0)
    ) {
      map.flyTo([focusedCamera.latitude, focusedCamera.longitude], 15, {
        duration: 1.2,
        easeLinearity: 0.25,
      });
    }
  }, [focusedCamera, map]);

  return null;
}

// Generate custom SVG / DivIcon marker based on status and source
function createCameraIcon(camera, isSelected) {
  let statusColor = '#64748b'; // UNKNOWN (slate)
  let glowColor = 'rgba(100, 116, 139, 0.4)';

  if (camera.status === 'ONLINE') {
    statusColor = '#10b981'; // green
    glowColor = 'rgba(16, 185, 129, 0.6)';
  } else if (camera.status === 'OFFLINE') {
    statusColor = '#f43f5e'; // red
    glowColor = 'rgba(244, 63, 94, 0.6)';
  } else if (camera.status === 'MAINTENANCE') {
    statusColor = '#f59e0b'; // amber
    glowColor = 'rgba(245, 158, 11, 0.6)';
  }

  const isRecorded = camera.source_type === 'RECORDED_FOOTAGE';
  const size = isSelected ? 42 : 34;

  const html = `
    <div style="
      position: relative;
      width: ${size}px;
      height: ${size}px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
    ">
      ${
        isSelected
          ? `<div style="
              position: absolute;
              inset: -6px;
              border-radius: 50%;
              background: ${glowColor};
              animation: markerPulse 1.8s infinite;
            "></div>`
          : ''
      }
      <div style="
        position: relative;
        width: 100%;
        height: 100%;
        border-radius: 50%;
        background: #081120;
        border: 2px solid ${statusColor};
        box-shadow: 0 4px 12px ${glowColor};
        display: flex;
        align-items: center;
        justify-content: center;
        color: ${statusColor};
        transition: transform 0.2s ease;
      ">
        ${
          isRecorded
            ? `<svg width="${size * 0.5}" height="${size * 0.5}" viewBox="0 0 24 24" fill="none" stroke="${statusColor}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="20" x="2" y="2" rx="2.18"/><line x1="7" x2="7" y1="2" y2="22"/><line x1="17" x2="17" y1="2" y2="22"/><line x1="2" x2="22" y1="12" y2="12"/><line x1="2" x2="7" y1="7" y2="7"/><line x1="2" x2="7" y1="17" y2="17"/><line x1="17" x2="22" y1="17" y2="17"/><line x1="17" x2="22" y1="7" y2="7"/></svg>`
            : `<svg width="${size * 0.5}" height="${size * 0.5}" viewBox="0 0 24 24" fill="none" stroke="${statusColor}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/></svg>`
        }
      </div>
      <div style="
        position: absolute;
        bottom: -3px;
        right: -3px;
        width: ${size * 0.35}px;
        height: ${size * 0.35}px;
        border-radius: 50%;
        background: ${statusColor};
        border: 2px solid #081120;
      "></div>
    </div>
  `;

  return L.divIcon({
    html,
    className: 'custom-cctv-marker',
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2],
  });
}

export default function GisMap({
  cameras = [],
  focusedCamera,
  onSelectCamera,
  onViewDetails,
  onViewFootage,
  onOpenInViewer,
}) {
  const markerRefs = useRef({});
  const [resetTrigger, setResetTrigger] = useState(0);

  // Filter only cameras with genuinely valid geographic coordinates
  const mappedCameras = useMemo(() => {
    return cameras.filter(
      (c) =>
        typeof c.latitude === 'number' &&
        typeof c.longitude === 'number' &&
        !isNaN(c.latitude) &&
        !isNaN(c.longitude) &&
        c.latitude >= -90 &&
        c.latitude <= 90 &&
        c.longitude >= -180 &&
        c.longitude <= 180 &&
        (c.latitude !== 0 || c.longitude !== 0)
    );
  }, [cameras]);

  // Open popup automatically when focusedCamera changes
  useEffect(() => {
    if (focusedCamera && markerRefs.current[focusedCamera.id]) {
      markerRefs.current[focusedCamera.id].openPopup();
    }
  }, [focusedCamera]);

  return (
    <div className="relative w-full h-full min-h-[580px] rounded-xl overflow-hidden border border-slate-800 shadow-2xl bg-[#070d18]">
      
      {/* Floating Toolbar: Reset Gujarat View */}
      <div className="absolute top-3 right-3 z-20 flex items-center space-x-2">
        <button
          onClick={() => setResetTrigger((prev) => prev + 1)}
          className="px-3 py-1.5 rounded-lg bg-[#081120]/90 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-bold shadow-xl backdrop-blur-md transition flex items-center space-x-1.5"
          title="Reset map view to whole Gujarat state"
        >
          <RotateCcw className="w-3.5 h-3.5 text-blue-400" />
          <span>Reset Gujarat View</span>
        </button>
      </div>

      {/* Map Container */}
      <MapContainer
        center={GUJARAT_CENTER}
        zoom={GUJARAT_ZOOM}
        zoomControl={false}
        className="w-full h-full z-10"
        style={{ minHeight: '580px', height: '100%' }}
      >
        {/* OpenStreetMap Base Layer - Zero API Key Dependency */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          maxZoom={19}
        />

        <ZoomControl position="bottomleft" />

        <MapController
          focusedCamera={focusedCamera}
          resetViewTrigger={resetTrigger}
        />

        {/* Render Markers for all Mapped Cameras (Strictly at DB coordinates) */}
        {mappedCameras.map((cam) => {
          const isSelected = focusedCamera && focusedCamera.id === cam.id;
          const customIcon = createCameraIcon(cam, isSelected);

          return (
            <Marker
              key={cam.id}
              position={[cam.latitude, cam.longitude]}
              icon={customIcon}
              ref={(ref) => {
                if (ref) markerRefs.current[cam.id] = ref;
              }}
              eventHandlers={{
                click: () => {
                  if (onSelectCamera) onSelectCamera(cam);
                },
              }}
            >
              <Popup className="cctv-custom-popup" minWidth={290} maxWidth={330}>
                <div className="p-4 bg-[#0a1424] text-slate-100 rounded-xl space-y-3 font-sans">
                  
                  {/* Header */}
                  <div className="flex items-start justify-between border-b border-slate-800 pb-2.5">
                    <div>
                      <div className="font-bold text-sm text-white leading-tight">
                        {cam.camera_name}
                      </div>
                      <div className="font-mono text-xs font-bold text-blue-400 mt-0.5">
                        {cam.camera_code}
                      </div>
                    </div>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                        cam.status === 'ONLINE'
                          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                          : cam.status === 'OFFLINE'
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                          : cam.status === 'MAINTENANCE'
                          ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                          : 'bg-slate-800 text-slate-300 border border-slate-700'
                      }`}
                    >
                      {cam.status}
                    </span>
                  </div>

                  {/* Details */}
                  <div className="space-y-1.5 text-xs text-slate-300">
                    <div className="flex justify-between">
                      <span className="text-slate-500 font-mono">Department:</span>
                      <span className="font-semibold text-slate-200 text-right truncate max-w-[160px]">
                        {cam.department}
                      </span>
                    </div>

                    <div className="flex justify-between">
                      <span className="text-slate-500 font-mono">Location:</span>
                      <span className="text-slate-200 text-right truncate max-w-[160px]" title={cam.location_name}>
                        {cam.location_name}
                      </span>
                    </div>

                    <div className="flex justify-between">
                      <span className="text-slate-500 font-mono">GPS:</span>
                      <span className="font-mono text-[11px] text-emerald-400">
                        {cam.latitude.toFixed(4)}°N, {cam.longitude.toFixed(4)}°E
                      </span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-slate-500 font-mono">Source:</span>
                      {cam.source_type === 'RECORDED_FOOTAGE' ? (
                        <span className="inline-flex items-center space-x-1 text-[11px] font-semibold text-amber-300 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                          <Film className="w-3 h-3" />
                          <span>RECORDED FOOTAGE</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center space-x-1 text-[11px] font-semibold text-blue-300 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
                          <Radio className="w-3 h-3" />
                          <span>LIVE CAMERA</span>
                        </span>
                      )}
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-slate-500 font-mono">Connectivity:</span>
                      <span className="font-mono text-[11px] font-bold text-cyan-400 bg-cyan-950/40 px-1.5 py-0.5 rounded border border-cyan-800/40">
                        {cam.connectivity_type || 'UNKNOWN'}
                      </span>
                    </div>

                    {cam.source_type === 'RECORDED_FOOTAGE' && (
                      <div className="flex justify-between items-center pt-1">
                        <span className="text-slate-500 font-mono">Footage:</span>
                        <span className="font-mono text-xs text-amber-400 font-bold">
                          {cam.footage_count || 0} {(cam.footage_count || 0) === 1 ? 'Clip' : 'Clips'}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Actions (Milestone 10: Unified Viewer Integration) */}
                  <div className="space-y-1.5 pt-2 border-t border-slate-800">
                    <button
                      onClick={() => onOpenInViewer && onOpenInViewer(cam)}
                      className="w-full px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs flex items-center justify-center space-x-1 transition shadow-sm"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                      <span>Open in Unified Viewer</span>
                    </button>

                    <div className="grid grid-cols-2 gap-2">
                      <button
                        onClick={() => onViewDetails && onViewDetails(cam)}
                        className="w-full px-2 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-xs flex items-center justify-center space-x-1 transition"
                      >
                        <Eye className="w-3 h-3" />
                        <span>Details</span>
                      </button>

                      {cam.source_type === 'RECORDED_FOOTAGE' ? (
                        <button
                          onClick={() => onViewFootage && onViewFootage(cam)}
                          className="w-full px-2 py-1 rounded-lg bg-amber-600/20 hover:bg-amber-600/30 text-amber-300 border border-amber-500/40 font-medium text-xs flex items-center justify-center space-x-1 transition"
                        >
                          <HardDrive className="w-3 h-3" />
                          <span>Footage ({cam.footage_count || 0})</span>
                        </button>
                      ) : (
                        <button
                          onClick={() => onViewDetails && onViewDetails(cam)}
                          className="w-full px-2 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium text-xs flex items-center justify-center space-x-1 transition"
                        >
                          <span>Manage</span>
                        </button>
                      )}
                    </div>
                  </div>

                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>

      {/* Floating Map Legend Overlay */}
      <div className="absolute bottom-4 right-4 z-20 bg-[#081120]/90 backdrop-blur-md border border-slate-800 rounded-xl p-3.5 shadow-2xl text-xs space-y-2.5 max-w-[220px]">
        <div className="flex items-center space-x-1.5 text-white font-bold border-b border-slate-800 pb-1.5">
          <Layers className="w-3.5 h-3.5 text-blue-400" />
          <span>GIS Map Legend</span>
        </div>

        {/* Status Colors */}
        <div className="space-y-1">
          <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
            Camera Status
          </span>
          <div className="grid grid-cols-2 gap-1.5 text-[11px]">
            <div className="flex items-center space-x-1.5 text-slate-300">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
              <span>Online</span>
            </div>
            <div className="flex items-center space-x-1.5 text-slate-300">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-400"></span>
              <span>Offline</span>
            </div>
            <div className="flex items-center space-x-1.5 text-slate-300">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-400"></span>
              <span>Maint.</span>
            </div>
            <div className="flex items-center space-x-1.5 text-slate-300">
              <span className="w-2.5 h-2.5 rounded-full bg-slate-500"></span>
              <span>Unknown</span>
            </div>
          </div>
        </div>

        {/* Source Types */}
        <div className="space-y-1 pt-1 border-t border-slate-800/80">
          <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
            CCTV Source
          </span>
          <div className="space-y-1 text-[11px]">
            <div className="flex items-center space-x-1.5 text-blue-300">
              <Radio className="w-3 h-3 text-blue-400" />
              <span>Live Camera (RTSP)</span>
            </div>
            <div className="flex items-center space-x-1.5 text-amber-300">
              <Film className="w-3 h-3 text-amber-400" />
              <span>Recorded Footage (File)</span>
            </div>
          </div>
        </div>

        {/* Total Mapped Info */}
        <div className="pt-1.5 border-t border-slate-800/80 text-[10px] font-mono text-slate-400 flex justify-between">
          <span>Active on Map:</span>
          <span className="text-emerald-400 font-bold">{mappedCameras.length} Cameras</span>
        </div>
      </div>

    </div>
  );
}
