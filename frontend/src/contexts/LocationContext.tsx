import React, { createContext, useContext, useState, useEffect } from "react";

export interface LocationData {
  address: string;
  city?: string;
  state?: string;
  lat: number | null;
  lon: number | null;
  label?: string; // 'Home', 'Work', etc.
  type?: 'gps' | 'saved' | 'manual';
}

interface LocationContextType {
  location: LocationData | null;
  setLocation: (loc: LocationData | null) => void;
  savedLocations: LocationData[];
  addSavedLocation: (loc: LocationData) => void;
  removeSavedLocation: (label: string) => void;
  isModalOpen: boolean;
  setIsModalOpen: (isOpen: boolean) => void;
}

const LocationContext = createContext<LocationContextType | undefined>(undefined);

export function LocationProvider({ children }: { children: React.ReactNode }) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  const [location, setLocationState] = useState<LocationData | null>(() => {
    const saved = localStorage.getItem("pricepilot_location");
    return saved ? JSON.parse(saved) : null;
  });

  const [savedLocations, setSavedLocations] = useState<LocationData[]>(() => {
    const saved = localStorage.getItem("pricepilot_saved_locations");
    return saved ? JSON.parse(saved) : [
      { address: "Sector 62, Noida, Uttar Pradesh", city: "Noida", state: "Uttar Pradesh", lat: 28.6273928, lon: 77.3712255, label: "Work", type: "saved" }
    ];
  });

  const setLocation = (loc: LocationData | null) => {
    setLocationState(loc);
    if (loc) {
      localStorage.setItem("pricepilot_location", JSON.stringify(loc));
      setIsModalOpen(false);
    } else {
      localStorage.removeItem("pricepilot_location");
    }
  };

  const addSavedLocation = (loc: LocationData) => {
    setSavedLocations(prev => {
      const filtered = prev.filter(p => p.label !== loc.label);
      const updated = [...filtered, loc];
      localStorage.setItem("pricepilot_saved_locations", JSON.stringify(updated));
      return updated;
    });
  };

  const removeSavedLocation = (label: string) => {
    setSavedLocations(prev => {
      const updated = prev.filter(p => p.label !== label);
      localStorage.setItem("pricepilot_saved_locations", JSON.stringify(updated));
      return updated;
    });
  };

  // Ensure modal is open if no location exists on mount
  useEffect(() => {
    if (!location) {
      setIsModalOpen(true);
    }
  }, [location]);

  return (
    <LocationContext.Provider value={{ 
      location, 
      setLocation, 
      savedLocations, 
      addSavedLocation, 
      removeSavedLocation,
      isModalOpen,
      setIsModalOpen
    }}>
      {children}
    </LocationContext.Provider>
  );
}

export function useLocationStore() {
  const context = useContext(LocationContext);
  if (context === undefined) {
    throw new Error("useLocationStore must be used within a LocationProvider");
  }
  return context;
}
