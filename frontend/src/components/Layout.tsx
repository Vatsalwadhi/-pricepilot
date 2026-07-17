import { History, Search, ShoppingBasket, MapPin, Heart, Moon, Sun, ShoppingCart, Menu, X, ChevronDown, BrainCircuit } from "lucide-react";
import { type ReactNode, useState, useEffect } from "react";
import { NavLink, useLocation } from "react-router-dom";
import LocationModal from "./LocationModal";
import { useLocationStore } from "../contexts/LocationContext";
import { useTheme } from "../contexts/ThemeContext";
import { useCart } from "../contexts/CartContext";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "../lib/cn";

type LayoutProps = {
  children: ReactNode;
};

export default function Layout({ children }: LayoutProps) {
  const { location, setIsModalOpen } = useLocationStore();
  const { isDarkMode, toggleTheme } = useTheme();
  const { cart } = useCart();
  const routerLocation = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Close mobile menu on route change
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [routerLocation.pathname]);

  const navLinks = [
    { to: "/", icon: Search, label: "Search" },
    { to: "/ai-shopping", icon: BrainCircuit, label: "AI Shopping" },
    { to: "/history", icon: History, label: "History" },
    { to: "/favorites", icon: Heart, label: "Favorites" },
    { to: "/memory", icon: BrainCircuit, label: "AI Memory" },
  ];

  return (
    <div className="min-h-screen bg-mist dark:bg-gray-950 text-gray-900 dark:text-gray-100 transition-colors duration-200 font-sans">
      <LocationModal />
      
      <header className="sticky top-0 z-40 w-full glass-nav">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
          
          {/* Logo & Location */}
          <div className="flex items-center gap-4 sm:gap-6">
            {/* Mobile Menu Toggle */}
            <button 
              className="sm:hidden p-2 -ml-2 rounded-xl text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
              onClick={() => setMobileMenuOpen(true)}
            >
              <Menu size={22} />
            </button>

            <NavLink to="/" className="flex items-center gap-2.5 group">
              <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-tr from-blue-600 to-blue-500 text-white shadow-lg shadow-blue-500/30 group-hover:shadow-blue-500/50 group-hover:scale-105 transition-all duration-300">
                <ShoppingBasket size={22} aria-hidden="true" />
              </span>
              <span className="hidden lg:block text-xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-gray-900 to-gray-600 dark:from-white dark:to-gray-300 font-display">
                PricePilot
              </span>
            </NavLink>

            <div className="h-8 w-px bg-gray-200 dark:bg-gray-800 hidden sm:block mx-1"></div>

            {/* Location Chip */}
            <button 
              onClick={() => setIsModalOpen(true)}
              className="flex items-center gap-2 group text-left"
            >
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 group-hover:bg-blue-100 dark:group-hover:bg-blue-900/40 transition-colors">
                <MapPin size={18} className="fill-blue-600/20" />
              </div>
              <div className="flex flex-col">
                <span className="text-[11px] font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400 flex items-center gap-1">
                  Deliver to <ChevronDown size={12} className="text-gray-400 group-hover:text-blue-500 transition-colors" />
                </span>
                <span className="text-sm font-semibold text-gray-900 dark:text-white max-w-[120px] sm:max-w-[200px] truncate leading-tight">
                  {location ? (location.label || location.city || location.address.split(',')[0]) : "Select Location"}
                </span>
              </div>
            </button>
          </div>

          {/* Desktop Nav */}
          <nav className="hidden sm:flex items-center gap-2">
            {navLinks.map((link) => (
              <NavLink 
                key={link.to} 
                to={link.to} 
                className={({ isActive }) => cn(
                  "flex items-center gap-2 px-3 py-2 rounded-xl transition-all font-medium text-sm",
                  isActive 
                    ? "text-blue-700 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/20" 
                    : "text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800"
                )}
              >
                <link.icon size={18} />
                <span>{link.label}</span>
              </NavLink>
            ))}
            
            <div className="h-6 w-px bg-gray-200 dark:bg-gray-800 mx-1"></div>

            <button 
              onClick={toggleTheme} 
              className="p-2.5 rounded-xl text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              aria-label="Toggle theme"
            >
              {isDarkMode ? <Sun size={18} /> : <Moon size={18} />}
            </button>

            <NavLink 
              to="/cart" 
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gray-900 dark:bg-white text-white dark:text-gray-900 hover:bg-gray-800 dark:hover:bg-gray-100 transition-all font-medium text-sm ml-2 shadow-sm hover:shadow-md"
            >
              <div className="relative">
                <ShoppingCart size={18} />
                {cart.length > 0 && (
                  <span className="absolute -top-1.5 -right-1.5 w-4 h-4 bg-red-500 text-white text-[10px] font-bold flex items-center justify-center rounded-full ring-2 ring-gray-900 dark:ring-white">
                    {cart.length}
                  </span>
                )}
              </div>
              <span className="hidden md:block">Basket</span>
            </NavLink>
          </nav>

          {/* Mobile Cart Button (Navbar) */}
          <NavLink 
            to="/cart" 
            className="sm:hidden relative p-2 rounded-xl text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <ShoppingCart size={22} />
            {cart.length > 0 && (
              <span className="absolute top-1 right-1 w-4 h-4 bg-red-500 text-white text-[10px] font-bold flex items-center justify-center rounded-full ring-2 ring-white dark:ring-gray-900">
                {cart.length}
              </span>
            )}
          </NavLink>
        </div>
      </header>

      {/* Mobile Sidebar Overlay */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <>
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setMobileMenuOpen(false)}
              className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm sm:hidden"
            />
            <motion.div 
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="fixed inset-y-0 left-0 z-50 w-72 bg-white dark:bg-gray-900 shadow-2xl sm:hidden flex flex-col"
            >
              <div className="p-5 flex items-center justify-between border-b border-gray-100 dark:border-gray-800">
                <div className="flex items-center gap-2.5">
                  <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white">
                    <ShoppingBasket size={18} />
                  </span>
                  <span className="text-lg font-bold font-display">PricePilot</span>
                </div>
                <button 
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full"
                >
                  <X size={20} />
                </button>
              </div>

              <div className="p-4 flex-1 overflow-y-auto space-y-1">
                {navLinks.map((link) => (
                  <NavLink 
                    key={link.to} 
                    to={link.to}
                    className={({ isActive }) => cn(
                      "flex items-center gap-3 px-4 py-3 rounded-xl transition-colors font-medium",
                      isActive 
                        ? "text-blue-700 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/20" 
                        : "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
                    )}
                  >
                    <link.icon size={20} />
                    {link.label}
                  </NavLink>
                ))}
              </div>

              <div className="p-4 border-t border-gray-100 dark:border-gray-800">
                <button 
                  onClick={toggleTheme}
                  className="w-full flex items-center justify-between px-4 py-3 rounded-xl text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors font-medium"
                >
                  <div className="flex items-center gap-3">
                    {isDarkMode ? <Sun size={20} /> : <Moon size={20} />}
                    Theme
                  </div>
                  <span className="text-sm text-gray-500">{isDarkMode ? 'Dark' : 'Light'}</span>
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      <main className="w-full relative z-10">{children}</main>
    </div>
  );
}
