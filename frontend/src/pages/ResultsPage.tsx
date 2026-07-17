import { Loader2, Search, SlidersHorizontal, List, Grid } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { useNavigate, useParams, useLocation } from "react-router-dom";
import { useLocationStore } from "../contexts/LocationContext";
import { motion, AnimatePresence } from "framer-motion";

import EmptyState from "../components/EmptyState";
import ProductDiscoveryCard from "../components/ProductDiscoveryCard";
import SearchLoadingState from "../components/SearchLoadingState";
import { getComparison, searchProducts } from "../services/api";
import { formatDate } from "../services/format";
import type { Comparison } from "../types";
import { cn } from "../lib/cn";

export default function ResultsPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const routerLocation = useLocation();
  const { location, setIsModalOpen } = useLocationStore();
  
  const [comparison, setComparison] = useState<Comparison | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');

  useEffect(() => {
    if (!id) return;

    // If id is not a number, it's a direct search from HomePage
    if (isNaN(Number(id))) {
      const term = decodeURIComponent(id);
      setSearchQuery(term);
      if (!location) {
        setIsModalOpen(true);
        setIsLoading(false);
        return;
      }
      
      setIsLoading(true);
      setIsSearching(true);
      searchProducts(term, location?.lat, location?.lon)
        .then((data) => {
          setComparison(data);
          navigate(`/results/${data.id}`, { replace: true });
        })
        .catch((exc) => setError(exc instanceof Error ? exc.message : "Unable to load results."))
        .finally(() => {
          setIsLoading(false);
          setIsSearching(false);
        });
      return;
    }

    setIsLoading(true);
    getComparison(id)
      .then((data) => {
        setComparison(data);
        setSearchQuery(data.query);
      })
      .catch((exc) => setError(exc instanceof Error ? exc.message : "Unable to load results."))
      .finally(() => setIsLoading(false));
  }, [id, location?.lat, location?.lon, navigate]);

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (!searchQuery.trim()) return;
    if (!location) {
      setIsModalOpen(true);
      return;
    }

    setIsSearching(true);
    try {
      const newComparison = await searchProducts(searchQuery, location.lat, location.lon);
      navigate(`/results/${newComparison.id}`);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Search failed.");
    } finally {
      setIsSearching(false);
    }
  }

  const validResultsCount = comparison?.results.length || 0;

  return (
    <div className="space-y-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-fade-in">
      {/* Search Bar section */}
      <div className="rounded-2xl border border-gray-200 dark:border-gray-800 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md p-3 sm:p-4 shadow-sm sticky top-[72px] z-30">
        <form onSubmit={handleSearch} className="flex flex-col gap-3 sm:flex-row">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
            <input
              id="product-search"
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Search anything..."
              className="w-full rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 pl-12 pr-4 py-3 sm:py-3.5 text-base focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none transition-all dark:text-white"
            />
          </div>
          <button
            type="submit"
            disabled={isSearching}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-8 py-3 sm:py-3.5 font-semibold text-white hover:bg-blue-700 active:bg-blue-800 disabled:opacity-50 transition-all shadow-md shadow-blue-500/20 hover:shadow-blue-500/40"
          >
            {isSearching ? <Loader2 size={20} className="animate-spin" /> : null}
            {isSearching ? "Searching..." : "Search"}
          </button>
        </form>
      </div>

      <AnimatePresence mode="wait">
        {isSearching ? (
          <motion.div
            key="searching"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <SearchLoadingState query={searchQuery} />
          </motion.div>
        ) : error ? (
          <motion.div key="error" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <EmptyState title="Results unavailable" message={error} variant="provider-error" />
          </motion.div>
        ) : !comparison || comparison.results.length === 0 ? (
          <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <EmptyState title="No comparison found" message="Try searching for something else." variant="no-results" />
          </motion.div>
        ) : (
          <motion.div
            key="results"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-8"
          >
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-gray-200 dark:border-gray-800 pb-6">
              <div>
                <p className="text-sm font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
                  {formatDate(comparison.created_at)}
                </p>
                <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-gray-900 dark:text-white font-display">
                  Results for <span className="text-blue-600 dark:text-blue-400">"{comparison.query}"</span>
                </h1>
                <p className="text-gray-500 dark:text-gray-400 mt-2">
                  Found {validResultsCount} unique products across platforms
                </p>
              </div>

              {validResultsCount > 0 && (
                <div className="flex items-center gap-2">
                  <button className="p-2.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors flex items-center gap-2 text-sm font-medium">
                    <SlidersHorizontal size={16} />
                    <span className="hidden sm:inline">Filters</span>
                  </button>
                </div>
              )}
            </div>
            
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 pt-4">
              {comparison.results.map((product) => (
                <ProductDiscoveryCard 
                  key={product.id} 
                  product={product} 
                  searchId={comparison.id} 
                />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
