import React, { useState, useEffect } from "react";
import { Search, Clock, TrendingUp, X } from "lucide-react";
import { POPULAR_SEARCHES, TRENDING_SEARCHES } from "../lib/constants";
import { cn } from "../lib/cn";
import { motion, AnimatePresence } from "framer-motion";

interface SearchDropdownProps {
  query: string;
  isOpen: boolean;
  onSelect: (term: string) => void;
  onClose: () => void;
}

export default function SearchDropdown({ query, isOpen, onSelect, onClose }: SearchDropdownProps) {
  const [recentSearches, setRecentSearches] = useState<string[]>([]);

  useEffect(() => {
    const saved = localStorage.getItem("pricepilot_recent_searches");
    if (saved) {
      try {
        setRecentSearches(JSON.parse(saved));
      } catch (e) { }
    }
  }, [isOpen]);

  const removeRecent = (e: React.MouseEvent, term: string) => {
    e.stopPropagation();
    const updated = recentSearches.filter(t => t !== term);
    setRecentSearches(updated);
    localStorage.setItem("pricepilot_recent_searches", JSON.stringify(updated));
  };

  const clearAllRecent = (e: React.MouseEvent) => {
    e.stopPropagation();
    setRecentSearches([]);
    localStorage.removeItem("pricepilot_recent_searches");
  };

  if (!isOpen) return null;

  const showRecent = query.length === 0 && recentSearches.length > 0;
  const showTrending = query.length === 0;
  const showSuggestions = query.length > 0;

  const filteredSuggestions = POPULAR_SEARCHES
    .filter(p => p.term.toLowerCase().includes(query.toLowerCase()))
    .slice(0, 5);

  return (
    <motion.div 
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="absolute top-full left-0 right-0 mt-2 bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-100 dark:border-gray-800 overflow-hidden z-50 py-2"
    >
      {showSuggestions && (
        <div>
          {filteredSuggestions.length > 0 ? (
            filteredSuggestions.map((item, i) => (
              <button
                key={i}
                onClick={() => onSelect(item.term)}
                className="w-full text-left px-5 py-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors flex items-center gap-3 group"
              >
                <Search size={16} className="text-gray-400 group-hover:text-blue-500" />
                <span className="text-gray-900 dark:text-white flex-1">{item.term}</span>
                <span>{item.emoji}</span>
              </button>
            ))
          ) : (
            <button
              onClick={() => onSelect(query)}
              className="w-full text-left px-5 py-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors flex items-center gap-3 text-blue-600 dark:text-blue-400"
            >
              <Search size={16} />
              <span>Search for "{query}"</span>
            </button>
          )}
        </div>
      )}

      {showRecent && (
        <div className="mb-2">
          <div className="flex items-center justify-between px-5 py-2">
            <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Recent Searches</h3>
            <button onClick={clearAllRecent} className="text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400">Clear</button>
          </div>
          {recentSearches.slice(0, 4).map((term, i) => (
            <button
              key={i}
              onClick={() => onSelect(term)}
              className="w-full text-left px-5 py-2.5 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors flex items-center justify-between group"
            >
              <div className="flex items-center gap-3 text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-white">
                <Clock size={16} className="text-gray-400 group-hover:text-blue-500" />
                <span>{term}</span>
              </div>
              <div 
                onClick={(e) => removeRecent(e, term)}
                className="p-1 rounded-md text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 opacity-0 group-hover:opacity-100 transition-all"
              >
                <X size={14} />
              </div>
            </button>
          ))}
        </div>
      )}

      {showTrending && (
        <div className={cn("pt-2", showRecent && "border-t border-gray-100 dark:border-gray-800")}>
          <div className="px-5 py-2">
            <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Trending Now</h3>
          </div>
          {TRENDING_SEARCHES.map((term, i) => (
            <button
              key={i}
              onClick={() => onSelect(term)}
              className="w-full text-left px-5 py-2.5 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors flex items-center gap-3 group"
            >
              <TrendingUp size={16} className="text-gray-400 group-hover:text-purple-500" />
              <span className="text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-white">{term}</span>
            </button>
          ))}
        </div>
      )}
    </motion.div>
  );
}
