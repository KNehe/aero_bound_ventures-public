"use client";

import React from 'react';

const ConstructionBanner = () => {
    return (
        <div className="w-full bg-gradient-to-r from-amber-400 via-orange-500 to-amber-500 text-white py-2 px-4 text-center text-[10px] md:text-sm font-black uppercase tracking-widest flex items-center justify-center shadow-md relative overflow-hidden">
            {/* Glossy overlay effect */}
            <div className="absolute inset-0 bg-white/10 pointer-events-none"></div>

            <div className="flex items-center gap-3 relative z-10">
                <span className="flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-white"></span>
                </span>

                <p className="drop-shadow-sm flex items-center gap-1.5">
                    <span className="opacity-80">⚠️</span>
                    Web application still under construction
                    <span className="opacity-80">⚠️</span>
                </p>

                <span className="flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-white"></span>
                </span>
            </div>
        </div>
    );
};

export default ConstructionBanner;
