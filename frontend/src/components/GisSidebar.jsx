import React from 'react';
import {
  Search,
  Filter,
  MapPin,
  Film,
  Radio,
  Eye,
  SlidersHorizontal,
  HardDrive,
  Camera as CamIcon,
  Navigation,
  AlertCircle,
} from 'lucide-react';

export default function GisSidebar({
  cameras = [],
  focusedCamera,
  onSelectCamera,
  onViewDetails,
  search,
  setSearch,
  department,
  setDepartment,
  statusFilter,
  setStatusFilter,
  sourceTypeFilter,
  setSourceTypeFilter,
  cameraTypeFilter,
  setCameraTypeFilter,
}) {
  const mappedCount = cameras.filter(
    (c) =>
      typeof c.latitude === 'number' &&
      typeof c.longitude === 'number' &&
      !isNaN(c.latitude) &&
      !isNaN(c.longitude)
  ).length;

  const unmappedCount = cameras.length - mappedCount;

  return (
    <div className="flex flex-col h-full bg-[#0b1424] border border-slate-800 rounded-xl shadow-xl overflow-hidden text-xs">
      
      {/* Sidebar Header & Counts */}
      <div className="p-4 border-b border-slate-800 bg-[#080f1c] space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CamIcon className="w-4 h-4 text-blue-400" />
            <h2 className="font-bold text-white text-sm">GIS Camera Explorer</h2>
          </div>
          <div className="flex items-center space-x-1.5 font-mono text-[10px]">
            <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-300 border border-blue-500/20">
              Total: {cameras.length}
            </span>
            <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
              Mapped: {mappedCount}
            </span>
            {unmappedCount > 0 && (
              <span className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/20">
                Unmapped: {unmappedCount}
              </span>
            )}
          </div>
        </div>

        {/* Search Input */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search camera name, code, junction..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-8 pr-7 py-2 rounded-lg bg-[#070d18] border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
          {search && (
            <button
              onClick={() => setSearch('')}
              className="absolute right-2.5 top-2 text-slate-500 hover:text-slate-300 text-sm"
            >
              ×
            </button>
          )}
        </div>

        {/* Quick Filter Selectors */}
        <div className="grid grid-cols-2 gap-2 text-[11px]">
          <select
            value={sourceTypeFilter}
            onChange={(e) => setSourceTypeFilter(e.target.value)}
            className="w-full px-2 py-1.5 rounded-lg bg-[#070d18] border border-slate-700 text-slate-200 focus:outline-none focus:border-blue-500"
          >
            <option value="">All Sources</option>
            <option value="RECORDED_FOOTAGE">Recorded Footage</option>
            <option value="LIVE_CAMERA">Live Camera</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full px-2 py-1.5 rounded-lg bg-[#070d18] border border-slate-700 text-slate-200 focus:outline-none focus:border-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="ONLINE">ONLINE</option>
            <option value="OFFLINE">OFFLINE</option>
            <option value="MAINTENANCE">MAINTENANCE</option>
            <option value="UNKNOWN">UNKNOWN</option>
          </select>
        </div>

        {/* Active Filter Reset */}
        {(search || sourceTypeFilter || statusFilter || department || cameraTypeFilter) && (
          <div className="flex items-center justify-between pt-1 text-[10px] text-slate-400 font-mono">
            <span>Filters Active ({cameras.length} matched)</span>
            <button
              onClick={() => {
                setSearch('');
                setSourceTypeFilter('');
                setStatusFilter('');
                setDepartment('');
                setCameraTypeFilter('');
              }}
              className="text-blue-400 hover:underline"
            >
              Clear All
            </button>
          </div>
        )}
      </div>

      {/* Scrollable Camera List */}
      <div className="flex-1 overflow-y-auto divide-y divide-slate-800/60 max-h-[580px]">
        {cameras.length === 0 ? (
          <div className="p-8 text-center text-slate-400 space-y-2">
            <CamIcon className="w-8 h-8 text-slate-600 mx-auto" />
            <p className="font-semibold text-slate-300">No cameras found</p>
            <p className="text-[11px] text-slate-500">
              Try adjusting your search keywords or filter options.
            </p>
          </div>
        ) : (
          cameras.map((cam) => {
            const isSelected = focusedCamera && focusedCamera.id === cam.id;
            const hasLocation =
              typeof cam.latitude === 'number' &&
              typeof cam.longitude === 'number' &&
              !isNaN(cam.latitude) &&
              !isNaN(cam.longitude);

            return (
              <div
                key={cam.id}
                onClick={() => onSelectCamera(cam)}
                className={`p-3.5 transition-all duration-150 cursor-pointer ${
                  isSelected
                    ? 'bg-blue-600/15 border-l-4 border-blue-500'
                    : 'hover:bg-slate-800/40 border-l-4 border-transparent'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="font-bold text-white tracking-tight leading-tight">
                      {cam.camera_name}
                    </div>
                    <div className="font-mono text-[11px] text-blue-400 mt-0.5">
                      {cam.camera_code}
                    </div>
                  </div>

                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase font-bold shrink-0 ${
                      cam.status === 'ONLINE'
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                        : cam.status === 'OFFLINE'
                        ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                        : cam.status === 'MAINTENANCE'
                        ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                        : 'bg-slate-800 text-slate-400 border border-slate-700'
                    }`}
                  >
                    {cam.status}
                  </span>
                </div>

                <div className="mt-2 space-y-1 text-slate-300 text-[11px]">
                  <div className="flex items-center space-x-1 text-slate-400 truncate">
                    <MapPin className="w-3 h-3 text-slate-500 shrink-0" />
                    <span className="truncate" title={cam.location_name}>
                      {cam.location_name}
                    </span>
                  </div>

                  <div className="flex items-center justify-between pt-1">
                    {/* Coordinates */}
                    {hasLocation ? (
                      <span className="font-mono text-[10px] text-emerald-400 bg-[#060c16] px-1.5 py-0.5 rounded border border-slate-800">
                        {cam.latitude.toFixed(3)}°N, {cam.longitude.toFixed(3)}°E
                      </span>
                    ) : (
                      <span className="font-mono text-[10px] text-rose-400 flex items-center space-x-1">
                        <AlertCircle className="w-3 h-3" />
                        <span>Location Unavailable</span>
                      </span>
                    )}

                    {/* Source Pill */}
                    {cam.source_type === 'RECORDED_FOOTAGE' ? (
                      <span className="inline-flex items-center space-x-1 text-[10px] font-semibold text-amber-300 bg-amber-500/10 px-1.5 py-0.5 rounded">
                        <Film className="w-3 h-3" />
                        <span>RECORDED ({cam.footage_count || 0})</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center space-x-1 text-[10px] font-semibold text-blue-300 bg-blue-500/10 px-1.5 py-0.5 rounded">
                        <Radio className="w-3 h-3" />
                        <span>LIVE</span>
                      </span>
                    )}
                  </div>
                </div>

                {/* Actions Bar */}
                <div className="mt-2.5 pt-2 border-t border-slate-800/80 flex items-center justify-between">
                  <span className="text-[10px] text-slate-500 font-mono">
                    {cam.department}
                  </span>
                  <div className="flex items-center space-x-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectCamera(cam);
                      }}
                      className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                      title="Focus on Map"
                    >
                      <Navigation className="w-3 h-3 text-blue-400" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onViewDetails(cam);
                      }}
                      className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                      title="View Details"
                    >
                      <Eye className="w-3 h-3 text-slate-300" />
                    </button>
                  </div>
                </div>

              </div>
            );
          })
        )}
      </div>

    </div>
  );
}
