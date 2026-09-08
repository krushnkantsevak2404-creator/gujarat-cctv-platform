import React, { useState, useEffect } from 'react';
import { X, Shield, MapPin, Film, Radio, AlertCircle, Check, Map, Compass } from 'lucide-react';
import { MapContainer, TileLayer, Marker, useMapEvents, useMap } from 'react-leaflet';
import L from 'leaflet';

const GUJARAT_DISTRICT_PRESETS = [
  { name: 'Vadodara', lat: 22.3072, lng: 73.1812 },
  { name: 'Ahmedabad', lat: 23.0225, lng: 72.5714 },
  { name: 'Surat', lat: 21.1702, lng: 72.8311 },
  { name: 'Rajkot', lat: 22.2965, lng: 70.7983 },
  { name: 'Gandhinagar', lat: 23.2156, lng: 72.6369 },
  { name: 'Bhavnagar', lat: 21.7645, lng: 72.1519 },
];

const pickerPinIcon = L.divIcon({
  className: 'custom-picker-pin',
  html: `
    <div style="
      display: flex;
      align-items: center;
      justify-content: center;
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: #10b981;
      border: 2.5px solid #ffffff;
      color: #ffffff;
      font-size: 16px;
      box-shadow: 0 0 12px rgba(16, 185, 129, 0.8);
      cursor: pointer;
    ">
      📍
    </div>
  `,
  iconSize: [32, 32],
  iconAnchor: [16, 16],
});

function MapClickHandler({ onSelectLocation }) {
  useMapEvents({
    click(e) {
      onSelectLocation(Number(e.latlng.lat.toFixed(6)), Number(e.latlng.lng.toFixed(6)));
    },
  });
  return null;
}

function MapCenterController({ centerCoords }) {
  const map = useMap();
  useEffect(() => {
    if (centerCoords && centerCoords[0] && centerCoords[1]) {
      map.flyTo(centerCoords, 14, { duration: 0.8 });
    }
  }, [centerCoords, map]);
  return null;
}

export default function CameraModal({ isOpen, onClose, onSave, camera }) {
  const isEditing = !!camera;

  const [formData, setFormData] = useState({
    camera_name: '',
    camera_code: '',
    department: 'Traffic Police',
    location_name: '',
    latitude: '',
    longitude: '',
    camera_type: 'FIXED',
    source_type: 'RECORDED_FOOTAGE',
    connectivity_type: 'FILE',
    status: 'UNKNOWN',
    installation_date: '',
    description: '',
  });

  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [showMapPicker, setShowMapPicker] = useState(false);

  useEffect(() => {
    if (camera) {
      setFormData({
        camera_name: camera.camera_name || '',
        camera_code: camera.camera_code || '',
        department: camera.department || '',
        location_name: camera.location_name || '',
        latitude: camera.latitude !== undefined && camera.latitude !== null ? camera.latitude : '',
        longitude: camera.longitude !== undefined && camera.longitude !== null ? camera.longitude : '',
        camera_type: camera.camera_type || 'FIXED',
        source_type: camera.source_type || 'LIVE_CAMERA',
        connectivity_type: camera.connectivity_type || 'UNKNOWN',
        status: camera.status || 'UNKNOWN',
        installation_date: camera.installation_date || '',
        description: camera.description || '',
      });
    } else {
      // Default new camera template - no hardcoded coordinates
      setFormData({
        camera_name: '',
        camera_code: `CAM-${Math.floor(100 + Math.random() * 900)}`,
        department: 'Traffic Police',
        location_name: '',
        latitude: '',
        longitude: '',
        camera_type: 'FIXED',
        source_type: 'RECORDED_FOOTAGE',
        connectivity_type: 'FILE',
        status: 'UNKNOWN',
        installation_date: new Date().toISOString().split('T')[0],
        description: '',
      });
    }
    setErrors({});
  }, [camera, isOpen]);

  if (!isOpen) return null;

  const validate = () => {
    const errs = {};
    if (!formData.camera_name.trim()) errs.camera_name = 'Camera name is required';
    if (!formData.camera_code.trim()) errs.camera_code = 'Camera code is required';
    if (!formData.department.trim()) errs.department = 'Department is required';
    if (!formData.location_name.trim()) errs.location_name = 'Location name is required';

    if (formData.latitude === '' || formData.latitude === null || formData.latitude === undefined) {
      errs.latitude = 'Latitude is required (e.g. 22.3072 for Vadodara)';
    } else {
      const lat = parseFloat(formData.latitude);
      if (isNaN(lat) || lat < -90 || lat > 90) {
        errs.latitude = 'Latitude must be between -90 and +90';
      }
    }

    if (formData.longitude === '' || formData.longitude === null || formData.longitude === undefined) {
      errs.longitude = 'Longitude is required (e.g. 73.1812 for Vadodara)';
    } else {
      const lon = parseFloat(formData.longitude);
      if (isNaN(lon) || lon < -180 || lon > 180) {
        errs.longitude = 'Longitude must be between -180 and +180';
      }
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const applyPreset = (preset) => {
    setFormData((prev) => ({
      ...prev,
      latitude: preset.lat,
      longitude: preset.lng,
      location_name: prev.location_name ? prev.location_name : `${preset.name} City Area`,
    }));
    setErrors((prev) => ({ ...prev, latitude: null, longitude: null }));
  };

  const handleMapLocationSelect = (lat, lng) => {
    setFormData((prev) => ({
      ...prev,
      latitude: lat,
      longitude: lng,
    }));
    setErrors((prev) => ({ ...prev, latitude: null, longitude: null }));
    setShowMapPicker(false);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    let updated = { ...formData, [name]: value };

    // Auto-select connectivity when source_type changes
    if (name === 'source_type') {
      if (value === 'RECORDED_FOOTAGE') {
        updated.connectivity_type = 'FILE';
      } else if (value === 'LIVE_CAMERA' && updated.connectivity_type === 'FILE') {
        updated.connectivity_type = 'UNKNOWN';
      }
    }

    setFormData(updated);
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: null }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setSubmitting(true);
    try {
      const payload = {
        ...formData,
        latitude: parseFloat(formData.latitude),
        longitude: parseFloat(formData.longitude),
        installation_date: formData.installation_date || null,
        description: formData.description || null,
      };
      await onSave(payload, isEditing ? camera.id : null);
      onClose();
    } catch (err) {
      setErrors((prev) => ({
        ...prev,
        submit: err.message || 'Failed to save camera record',
      }));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm overflow-y-auto">
      <div className="bg-[#0b1424] border border-slate-700/80 rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden my-8">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-[#080f1c]">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-lg bg-blue-600/20 border border-blue-500/40 text-blue-400">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white">
                {isEditing ? `Edit Camera: ${camera.camera_code}` : 'Register New CCTV Camera'}
              </h2>
              <p className="text-xs text-slate-400">
                PostgreSQL + PostGIS Asset Registry
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body / Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4 text-xs">
          {errors.submit && (
            <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-500/40 text-rose-300 flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{errors.submit}</span>
            </div>
          )}

          {/* Row 1: Camera Name & Code */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="sm:col-span-2">
              <label className="block text-slate-300 font-medium mb-1">
                Camera Name <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                name="camera_name"
                value={formData.camera_name}
                onChange={handleChange}
                placeholder="e.g. SG Highway Iskcon Junction 01"
                className="w-full px-3 py-2 rounded-lg bg-[#070d18] border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 font-sans"
              />
              {errors.camera_name && (
                <p className="text-rose-400 text-[11px] mt-1">{errors.camera_name}</p>
              )}
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1">
                Camera Code <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                name="camera_code"
                value={formData.camera_code}
                onChange={handleChange}
                placeholder="GJ-AHM-001"
                className="w-full px-3 py-2 rounded-lg bg-[#070d18] border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 font-mono uppercase"
              />
              {errors.camera_code && (
                <p className="text-rose-400 text-[11px] mt-1">{errors.camera_code}</p>
              )}
            </div>
          </div>

          {/* Row 2: Department & Location Name */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-300 font-medium mb-1">
                Police Department / Jurisdiction <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                name="department"
                value={formData.department}
                onChange={handleChange}
                placeholder="e.g. Traffic Police - Ahmedabad West"
                className="w-full px-3 py-2 rounded-lg bg-[#070d18] border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
              {errors.department && (
                <p className="text-rose-400 text-[11px] mt-1">{errors.department}</p>
              )}
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1">
                Location Name <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                name="location_name"
                value={formData.location_name}
                onChange={handleChange}
                placeholder="e.g. Iskcon Cross Road, SG Highway"
                className="w-full px-3 py-2 rounded-lg bg-[#070d18] border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
              {errors.location_name && (
                <p className="text-rose-400 text-[11px] mt-1">{errors.location_name}</p>
              )}
            </div>
          </div>

          {/* Row 3: Coordinates (GPS) + District Presets + Map Picker */}
          <div className="p-3.5 rounded-xl bg-[#070d18]/80 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-1.5 text-slate-300 font-semibold">
                <MapPin className="w-4 h-4 text-emerald-400" />
                <span>Geographic GPS Coordinates</span>
                <span className="text-rose-400">*</span>
              </div>
              <button
                type="button"
                onClick={() => setShowMapPicker(true)}
                className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/40 text-[11px] font-semibold transition shadow-sm"
              >
                <Map className="w-3.5 h-3.5" />
                <span>🗺️ Pick on Map</span>
              </button>
            </div>

            {/* District Quick-Preset Buttons */}
            <div>
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-mono block mb-1.5">
                Quick District Presets:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {GUJARAT_DISTRICT_PRESETS.map((p) => {
                  const isSelected =
                    Number(formData.latitude) === p.lat && Number(formData.longitude) === p.lng;
                  return (
                    <button
                      key={p.name}
                      type="button"
                      onClick={() => applyPreset(p)}
                      className={`px-2 py-1 rounded-md text-[11px] font-medium border transition ${
                        isSelected
                          ? 'bg-blue-600 text-white border-blue-400 font-bold shadow-sm'
                          : 'bg-[#0b1424] text-slate-300 border-slate-700 hover:border-blue-500/60 hover:text-white'
                      }`}
                    >
                      {p.name} ({p.lat.toFixed(2)}, {p.lng.toFixed(2)})
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Latitude & Longitude Inputs */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
              <div>
                <label className="block text-slate-400 text-[11px] font-medium mb-1">
                  Latitude (North/South)
                </label>
                <input
                  type="number"
                  step="any"
                  name="latitude"
                  value={formData.latitude}
                  onChange={handleChange}
                  placeholder="e.g. 22.3072"
                  className="w-full px-3 py-2 rounded-lg bg-[#0b1424] border border-slate-700 text-emerald-400 font-mono focus:outline-none focus:border-emerald-500 text-xs"
                />
                {errors.latitude && (
                  <p className="text-rose-400 text-[11px] mt-1">{errors.latitude}</p>
                )}
              </div>

              <div>
                <label className="block text-slate-400 text-[11px] font-medium mb-1">
                  Longitude (East/West)
                </label>
                <input
                  type="number"
                  step="any"
                  name="longitude"
                  value={formData.longitude}
                  onChange={handleChange}
                  placeholder="e.g. 73.1812"
                  className="w-full px-3 py-2 rounded-lg bg-[#0b1424] border border-slate-700 text-cyan-400 font-mono focus:outline-none focus:border-cyan-500 text-xs"
                />
                {errors.longitude && (
                  <p className="text-rose-400 text-[11px] mt-1">{errors.longitude}</p>
                )}
              </div>
            </div>
          </div>

          {/* Row 4: Source Type Selector with Explanatory Notice */}
          <div className="p-3.5 rounded-xl bg-blue-950/20 border border-blue-900/40 space-y-2">
            <label className="block text-slate-200 font-semibold mb-1">
              CCTV Source Type <span className="text-rose-400">*</span>
            </label>
            <div className="grid grid-cols-2 gap-3">
              <label
                className={`flex items-center space-x-2 p-3 rounded-lg border cursor-pointer transition ${
                  formData.source_type === 'RECORDED_FOOTAGE'
                    ? 'bg-amber-500/10 border-amber-500/50 text-amber-300'
                    : 'bg-[#070d18] border-slate-700 text-slate-400'
                }`}
              >
                <input
                  type="radio"
                  name="source_type"
                  value="RECORDED_FOOTAGE"
                  checked={formData.source_type === 'RECORDED_FOOTAGE'}
                  onChange={handleChange}
                  className="hidden"
                />
                <Film className="w-4 h-4 text-amber-400 shrink-0" />
                <div>
                  <div className="font-bold">RECORDED FOOTAGE</div>
                  <div className="text-[10px] opacity-80">Local CCTV video files</div>
                </div>
              </label>

              <label
                className={`flex items-center space-x-2 p-3 rounded-lg border cursor-pointer transition ${
                  formData.source_type === 'LIVE_CAMERA'
                    ? 'bg-blue-500/10 border-blue-500/50 text-blue-300'
                    : 'bg-[#070d18] border-slate-700 text-slate-400'
                }`}
              >
                <input
                  type="radio"
                  name="source_type"
                  value="LIVE_CAMERA"
                  checked={formData.source_type === 'LIVE_CAMERA'}
                  onChange={handleChange}
                  className="hidden"
                />
                <Radio className="w-4 h-4 text-blue-400 shrink-0" />
                <div>
                  <div className="font-bold">LIVE CAMERA</div>
                  <div className="text-[10px] opacity-80">RTSP / VMS feed</div>
                </div>
              </label>
            </div>

            {/* Explanatory helper notice */}
            {formData.source_type === 'RECORDED_FOOTAGE' ? (
              <p className="text-[11px] text-amber-300/90 flex items-center space-x-1.5 pt-1 font-mono">
                <Check className="w-3.5 h-3.5 text-amber-400" />
                <span>This camera will use uploaded CCTV footage for analysis.</span>
              </p>
            ) : (
              <p className="text-[11px] text-blue-300/90 flex items-center space-x-1.5 pt-1 font-mono">
                <Check className="w-3.5 h-3.5 text-blue-400" />
                <span>Live stream integration (RTSP/ONVIF) will be configured in a later milestone.</span>
              </p>
            )}
          </div>

          {/* Row 5: Hardware Type, Connectivity & Status */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-slate-300 font-medium mb-1">Camera Type</label>
              <select
                name="camera_type"
                value={formData.camera_type}
                onChange={handleChange}
                className="w-full px-3 py-2 rounded-lg bg-[#070d18] border border-slate-700 text-slate-100 focus:outline-none focus:border-blue-500"
              >
                <option value="FIXED">FIXED</option>
                <option value="PTZ">PTZ</option>
                <option value="DOME">DOME</option>
                <option value="BULLET">BULLET</option>
                <option value="OTHER">OTHER</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1">Connectivity</label>
              <select
                name="connectivity_type"
                value={formData.connectivity_type}
                onChange={handleChange}
                className="w-full px-3 py-2 rounded-lg bg-[#070d18] border border-slate-700 text-slate-100 focus:outline-none focus:border-blue-500"
              >
                <option value="FILE">FILE (Recorded Media)</option>
                <option value="RTSP">RTSP (Real-Time)</option>
                <option value="ONVIF">ONVIF</option>
                <option value="VMS_API">VMS API</option>
                <option value="SDK">Vendor SDK</option>
                <option value="UNKNOWN">UNKNOWN</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1">Initial Status</label>
              <select
                name="status"
                value={formData.status}
                onChange={handleChange}
                className="w-full px-3 py-2 rounded-lg bg-[#070d18] border border-slate-700 text-slate-100 focus:outline-none focus:border-blue-500"
              >
                <option value="UNKNOWN">UNKNOWN</option>
                <option value="ONLINE">ONLINE</option>
                <option value="OFFLINE">OFFLINE</option>
                <option value="MAINTENANCE">MAINTENANCE</option>
              </select>
            </div>
          </div>

          {/* Row 6: Description */}
          <div>
            <label className="block text-slate-300 font-medium mb-1">Description / Notes</label>
            <textarea
              name="description"
              rows={2}
              value={formData.description}
              onChange={handleChange}
              placeholder="e.g. High vantage point covering 4-way signal junction..."
              className="w-full px-3 py-2 rounded-lg bg-[#070d18] border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Modal Footer */}
          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold transition shadow-lg shadow-blue-600/30 flex items-center space-x-2"
            >
              {submitting ? (
                <span>Saving...</span>
              ) : (
                <span>{isEditing ? 'Update Camera' : 'Register Camera'}</span>
              )}
            </button>
          </div>
        </form>

        {/* Interactive Location Picker Modal */}
        {showMapPicker && (
          <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
            <div className="bg-[#0b1424] border border-slate-700 rounded-2xl w-full max-w-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
              {/* Picker Header */}
              <div className="flex items-center justify-between px-5 py-3.5 border-b border-slate-800 bg-[#080f1c]">
                <div className="flex items-center space-x-2">
                  <div className="p-1.5 rounded-lg bg-emerald-600/20 text-emerald-400 border border-emerald-500/40">
                    <Map className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white">Select Camera Location on Gujarat Map</h3>
                    <p className="text-[11px] text-slate-400">
                      Click anywhere on the map to set exact coordinates. Powered by OpenStreetMap.
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setShowMapPicker(false)}
                  className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Picker Map Area */}
              <div className="h-[420px] w-full relative bg-[#070d18]">
                <MapContainer
                  center={
                    formData.latitude &&
                    formData.longitude &&
                    !isNaN(parseFloat(formData.latitude)) &&
                    !isNaN(parseFloat(formData.longitude))
                      ? [parseFloat(formData.latitude), parseFloat(formData.longitude)]
                      : [22.30, 71.80]
                  }
                  zoom={
                    formData.latitude &&
                    formData.longitude &&
                    !isNaN(parseFloat(formData.latitude)) &&
                    !isNaN(parseFloat(formData.longitude))
                      ? 12
                      : 7
                  }
                  className="h-full w-full"
                >
                  <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  />
                  <MapClickHandler onSelectLocation={handleMapLocationSelect} />
                  {formData.latitude &&
                    formData.longitude &&
                    !isNaN(parseFloat(formData.latitude)) &&
                    !isNaN(parseFloat(formData.longitude)) && (
                      <Marker
                        position={[parseFloat(formData.latitude), parseFloat(formData.longitude)]}
                        icon={pickerPinIcon}
                      />
                    )}
                </MapContainer>

                <div className="absolute bottom-3 left-3 z-[1000] bg-[#0b1424]/90 backdrop-blur-sm border border-slate-700 px-3 py-1.5 rounded-lg text-[11px] text-slate-300 font-mono shadow-lg">
                  {formData.latitude && formData.longitude ? (
                    <span>
                      📍 Selected: {Number(formData.latitude).toFixed(4)},{' '}
                      {Number(formData.longitude).toFixed(4)}
                    </span>
                  ) : (
                    <span>Click on map to drop pin</span>
                  )}
                </div>
              </div>

              {/* Picker Footer */}
              <div className="flex items-center justify-between px-5 py-3 border-t border-slate-800 bg-[#080f1c] text-xs">
                <span className="text-slate-400">
                  Clicking anywhere on the map sets the coordinates and closes the picker.
                </span>
                <button
                  type="button"
                  onClick={() => setShowMapPicker(false)}
                  className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold transition"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
