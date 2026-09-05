import React, { useState, useMemo } from 'react';
import {
  MapPin,
  Layers,
  Radio,
  Film,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  XCircle,
  HardDrive,
  Globe,
  SlidersHorizontal,
} from 'lucide-react';
import GisMap from './GisMap';
import GisSidebar from './GisSidebar';

export default function GisView({
  cameras = [],
  stats,
  focusedCamera,
  onSelectCamera,
  onViewDetails,
  onViewFootage,
}) {
  const [search, setSearch] = useState('');
  const [department, setDepartment] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [sourceTypeFilter, setSourceTypeFilter] = useState('');
  const [cameraTypeFilter, setCameraTypeFilter] = useState('');

  // Filter cameras locally for instant search response
  const filteredCameras = useMemo(() => {
    return cameras.filter((cam) => {
      // Keyword search
      if (search.trim()) {
        const q = search.toLowerCase().trim();
        const nameMatch = cam.camera_name?.toLowerCase().includes(q);
        const codeMatch = cam.camera_code?.toLowerCase().includes(q);
        const deptMatch = cam.department?.toLowerCase().includes(q);
        const locMatch = cam.location_name?.toLowerCase().includes(q);
        if (!nameMatch && !codeMatch && !deptMatch && !locMatch) return false;
      }

      // Category filters
      if (department && !cam.department?.toLowerCase().includes(department.toLowerCase())) {
        return false;
      }
      if (statusFilter && cam.status !== statusFilter) {
        return false;
      }
      if (sourceTypeFilter && cam.source_type !== sourceTypeFilter) {
        return false;
      }
      if (cameraTypeFilter && cam.camera_type !== cameraTypeFilter) {
        return false;
      }

      return true;
    });
  }, [cameras, search, department, statusFilter, sourceTypeFilter, cameraTypeFilter]);

  const mappedCount = useMemo(() => {
    return filteredCameras.filter(
      (c) =>
        typeof c.latitude === 'number' &&
        typeof c.longitude === 'number' &&
        !isNaN(c.latitude) &&
        !isNaN(c.longitude)
    ).length;
  }, [filteredCameras]);

  const unmappedCount = filteredCameras.length - mappedCount;

  return (
    <div className="space-y-4">
      
      {/* GIS Summary Statistics Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
        <div className="p-3 rounded-xl bg-[#0a1222] border border-blue-500/20 shadow">
          <div className="flex items-center justify-between text-[11px] text-slate-400">
            <span>Total Cameras</span>
            <Globe className="w-3.5 h-3.5 text-blue-400" />
          </div>
          <div className="text-xl font-bold font-mono text-white mt-1">
            {cameras.length}
          </div>
        </div>

        <div className="p-3 rounded-xl bg-[#0a1222] border border-emerald-500/20 shadow">
          <div className="flex items-center justify-between text-[11px] text-slate-400">
            <span>Mapped on PostGIS</span>
            <MapPin className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <div className="text-xl font-bold font-mono text-emerald-400 mt-1">
            {mappedCount}
          </div>
        </div>

        <div className="p-3 rounded-xl bg-[#0a1222] border border-blue-500/20 shadow">
          <div className="flex items-center justify-between text-[11px] text-slate-400">
            <span>Live Streams</span>
            <Radio className="w-3.5 h-3.5 text-blue-400" />
          </div>
          <div className="text-xl font-bold font-mono text-blue-400 mt-1">
            {stats?.live_cameras || 0}
          </div>
        </div>

        <div className="p-3 rounded-xl bg-[#0a1222] border border-amber-500/20 shadow">
          <div className="flex items-center justify-between text-[11px] text-slate-400">
            <span>Recorded Footage</span>
            <Film className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="text-xl font-bold font-mono text-amber-400 mt-1">
            {stats?.recorded_cameras || 0}
          </div>
        </div>

        <div className="p-3 rounded-xl bg-[#0a1222] border border-green-500/20 shadow">
          <div className="flex items-center justify-between text-[11px] text-slate-400">
            <span>Online</span>
            <CheckCircle2 className="w-3.5 h-3.5 text-green-400" />
          </div>
          <div className="text-xl font-bold font-mono text-green-400 mt-1">
            {stats?.online_cameras || 0}
          </div>
        </div>

        <div className="p-3 rounded-xl bg-[#0a1222] border border-indigo-500/20 shadow">
          <div className="flex items-center justify-between text-[11px] text-slate-400">
            <span>Footage Clips</span>
            <HardDrive className="w-3.5 h-3.5 text-indigo-400" />
          </div>
          <div className="text-xl font-bold font-mono text-indigo-400 mt-1">
            {stats?.total_footage_files || 0}
          </div>
        </div>
      </div>

      {/* Side-by-Side Command Center Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
        
        {/* Left Side Panel: Camera Explorer & Filter List (4 cols) */}
        <div className="lg:col-span-4 h-[640px]">
          <GisSidebar
            cameras={filteredCameras}
            focusedCamera={focusedCamera}
            onSelectCamera={onSelectCamera}
            onViewDetails={onViewDetails}
            search={search}
            setSearch={setSearch}
            department={department}
            setDepartment={setDepartment}
            statusFilter={statusFilter}
            setStatusFilter={setStatusFilter}
            sourceTypeFilter={sourceTypeFilter}
            setSourceTypeFilter={setSourceTypeFilter}
            cameraTypeFilter={cameraTypeFilter}
            setCameraTypeFilter={setCameraTypeFilter}
          />
        </div>

        {/* Right Map Canvas: Leaflet PostGIS Map (8 cols) */}
        <div className="lg:col-span-8 h-[640px]">
          <GisMap
            cameras={filteredCameras}
            focusedCamera={focusedCamera}
            onSelectCamera={onSelectCamera}
            onViewDetails={onViewDetails}
            onViewFootage={onViewFootage}
          />
        </div>

      </div>

    </div>
  );
}
