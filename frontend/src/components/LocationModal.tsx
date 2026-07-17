import React, { useState, useEffect, useRef } from "react";
import { useLocationStore, type LocationData } from "../contexts/LocationContext";
import { MapPin, Navigation, Search, Home, Briefcase, X, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "../lib/cn";

interface NominatimResult {
  place_id: number;
  lat: string;
  lon: string;
  display_name: string;
  address: {
    city?: string;
    state?: string;
    town?: string;
    village?: string;
    suburb?: string;
  };
}

export default function LocationModal() {
  const { location, setLocation, savedLocations, isModalOpen, setIsModalOpen } = useLocationStore();
  const [address, setAddress] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [suggestions, setSuggestions] = useState<NominatimResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  
  const searchTimeoutRef = useRef<NodeJS.Timeout>();

  const handleDetectLocation = () => {
    setLoading(true);
    setError("");
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          try {
            const res = await fetch(
              `https://nominatim.openstreetmap.org/reverse?format=json&lat=${position.coords.latitude}&lon=${position.coords.longitude}`
            );
            const data = await res.json();
            const city = data.address.city || data.address.town || data.address.village;
            setLocation({
              address: data.address.suburb || data.address.city_district || city || data.display_name,
              city: city,
              state: data.address.state,
              lat: position.coords.latitude,
              lon: position.coords.longitude,
              type: "gps"
            });
          } catch (err) {
            setError("Failed to fetch address. Try manually entering it.");
          } finally {
            setLoading(false);
          }
        },
        (err) => {
          setError("Location permission denied.");
          setLoading(false);
        },
        { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
      );
    } else {
      setError("Geolocation is not supported by your browser.");
      setLoading(false);
    }
  };

  const searchAddress = async (query: string) => {
    if (!query.trim()) {
      setSuggestions([]);
      return;
    }
    setIsSearching(true);
    try {
      const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&addressdetails=1&limit=5&countrycodes=in`);
      const data: NominatimResult[] = await res.json();
      setSuggestions(data);
    } catch (err) {
      console.error("Geocoding failed", err);
    } finally {
      setIsSearching(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setAddress(val);
    
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    
    if (val.trim().length > 2) {
      searchTimeoutRef.current = setTimeout(() => {
        searchAddress(val);
      }, 500);
    } else {
      setSuggestions([]);
    }
  };

  const handleSelectSuggestion = (suggestion: NominatimResult) => {
    const city = suggestion.address.city || suggestion.address.town || suggestion.address.village;
    setLocation({
      address: suggestion.display_name.split(",").slice(0, 3).join(","), // Shorter display name
      city: city,
      state: suggestion.address.state,
      lat: parseFloat(suggestion.lat),
      lon: parseFloat(suggestion.lon),
      type: "manual"
    });
  };

  const handleSelectSaved = (savedLoc: LocationData) => {
    setLocation(savedLoc);
  };

  return (
    <AnimatePresence>
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4">
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => location && setIsModalOpen(false)}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          />
          
          <motion.div 
            initial={{ opacity: 0, y: "100%" }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: "100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="relative w-full max-w-lg bg-white dark:bg-gray-900 rounded-t-3xl sm:rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-5 border-b border-gray-100 dark:border-gray-800">
              <div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">Select Location</h2>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">To check serviceability & prices</p>
              </div>
              {location && (
                <button 
                  onClick={() => setIsModalOpen(false)}
                  className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-gray-500"
                >
                  <X size={20} />
                </button>
              )}
            </div>

            <div className="p-5 overflow-y-auto custom-scrollbar">
              {error && (
                <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm rounded-xl border border-red-100 dark:border-red-900/30">
                  {error}
                </div>
              )}

              {/* Search Input */}
              <div className="relative mb-6">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                <input
                  type="text"
                  placeholder="Search your area, building, or pincode..."
                  value={address}
                  onChange={handleInputChange}
                  className="w-full bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl pl-12 pr-4 py-3.5 text-gray-900 dark:text-white placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all font-medium"
                />
                {isSearching && (
                  <Loader2 className="absolute right-4 top-1/2 -translate-y-1/2 text-blue-500 animate-spin" size={18} />
                )}
              </div>

              {/* Suggestions */}
              {suggestions.length > 0 ? (
                <div className="space-y-1 mb-6">
                  {suggestions.map((s, i) => (
                    <button
                      key={s.place_id}
                      onClick={() => handleSelectSuggestion(s)}
                      className="w-full text-left p-3 flex items-start gap-3 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-xl transition-colors"
                    >
                      <MapPin className="text-gray-400 shrink-0 mt-0.5" size={18} />
                      <div>
                        <p className="font-medium text-gray-900 dark:text-white line-clamp-1">{s.display_name.split(",")[0]}</p>
                        <p className="text-sm text-gray-500 dark:text-gray-400 line-clamp-1 mt-0.5">{s.display_name.substring(s.display_name.indexOf(",") + 1).trim()}</p>
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <>
                  {/* Current Location Button */}
                  <button
                    onClick={handleDetectLocation}
                    disabled={loading}
                    className="w-full flex items-center gap-4 p-4 mb-6 rounded-2xl border border-blue-100 dark:border-blue-900/50 bg-blue-50/50 dark:bg-blue-900/20 hover:bg-blue-50 dark:hover:bg-blue-900/40 transition-colors text-left group"
                  >
                    <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-800 text-blue-600 dark:text-blue-300 flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform">
                      {loading ? <Loader2 className="animate-spin" size={20} /> : <Navigation size={20} className="fill-current" />}
                    </div>
                    <div>
                      <p className="font-semibold text-blue-700 dark:text-blue-400">Use my current location</p>
                      <p className="text-sm text-blue-600/70 dark:text-blue-400/70 mt-0.5">Using GPS</p>
                    </div>
                  </button>

                  {/* Saved Locations */}
                  {savedLocations.length > 0 && (
                    <div>
                      <h3 className="text-sm font-bold text-gray-400 dark:text-gray-500 uppercase tracking-wider mb-3 px-1">Saved Locations</h3>
                      <div className="grid gap-3">
                        {savedLocations.map((loc, i) => (
                          <button
                            key={i}
                            onClick={() => handleSelectSaved(loc)}
                            className="flex items-center gap-4 p-3 rounded-xl border border-gray-100 dark:border-gray-800 hover:border-gray-300 dark:hover:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-all text-left group"
                          >
                            <div className="w-10 h-10 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 flex items-center justify-center shrink-0 group-hover:bg-white dark:group-hover:bg-gray-700 group-hover:shadow-sm transition-all">
                              {loc.label === 'Home' ? <Home size={18} /> : loc.label === 'Work' ? <Briefcase size={18} /> : <MapPin size={18} />}
                            </div>
                            <div className="flex-1 overflow-hidden">
                              <p className="font-semibold text-gray-900 dark:text-white">{loc.label || "Saved Location"}</p>
                              <p className="text-sm text-gray-500 dark:text-gray-400 truncate mt-0.5">{loc.address}</p>
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
