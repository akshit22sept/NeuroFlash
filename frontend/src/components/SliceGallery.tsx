import React, { useState } from "react";

interface SliceData {
    slice_num: number;
    lesion_voxels: number;
    stroke_voxels: number;
    hemorrhage_voxels: number;
    axis: string;
    image_data?: string;  // Base64 encoded PNG
}

interface SliceGalleryProps {
    slices: SliceData[];
    fileId: string;
}

export default function SliceGallery({ slices, fileId }: SliceGalleryProps) {
    const [selectedSlice, setSelectedSlice] = useState<number | null>(null);

    const handlePrevious = () => {
        if (selectedSlice !== null && selectedSlice > 0) {
            setSelectedSlice(selectedSlice - 1);
        }
    };

    const handleNext = () => {
        if (selectedSlice !== null && selectedSlice < slices.length - 1) {
            setSelectedSlice(selectedSlice + 1);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'ArrowLeft') handlePrevious();
        if (e.key === 'ArrowRight') handleNext();
        if (e.key === 'Escape') setSelectedSlice(null);
    };

    return (
        <>
            {/* Thumbnail Grid */}
            <div className="grid grid-cols-3 gap-4">
                {slices.map((slice, idx) => (
                    <div
                        key={idx}
                        onClick={() => setSelectedSlice(idx)}
                        className="relative cursor-pointer group overflow-hidden rounded-lg border-2 border-slate-700 hover:border-blue-500 transition-all duration-300"
                        style={{
                            background: 'linear-gradient(135deg, #1e293b, #334155)',
                        }}
                    >
                        {/* Slice Image */}
                        <div className="aspect-square bg-slate-800 flex items-center justify-center relative overflow-hidden">
                            <img
                                src={slice.image_data || 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="200"%3E%3Crect fill="%23374151" width="200" height="200"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" fill="%239ca3af" font-size="14" dy=".3em"%3ESlice %23' + slice.slice_num + '%3C/text%3E%3C/svg%3E'}
                                alt={`Slice #${slice.slice_num}`}
                                className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
                            />

                            {/* Overlay on hover */}
                            <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                <span className="text-white font-bold">🔍 View</span>
                            </div>
                        </div>

                        {/* Info Badge */}
                        <div className="absolute top-2 left-2 bg-slate-950/80 backdrop-blur-sm px-2 py-1 rounded-md">
                            <p className="text-xs text-white font-bold">#{slice.slice_num}</p>
                        </div>

                        {/* Voxel Count Badge */}
                        <div className="absolute bottom-0 left-0 right-0 bg-slate-950/80 backdrop-blur-sm px-2 py-1">
                            <p className="text-xs text-slate-300">
                                {slice.lesion_voxels} voxels
                            </p>
                            <div className="flex gap-2 text-[10px] mt-0.5">
                                {slice.stroke_voxels > 0 && (
                                    <span className="text-cyan-400">S: {slice.stroke_voxels}</span>
                                )}
                                {slice.hemorrhage_voxels > 0 && (
                                    <span className="text-red-400">H: {slice.hemorrhage_voxels}</span>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Lightbox Modal */}
            {selectedSlice !== null && (
                <div
                    className="fixed inset-0 z-50 bg-black/95 backdrop-blur-sm flex items-center justify-center"
                    onClick={() => setSelectedSlice(null)}
                    onKeyDown={handleKeyDown}
                    tabIndex={0}
                >
                    <div className="relative w-full h-full flex items-center justify-center p-8">
                        {/* Close Button */}
                        <button
                            onClick={() => setSelectedSlice(null)}
                            className="absolute top-4 right-4 z-10 w-12 h-12 flex items-center justify-center rounded-full bg-red-500/80 hover:bg-red-500 text-white font-bold text-2xl transition-all"
                        >
                            ×
                        </button>

                        {/* Previous Button */}
                        {selectedSlice > 0 && (
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    handlePrevious();
                                }}
                                className="absolute left-4 z-10 w-12 h-12 flex items-center justify-center rounded-full bg-slate-700/80 hover:bg-slate-600 text-white font-bold text-2xl transition-all"
                            >
                                ‹
                            </button>
                        )}

                        {/* Next Button */}
                        {selectedSlice < slices.length - 1 && (
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    handleNext();
                                }}
                                className="absolute right-4 z-10 w-12 h-12 flex items-center justify-center rounded-full bg-slate-700/80 hover:bg-slate-600 text-white font-bold text-2xl transition-all"
                            >
                                ›
                            </button>
                        )}

                        {/* Large Image */}
                        <div
                            className="relative max-w-4xl max-h-full"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <img
                                src={slices[selectedSlice].image_data || 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="800" height="800"%3E%3Crect fill="%23374151" width="800" height="800"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" fill="%239ca3af" font-size="24" dy=".3em"%3ESlice %23' + slices[selectedSlice].slice_num + '%3C/text%3E%3C/svg%3E'}
                                alt={`Slice #${slices[selectedSlice].slice_num}`}
                                className="max-w-full max-h-[80vh] object-contain rounded-lg border-2 border-slate-600 shadow-2xl"
                            />

                            {/* Info Overlay */}
                            <div className="absolute bottom-4 left-4 right-4 bg-slate-950/90 backdrop-blur-md rounded-lg p-4 border border-slate-700">
                                <div className="flex justify-between items-center">
                                    <div>
                                        <h3 className="text-white font-bold text-lg">Slice #{slices[selectedSlice].slice_num}</h3>
                                        <p className="text-slate-400 text-sm">{slices[selectedSlice].lesion_voxels} total voxels</p>
                                    </div>
                                    <div className="flex gap-4">
                                        {slices[selectedSlice].stroke_voxels > 0 && (
                                            <div className="text-center">
                                                <p className="text-cyan-400 font-bold">{slices[selectedSlice].stroke_voxels}</p>
                                                <p className="text-slate-500 text-xs">Stroke</p>
                                            </div>
                                        )}
                                        {slices[selectedSlice].hemorrhage_voxels > 0 && (
                                            <div className="text-center">
                                                <p className="text-red-400 font-bold">{slices[selectedSlice].hemorrhage_voxels}</p>
                                                <p className="text-slate-500 text-xs">Hemorrhage</p>
                                            </div>
                                        )}
                                    </div>
                                </div>
                                <p className="text-slate-500 text-xs mt-2">
                                    Use ← → arrow keys to navigate • Press ESC to close
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
