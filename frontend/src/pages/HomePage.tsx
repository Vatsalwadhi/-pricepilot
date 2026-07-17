import React, { useState, useRef, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Search, MapPin, TrendingUp, ShoppingBag, Zap, ListChecks, ArrowRight } from "lucide-react";
import { useLocationStore } from "../contexts/LocationContext";
import { motion } from "framer-motion";
import { POPULAR_SEARCHES } from "../lib/constants";
import SearchDropdown from "../components/SearchDropdown";
import { cn } from "../lib/cn";

export default function HomePage() {
  const [query, setQuery] = useState("");
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const navigate = useNavigate();
  const { location, setIsModalOpen } = useLocationStore();
  const formRef = useRef<HTMLFormElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (formRef.current && !formRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const saveRecentSearch = (term: string) => {
    try {
      const saved = localStorage.getItem("pricepilot_recent_searches");
      let recent = saved ? JSON.parse(saved) : [];
      recent = [term, ...recent.filter((t: string) => t !== term)].slice(0, 5);
      localStorage.setItem("pricepilot_recent_searches", JSON.stringify(recent));
    } catch (e) { }
  };

  const executeSearch = (term: string) => {
    if (!term.trim()) return;
    
    if (!location) {
      setIsModalOpen(true);
      return;
    }

    saveRecentSearch(term.trim());
    setIsDropdownOpen(false);
    navigate(`/results/${encodeURIComponent(term.trim())}`);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    executeSearch(query);
  };

  return (
    <div className="relative overflow-hidden min-h-[calc(100vh-64px)] flex flex-col items-center justify-center py-20 px-4 sm:px-6 lg:px-8">
      {/* Animated Background Gradients */}
      <div className="absolute top-10 -left-10 w-96 h-96 bg-purple-400 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob dark:opacity-20 dark:bg-purple-900"></div>
      <div className="absolute top-10 -right-10 w-96 h-96 bg-yellow-300 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-2000 dark:opacity-20 dark:bg-yellow-700"></div>
      <div className="absolute -bottom-10 left-20 w-96 h-96 bg-pink-400 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-4000 dark:opacity-20 dark:bg-pink-900"></div>

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="relative z-10 max-w-3xl w-full text-center"
      >
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 text-sm font-medium mb-6 shadow-sm">
          <Zap size={16} className="text-yellow-500" fill="currentColor" /> Fast, accurate, and free
        </span>

        <h1 className="text-5xl md:text-7xl font-extrabold text-gray-900 dark:text-white tracking-tight mb-6 font-display">
          Compare Before You <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">Buy.</span>
        </h1>
        
        <p className="text-xl text-gray-600 dark:text-gray-300 mb-10 max-w-2xl mx-auto">
          Compare grocery prices across Blinkit, Zepto, Swiggy Instamart and BigBasket instantly. Find the best deal in seconds.
        </p>

        <form ref={formRef} onSubmit={handleSearch} className="relative max-w-2xl mx-auto group">
          <div className="absolute inset-y-0 left-0 pl-5 flex items-center pointer-events-none z-10">
            <Search className="h-6 w-6 text-gray-400 group-focus-within:text-blue-500 transition-colors" />
          </div>
          <input
            type="text"
            className={cn(
              "block w-full pl-14 pr-32 py-5 text-lg border-2 border-transparent bg-white dark:bg-gray-800 shadow-xl focus:border-blue-500 focus:ring-0 focus:outline-none dark:text-white transition-all relative z-10",
              isDropdownOpen ? "rounded-t-2xl" : "rounded-2xl"
            )}
            placeholder="Search for groceries (e.g. Milk, Bread, Eggs)..."
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setIsDropdownOpen(true);
            }}
            onFocus={() => setIsDropdownOpen(true)}
          />
          <div className="absolute inset-y-2 right-2 z-10">
            <button
              type="submit"
              disabled={!query.trim()}
              className="h-full px-8 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium rounded-xl transition-colors shadow-md shadow-blue-500/30 text-lg"
            >
              Search
            </button>
          </div>
          
          <SearchDropdown 
            query={query} 
            isOpen={isDropdownOpen} 
            onSelect={executeSearch}
            onClose={() => setIsDropdownOpen(false)}
          />
        </form>

        <div className="mt-12">
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-4 font-bold uppercase tracking-wider">Popular Searches</p>
          <div className="flex flex-wrap justify-center gap-3 max-w-2xl mx-auto">
            {POPULAR_SEARCHES.map((item, index) => (
              <motion.button
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.3 + (index * 0.05) }}
                key={item.term}
                onClick={() => executeSearch(item.term)}
                className="px-4 py-2 rounded-full bg-white dark:bg-gray-800/80 backdrop-blur-sm border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:border-blue-500 dark:hover:border-blue-500 hover:text-blue-600 dark:hover:text-blue-400 transition-all text-sm shadow-sm hover:shadow-md flex items-center gap-2 group"
              >
                <span>{item.emoji}</span>
                <span className="font-medium">{item.term}</span>
              </motion.button>
            ))}
          </div>
        </div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="mt-12 flex justify-center"
        >
          <Link to="/cart" className="inline-flex items-center gap-2 px-6 py-4 rounded-2xl bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-semibold hover:from-purple-700 hover:to-indigo-700 transition-all shadow-lg hover:shadow-xl hover:-translate-y-1 group">
            <ListChecks size={24} className="group-hover:scale-110 transition-transform" />
            <div className="text-left">
              <div className="text-sm text-purple-200 font-medium">Have a long shopping list?</div>
              <div className="text-lg">Try the Smart Cart Optimizer</div>
            </div>
            <ArrowRight size={20} className="ml-2 group-hover:translate-x-1 transition-transform" />
          </Link>
        </motion.div>
      </motion.div>

      {/* Feature grid */}
      <motion.div 
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.2 }}
        className="relative z-10 grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl w-full mt-24"
      >
        <div className="glass-card rounded-3xl p-8 text-center hover:-translate-y-1 transition-transform duration-300">
          <div className="mx-auto bg-blue-100 dark:bg-blue-900/30 w-14 h-14 rounded-2xl flex items-center justify-center mb-5 text-blue-600 shadow-inner">
            <TrendingUp size={24} />
          </div>
          <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">Track Savings</h3>
          <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">See average prices, highest prices, and exactly how much you save on every order.</p>
        </div>
        <div className="glass-card rounded-3xl p-8 text-center hover:-translate-y-1 transition-transform duration-300">
          <div className="mx-auto bg-purple-100 dark:bg-purple-900/30 w-14 h-14 rounded-2xl flex items-center justify-center mb-5 text-purple-600 shadow-inner">
            <MapPin size={24} />
          </div>
          <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">Local Availability</h3>
          <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">Results are tailored to your specific delivery location for accurate pricing.</p>
        </div>
        <div className="glass-card rounded-3xl p-8 text-center hover:-translate-y-1 transition-transform duration-300">
          <div className="mx-auto bg-green-100 dark:bg-green-900/30 w-14 h-14 rounded-2xl flex items-center justify-center mb-5 text-green-600 shadow-inner">
            <ShoppingBag size={24} />
          </div>
          <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">Basket Optimizer</h3>
          <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">Add multiple items and we'll tell you the cheapest combination of platforms to use.</p>
        </div>
      </motion.div>
    </div>
  );
}
