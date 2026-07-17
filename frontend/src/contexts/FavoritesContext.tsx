import React, { createContext, useContext, useState } from "react";
import { ComparisonResult } from "../types";

interface FavoritesContextType {
  favorites: ComparisonResult[];
  addFavorite: (product: ComparisonResult) => void;
  removeFavorite: (productId: number) => void;
  isFavorite: (productId: number) => boolean;
}

const FavoritesContext = createContext<FavoritesContextType | undefined>(undefined);

export function FavoritesProvider({ children }: { children: React.ReactNode }) {
  const [favorites, setFavorites] = useState<ComparisonResult[]>(() => {
    const saved = localStorage.getItem("pricepilot_favorites");
    return saved ? JSON.parse(saved) : [];
  });

  const addFavorite = (product: ComparisonResult) => {
    setFavorites((prev) => {
      const next = [...prev, product];
      localStorage.setItem("pricepilot_favorites", JSON.stringify(next));
      return next;
    });
  };

  const removeFavorite = (productId: number) => {
    setFavorites((prev) => {
      const next = prev.filter((p) => p.id !== productId);
      localStorage.setItem("pricepilot_favorites", JSON.stringify(next));
      return next;
    });
  };

  const isFavorite = (productId: number) => favorites.some((p) => p.id === productId);

  return (
    <FavoritesContext.Provider value={{ favorites, addFavorite, removeFavorite, isFavorite }}>
      {children}
    </FavoritesContext.Provider>
  );
}

export function useFavorites() {
  const context = useContext(FavoritesContext);
  if (context === undefined) {
    throw new Error("useFavorites must be used within a FavoritesProvider");
  }
  return context;
}
