import React, { useState, useEffect } from 'react';
import {
  Search,
  Shield,
  Car,
  MapPin,
  Clock,
  CheckCircle2,
  AlertTriangle,
  ZoomIn,
  Play,
  FileCheck,
  Sparkles,
  ExternalLink,
  Layers,
  X,
} from 'lucide-react';

export default function AnprSearchGlobal({
  onSelectResult,
  onNavigateToGis,
}) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [zoomedCrop, setZoomedCrop] = useState(null);

  const handleSearch = async (e) => {
    if (e) e.preventDefault();
    if (!query.trim() || query.trim().length < 2) return;

    setLoading(true);
    setSearched(true);
    try {
      const res = await fetch(`/api/anpr/search?query=${encodeURIComponent(query.trim())}&limit=50`);
      if (res.ok) {
        const data = await res.json();
        setResults(data.results || []);
      } else {
        setResults([]);
      }
    } catch (err) {
      console.error('Failed to search plates:', err);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Header Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-[#0a1426] via-[#0d1d3a] to-[#0a1426] border border-slate-800 shadow-xl flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center space-x-3.5">
          <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400 shadow-inner">
            <Shield className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-lg font-bold text-white tracking-wide">
                Central License Plate Intelligence & ANPR Search
              </h2>
              <span className="px-2.5 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">
                CROSS-CAMERA REGISTRY
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Search verified vehicle license plate sightings, OCR readouts, and timestamps across all registered Gujarat CCTV cameras.
            </p>
          </div>
        </div>

        {/* Quick Search Input */}
        <form onSubmit={handleSearch} className="w-full md:w-auto flex items-center space-x-2">
          <div className="relative w-full md:w-80">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
            <input
              type="text"
              placeholder="Search plate (e.g. GJ01, GJ, 1234, CEGI)..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full bg-[#060c18] border border-slate-700/80 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500 font-mono"
            />
          </div>
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 disabled:bg-slate-800 text-white font-bold text-xs shadow-lg shadow-amber-600/30 transition flex items-center space-x-1.5 shrink-0"
          >
            <Search className="w-3.5 h-3.5" />
            <span>{loading ? 'Searching...' : 'Search'}</span>
          </button>
        </form>
      </div>

      {/* Results Section */}
      <div className="space-y-3">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span>
            {searched ? (
              <span>Found <strong className="text-amber-400">{results.length}</strong> matching plate sighting(s) for "<span className="font-mono text-white">{query}</span>"</span>
            ) : (
              <span>Enter a license plate query above to search across registered cameras.</span>
            )}
          </span>
        </div>

        {results.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {results.map((item) => (
              <div
                key={item.id}
                className="p-4 rounded-xl bg-[#08101f] border border-slate-800 hover:border-slate-700 transition flex flex-col justify-between space-y-3 shadow"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] font-mono text-slate-400 flex items-center space-x-1">
                      <Clock className="w-3 h-3 text-blue-400" />
                      <span>{item.formatted_timestamp} in footage</span>
                    </span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                      item.status === 'OCR_SUCCESS'
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                        : item.status === 'OCR_LOW_CONFIDENCE'
                        ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                        : 'bg-slate-800 text-slate-400 border border-slate-700'
                    }`}>
                      {item.status}
                    </span>
                  </div>

                  {/* License Plate Display */}
                  <div className="flex items-center space-x-3 mb-3">
                    <div className="relative inline-flex items-center rounded-lg border-2 border-slate-900 bg-[#f8fafc] text-slate-950 font-black shadow px-3 py-1.5 tracking-wider font-mono text-base">
                      <div className="absolute left-1 top-1 bottom-1 w-3 bg-[#003893] rounded-l flex flex-col items-center justify-center text-[5px] text-white font-bold font-sans">
                        <span className="text-amber-400">IND</span>
                      </div>
                      <span className="pl-3.5">
                        {item.plate_number_normalized || item.plate_number_raw || 'UNREADABLE'}
                      </span>
                    </div>

                    <div className="text-[11px] font-mono">
                      <p className="text-slate-300 font-semibold uppercase">{item.vehicle_class}</p>
                      <p className="text-amber-400 font-bold">{item.confidence_percent}</p>
                    </div>
                  </div>

                  {/* Plate Crop Image */}
                  {item.has_crop && (
                    <div className="relative bg-black rounded-lg border border-slate-800 p-1 flex items-center justify-center max-h-24 overflow-hidden mb-2">
                      <img
                        src={item.plate_crop_url}
                        alt="Plate Crop"
                        className="max-h-20 object-contain rounded cursor-pointer hover:scale-105 transition"
                        onClick={() => setZoomedCrop(item.plate_crop_url)}
                      />
                      <button
                        onClick={() => setZoomedCrop(item.plate_crop_url)}
                        className="absolute bottom-1 right-1 p-1 rounded bg-black/70 text-amber-400 hover:text-white"
                        title="Zoom Image"
                      >
                        <ZoomIn className="w-3 h-3" />
                      </button>
                    </div>
                  )}

                  {/* Camera Location Details */}
                  <div className="p-2.5 rounded-lg bg-[#050b16] border border-slate-800/80 text-xs space-y-1 font-mono">
                    <div className="flex items-center space-x-1.5 text-slate-200">
                      <MapPin className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                      <span className="font-semibold truncate">{item.camera_code} — {item.camera_name}</span>
                    </div>
                    <p className="text-[11px] text-slate-400 truncate pl-5">
                      {item.location_name}
                    </p>
                    {item.latitude && item.longitude && (
                      <p className="text-[10px] text-slate-500 pl-5">
                        Geo: {item.latitude.toFixed(4)}, {item.longitude.toFixed(4)}
                      </p>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center justify-between pt-2 border-t border-slate-800/80">
                  {item.latitude && item.longitude && onNavigateToGis && (
                    <button
                      onClick={() => onNavigateToGis(item.camera_id)}
                      className="text-[11px] text-blue-400 hover:text-blue-300 flex items-center space-x-1 font-semibold"
                    >
                      <MapPin className="w-3 h-3" />
                      <span>View on GIS Map</span>
                    </button>
                  )}
                  {onSelectResult && (
                    <button
                      onClick={() => onSelectResult(item)}
                      className="px-2.5 py-1 rounded bg-amber-600 hover:bg-amber-500 text-white text-[11px] font-bold flex items-center space-x-1 ml-auto shadow"
                    >
                      <Play className="w-3 h-3 fill-current" />
                      <span>Open ANPR Dossier</span>
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : searched && !loading ? (
          <div className="p-12 rounded-2xl bg-[#08101f] border border-slate-800 text-center text-xs font-mono text-slate-400">
            <Shield className="w-10 h-10 text-slate-600 mx-auto mb-2" />
            <p className="text-slate-300 font-bold">No license plate records found for "{query}"</p>
            <p className="text-slate-500 mt-1">Try searching for a state prefix (e.g. GJ, MH, DL) or partial plate numbers.</p>
          </div>
        ) : null}
      </div>

      {/* Image Zoom Modal */}
      {zoomedCrop && (
        <div
          className="fixed inset-0 z-60 flex items-center justify-center p-4 bg-black/90 backdrop-blur-md"
          onClick={() => setZoomedCrop(null)}
        >
          <div
            className="relative bg-[#0b1424] p-4 rounded-xl border border-slate-700 max-w-lg shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800">
              <span className="text-xs font-bold text-white font-mono">License Plate Crop View</span>
              <button
                onClick={() => setZoomedCrop(null)}
                className="p-1 rounded bg-slate-800 text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <img
              src={zoomedCrop}
              alt="Zoomed Plate Crop"
              className="w-full rounded border border-slate-700 bg-black object-contain max-h-[300px]"
            />
          </div>
        </div>
      )}

    </div>
  );
}
