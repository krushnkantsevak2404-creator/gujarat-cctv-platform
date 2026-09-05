import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Plus,
  Search,
  Filter,
  RefreshCw,
  Edit2,
  Trash2,
  Bell,
  CheckCircle2,
  XCircle,
  AlertOctagon,
  Car,
  AlertTriangle,
  SlidersHorizontal,
} from 'lucide-react';
import WatchlistModal from './WatchlistModal';

const CATEGORY_COLORS = {
  GENERAL: 'bg-slate-700 text-slate-200 border-slate-600',
  STOLEN: 'bg-rose-900/40 text-rose-300 border-rose-600/60',
  SUSPECT: 'bg-amber-900/40 text-amber-300 border-amber-600/60',
  WARRANT: 'bg-red-900/40 text-red-300 border-red-600/60',
  RESTRICTED: 'bg-purple-900/40 text-purple-300 border-purple-600/60',
  EXPIRED: 'bg-blue-900/40 text-blue-300 border-blue-600/60',
  SPECIAL_INTEREST: 'bg-cyan-900/40 text-cyan-300 border-cyan-600/60',
};

const PRIORITY_BADGES = {
  LOW: 'text-slate-300 bg-slate-800 border-slate-600',
  MEDIUM: 'text-blue-300 bg-blue-900/40 border-blue-600',
  HIGH: 'text-orange-300 bg-orange-900/40 border-orange-600',
  CRITICAL: 'text-rose-300 bg-rose-900/50 border-rose-500 animate-pulse',
};

export default function WatchlistPage({ onNavigateToAlerts }) {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [entryToEdit, setEntryToEdit] = useState(null);

  const fetchWatchlist = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search.trim()) params.append('query', search.trim());
      if (categoryFilter) params.append('category', categoryFilter);
      if (priorityFilter) params.append('priority', priorityFilter);
      if (statusFilter) params.append('status', statusFilter);

      const res = await fetch(`/api/watchlist?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setEntries(data);
      }
    } catch (err) {
      console.error('Failed to fetch watchlist entries:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchWatchlist();
    }, 250);
    return () => clearTimeout(timer);
  }, [search, categoryFilter, priorityFilter, statusFilter]);

  const handleSaveEntry = async (payload, entryId) => {
    const url = entryId ? `/api/watchlist/${entryId}` : '/api/watchlist';
    const method = entryId ? 'PUT' : 'POST';

    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to save watchlist entry.');
    }

    fetchWatchlist();
  };

  const handleToggleStatus = async (entry) => {
    const newStatus = entry.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE';
    try {
      const res = await fetch(`/api/watchlist/${entry.id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });
      if (res.ok) {
        fetchWatchlist();
      }
    } catch (err) {
      console.error('Failed to toggle status:', err);
    }
  };

  const handleDeleteEntry = async (entry) => {
    if (!window.confirm(`Are you sure you want to remove "${entry.plate_text}" from the watchlist?`)) {
      return;
    }

    try {
      const res = await fetch(`/api/watchlist/${entry.id}`, { method: 'DELETE' });
      if (res.ok) {
        fetchWatchlist();
      } else {
        alert('Failed to delete watchlist entry.');
      }
    } catch (err) {
      alert(`Error deleting watchlist entry: ${err.message}`);
    }
  };

  // Compute local KPI counts
  const totalEntries = entries.length;
  const activeEntries = entries.filter((e) => e.status === 'ACTIVE').length;
  const criticalEntries = entries.filter((e) => e.priority === 'CRITICAL' || e.priority === 'HIGH').length;
  const totalAlertsGenerated = entries.reduce((acc, curr) => acc + (curr.alert_count || 0), 0);

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* KPI Cards Header */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-[#0b1424] border border-slate-800 rounded-xl p-4 shadow-lg flex items-center justify-between">
          <div>
            <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Monitored Plates
            </p>
            <h3 className="text-2xl font-black text-white mt-1">{totalEntries}</h3>
            <p className="text-[11px] text-slate-500 mt-0.5">Total watchlist rules</p>
          </div>
          <div className="p-3 bg-blue-600/15 border border-blue-500/30 rounded-xl text-blue-400">
            <Car className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-[#0b1424] border border-slate-800 rounded-xl p-4 shadow-lg flex items-center justify-between">
          <div>
            <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Active Rules
            </p>
            <h3 className="text-2xl font-black text-emerald-400 mt-1">{activeEntries}</h3>
            <p className="text-[11px] text-emerald-500/80 mt-0.5">Live surveillance active</p>
          </div>
          <div className="p-3 bg-emerald-600/15 border border-emerald-500/30 rounded-xl text-emerald-400">
            <CheckCircle2 className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-[#0b1424] border border-slate-800 rounded-xl p-4 shadow-lg flex items-center justify-between">
          <div>
            <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              High / Critical Priority
            </p>
            <h3 className="text-2xl font-black text-rose-400 mt-1">{criticalEntries}</h3>
            <p className="text-[11px] text-rose-500/80 mt-0.5">Immediate intercept targets</p>
          </div>
          <div className="p-3 bg-rose-600/15 border border-rose-500/30 rounded-xl text-rose-400">
            <AlertOctagon className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-[#0b1424] border border-slate-800 rounded-xl p-4 shadow-lg flex items-center justify-between">
          <div>
            <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Total Alerts Triggered
            </p>
            <h3 className="text-2xl font-black text-amber-400 mt-1">{totalAlertsGenerated}</h3>
            <p className="text-[11px] text-amber-500/80 mt-0.5">ANPR CCTV sightings</p>
          </div>
          <div className="p-3 bg-amber-600/15 border border-amber-500/30 rounded-xl text-amber-400">
            <Bell className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Toolbar & Filter Bar */}
      <div className="bg-[#0b1424] border border-slate-800 rounded-xl p-4 shadow-lg space-y-3">
        <div className="flex flex-col md:flex-row items-center justify-between gap-3">
          {/* Search */}
          <div className="relative w-full md:w-80">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search plate or case notes..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-[#060c18] border border-slate-700/80 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-rose-500"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-2.5 w-full md:w-auto justify-end">
            <button
              onClick={fetchWatchlist}
              className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl transition"
              title="Refresh Watchlist"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            <button
              onClick={() => {
                setEntryToEdit(null);
                setIsModalOpen(true);
              }}
              className="flex items-center space-x-1.5 px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-xs font-bold transition shadow-lg shadow-rose-600/30"
            >
              <Plus className="w-4 h-4" />
              <span>Add Vehicle to Watchlist</span>
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-2 border-t border-slate-800/60">
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-3 py-1.5 bg-[#060c18] border border-slate-700/60 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-rose-500"
          >
            <option value="">All Categories</option>
            <option value="STOLEN">Stolen Vehicle</option>
            <option value="SUSPECT">Suspect / Person of Interest</option>
            <option value="WARRANT">Active Police Warrant</option>
            <option value="RESTRICTED">Restricted Entry</option>
            <option value="EXPIRED">Expired Permit</option>
            <option value="SPECIAL_INTEREST">Special Security Interest</option>
            <option value="GENERAL">General</option>
          </select>

          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="px-3 py-1.5 bg-[#060c18] border border-slate-700/60 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-rose-500"
          >
            <option value="">All Priorities</option>
            <option value="CRITICAL">Critical Priority</option>
            <option value="HIGH">High Priority</option>
            <option value="MEDIUM">Medium Priority</option>
            <option value="LOW">Low Priority</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 bg-[#060c18] border border-slate-700/60 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-rose-500"
          >
            <option value="">All Statuses</option>
            <option value="ACTIVE">ACTIVE (Generating Alerts)</option>
            <option value="INACTIVE">INACTIVE (Muted)</option>
          </select>
        </div>
      </div>

      {/* Watchlist Table */}
      <div className="bg-[#0b1424] border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-[#081120] text-[11px] uppercase tracking-wider text-slate-400 font-semibold">
                <th className="py-3 px-4">License Plate</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Priority</th>
                <th className="py-3 px-4">Case Notes / Reason</th>
                <th className="py-3 px-4 text-center">Alerts</th>
                <th className="py-3 px-4 text-center">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-xs">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400">
                    <div className="flex flex-col items-center justify-center space-y-2">
                      <RefreshCw className="w-6 h-6 animate-spin text-rose-500" />
                      <span>Loading watchlist records...</span>
                    </div>
                  </td>
                </tr>
              ) : entries.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400">
                    <div className="flex flex-col items-center justify-center space-y-2">
                      <ShieldAlert className="w-8 h-8 text-slate-600" />
                      <p className="text-sm font-semibold text-slate-300">No watchlist entries found</p>
                      <p className="text-xs text-slate-500 max-w-sm">
                        Add monitored vehicle plates to enable automated detection alerts whenever CCTV footage is processed.
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                entries.map((entry) => {
                  const catColor = CATEGORY_COLORS[entry.category] || CATEGORY_COLORS.GENERAL;
                  const priColor = PRIORITY_BADGES[entry.priority] || PRIORITY_BADGES.MEDIUM;
                  const isActive = entry.status === 'ACTIVE';

                  return (
                    <tr key={entry.id} className="hover:bg-slate-800/30 transition">
                      {/* License Plate */}
                      <td className="py-3.5 px-4">
                        <div className="flex items-center space-x-2">
                          <span className="font-mono text-xs px-2.5 py-1 bg-[#060c18] border border-slate-700 text-white font-bold rounded-lg tracking-wider shadow-inner">
                            {entry.plate_text}
                          </span>
                          <span className="text-[10px] text-slate-500 font-mono hidden sm:inline">
                            [{entry.normalized_plate_text}]
                          </span>
                        </div>
                      </td>

                      {/* Category */}
                      <td className="py-3.5 px-4">
                        <span className={`inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${catColor}`}>
                          {entry.category.replace('_', ' ')}
                        </span>
                      </td>

                      {/* Priority */}
                      <td className="py-3.5 px-4">
                        <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold border ${priColor}`}>
                          {entry.priority}
                        </span>
                      </td>

                      {/* Description */}
                      <td className="py-3.5 px-4 max-w-xs truncate text-slate-300">
                        {entry.description || <span className="text-slate-500 italic">No notes provided</span>}
                      </td>

                      {/* Alert Count */}
                      <td className="py-3.5 px-4 text-center">
                        {entry.alert_count > 0 ? (
                          <button
                            onClick={() => onNavigateToAlerts && onNavigateToAlerts(entry.normalized_plate_text)}
                            className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/40 text-[11px] font-bold hover:bg-rose-500/30 transition"
                            title="View Alerts for this Vehicle"
                          >
                            <Bell className="w-3 h-3" />
                            <span>{entry.alert_count}</span>
                          </button>
                        ) : (
                          <span className="text-slate-500 font-mono text-[11px]">0</span>
                        )}
                      </td>

                      {/* Status Toggle */}
                      <td className="py-3.5 px-4 text-center">
                        <button
                          onClick={() => handleToggleStatus(entry)}
                          className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold border transition ${
                            isActive
                              ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40 hover:bg-emerald-500/25'
                              : 'bg-slate-800 text-slate-400 border-slate-700 hover:bg-slate-700'
                          }`}
                        >
                          {isActive ? (
                            <>
                              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                              <span>ACTIVE</span>
                            </>
                          ) : (
                            <>
                              <XCircle className="w-3 h-3 text-slate-400" />
                              <span>MUTED</span>
                            </>
                          )}
                        </button>
                      </td>

                      {/* Actions */}
                      <td className="py-3.5 px-4 text-right">
                        <div className="flex items-center justify-end space-x-1.5">
                          <button
                            onClick={() => {
                              setEntryToEdit(entry);
                              setIsModalOpen(true);
                            }}
                            className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
                            title="Edit Entry"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => handleDeleteEntry(entry)}
                            className="p-1.5 bg-rose-950/40 hover:bg-rose-900/60 border border-rose-800/40 text-rose-300 rounded-lg transition"
                            title="Delete Entry"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal */}
      <WatchlistModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSaveEntry}
        entryToEdit={entryToEdit}
      />
    </div>
  );
}
