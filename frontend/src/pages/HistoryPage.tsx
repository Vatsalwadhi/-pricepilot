import { Loader2, Trash2, History as HistoryIcon, Search, ExternalLink } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";

import EmptyState from "../components/EmptyState";
import { deleteHistoryItem, getHistory } from "../services/api";
import { formatCurrency } from "../services/format";
import type { SearchHistoryItem } from "../types";
import { PLATFORMS } from "../lib/constants";
import { cn } from "../lib/cn";

export default function HistoryPage() {
  const [items, setItems] = useState<SearchHistoryItem[]>([]);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    getHistory()
      .then(setItems)
      .catch((exc) => setError(exc instanceof Error ? exc.message : "Unable to load history."))
      .finally(() => setIsLoading(false));
  }, []);

  async function handleDelete(id: number, e?: React.MouseEvent) {
    if (e) e.preventDefault();
    
    // Optimistic delete
    setItems((current) => current.filter((item) => item.id !== id));
    
    try {
      await deleteHistoryItem(id);
    } catch (err) {
      // Revert if failed
      getHistory().then(setItems);
      console.error("Failed to delete history item", err);
    }
  }

  // Group items by date
  const groupedItems = items.reduce((acc, item) => {
    const date = new Date(item.created_at);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    let group = date.toLocaleDateString();
    if (date.toDateString() === today.toDateString()) group = "Today";
    else if (date.toDateString() === yesterday.toDateString()) group = "Yesterday";

    if (!acc[group]) acc[group] = [];
    acc[group].push(item);
    return acc;
  }, {} as Record<string, SearchHistoryItem[]>);

  if (isLoading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center flex-col gap-4 animate-fade-in">
        <Loader2 className="animate-spin text-blue-600" size={32} />
        <p className="text-gray-500 font-medium">Loading history...</p>
      </div>
    );
  }

  if (error) {
    return <EmptyState title="History unavailable" message={error} variant="provider-error" />;
  }

  if (items.length === 0) {
    return (
      <EmptyState 
        title="No searches yet" 
        message="Your recent price comparisons will appear here."
        variant="no-results"
        action={
          <Link to="/" className="btn-primary mt-4">
            <Search size={18} /> Start Shopping
          </Link>
        }
      />
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 animate-fade-in">
      <div className="mb-10 border-b border-gray-200 dark:border-gray-800 pb-6">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 rounded-2xl">
            <HistoryIcon size={28} />
          </div>
          <div>
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-gray-900 dark:text-white font-display">
              Search History
            </h1>
            <p className="text-gray-500 dark:text-gray-400 mt-1">Review your past price comparisons</p>
          </div>
        </div>
      </div>
      
      <div className="space-y-10">
        {Object.entries(groupedItems).map(([dateLabel, groupItems]) => (
          <section key={dateLabel}>
            <h2 className="text-sm font-bold text-gray-400 dark:text-gray-500 uppercase tracking-wider mb-4 px-2">
              {dateLabel}
            </h2>
            <div className="grid gap-4">
              <AnimatePresence>
                {groupItems.map((item) => {
                  const platformConfig = item.cheapest_platform ? PLATFORMS[item.cheapest_platform.provider_key as keyof typeof PLATFORMS] : null;
                  
                  return (
                      <motion.div
                        layout
                        initial={{ opacity: 0, scale: 0.98 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        transition={{ duration: 0.2 }}
                        key={item.id}
                      >
                      <Link 
                        to={`/results/${item.id}`}
                        className="group block bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-5 sm:p-6 transition-all hover:shadow-lg hover:border-gray-300 dark:hover:border-gray-700 relative overflow-hidden"
                      >
                        {/* Hover accent line */}
                        <div className="absolute left-0 top-0 bottom-0 w-1 bg-blue-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                        
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
                          <div className="flex-1">
                            <h3 className="text-xl font-bold text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors capitalize line-clamp-1 mb-1">
                              {item.query}
                            </h3>
                            <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                              <span>{new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                              <span>•</span>
                              <span>{item.result_count || 0} products compared</span>
                            </div>
                          </div>

                          <div className="flex flex-wrap sm:flex-nowrap items-center gap-6 bg-gray-50 dark:bg-gray-800/50 rounded-xl p-4 sm:p-0 sm:bg-transparent">
                            <div className="flex-1 sm:flex-none">
                              <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Lowest Price</p>
                              <div className="flex items-baseline gap-2">
                                <span className="text-xl font-extrabold text-gray-900 dark:text-white">
                                  {formatCurrency(item.cheapest_total_price)}
                                </span>
                              </div>
                            </div>
                            
                            <div className="hidden sm:block w-px h-10 bg-gray-200 dark:bg-gray-800" />
                            
                            <div className="flex-1 sm:flex-none">
                              <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Cheapest At</p>
                              <div className="flex items-center gap-2">
                                {platformConfig?.logo_url ? (
                                  <img src={platformConfig.logo_url} alt="" className="w-5 h-5 object-contain rounded bg-white p-0.5" />
                                ) : (
                                  <div className="w-5 h-5 rounded-full bg-gray-200 dark:bg-gray-700" />
                                )}
                                <span className="font-bold text-gray-700 dark:text-gray-300">
                                  {item.cheapest_platform?.name || "N/A"}
                                </span>
                              </div>
                            </div>

                            <button
                              onClick={(e) => handleDelete(item.id, e)}
                              className="absolute top-4 right-4 sm:relative sm:top-0 sm:right-0 p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl transition-all opacity-0 group-hover:opacity-100"
                              title="Delete history"
                            >
                              <Trash2 size={20} />
                            </button>
                          </div>
                        </div>
                      </Link>
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
