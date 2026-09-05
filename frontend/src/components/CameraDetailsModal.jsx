import React, { useState, useEffect } from 'react';
import {
  X,
  Shield,
  MapPin,
  Camera as CamIcon,
  Film,
  Radio,
  Clock,
  Calendar,
  Layers,
  HardDrive,
  Navigation,
} from 'lucide-react';
import FootageManager from './FootageManager';

export default function CameraDetailsModal({
  isOpen,
  onClose,
  camera,
  onPlayFootage,
  onViewOnMap,
  onAnalyzeFootage,
  onViewDetections,
  onViewAnpr,
  onRunAnpr,
}) {
  const [footageList, setFootageList] = useState([]);
  const [loadingFootage, setLoadingFootage] = useState(false);

  const fetchFootage = async () => {
    if (!camera) return;
    setLoadingFootage(true);
    try {
      const res = await fetch(`/api/cameras/${camera.id}/footage`);
      if (res.ok) {
        const data = await res.json();
        setFootageList(data);
      }
    } catch (err) {
      console.error('Failed to load camera footage:', err);
    } finally {
      setLoadingFootage(false);
    }
  };

  useEffect(() => {
    if (isOpen && camera) {
      fetchFootage();
    }
  }, [isOpen, camera]);

  if (!isOpen || !camera) return null;

  const handleDeleteFootage = async (clip) => {
    if (!window.confirm(`Permanently delete video clip "${clip.original_file_name}" from storage?`)) {
      return;
    }
    try {
      const res = await fetch(`/api/footage/${clip.id}`, { method: 'DELETE' });
      if (res.ok) {
        setFootageList((prev) => prev.filter((f) => f.id !== clip.id));
      } else {
        alert('Failed to delete footage.');
      }
    } catch (err) {
      alert(`Error deleting footage: ${err.message}`);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md overflow-y-auto">
      <div className="bg-[#0b1424] border border-slate-700/80 rounded-2xl w-full max-w-4xl shadow-2xl overflow-hidden my-6">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-[#080f1c]">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-blue-600/20 border border-blue-500/40 text-blue-400">
              <CamIcon className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-base font-bold text-white tracking-tight">
                  {camera.camera_name}
                </h2>
                <span className="px-2 py-0.5 rounded text-xs font-mono font-bold bg-blue-900/60 text-blue-300 border border-blue-700/50">
                  {camera.camera_code}
                </span>
              </div>
              <p className="text-xs text-slate-400">
                {camera.department} • Gujarat Police CCTV Asset
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {onViewOnMap && (
              <button
                onClick={() => {
                  onClose();
                  onViewOnMap(camera);
                }}
                className="px-3 py-1.5 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/40 text-xs font-bold flex items-center space-x-1.5 transition"
              >
                <Navigation className="w-3.5 h-3.5 text-emerald-400" />
                <span>View on GIS Map</span>
              </button>
            )}

            <button
              onClick={onClose}
              className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-6 max-h-[80vh] overflow-y-auto">
          
          {/* Metadata Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-xl bg-[#070d18] border border-slate-800 text-xs">
            <div>
              <span className="text-slate-500 font-mono">LOCATION</span>
              <div className="font-semibold text-white mt-0.5 flex items-center space-x-1">
                <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                <span className="truncate">{camera.location_name}</span>
              </div>
            </div>

            <div>
              <span className="text-slate-500 font-mono">GPS COORDINATES</span>
              <div className="font-mono text-emerald-400 mt-0.5">
                {camera.latitude?.toFixed(4)}°N, {camera.longitude?.toFixed(4)}°E
              </div>
            </div>

            <div>
              <span className="text-slate-500 font-mono">SOURCE & TYPE</span>
              <div className="font-semibold text-slate-200 mt-0.5">
                {camera.source_type === 'RECORDED_FOOTAGE' ? 'Recorded Footage' : 'Live Camera'} ({camera.camera_type})
              </div>
            </div>

            <div>
              <span className="text-slate-500 font-mono">CONNECTIVITY / STATUS</span>
              <div className="font-semibold text-slate-200 mt-0.5">
                {camera.connectivity_type} • <span className="text-amber-400">{camera.status}</span>
              </div>
            </div>
          </div>

          {camera.description && (
            <div className="p-3 rounded-lg bg-[#070d18] border border-slate-800/80 text-xs">
              <span className="text-slate-500 font-mono">DESCRIPTION</span>
              <p className="text-slate-300 mt-0.5">{camera.description}</p>
            </div>
          )}

          {/* Footage Management Section */}
          <div className="pt-2 border-t border-slate-800">
            <FootageManager
              camera={camera}
              footageList={footageList}
              onUploadSuccess={fetchFootage}
              onPlayFootage={(clip) => onPlayFootage(clip, camera)}
              onDeleteFootage={handleDeleteFootage}
              onAnalyzeFootage={(clip) => onAnalyzeFootage && onAnalyzeFootage(clip, camera)}
              onViewDetections={(clip) => onViewDetections && onViewDetections(clip, camera)}
              onViewAnpr={(clip) => onViewAnpr && onViewAnpr(clip, camera)}
              onRunAnpr={(clip) => onRunAnpr && onRunAnpr(clip, camera)}
            />
          </div>

        </div>

      </div>
    </div>
  );
}
