import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

type MemoryState = {
  diet: string;
  budget: string;
  preferredPlatforms: string[];
  favoriteBrands: string[];
  avoidBrands: string[];
  deliverySpeedPreference: string;
  customNotes: string;
};

const defaultMemory: MemoryState = {
  diet: '',
  budget: '',
  preferredPlatforms: [],
  favoriteBrands: [],
  avoidBrands: [],
  deliverySpeedPreference: 'Fastest',
  customNotes: ''
};

type MemoryContextType = {
  memory: MemoryState;
  updateMemory: (newMemory: Partial<MemoryState>) => void;
  clearMemory: () => void;
};

const MemoryContext = createContext<MemoryContextType | undefined>(undefined);

export function MemoryProvider({ children }: { children: ReactNode }) {
  const [memory, setMemory] = useState<MemoryState>(() => {
    try {
      const stored = localStorage.getItem('pricepilot_memory');
      return stored ? { ...defaultMemory, ...JSON.parse(stored) } : defaultMemory;
    } catch {
      return defaultMemory;
    }
  });

  useEffect(() => {
    localStorage.setItem('pricepilot_memory', JSON.stringify(memory));
  }, [memory]);

  const updateMemory = (newMemory: Partial<MemoryState>) => {
    setMemory(prev => ({ ...prev, ...newMemory }));
  };

  const clearMemory = () => {
    setMemory(defaultMemory);
  };

  return (
    <MemoryContext.Provider value={{ memory, updateMemory, clearMemory }}>
      {children}
    </MemoryContext.Provider>
  );
}

export function useMemory() {
  const context = useContext(MemoryContext);
  if (context === undefined) {
    throw new Error('useMemory must be used within a MemoryProvider');
  }
  return context;
}
