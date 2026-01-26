"use client";
import React, { useState, useMemo, useCallback, memo } from "react";
import { FaToilet, FaCoffee, FaDoorOpen, FaUserLock, FaLock, FaCheckCircle, FaExclamationTriangle } from "react-icons/fa";
import { MdExitToApp } from "react-icons/md";
import { GiPlaneWing } from "react-icons/gi";

// --- Types ---

interface Coordinate {
    x: number;
    y: number;
}

interface Price {
    total: string;
    currency: string;
}

interface TravelerPricing {
    travelerId: string;
    seatAvailabilityStatus: "AVAILABLE" | "OCCUPIED" | "BLOCKED";
    price?: Price;
}

interface Seat {
    number: string;
    coordinates: Coordinate;
    travelerPricing?: TravelerPricing[];
    characteristicsCodes?: string[];
    cabin?: string;
}

interface Facility {
    code: string;
    coordinates: Coordinate;
}

interface DeckConfiguration {
    width: number;
    length: number;
    startSeatRow?: number;
    endSeatRow?: number;
    startWingsX?: number;
    endWingsX?: number;
    startWingsRow?: number;
    endWingsRow?: number;
    exitRowsX?: number[];
}

interface Deck {
    deckConfiguration: DeckConfiguration;
    seats: Seat[];
    facilities: Facility[];
}

interface SeatMapProps {
    seatMapData: {
        decks: Deck[];
    };
    onSelectSeat: (travelerId: string, seatNumber: string, price?: Price) => void;
    selectedSeats: Record<string, string>;
    travelerId: string;
}

// --- Sub-components (Memoized for performance) ---

const SeatItem = memo(({
    seat,
    status,
    isSelected,
    onHover,
    onSelect,
    isExitRow,
    travelerPricing
}: {
    seat: Seat;
    status: string;
    isSelected: boolean;
    onHover: (seat: Seat | null) => void;
    onSelect: (seatNumber: string, price?: Price) => void;
    isExitRow: boolean;
    travelerPricing?: TravelerPricing;
}) => {
    const price = travelerPricing?.price;
    const isChargeable = !!price && parseFloat(price.total) > 0;


    const baseClasses = "relative w-full aspect-[4/5] flex flex-col items-center justify-center rounded-md border-2 transition-all duration-200 group";

    const statusClasses = {
        AVAILABLE: isChargeable
            ? "bg-indigo-50 border-indigo-200 text-indigo-700 hover:border-indigo-400 hover:shadow-md cursor-pointer"
            : "bg-emerald-50 border-emerald-200 text-emerald-700 hover:border-emerald-400 hover:shadow-md cursor-pointer",
        OCCUPIED: "bg-slate-100 border-slate-200 text-slate-400 cursor-not-allowed",
        BLOCKED: "bg-rose-50 border-rose-100 text-rose-300 cursor-not-allowed",
        SELECTED: "bg-indigo-600 border-indigo-700 text-white shadow-lg transform scale-105 z-20",
    };

    const currentStatus = isSelected ? "SELECTED" : status;
    const activeStatusClass = statusClasses[currentStatus as keyof typeof statusClasses] || statusClasses.AVAILABLE;

    return (
        <div className="relative group/seat w-full">
            <button
                type="button"
                onClick={() => (status === "AVAILABLE" || isSelected) && onSelect(seat.number, price)}
                onMouseEnter={() => onHover(seat)}
                onMouseLeave={() => onHover(null)}
                className={`${baseClasses} ${activeStatusClass} ${isExitRow ? 'ring-1 ring-amber-400' : ''}`}
            >
                <span className="text-[10px] font-bold tracking-tighter">{seat.number}</span>
                {isChargeable && !isSelected && status === "AVAILABLE" && (
                    <div className="text-[8px] opacity-80 font-medium">
                        {price.currency}{Math.round(parseFloat(price.total))}
                    </div>
                )}
                {isSelected && <FaCheckCircle className="absolute -top-1 -right-1 text-white bg-indigo-600 rounded-full text-[10px]" />}
                {isExitRow && (
                    <div className="absolute -bottom-1 w-full flex justify-center pointer-events-none">
                        <div className="h-[2px] w-5 bg-amber-400/60 rounded-full" />
                    </div>
                )}

                {/* Corner Indicators for features */}
                {seat.characteristicsCodes?.includes("W") && !isSelected && (
                    <div className="absolute top-0.5 right-0.5 w-1 h-1 bg-blue-300 rounded-full" title="Window" />
                )}
            </button>
        </div>
    );
});

SeatItem.displayName = "SeatItem";

const FacilityItem = memo(({ code }: { code: string }) => {
    const getIcon = () => {
        switch (code) {
            case "G": return <FaCoffee className="text-slate-400" title="Galley" />;
            case "LA": return <FaToilet className="text-slate-400" title="Lavatory" />;
            case "CL": return <FaLock className="text-slate-300" title="Closet" />;
            case "ST": return <FaDoorOpen className="text-slate-400" title="Stairs" />;
            default: return <div className="w-2 h-2 bg-slate-200 rounded-full" />;
        }
    };

    return (
        <div className="w-full aspect-square flex items-center justify-center bg-slate-50 rounded-lg border border-slate-100 shadow-inner overflow-hidden">
            <div className="text-lg opacity-60 grayscale hover:grayscale-0 transition-all hover:scale-110">
                {getIcon()}
            </div>
        </div>
    );
});

FacilityItem.displayName = "FacilityItem";

// --- Main Component ---

export default function SeatMap({ seatMapData, onSelectSeat, selectedSeats, travelerId }: SeatMapProps) {
    const [hoveredSeat, setHoveredSeat] = useState<Seat | null>(null);

    const deck = seatMapData?.decks?.[0];
    if (!deck) return (
        <div className="flex flex-col items-center justify-center p-12 bg-slate-50 rounded-2xl border-2 border-dashed border-slate-200">
            <FaExclamationTriangle className="text-slate-300 text-4xl mb-4" />
            <p className="text-slate-500 font-medium">No seat map available for this flight.</p>
        </div>
    );

    const { width, length, exitRowsX, startWingsX, endWingsX } = deck.deckConfiguration;

    // Row height calculation for absolute positioning (Seat height + gap)
    // Seat height = 42px * 1.25 (aspect 4:5) = 52.5px
    // Gap = 8px (gap-y-2)
    const ROW_HEIGHT = 60.5;
    const GRID_PADDING = 24; // p-6

    // Build grid once
    const seatGrid = useMemo(() => {
        const grid: (Seat | Facility | null)[][] = Array(length).fill(null).map(() => Array(width).fill(null));
        deck.seats?.forEach(s => {
            if (s.coordinates.x < length && s.coordinates.y < width) grid[s.coordinates.x][s.coordinates.y] = s;
        });
        deck.facilities?.forEach(f => {
            if (f.coordinates.x < length && (f.coordinates.y ?? 0) < width) grid[f.coordinates.x][f.coordinates.y ?? 0] = f;
        });
        return grid;
    }, [deck, width, length]);

    const handleSelect = useCallback((seatNumber: string, price?: Price) => {
        onSelectSeat(travelerId, seatNumber, price);
    }, [onSelectSeat, travelerId]);

    const handleHover = useCallback((seat: Seat | null) => {
        setHoveredSeat(seat);
    }, []);

    return (
        <div className="w-full flex flex-col lg:flex-row gap-8 items-start select-none">
            {/* Scrollable Map Area */}
            <div className="flex-1 w-full bg-slate-50 rounded-3xl p-8 border border-slate-200 shadow-sm overflow-hidden relative">

                {/* Legend & Summary Float (Moved to Top) */}
                <div className="mb-10 w-full max-w-4xl mx-auto grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 px-4 py-3 bg-white/60 backdrop-blur-md rounded-2xl border border-white/50 shadow-md">
                    <LegendItem color="bg-emerald-50 border-emerald-200 text-emerald-700" label="Free" />
                    <LegendItem color="bg-indigo-50 border-indigo-200 text-indigo-700" label="Preferred" />
                    <LegendItem color="bg-indigo-600 border-indigo-700 text-white" label="Selected" />
                    <LegendItem color="bg-slate-100 border-slate-200 text-slate-400" label="Occupied" icon={<FaUserLock size={10} />} />
                    <LegendItem color="bg-rose-50 border-rose-100 text-rose-300" label="Blocked" />
                    <LegendItem color="bg-slate-200/50 border-slate-300 text-slate-500" label="Wing" icon={<GiPlaneWing size={12} />} />
                </div>


                {/* Nose Section */}
                <div className="w-full flex flex-col items-center mb-12">

                    <div className="w-48 h-20 bg-white border border-slate-200 rounded-t-[100px] shadow-sm flex flex-col items-center justify-center relative">
                        <div className="absolute top-4 w-12 h-1 bg-slate-100 rounded-full" />
                        <span className="mt-4 text-[10px] font-bold text-slate-400 uppercase tracking-[0.2em]">Cockpit</span>
                    </div>
                </div>

                <div className="overflow-x-auto pb-8 custom-scrollbar">
                    <div
                        className="grid mx-auto relative gap-x-3 gap-y-2 p-6 bg-white rounded-2xl border border-slate-100 shadow-sm"
                        style={{
                            gridTemplateColumns: `repeat(${width}, 42px)`,
                            width: 'fit-content'
                        }}
                    >
                        {/* Wing Markers */}
                        {(startWingsX !== undefined && endWingsX !== undefined) && (
                            <>
                                {/* Left Wing */}
                                <div
                                    className="absolute left-[-45px] w-[35px] bg-indigo-50/80 rounded-l-2xl border-y-2 border-l-2 border-indigo-200 shadow-[inset_-4px_0_8px_-4px_rgba(0,0,0,0.05)] pointer-events-none flex flex-col items-center justify-center gap-4 transition-all duration-500"
                                    style={{
                                        top: `${startWingsX * ROW_HEIGHT + GRID_PADDING}px`,
                                        height: `${(endWingsX - startWingsX + 1) * ROW_HEIGHT - 8}px`
                                    }}
                                >
                                    <GiPlaneWing className="text-indigo-200 text-xl" />
                                    <div className="text-[10px] font-black text-indigo-300 vertical-text uppercase tracking-widest leading-none">WING</div>
                                    <GiPlaneWing className="text-indigo-200 text-xl scale-y-[-1]" />
                                </div>
                                {/* Right Wing */}
                                <div
                                    className="absolute right-[-45px] w-[35px] bg-indigo-50/80 rounded-r-2xl border-y-2 border-r-2 border-indigo-200 shadow-[inset_4px_0_8px_-4px_rgba(0,0,0,0.05)] pointer-events-none flex flex-col items-center justify-center gap-4 transition-all duration-500"
                                    style={{
                                        top: `${startWingsX * ROW_HEIGHT + GRID_PADDING}px`,
                                        height: `${(endWingsX - startWingsX + 1) * ROW_HEIGHT - 8}px`
                                    }}
                                >
                                    <GiPlaneWing className="text-indigo-200 text-xl scale-x-[-1]" />
                                    <div className="text-[10px] font-black text-indigo-300 vertical-text uppercase tracking-widest leading-none">WING</div>
                                    <GiPlaneWing className="text-indigo-200 text-xl scale-x-[-1] scale-y-[-1]" />
                                </div>
                                {/* Mid-Section Highlight */}
                                <div
                                    className="absolute left-0 right-0 bg-slate-100/30 border-y border-dashed border-slate-200 pointer-events-none"
                                    style={{
                                        top: `${startWingsX * ROW_HEIGHT + GRID_PADDING}px`,
                                        height: `${(endWingsX - startWingsX + 1) * ROW_HEIGHT - 8}px`
                                    }}
                                />
                            </>
                        )}

                        {/* Exit Row Indicators (Sides) */}
                        {exitRowsX?.map(x => (
                            <React.Fragment key={`exit-side-${x}`}>
                                {/* Left Exit Label */}
                                <div
                                    className="absolute left-[-105px] w-[55px] flex items-center gap-1.5 text-[10px] font-bold text-amber-600 bg-amber-50/90 py-1.5 px-2 rounded-lg border border-amber-200 shadow-sm pointer-events-none transition-all duration-300 hover:scale-105 z-30"
                                    style={{
                                        top: `${x * ROW_HEIGHT + GRID_PADDING + 8}px`,
                                    }}
                                >
                                    <MdExitToApp className="rotate-90 text-sm" />
                                    <span className="tracking-tight">EXIT</span>
                                </div>
                                {/* Right Exit Label */}
                                <div
                                    className="absolute right-[-105px] w-[55px] flex items-center justify-end gap-1.5 text-[10px] font-bold text-amber-600 bg-amber-50/90 py-1.5 px-2 rounded-lg border border-amber-200 shadow-sm pointer-events-none transition-all duration-300 hover:scale-105 z-30"
                                    style={{
                                        top: `${x * ROW_HEIGHT + GRID_PADDING + 8}px`,
                                    }}
                                >
                                    <span className="tracking-tight">EXIT</span>
                                    <MdExitToApp className="-rotate-90 text-sm" />
                                </div>

                                {/* Row Highlight Line */}
                                <div
                                    className="absolute left-[-45px] right-[-45px] h-[2px] bg-amber-100/50 border-y border-amber-200/30 pointer-events-none"
                                    style={{
                                        top: `${x * ROW_HEIGHT + GRID_PADDING + 26}px`,
                                    }}
                                />
                            </React.Fragment>
                        ))}


                        {seatGrid.map((row, x) => {
                            const isExitRow = exitRowsX?.includes(x);
                            return row.map((cell, y) => {
                                if (!cell) return <div key={`void-${x}-${y}`} className="w-10" />;

                                if ("code" in cell) {
                                    return <FacilityItem key={`fac-${x}-${y}`} code={cell.code} />;
                                }

                                const pricing = cell.travelerPricing?.find(p => p.travelerId === travelerId) || cell.travelerPricing?.[0];
                                const isSelected = Object.values(selectedSeats).includes(cell.number);


                                return (
                                    <div key={cell.number} className="relative">
                                        <SeatItem
                                            seat={cell}
                                            status={pricing?.seatAvailabilityStatus || cell.travelerPricing?.[0]?.seatAvailabilityStatus || 'AVAILABLE'}
                                            isSelected={isSelected}
                                            onHover={handleHover}
                                            onSelect={handleSelect}
                                            isExitRow={!!isExitRow}
                                            travelerPricing={pricing}
                                        />
                                        {isExitRow && y === 0 && (
                                            <span className="absolute -left-6 top-1/2 -translate-y-1/2 text-[7px] font-black text-rose-500 uppercase tracking-tighter vertical-text leading-none opacity-60">EXIT</span>
                                        )}
                                        {isExitRow && y === width - 1 && (
                                            <span className="absolute -right-6 top-1/2 -translate-y-1/2 text-[7px] font-black text-rose-500 uppercase tracking-tighter vertical-text leading-none opacity-60">EXIT</span>
                                        )}
                                    </div>
                                );


                            });
                        })}
                    </div>
                </div>
            </div>

            {/* Sidebar Details - Glassmorphism */}

            <div className="w-full lg:w-80 shrink-0 space-y-4 sticky top-4">
                <div className="bg-white/80 backdrop-blur-md p-6 rounded-3xl border border-slate-200 shadow-xl overflow-hidden relative">
                    <div className="absolute top-0 left-0 w-1 h-full bg-indigo-500" />

                    <h4 className="text-slate-900 font-bold mb-4 flex items-center justify-between">
                        Selection Details
                        {selectedSeats[travelerId] && <span className="text-[10px] bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full uppercase tracking-tighter">Verified</span>}
                    </h4>

                    {hoveredSeat ? (
                        <div className="space-y-4 animate-in fade-in slide-in-from-right-2 duration-200">
                            <div>
                                <div className="text-4xl font-extrabold text-slate-900 leading-none">{hoveredSeat.number}</div>
                                <div className="text-slate-500 text-xs font-medium uppercase mt-1 tracking-widest">
                                    {Object.entries(selectedSeats).find(([_, seat]) => seat === hoveredSeat.number)?.[0]
                                        ? `Assigned to Passenger ${Object.entries(selectedSeats).find(([_, seat]) => seat === hoveredSeat.number)?.[0]}`
                                        : hoveredSeat.cabin || "Economy Class"}
                                </div>
                            </div>


                            <div className="flex flex-wrap gap-2">
                                {hoveredSeat.characteristicsCodes?.map(c => (
                                    <span key={c} className="text-[10px] bg-slate-100 text-slate-600 px-2 py-1 rounded font-bold">
                                        {getFeatureLabel(c)}
                                    </span>
                                ))}
                            </div>

                            <div className="pt-4 border-t border-slate-100">
                                <div className="flex justify-between items-end">
                                    <span className="text-slate-400 text-xs font-bold uppercase">Base Fare</span>
                                    <span className="text-2xl font-black text-indigo-600">
                                        {(() => {
                                            const p = hoveredSeat.travelerPricing?.find(tp => tp.travelerId === travelerId) || hoveredSeat.travelerPricing?.[0];
                                            return p?.price ? `${p.price.currency} ${p.price.total}` : "FREE";
                                        })()}
                                    </span>
                                </div>
                            </div>


                            <p className="text-[10px] text-slate-400 leading-relaxed italic border-l-2 border-slate-100 pl-3">
                                * Prices are verified in real-time. Final totals include taxes and airport fees where applicable.
                            </p>
                        </div>
                    ) : (
                        <div className="py-12 flex flex-col items-center justify-center text-center space-y-4">
                            <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center text-slate-200">
                                <FaCheckCircle size={32} />
                            </div>
                            <p className="text-sm text-slate-400 italic">Hover over a seat to view features and pricing details.</p>
                        </div>
                    )}
                </div>

                {/* Selected Summary */}
                {selectedSeats[travelerId] && (
                    <div className="bg-indigo-600 p-6 rounded-3xl text-white shadow-lg animate-in zoom-in-95 duration-300">
                        <div className="uppercase text-[10px] font-bold tracking-widest opacity-80 mb-1">Traveler Assignment</div>
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center font-bold text-xl">
                                {selectedSeats[travelerId]}
                            </div>
                            <div>
                                <div className="font-bold">Passenger {travelerId}</div>
                                <div className="text-xs opacity-80">Seat reserved and locked</div>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            <style jsx>{`
                .vertical-text {
                    writing-mode: vertical-rl;
                    text-orientation: mixed;
                }
                .custom-scrollbar::-webkit-scrollbar {
                    height: 8px;
                }
                .custom-scrollbar::-webkit-scrollbar-track {
                    background: transparent;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background: #e2e8f0;
                    border-radius: 10px;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                    background: #cbd5e1;
                }
            `}</style>
        </div>
    );
}

// --- Helpers ---

function LegendItem({ color, label, icon }: { color: string; label: string; icon?: React.ReactNode }) {
    return (
        <div className="flex items-center gap-2">
            <div className={`w-4 h-4 rounded border ${color} flex items-center justify-center`}>
                {icon}
            </div>
            <span className="text-[11px] font-bold text-slate-500 tracking-tight">{label}</span>
        </div>
    );
}

function getFeatureLabel(code: string) {
    const map: Record<string, string> = {
        'W': 'Window',
        'A': 'Aisle',
        'E': 'Exit Row',
        'L': 'Legroom+',
        'K': 'Bulkhead',
        'O': 'Standard',
        'EK': 'Blocked',
    };
    return map[code] || code;
}
