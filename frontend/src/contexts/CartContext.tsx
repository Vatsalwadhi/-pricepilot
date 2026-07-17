import React, { createContext, useContext, useState } from "react";

export interface CartItem {
  id: string;
  query: string;
  quantity: number;
}

interface CartContextType {
  cart: CartItem[];
  addToCart: (query: string) => void;
  removeFromCart: (id: string) => void;
  clearCart: () => void;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

export function CartProvider({ children }: { children: React.ReactNode }) {
  const [cart, setCart] = useState<CartItem[]>(() => {
    const saved = localStorage.getItem("pricepilot_cart");
    return saved ? JSON.parse(saved) : [];
  });

  const save = (newCart: CartItem[]) => {
    setCart(newCart);
    localStorage.setItem("pricepilot_cart", JSON.stringify(newCart));
  };

  const addToCart = (query: string) => {
    const existing = cart.find((c) => c.query.toLowerCase() === query.toLowerCase());
    if (existing) {
      save(
        cart.map((c) =>
          c.id === existing.id ? { ...c, quantity: c.quantity + 1 } : c
        )
      );
    } else {
      save([...cart, { id: Date.now().toString(), query, quantity: 1 }]);
    }
  };

  const removeFromCart = (id: string) => {
    save(cart.filter((c) => c.id !== id));
  };

  const clearCart = () => save([]);

  return (
    <CartContext.Provider value={{ cart, addToCart, removeFromCart, clearCart }}>
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const context = useContext(CartContext);
  if (context === undefined) {
    throw new Error("useCart must be used within a CartProvider");
  }
  return context;
}
