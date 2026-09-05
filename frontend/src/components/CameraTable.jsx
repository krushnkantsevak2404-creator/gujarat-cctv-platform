import React from 'react';
import {
  Eye,
  Edit2,
  Trash2,
  Film,
  Radio,
  MapPin,
  Camera as CamIcon,
  HardDrive,
  Clock,
  Shield,
  Navigation,
} from 'lucide-react';

export default function CameraTable({
  cameras,
  loading,
  onView,
  onEdit,
  onDelete,
  onViewOnMap,
}) {
  const getStatusBadge = (status) => {
    switch (status) {
      case 'ONLINE':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1.5 animate-pulse"></span>
            Online
          </span>
        );
      case 'OFFLINE':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-400 mr-1.5"></span>
            Offline
          </span>
        );
      case 'MAINTENANCE':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mr-1.5"></span>
            Maintenance
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700">
            <span className="w-1.5 h-1.5 rounded-full bg-slate-400 mr-1.5"></span>
            Unknown
          </span>
        );
    }
  };

  const getSourceBadge = (source) => {
    if (source === 'RECORDED_FOOTAGE') {
      return (
        <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-300 border border-amber-500/30">
          <Film className="w-3 h-3" />
          <span>RECORDED</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-300 border border-blue-500/30">
        <Radio className="w-3 h-3" />
        <span>LIVE</span>
      </span>
    );
  };

  if (loading) {
    return (
      <div className="bg-[#0b1424] border border-slate-800 rounded-xl p-12 text-center">
        <div className="inline-block w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="mt-3 text-sm text-slate-400 font-mono">Loading CCTV Camera Registry...</p>
      </div>
    );
  }

  if (!cameras || cameras.length === 0) {
    return (
      <div className="bg-[#0b1424] border border-slate-800 rounded-xl p-12 text-center">
        <CamIcon className="w-12 h-12 text-slate-600 mx-auto mb-3" />
        <h3 className="text-base font-semibold text-white">No CCTV Cameras Found</h3>
        <p className="mt-1 text-xs text-slate-400 max-w-sm mx-auto">
          No registered cameras match the specified filters or the registry is currently empty.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-[#0b1424] border border-slate-800 rounded-xl shadow-xl overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-800 bg-[#080f1c] text-slate-400 font-mono uppercase tracking-wider">
              <th className="py-3.5 px-4">Camera ID & Name</th>
              <th className="py-3.5 px-4">Department / Location</th>
              <th className="py-3.5 px-4">Coordinates (GPS)</th>
              <th className="py-3.5 px-4">Source Type</th>
              <th className="py-3.5 px-4">Type</th>
              <th className="py-3.5 px-4">Status</th>
              <th className="py-3.5 px-4">Footage</th>
              <th className="py-3.5 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-sans">
            {cameras.map((cam) => (
              <tr
                key={cam.id}
                className="hover:bg-slate-800/40 transition-colors duration-150 group"
              >
                {/* Camera Code & Name */}
                <td className="py-3.5 px-4">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 rounded-lg bg-blue-950/60 border border-blue-800/40 text-blue-400 shrink-0">
                      <CamIcon className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="font-bold text-white text-sm tracking-tight flex items-center space-x-1.5">
                        <span>{cam.camera_name}</span>
                      </div>
                      <div className="font-mono text-[11px] text-blue-400">
                        {cam.camera_code}
                      </div>
                    </div>
                  </div>
                </td>

                {/* Department & Location */}
                <td className="py-3.5 px-4">
                  <div className="font-semibold text-slate-200">{cam.department}</div>
                  <div className="text-slate-400 flex items-center space-x-1 mt-0.5">
                    <MapPin className="w-3 h-3 text-slate-500 shrink-0" />
                    <span className="truncate max-w-[200px]" title={cam.location_name}>
                      {cam.location_name}
                    </span>
                  </div>
                </td>

                {/* Coordinates */}
                <td className="py-3.5 px-4 font-mono text-[11px] text-slate-300">
                  <div className="bg-[#060c16] px-2 py-1 rounded border border-slate-800/80 inline-block">
                    <span className="text-emerald-400">{cam.latitude.toFixed(4)}°N</span>,{' '}
                    <span className="text-cyan-400">{cam.longitude.toFixed(4)}°E</span>
                  </div>
                </td>

                {/* Source Type */}
                <td className="py-3.5 px-4">{getSourceBadge(cam.source_type)}</td>

                {/* Camera Hardware Type */}
                <td className="py-3.5 px-4">
                  <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-slate-800/80 text-slate-300 border border-slate-700/60">
                    {cam.camera_type}
                  </span>
                </td>

                {/* Status */}
                <td className="py-3.5 px-4">{getStatusBadge(cam.status)}</td>

                {/* Footage count */}
                <td className="py-3.5 px-4">
                  {cam.source_type === 'RECORDED_FOOTAGE' ? (
                    <span
                      className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded text-xs font-mono ${
                        cam.footage_count > 0
                          ? 'bg-amber-500/10 text-amber-300 border border-amber-500/30'
                          : 'bg-slate-800/60 text-slate-400 border border-slate-700/40'
                      }`}
                    >
                      <HardDrive className="w-3 h-3" />
                      <span>{cam.footage_count} {cam.footage_count === 1 ? 'Clip' : 'Clips'}</span>
                    </span>
                  ) : (
                    <span className="text-slate-500 font-mono text-[11px]">—</span>
                  )}
                </td>

                {/* Actions */}
                <td className="py-3.5 px-4 text-right">
                  <div className="flex items-center justify-end space-x-1.5">
                    {/* View on GIS Map */}
                    <button
                      onClick={() => onViewOnMap && onViewOnMap(cam)}
                      className="p-1.5 rounded-lg bg-emerald-600/10 hover:bg-emerald-600/20 text-emerald-400 border border-emerald-500/30 transition"
                      title="View on GIS Map"
                    >
                      <Navigation className="w-3.5 h-3.5" />
                    </button>

                    {/* View Details */}
                    <button
                      onClick={() => onView(cam)}
                      className="p-1.5 rounded-lg bg-blue-600/10 hover:bg-blue-600/20 text-blue-400 border border-blue-500/30 transition"
                      title="View Details & Footage"
                    >
                      <Eye className="w-3.5 h-3.5" />
                    </button>

                    {/* Edit */}
                    <button
                      onClick={() => onEdit(cam)}
                      className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
                      title="Edit Camera"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>

                    {/* Delete */}
                    <button
                      onClick={() => onDelete(cam)}
                      className="p-1.5 rounded-lg bg-rose-600/10 hover:bg-rose-600/20 text-rose-400 border border-rose-500/30 transition"
                      title="Delete Camera"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
