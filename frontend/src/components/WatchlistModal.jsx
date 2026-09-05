import React, { useState, useEffect } from 'react';
import { X, ShieldAlert, AlertTriangle, Check, Save } from 'lucide-react';

const CATEGORIES = [
  { value: 'GENERAL', label: 'General Monitoring' },
  { value: 'STOLEN', label: 'Stolen Vehicle' },
  { value: 'SUSPECT', label: 'Suspect / Person of Interest' },
  { value: 'WARRANT', label: 'Active Police Warrant' },
  { value: 'RESTRICTED', label: 'Restricted / Entry Prohibited' },
  { value: 'EXPIRED', label: 'Expired Registration / Permit' },
  { value: 'SPECIAL_INTEREST', label: 'Special Security Interest' },
];

const PRIORITIES = [
  { value: 'LOW', label: 'Low', color: 'text-slate-300 bg-slate-800/80 border-slate-600' },
  { value: 'MEDIUM', label: 'Medium', color: 'text-blue-300 bg-blue-900/30 border-blue-600' },
  { value: 'HIGH', label: 'High', color: 'text-orange-300 bg-orange-900/30 border-orange-600' },
  { value: 'CRITICAL', label: 'Critical', color: 'text-rose-300 bg-rose-900/30 border-rose-600' },
];

export default function WatchlistModal({ isOpen, onClose, onSave, entryToEdit }) {
  const [plateText, setPlateText] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('STOLEN');
  const [priority, setPriority] = useState('HIGH');
  const [status, setStatus] = useState('ACTIVE');
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (entryToEdit) {
      setPlateText(entryToEdit.plate_text || '');
      setDescription(entryToEdit.description || '');
      setCategory(entryToEdit.category || 'STOLEN');
      setPriority(entryToEdit.priority || 'HIGH');
      setStatus(entryToEdit.status || 'ACTIVE');
    } else {
      setPlateText('');
      setDescription('');
      setCategory('STOLEN');
      setPriority('HIGH');
      setStatus('ACTIVE');
    }
    setError(null);
  }, [entryToEdit, isOpen]);

  if (!isOpen) return null;

  // Normalized preview
  const normalizedPreview = plateText.replace(/[^a-zA-Z0-9]/g, '').toUpperCase();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!plateText.trim()) {
      setError('Please enter a vehicle license plate number.');
      return;
    }

    if (normalizedPreview.length < 3) {
      setError('License plate must contain at least 3 alphanumeric characters.');
      return;
    }

    setIsSubmitting(true);
    try {
      await onSave({
        plate_text: plateText.trim().toUpperCase(),
        description: description.trim() || null,
        category,
        priority,
        status,
      }, entryToEdit ? entryToEdit.id : null);
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to save watchlist entry.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
      <div className="bg-[#0b1424] border border-slate-700/80 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 bg-[#081120] flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-rose-500/20 border border-rose-500/40 rounded-lg text-rose-400">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white tracking-wide">
                {entryToEdit ? 'Edit Watchlist Entry' : 'Add Vehicle to Watchlist'}
              </h2>
              <p className="text-xs text-slate-400">
                Automatic vehicle surveillance matching rule
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="flex items-center space-x-2 p-3 bg-rose-500/15 border border-rose-500/40 rounded-xl text-rose-300 text-xs font-medium">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* License Plate Number */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              License Plate Number *
            </label>
            <input
              type="text"
              value={plateText}
              onChange={(e) => setPlateText(e.target.value)}
              placeholder="e.g. GJ 01 AB 1234 or MH 12 CD 5678"
              className="w-full px-3.5 py-2.5 bg-[#060c18] border border-slate-700 rounded-xl text-white font-mono text-sm placeholder-slate-500 focus:outline-none focus:border-rose-500 transition uppercase"
              required
            />
            {normalizedPreview && (
              <div className="mt-1.5 flex items-center space-x-2 text-[11px] text-slate-400">
                <span>Normalized matching key:</span>
                <span className="font-mono px-2 py-0.5 bg-rose-950/40 text-rose-300 border border-rose-800/40 rounded font-bold">
                  {normalizedPreview}
                </span>
              </div>
            )}
          </div>

          {/* Category & Priority Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Watchlist Category *
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3 py-2.5 bg-[#060c18] border border-slate-700 rounded-xl text-slate-200 text-xs focus:outline-none focus:border-rose-500 transition"
              >
                {CATEGORIES.map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Alert Priority *
              </label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="w-full px-3 py-2.5 bg-[#060c18] border border-slate-700 rounded-xl text-slate-200 text-xs focus:outline-none focus:border-rose-500 transition"
              >
                {PRIORITIES.map((p) => (
                  <option key={p.value} value={p.value}>
                    {p.label} Priority
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Monitoring Status */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Surveillance Status
            </label>
            <div className="flex items-center space-x-3">
              <button
                type="button"
                onClick={() => setStatus('ACTIVE')}
                className={`flex-1 flex items-center justify-center space-x-2 py-2 px-3 rounded-xl border text-xs font-bold transition ${
                  status === 'ACTIVE'
                    ? 'bg-emerald-500/20 border-emerald-500/60 text-emerald-300 shadow-inner'
                    : 'bg-slate-900 border-slate-700 text-slate-400 hover:text-slate-200'
                }`}
              >
                <Check className="w-3.5 h-3.5" />
                <span>ACTIVE (Generate Alerts)</span>
              </button>
              <button
                type="button"
                onClick={() => setStatus('INACTIVE')}
                className={`flex-1 flex items-center justify-center space-x-2 py-2 px-3 rounded-xl border text-xs font-bold transition ${
                  status === 'INACTIVE'
                    ? 'bg-slate-800 border-slate-600 text-slate-300'
                    : 'bg-slate-900 border-slate-700 text-slate-400 hover:text-slate-200'
                }`}
              >
                <span>INACTIVE (Muted)</span>
              </button>
            </div>
          </div>

          {/* Description & Case Notes */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Description / Case Notes / FIR Ref
            </label>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g. Reported stolen from Gandhinagar Sector 21 on 04-Sep. FIR #128/2026."
              className="w-full px-3.5 py-2.5 bg-[#060c18] border border-slate-700 rounded-xl text-slate-200 text-xs placeholder-slate-500 focus:outline-none focus:border-rose-500 transition resize-none"
            />
          </div>

          {/* Action Buttons */}
          <div className="pt-3 border-t border-slate-800 flex items-center justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-xl transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex items-center space-x-2 px-5 py-2 bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white text-xs font-bold rounded-xl shadow-lg shadow-rose-600/30 transition"
            >
              <Save className="w-4 h-4" />
              <span>{isSubmitting ? 'Saving...' : entryToEdit ? 'Update Entry' : 'Save Watchlist Entry'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
