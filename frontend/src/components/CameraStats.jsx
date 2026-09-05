import React from 'react';
import { Camera, Radio, Film, CheckCircle2, AlertTriangle, HelpCircle, HardDrive } from 'lucide-react';

export default function CameraStats({ stats, loading }) {
  if (!stats) return null;

  const items = [
    {
      label: 'Total Cameras',
      value: stats.total_cameras,
      icon: Camera,
      color: 'text-blue-400',
      bg: 'bg-blue-500/10 border-blue-500/20',
    },
    {
      label: 'Live Cameras',
      value: stats.live_cameras,
      icon: Radio,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10 border-emerald-500/20',
    },
    {
      label: 'Recorded Footage',
      value: stats.recorded_cameras,
      icon: Film,
      color: 'text-amber-400',
      bg: 'bg-amber-500/10 border-amber-500/20',
    },
    {
      label: 'Online',
      value: stats.online_cameras,
      icon: CheckCircle2,
      color: 'text-green-400',
      bg: 'bg-green-500/10 border-green-500/20',
    },
    {
      label: 'Offline / Maint.',
      value: stats.offline_cameras + stats.maintenance_cameras,
      icon: AlertTriangle,
      color: 'text-rose-400',
      bg: 'bg-rose-500/10 border-rose-500/20',
    },
    {
      label: 'Total Video Clips',
      value: stats.total_footage_files,
      icon: HardDrive,
      color: 'text-indigo-400',
      bg: 'bg-indigo-500/10 border-indigo-500/20',
    },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
      {items.map((item, idx) => {
        const Icon = item.icon;
        return (
          <div
            key={idx}
            className={`p-4 rounded-xl border backdrop-blur-sm bg-[#0a1222]/80 ${item.bg} transition-all duration-200 hover:scale-[1.02] shadow-lg`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400 truncate">{item.label}</span>
              <Icon className={`w-4 h-4 ${item.color}`} />
            </div>
            <div className="mt-2 text-2xl font-extrabold text-white font-mono tracking-tight">
              {loading ? (
                <span className="inline-block w-8 h-6 bg-slate-800 animate-pulse rounded"></span>
              ) : (
                item.value
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
