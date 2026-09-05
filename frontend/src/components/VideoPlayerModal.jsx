import React, { useState } from 'react';
import { X, Play, Film, HardDrive, Clock, Maximize2, AlertCircle, CheckCircle } from 'lucide-react';

export default function VideoPlayerModal({ isOpen, onClose, footage, camera, initialSeekTime }) {
  const [videoError, setVideoError] = useState(false);
  const videoRef = React.useRef(null);

  React.useEffect(() => {
    if (videoRef.current && initialSeekTime !== undefined && initialSeekTime !== null) {
      videoRef.current.currentTime = initialSeekTime;
    }
  }, [initialSeekTime, footage]);

  if (!isOpen || !footage) return null;

  const streamUrl = footage.stream_url || `/api/footage/${footage.id}/stream`;

  const handleLoadedMetadata = () => {
    if (videoRef.current && initialSeekTime !== undefined && initialSeekTime !== null) {
      videoRef.current.currentTime = initialSeekTime;
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md overflow-y-auto">
      <div className="bg-[#0b1424] border border-slate-700 rounded-2xl w-full max-w-4xl shadow-2xl overflow-hidden my-6">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-[#080f1c]">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-amber-500/20 border border-amber-500/40 text-amber-400">
              <Film className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-base font-bold text-white tracking-tight">
                  {footage.original_file_name}
                </h2>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-blue-500/20 text-blue-300 border border-blue-500/30">
                  {camera?.camera_code || `Camera #${footage.camera_id}`}
                </span>
              </div>
              <p className="text-xs text-slate-400">
                {camera?.location_name} • Gujarat Police CCTV Feed Player
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

        {/* Video Player Box */}
        <div className="bg-black relative aspect-video flex items-center justify-center overflow-hidden border-b border-slate-800">
          {!videoError ? (
            <video
              ref={videoRef}
              key={footage.id}
              controls
              autoPlay
              onLoadedMetadata={handleLoadedMetadata}
              className="w-full h-full object-contain"
              onError={() => setVideoError(true)}
            >
              <source src={streamUrl} type={footage.mime_type || 'video/mp4'} />
              Your browser does not support HTML5 video streaming.
            </video>
          ) : (
            <div className="p-8 text-center max-w-md">
              <AlertCircle className="w-12 h-12 text-amber-400 mx-auto mb-3" />
              <h3 className="text-base font-semibold text-white">
                Preview Unavailable in Browser
              </h3>
              <p className="text-xs text-slate-400 mt-2">
                This video file format or codec is not directly supported by your web browser. 
                The raw file is securely saved on the platform storage and will be processed by OpenCV / AI in Milestone 4.
              </p>
              <div className="mt-4 inline-flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-800 text-xs font-mono text-slate-300">
                <span>Safe Storage ID: {footage.file_name}</span>
              </div>
            </div>
          )}
        </div>

        {/* Metadata Bar */}
        <div className="p-6 bg-[#080f1c] text-xs space-y-4">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-3 rounded-lg bg-[#050912] border border-slate-800/80">
              <span className="text-slate-500 font-mono">FILE SIZE</span>
              <div className="text-sm font-bold text-white font-mono mt-0.5">
                {formatFileSize(footage.file_size)}
              </div>
            </div>

            <div className="p-3 rounded-lg bg-[#050912] border border-slate-800/80">
              <span className="text-slate-500 font-mono">RESOLUTION</span>
              <div className="text-sm font-bold text-cyan-400 font-mono mt-0.5">
                {footage.video_width && footage.video_height
                  ? `${footage.video_width} × ${footage.video_height}`
                  : '1920 × 1080 (HD)'}
              </div>
            </div>

            <div className="p-3 rounded-lg bg-[#050912] border border-slate-800/80">
              <span className="text-slate-500 font-mono">FRAME RATE / FPS</span>
              <div className="text-sm font-bold text-emerald-400 font-mono mt-0.5">
                {footage.fps ? `${footage.fps} FPS` : '30.0 FPS'}
              </div>
            </div>

            <div className="p-3 rounded-lg bg-[#050912] border border-slate-800/80">
              <span className="text-slate-500 font-mono">STATUS</span>
              <div className="text-sm font-bold text-amber-400 font-mono mt-0.5 flex items-center space-x-1">
                <span className="w-2 h-2 rounded-full bg-amber-400"></span>
                <span>{footage.status || 'UPLOADED'}</span>
              </div>
            </div>
          </div>

          {footage.description && (
            <div className="p-3 rounded-lg bg-[#050912] border border-slate-800/80">
              <span className="text-slate-500 font-mono">NOTES / DESCRIPTION</span>
              <p className="text-slate-300 mt-1">{footage.description}</p>
            </div>
          )}

          <div className="flex items-center justify-between pt-2 border-t border-slate-800 text-[11px] text-slate-500 font-mono">
            <span>Storage Path: {footage.file_path}</span>
            <span>Uploaded: {new Date(footage.created_at).toLocaleString()}</span>
          </div>
        </div>

      </div>
    </div>
  );
}
