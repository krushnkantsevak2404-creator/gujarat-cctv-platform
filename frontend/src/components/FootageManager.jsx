import React, { useState, useRef } from 'react';
import {
  Upload,
  Film,
  Play,
  Trash2,
  HardDrive,
  Clock,
  CheckCircle2,
  AlertCircle,
  FileVideo,
  Info,
  Cpu,
  Sparkles,
  RefreshCw,
  Shield,
} from 'lucide-react';

export default function FootageManager({
  camera,
  footageList,
  onUploadSuccess,
  onPlayFootage,
  onDeleteFootage,
  onAnalyzeFootage,
  onViewDetections,
  onViewAnpr,
  onRunAnpr,
}) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [description, setDescription] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState(null);
  const [uploadSuccessMsg, setUploadSuccessMsg] = useState(null);
  const fileInputRef = useRef(null);

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setUploadError(null);
      setUploadSuccessMsg(null);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setUploadError('Please select a video file to upload.');
      return;
    }

    setUploading(true);
    setUploadProgress(10);
    setUploadError(null);
    setUploadSuccessMsg(null);

    const formData = new FormData();
    formData.append('file', selectedFile);
    if (description.trim()) {
      formData.append('description', description.trim());
    }

    try {
      const xhr = new XMLHttpRequest();
      const uploadPromise = new Promise((resolve, reject) => {
        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable) {
            const percent = Math.round((event.loaded / event.total) * 90);
            setUploadProgress(percent);
          }
        });

        xhr.addEventListener('load', () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            setUploadProgress(100);
            try {
              const res = JSON.parse(xhr.responseText);
              resolve(res);
            } catch (err) {
              resolve(xhr.responseText);
            }
          } else {
            try {
              const errObj = JSON.parse(xhr.responseText);
              reject(new Error(errObj.detail || `Upload failed with status ${xhr.status}`));
            } catch (e) {
              reject(new Error(`Upload failed with status ${xhr.status}`));
            }
          }
        });

        xhr.addEventListener('error', () => {
          reject(new Error('Network error during video upload.'));
        });

        xhr.open('POST', `/api/cameras/${camera.id}/footage`);
        xhr.send(formData);
      });

      const result = await uploadPromise;
      setUploadSuccessMsg(`Successfully uploaded ${selectedFile.name}`);
      setSelectedFile(null);
      setDescription('');
      if (fileInputRef.current) fileInputRef.current.value = '';
      if (onUploadSuccess) onUploadSuccess(result);
    } catch (err) {
      setUploadError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Upload Section Box */}
      <div className="p-5 rounded-xl bg-[#070d18] border border-slate-800 shadow-inner">
        <div className="flex items-center space-x-2 text-white font-bold text-sm mb-3">
          <Upload className="w-4 h-4 text-amber-400" />
          <span>Upload CCTV Video Footage (Max 500 MB)</span>
        </div>

        <form onSubmit={handleUpload} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="sm:col-span-2">
              <label className="block text-slate-400 text-xs mb-1">
                Select Video File (.mp4, .avi, .mov, .mkv)
              </label>
              <input
                ref={fileInputRef}
                type="file"
                accept=".mp4,.avi,.mov,.mkv,.webm,video/*"
                onChange={handleFileChange}
                disabled={uploading}
                className="w-full text-xs text-slate-300 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-amber-600/20 file:text-amber-300 hover:file:bg-amber-600/30 file:cursor-pointer cursor-pointer border border-slate-700/80 rounded-lg bg-[#0b1424] p-1.5 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-slate-400 text-xs mb-1">
                Clip Description / Notes
              </label>
              <input
                type="text"
                placeholder="e.g. 15-min rush hour clip"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                disabled={uploading}
                className="w-full text-xs px-3 py-2 rounded-lg bg-[#0b1424] border border-slate-700/80 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500"
              />
            </div>
          </div>

          {/* Upload Progress Bar */}
          {uploading && (
            <div className="space-y-1.5 pt-1">
              <div className="flex justify-between text-[11px] font-mono text-amber-300">
                <span>Uploading to camera storage...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-amber-500 to-emerald-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
            </div>
          )}

          {/* Feedback Alerts */}
          {uploadError && (
            <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{uploadError}</span>
            </div>
          )}

          {uploadSuccessMsg && (
            <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 text-xs flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
              <span>{uploadSuccessMsg}</span>
            </div>
          )}

          <div className="flex items-center justify-between pt-1">
            <div className="text-[11px] text-slate-500 flex items-center space-x-1 font-mono">
              <Info className="w-3.5 h-3.5" />
              <span>Files are securely saved to storage/footage/camera_{camera.id}/</span>
            </div>

            <button
              type="submit"
              disabled={!selectedFile || uploading}
              className={`px-4 py-2 rounded-lg font-bold text-xs flex items-center space-x-1.5 transition ${
                !selectedFile || uploading
                  ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                  : 'bg-amber-600 hover:bg-amber-500 text-white shadow-lg shadow-amber-600/30'
              }`}
            >
              <Upload className="w-3.5 h-3.5" />
              <span>{uploading ? 'Uploading Footage...' : 'Upload Video File'}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Footage List Table */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <Film className="w-4 h-4 text-blue-400" />
            <h3 className="text-sm font-bold text-white">
              Associated CCTV Footage Clips ({footageList?.length || 0})
            </h3>
          </div>
        </div>

        {(!footageList || footageList.length === 0) ? (
          <div className="p-8 rounded-xl bg-[#070d18] border border-slate-800 text-center text-xs text-slate-400">
            <FileVideo className="w-10 h-10 text-slate-600 mx-auto mb-2" />
            <p className="font-semibold text-slate-300">No recorded footage uploaded</p>
            <p className="mt-1 text-slate-500">
              Upload local CCTV video files using the panel above to enable AI vehicle analytics.
            </p>
          </div>
        ) : (
          <div className="border border-slate-800 rounded-xl overflow-hidden bg-[#080f1c]">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 bg-[#050912] text-slate-400 font-mono">
                  <th className="py-2.5 px-3">Video File</th>
                  <th className="py-2.5 px-3">Size</th>
                  <th className="py-2.5 px-3">Resolution / FPS</th>
                  <th className="py-2.5 px-3">Uploaded At</th>
                  <th className="py-2.5 px-3">AI Status</th>
                  <th className="py-2.5 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {footageList.map((clip) => (
                  <tr key={clip.id} className="hover:bg-slate-800/30 transition">
                    <td className="py-3 px-3">
                      <div className="font-semibold text-white truncate max-w-[200px]" title={clip.original_file_name}>
                        {clip.original_file_name}
                      </div>
                      <div className="text-[10px] font-mono text-slate-500">
                        {clip.file_name}
                      </div>
                    </td>

                    <td className="py-3 px-3 font-mono text-slate-300">
                      {formatFileSize(clip.file_size)}
                    </td>

                    <td className="py-3 px-3 font-mono text-slate-300">
                      {clip.video_width && clip.video_height ? (
                        <span>{clip.video_width}×{clip.video_height} ({clip.fps || 30}fps)</span>
                      ) : (
                        <span>1080p (30fps)</span>
                      )}
                    </td>

                    <td className="py-3 px-3 text-slate-400 text-[11px]">
                      {new Date(clip.created_at).toLocaleDateString()} {new Date(clip.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>

                    <td className="py-3 px-3">
                      {clip.status === 'PROCESSING' ? (
                        <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-mono bg-blue-500/10 text-blue-300 border border-blue-500/30 animate-pulse">
                          <RefreshCw className="w-2.5 h-2.5 animate-spin" />
                          <span>PROCESSING</span>
                        </span>
                      ) : clip.status === 'COMPLETED' ? (
                        <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
                          <CheckCircle2 className="w-2.5 h-2.5 text-emerald-400" />
                          <span>AI COMPLETED</span>
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-400 border border-slate-700">
                          {clip.status || 'UPLOADED'}
                        </span>
                      )}
                    </td>

                    <td className="py-3 px-3 text-right">
                      <div className="flex items-center justify-end space-x-1.5">
                        {/* ANPR License Plate Recognition Button */}
                        <button
                          onClick={() => onViewAnpr && onViewAnpr(clip, camera)}
                          className="px-2.5 py-1 rounded bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 flex items-center space-x-1 font-semibold transition"
                          title="View ANPR Number Plate Intelligence & OCR"
                        >
                          <Shield className="w-3 h-3 text-amber-400" />
                          <span>ANPR</span>
                        </button>

                        {/* Analyze Vehicles / View Results Button */}
                        {clip.status === 'COMPLETED' ? (
                          <button
                            onClick={() => onViewDetections && onViewDetections(clip, camera)}
                            className="px-2.5 py-1 rounded bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 flex items-center space-x-1 font-semibold transition"
                            title="View YOLO Detections & Annotated Video"
                          >
                            <Cpu className="w-3 h-3 text-indigo-400" />
                            <span>Tracking</span>
                          </button>
                        ) : (
                          <button
                            onClick={() => onAnalyzeFootage && onAnalyzeFootage(clip, camera)}
                            className="px-2.5 py-1 rounded bg-indigo-600 hover:bg-indigo-500 text-white flex items-center space-x-1 font-bold transition shadow"
                            title="Run YOLO Vehicle Detection"
                          >
                            <Cpu className="w-3 h-3" />
                            <span>Analyze</span>
                          </button>
                        )}

                        {/* Play Raw Video */}
                        <button
                          onClick={() => onPlayFootage(clip)}
                          className="p-1.5 rounded bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 border border-blue-500/30 transition"
                          title="Play Raw Footage"
                        >
                          <Play className="w-3.5 h-3.5 fill-current" />
                        </button>

                        {/* Delete */}
                        <button
                          onClick={() => onDeleteFootage(clip)}
                          className="p-1.5 rounded bg-rose-600/10 hover:bg-rose-600/20 text-rose-400 border border-rose-500/30 transition"
                          title="Delete Video File"
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
        )}
      </div>

    </div>
  );
}
