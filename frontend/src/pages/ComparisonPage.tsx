import { ArrowLeft, ExternalLink, Loader2, TrendingUp, History as HistoryIcon, Tag, Store, Clock, XCircle, AlertCircle, TrendingDown, Percent, Box, Truck, Bell } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { motion, AnimatePresence } from "framer-motion";

import EmptyState from "../components/EmptyState";
import { getProductOffers, getProductHistory, deepSearchProduct, createPriceAlert } from "../services/api";
import { formatCurrency } from "../services/format";
import { useLocationStore } from "../contexts/LocationContext";
import type { ProductOffersResponse } from "../types";

export default function ComparisonPage() {
  const { comparisonId, normalizedProductId } = useParams();
  const [searchParams] = useSearchParams();
  const actualSearchId = searchParams.get("search_id") || comparisonId;
  const { location } = useLocationStore();
  
  const [data, setData] = useState<ProductOffersResponse | null>(null);
  const [historyData, setHistoryData] = useState<any[]>([]);
  const [historyStats, setHistoryStats] = useState<any>(null);
  const [availablePlatforms, setAvailablePlatforms] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isDeepSearching, setIsDeepSearching] = useState(false);
  const [deepSearchComplete, setDeepSearchComplete] = useState(false);
  const [isTracking, setIsTracking] = useState(false);
  const [trackSuccess, setTrackSuccess] = useState(false);

  useEffect(() => {
    if (!normalizedProductId) return;

    setIsLoading(true);
    Promise.all([
      getProductOffers(normalizedProductId, actualSearchId),
      getProductHistory(normalizedProductId).catch(() => [])
    ])
      .then(([offersData, histData]) => {
        setData(offersData);
        
        // Group history by date and calculate statistics
        const groupedData: Record<string, any> = {};
        const platformsSet = new Set<string>();
        let minPrice = Infinity;
        let maxPrice = -Infinity;
        let sumPrice = 0;
        let count = 0;
        
        let latestPrice = 0;
        let yesterdayPrice = 0;
        
        const now = new Date();
        const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        
        let sevenDayLow = Infinity;
        let thirtyDayLow = Infinity;
        
        // Sort history by date to find yesterday and today properly
        const sortedHistory = histData.sort((a: any, b: any) => new Date(a.date).getTime() - new Date(b.date).getTime());

        sortedHistory.forEach((h: any, idx: number) => {
          const dateObj = new Date(h.date);
          const dateStr = dateObj.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
          const price = parseFloat(h.price);
          const platform = h.platform;
          
          platformsSet.add(platform);
          
          if (!groupedData[dateStr]) {
            groupedData[dateStr] = { date: dateStr, rawDate: dateObj };
          }
          groupedData[dateStr][platform] = price;
          
          if (price < minPrice) minPrice = price;
          if (price > maxPrice) maxPrice = price;
          sumPrice += price;
          count++;
          
          if (dateObj >= sevenDaysAgo && price < sevenDayLow) sevenDayLow = price;
          if (dateObj >= thirtyDaysAgo && price < thirtyDayLow) thirtyDayLow = price;
          
          // Latest price is simply the last one we see in chronological order
          latestPrice = price;
        });
        
        // Convert to array and sort chronologically
        const chartData = Object.values(groupedData).sort((a, b) => a.rawDate.getTime() - b.rawDate.getTime());
        
        // Calculate yesterday's price from the second to last group if available
        if (chartData.length > 1) {
            const yesterdayGroup = chartData[chartData.length - 2];
            // Get average price across platforms on that day
            let ySum = 0, yCount = 0;
            for (const key in yesterdayGroup) {
                if (key !== 'date' && key !== 'rawDate') {
                    ySum += yesterdayGroup[key];
                    yCount++;
                }
            }
            if (yCount > 0) yesterdayPrice = ySum / yCount;
        }

        setHistoryData(chartData);
        setAvailablePlatforms(Array.from(platformsSet));
        
        if (count > 0) {
            setHistoryStats({
                lowest: minPrice,
                highest: maxPrice,
                average: sumPrice / count,
                current: latestPrice,
                changeFromYesterday: yesterdayPrice > 0 ? latestPrice - yesterdayPrice : 0,
                changePercent: yesterdayPrice > 0 ? ((latestPrice - yesterdayPrice) / yesterdayPrice) * 100 : 0,
                sevenDayLow: sevenDayLow === Infinity ? minPrice : sevenDayLow,
                thirtyDayLow: thirtyDayLow === Infinity ? minPrice : thirtyDayLow,
                volatility: maxPrice - minPrice
            });
        }
        
        // Trigger Deep Search
        if (offersData && offersData.product && !deepSearchComplete && !isDeepSearching) {
            setIsDeepSearching(true);
            deepSearchProduct(offersData.product.name, location?.lat, location?.lon)
              .then((newComparison) => {
                  // Re-fetch offers with the new deep search ID
                  return getProductOffers(normalizedProductId, newComparison.id.toString());
              })
              .then((deepOffersData) => {
                  setData(deepOffersData);
                  setDeepSearchComplete(true);
              })
              .catch((err) => console.error("Deep search failed:", err))
              .finally(() => setIsDeepSearching(false));
        }
      })
      .catch((exc) => setError(exc instanceof Error ? exc.message : "Unable to load product offers."))
      .finally(() => setIsLoading(false));
  }, [normalizedProductId, actualSearchId, location?.lat, location?.lon, deepSearchComplete]);

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="animate-spin text-blue-600" size={32} aria-label="Loading" />
      </div>
    );
  }

  if (error) {
    return <EmptyState title="Offers unavailable" message={error} />;
  }

  if (!data) {
    return <EmptyState title="Product not found" message="This product has no valid offers." />;
  }

  const { product, analytics, platforms } = data;

  const validOffers = platforms.filter(p => p.status === 'available' && p.offer).map(p => p.offer!);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      <Link
        to={comparisonId ? `/results/${comparisonId}` : "/"}
        className="inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-bold text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors w-fit"
      >
        <ArrowLeft size={16} aria-hidden="true" />
        Back to Discovery
      </Link>

      {/* Header */}
      <section className="bg-white dark:bg-gray-900 rounded-3xl p-6 md:p-8 border border-gray-200 dark:border-gray-800 shadow-sm flex flex-col md:flex-row items-center md:items-start gap-8 relative overflow-hidden">
        {isDeepSearching && (
          <div className="absolute top-0 left-0 w-full h-1 bg-blue-100 overflow-hidden z-20">
            <div className="h-full bg-blue-600 animate-pulse w-full"></div>
          </div>
        )}
        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/5 dark:bg-blue-500/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3"></div>
        
        {product.image ? (
          <div className="w-40 h-40 md:w-48 md:h-48 shrink-0 bg-white dark:bg-gray-800 rounded-2xl p-4 border border-gray-100 dark:border-gray-700 shadow-sm flex items-center justify-center relative z-10">
            <img src={product.image} alt={product.name} className="w-full h-full object-contain mix-blend-multiply dark:mix-blend-normal" />
          </div>
        ) : (
          <div className="w-40 h-40 md:w-48 md:h-48 shrink-0 bg-gray-50 dark:bg-gray-800 rounded-2xl flex items-center justify-center relative z-10 text-gray-400">
            <Box size={48} />
          </div>
        )}
        
        <div className="flex-1 text-center md:text-left z-10 w-full">
          <div className="inline-block bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 text-xs font-bold px-3 py-1 rounded-full uppercase tracking-widest mb-3">
            {product.brand || "Generic"}
          </div>
          <h1 className="text-2xl md:text-4xl font-extrabold text-gray-900 dark:text-white leading-tight mb-2 font-display">
            {product.name}
          </h1>
          <p className="text-lg text-gray-500 font-medium mb-6">{product.quantity || "1 pc"}</p>
          
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex flex-wrap items-center justify-center md:justify-start gap-3">
              <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-900/50 rounded-xl px-4 py-2 flex items-center gap-2">
                <span className="text-green-600 dark:text-green-500 font-bold">🏆 Best Deal:</span>
                <span className="text-xl font-extrabold text-green-700 dark:text-green-400">{formatCurrency(analytics.lowest_total_cost)}</span>
                <span className="text-green-600 dark:text-green-500 text-sm font-medium">on {analytics.cheapest_provider}</span>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              {isDeepSearching && (
                <div className="flex items-center gap-3 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 px-4 py-2 rounded-xl border border-blue-200 dark:border-blue-800/50">
                  <Loader2 size={16} className="animate-spin" />
                  <span className="text-sm font-bold">AI Deep Search running...</span>
                </div>
              )}
              
              <button 
                onClick={async () => {
                   if (!data) return;
                   setIsTracking(true);
                   try {
                      await createPriceAlert(
                         data.product.name, 
                         data.product.normalized_name, 
                         data.analytics.lowest_total_cost
                      );
                      setTrackSuccess(true);
                      setTimeout(() => setTrackSuccess(false), 3000);
                   } catch (e) {
                      console.error("Failed to track", e);
                   }
                   setIsTracking(false);
                }}
                disabled={isTracking || trackSuccess}
                className="flex items-center gap-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-200 px-4 py-2 rounded-xl font-bold transition-colors shadow-sm disabled:opacity-50"
              >
                <Bell size={18} className={trackSuccess ? "text-green-500" : "text-blue-500"} />
                {trackSuccess ? "Alert Set!" : "Track Price"}
              </button>
            </div>
            
            {deepSearchComplete && !isDeepSearching && (
              <div className="flex items-center gap-2 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 px-4 py-2 rounded-xl border border-green-200 dark:border-green-800/50">
                <span className="text-sm font-bold">✓ AI Deep Search complete</span>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Analytics Grid */}
      <section className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <div className="bg-white dark:bg-gray-900 p-5 rounded-2xl border border-gray-200 dark:border-gray-800 flex flex-col items-center justify-center text-center">
          <Tag className="text-blue-500 mb-2" size={20} />
          <div className="text-xs text-gray-500 font-bold uppercase tracking-wider mb-1">Lowest Price</div>
          <div className="text-xl font-extrabold text-gray-900 dark:text-white">{formatCurrency(analytics.lowest_product_price)}</div>
        </div>
        <div className="bg-white dark:bg-gray-900 p-5 rounded-2xl border border-gray-200 dark:border-gray-800 flex flex-col items-center justify-center text-center">
          <TrendingDown className="text-green-500 mb-2" size={20} />
          <div className="text-xs text-gray-500 font-bold uppercase tracking-wider mb-1">Total Payable</div>
          <div className="text-xl font-extrabold text-gray-900 dark:text-white">{formatCurrency(analytics.lowest_total_cost)}</div>
        </div>
        <div className="bg-white dark:bg-gray-900 p-5 rounded-2xl border border-gray-200 dark:border-gray-800 flex flex-col items-center justify-center text-center">
          <TrendingUp className="text-red-500 mb-2" size={20} />
          <div className="text-xs text-gray-500 font-bold uppercase tracking-wider mb-1">Highest Price</div>
          <div className="text-xl font-extrabold text-gray-900 dark:text-white">{formatCurrency(analytics.highest_price)}</div>
        </div>
        <div className="bg-white dark:bg-gray-900 p-5 rounded-2xl border border-gray-200 dark:border-gray-800 flex flex-col items-center justify-center text-center hidden md:flex">
          <Percent className="text-purple-500 mb-2" size={20} />
          <div className="text-xs text-gray-500 font-bold uppercase tracking-wider mb-1">Average</div>
          <div className="text-xl font-extrabold text-gray-900 dark:text-white">{formatCurrency(analytics.average_price)}</div>
        </div>
        <div className="bg-white dark:bg-gray-900 p-5 rounded-2xl border border-gray-200 dark:border-gray-800 flex flex-col items-center justify-center text-center hidden lg:flex">
          <Store className="text-orange-500 mb-2" size={20} />
          <div className="text-xs text-gray-500 font-bold uppercase tracking-wider mb-1">Platforms</div>
          <div className="text-xl font-extrabold text-gray-900 dark:text-white">{analytics.platforms_compared}</div>
        </div>
        <div className="bg-gradient-to-br from-green-500 to-emerald-600 p-5 rounded-2xl border border-green-600 flex flex-col items-center justify-center text-center shadow-lg shadow-green-500/20 text-white">
          <div className="text-xs text-green-100 font-bold uppercase tracking-wider mb-1">Money Saved</div>
          <div className="text-2xl font-extrabold">{formatCurrency(analytics.money_saved)}</div>
        </div>
      </section>

      {/* Comparison Cards */}
      <section>
        <h2 className="text-2xl font-bold mb-6 text-gray-900 dark:text-white font-display">Select Provider</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
          <AnimatePresence>
            {platforms.map((p, idx) => {
              const isCheapest = p.status === 'available' && parseFloat(p.offer?.total_price || "0") === analytics.lowest_total_cost;
              const isFastest = p.status === 'available' && p.platform.name === analytics.fastest_delivery;
              const discountStr = p.offer?.mrp && p.offer.price ? Math.round(((parseFloat(p.offer.mrp.toString()) - parseFloat(p.offer.price)) / parseFloat(p.offer.mrp.toString())) * 100) : 0;
              const isHighestDiscount = discountStr > 0 && discountStr === analytics.highest_discount;

              return (
                <motion.div
                  key={p.platform.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.1 }}
                  className={`bg-white dark:bg-gray-900 rounded-3xl border overflow-hidden flex flex-col transition-all duration-300 ${isCheapest ? "border-green-500 shadow-xl shadow-green-500/10 scale-100 md:scale-[1.02]" : "border-gray-200 dark:border-gray-800 shadow-sm hover:shadow-md"}`}
                >
                  {/* Card Header */}
                  <div className="p-5 flex items-center justify-between border-b border-gray-100 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/30">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-white border border-gray-200 dark:border-gray-700 flex items-center justify-center p-1.5 shrink-0 overflow-hidden shadow-sm">
                        {p.platform.logo_url ? (
                          <img src={p.platform.logo_url} className="w-full h-full object-contain" alt="" />
                        ) : (
                          <span className="text-sm font-bold text-gray-500">{p.platform.name[0]}</span>
                        )}
                      </div>
                      <div className="font-bold text-gray-900 dark:text-white text-lg">{p.platform.name}</div>
                    </div>
                  </div>

                  {/* Card Body */}
                  <div className="p-6 flex-1 flex flex-col">
                    {p.status === 'available' && p.offer ? (
                      <>
                        <div className="flex flex-col gap-4 mb-6 flex-1">
                          {/* Highlights */}
                          <div className="flex flex-wrap gap-2 min-h-[28px]">
                            {isCheapest && <span className="text-[10px] font-bold text-green-700 bg-green-100 dark:bg-green-900/30 dark:text-green-400 px-2 py-1 rounded-md uppercase tracking-wide">🏆 Best Deal</span>}
                            {isFastest && <span className="text-[10px] font-bold text-blue-700 bg-blue-100 dark:bg-blue-900/30 dark:text-blue-400 px-2 py-1 rounded-md uppercase tracking-wide">⚡ Fastest</span>}
                            {isHighestDiscount && <span className="text-[10px] font-bold text-red-700 bg-red-100 dark:bg-red-900/30 dark:text-red-400 px-2 py-1 rounded-md uppercase tracking-wide">🔥 {discountStr}% OFF</span>}
                          </div>

                          <div className="space-y-3">
                            <div className="flex justify-between items-center text-sm">
                              <span className="text-gray-500 dark:text-gray-400">Item Price</span>
                              <span className="font-semibold text-gray-900 dark:text-white">{formatCurrency(p.offer.price, p.offer.currency)}</span>
                            </div>
                            <div className="flex justify-between items-center text-sm">
                              <span className="text-gray-500 dark:text-gray-400">Delivery Fee</span>
                              <span className="font-semibold text-gray-900 dark:text-white">
                                {parseFloat(p.offer.delivery_charge || "0") > 0 ? formatCurrency(p.offer.delivery_charge, p.offer.currency) : <span className="text-green-500 uppercase">Free</span>}
                              </span>
                            </div>
                            {p.offer.raw_payload?.eta && (
                              <div className="flex justify-between items-center text-sm">
                                <span className="text-gray-500 dark:text-gray-400 flex items-center gap-1"><Clock size={14}/> ETA</span>
                                <span className="font-semibold text-gray-900 dark:text-white">{p.offer.raw_payload.eta}</span>
                              </div>
                            )}
                          </div>
                        </div>

                        <div className="pt-4 border-t border-gray-100 dark:border-gray-800">
                          <div className="flex justify-between items-end mb-4">
                            <span className="text-gray-500 font-medium">Total Payable</span>
                            <div className="text-right">
                              {p.offer.mrp && parseFloat(p.offer.mrp.toString()) > parseFloat(p.offer.price || "0") && (
                                <div className="text-xs text-gray-400 line-through mb-0.5">{formatCurrency(p.offer.mrp, p.offer.currency)} MRP</div>
                              )}
                              <div className="text-2xl font-extrabold text-gray-900 dark:text-white leading-none">
                                {formatCurrency(p.offer.total_price, p.offer.currency)}
                              </div>
                            </div>
                          </div>
                          
                          {p.offer.product_url ? (
                            <a
                              href={p.offer.product_url}
                              target="_blank"
                              rel="noreferrer"
                              style={{ backgroundColor: p.platform.brand_color || '#3B82F6' }}
                              className="flex w-full items-center justify-center gap-2 rounded-xl py-3.5 text-sm font-bold text-white transition-all hover:brightness-110 shadow-lg active:scale-95"
                            >
                              Buy on {p.platform.name}
                              <ExternalLink size={16} aria-hidden="true" />
                            </a>
                          ) : (
                            <button disabled className="w-full py-3.5 rounded-xl bg-gray-100 dark:bg-gray-800 text-gray-400 font-bold text-sm cursor-not-allowed">
                              App Only
                            </button>
                          )}
                        </div>
                      </>
                    ) : (
                      <div className="flex-1 flex flex-col items-center justify-center text-center p-6 space-y-4 opacity-70">
                        {p.status === 'not_serviceable' ? (
                          <>
                            <div className="w-16 h-16 rounded-full bg-orange-50 dark:bg-orange-900/20 flex items-center justify-center">
                              <Truck className="text-orange-400" size={32} />
                            </div>
                            <div className="font-bold text-gray-700 dark:text-gray-300">Unavailable in your location</div>
                          </>
                        ) : p.status === 'error' ? (
                          <>
                            <div className="w-16 h-16 rounded-full bg-red-50 dark:bg-red-900/20 flex items-center justify-center">
                              <AlertCircle className="text-red-400" size={32} />
                            </div>
                            <div className="font-bold text-gray-700 dark:text-gray-300">Service Error</div>
                          </>
                        ) : (
                          <>
                            <div className="w-16 h-16 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
                              <XCircle className="text-gray-400" size={32} />
                            </div>
                            <div className="font-bold text-gray-700 dark:text-gray-300">Product not found</div>
                          </>
                        )}
                        <p className="text-sm text-gray-500 font-medium">{p.status_message}</p>
                      </div>
                    )}
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      </section>

      {/* Comparison Table */}
      {validOffers.length > 0 && (
        <section className="bg-white dark:bg-gray-900 p-6 md:p-8 rounded-3xl border border-gray-200 dark:border-gray-800 shadow-sm overflow-hidden">
          <h2 className="text-xl font-bold mb-6 flex items-center gap-2 text-gray-900 dark:text-white font-display">
            Comparison Table
          </h2>
          <div className="overflow-x-auto -mx-6 md:mx-0">
            <table className="w-full text-left border-collapse min-w-[600px]">
              <thead>
                <tr className="border-b border-gray-100 dark:border-gray-800">
                  <th className="py-3 px-4 font-semibold text-gray-500 dark:text-gray-400 text-sm whitespace-nowrap">Platform</th>
                  <th className="py-3 px-4 font-semibold text-gray-500 dark:text-gray-400 text-sm text-right whitespace-nowrap">Item Price</th>
                  <th className="py-3 px-4 font-semibold text-gray-500 dark:text-gray-400 text-sm text-right whitespace-nowrap">Delivery</th>
                  <th className="py-3 px-4 font-semibold text-gray-500 dark:text-gray-400 text-sm text-right whitespace-nowrap">MRP</th>
                  <th className="py-3 px-4 font-bold text-gray-900 dark:text-white text-right text-base whitespace-nowrap">Total Cost</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50 dark:divide-gray-800/50">
                {validOffers.map((offer) => {
                  const isCheapest = parseFloat(offer.total_price || "0") === analytics.lowest_total_cost;
                  const discount = offer.mrp ? parseFloat(offer.mrp.toString()) - parseFloat(offer.price || "0") : 0;
                  
                  return (
                    <tr key={offer.id} className={`group transition-colors hover:bg-gray-50 dark:hover:bg-gray-800/50 ${isCheapest ? "bg-green-50/50 dark:bg-green-900/10" : ""}`}>
                      <td className="py-4 px-4 font-bold text-gray-900 dark:text-white">
                        <div className="flex items-center gap-2">
                          {offer.platform?.name}
                          {isCheapest && <span className="text-[10px] font-bold text-green-600 uppercase tracking-wide bg-green-100 dark:bg-green-900/30 px-2 py-0.5 rounded-sm">Best</span>}
                        </div>
                      </td>
                      <td className="py-4 px-4 text-right font-medium text-gray-700 dark:text-gray-300">
                        {formatCurrency(offer.price, offer.currency)}
                      </td>
                      <td className="py-4 px-4 text-right font-medium text-gray-500">
                        {parseFloat(offer.delivery_charge || "0") > 0 ? formatCurrency(offer.delivery_charge, offer.currency) : <span className="text-green-500">FREE</span>}
                      </td>
                      <td className="py-4 px-4 text-right font-medium text-gray-400">
                        {offer.mrp ? <span className="line-through">{formatCurrency(offer.mrp, offer.currency)}</span> : "-"}
                      </td>
                      <td className="py-4 px-4 text-right font-bold text-lg text-gray-900 dark:text-white">
                        {formatCurrency(offer.total_price, offer.currency)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* Price Trend Chart */}
      <section className="bg-white dark:bg-gray-900 p-6 md:p-8 rounded-3xl border border-gray-200 dark:border-gray-800 shadow-sm">
        <h2 className="text-xl font-bold mb-6 flex items-center gap-2 text-gray-900 dark:text-white font-display">
          <HistoryIcon size={22} className="text-purple-600" /> Price History
        </h2>
        {historyData.length > 0 ? (
          <>
            {historyStats && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <div className="bg-gray-50 dark:bg-gray-800/50 p-4 rounded-xl border border-gray-100 dark:border-gray-800">
                  <div className="text-xs text-gray-500 font-bold uppercase tracking-wider mb-1">Lowest Ever</div>
                  <div className="text-lg font-bold text-gray-900 dark:text-white">{formatCurrency(historyStats.lowest)}</div>
                </div>
                <div className="bg-gray-50 dark:bg-gray-800/50 p-4 rounded-xl border border-gray-100 dark:border-gray-800">
                  <div className="text-xs text-gray-500 font-bold uppercase tracking-wider mb-1">Highest Ever</div>
                  <div className="text-lg font-bold text-gray-900 dark:text-white">{formatCurrency(historyStats.highest)}</div>
                </div>
                <div className="bg-gray-50 dark:bg-gray-800/50 p-4 rounded-xl border border-gray-100 dark:border-gray-800">
                  <div className="text-xs text-gray-500 font-bold uppercase tracking-wider mb-1">7 Day Low</div>
                  <div className="text-lg font-bold text-gray-900 dark:text-white">{formatCurrency(historyStats.sevenDayLow)}</div>
                </div>
                <div className="bg-gray-50 dark:bg-gray-800/50 p-4 rounded-xl border border-gray-100 dark:border-gray-800">
                  <div className="text-xs text-gray-500 font-bold uppercase tracking-wider mb-1">Volatility</div>
                  <div className="text-lg font-bold text-gray-900 dark:text-white">{formatCurrency(historyStats.volatility)}</div>
                </div>
              </div>
            )}
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={historyData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.15} vertical={false} />
                  <XAxis dataKey="date" stroke="#9CA3AF" fontSize={12} tickLine={false} axisLine={false} dy={10} />
                  <YAxis stroke="#9CA3AF" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `₹${val}`} />
                  <Tooltip 
                    contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)', backgroundColor: 'rgba(255, 255, 255, 0.95)', padding: '12px' }}
                    labelStyle={{ color: '#6B7280', fontWeight: 600, marginBottom: '8px' }}
                  />
                  {availablePlatforms.map((platform) => {
                    const colors: Record<string, string> = { Blinkit: "#3B82F6", Zepto: "#8B5CF6", Instamart: "#10B981", BigBasket: "#F97316" };
                    return (
                      <Line 
                        key={platform} 
                        type="linear" 
                        dataKey={platform} 
                        name={platform}
                        stroke={colors[platform] || "#6B7280"} 
                        strokeWidth={3} 
                        dot={{ r: 4, fill: colors[platform] || "#6B7280", strokeWidth: 2, stroke: '#fff' }} 
                        activeDot={{ r: 6, fill: colors[platform] || "#6B7280", strokeWidth: 2, stroke: '#fff' }} 
                        connectNulls={true}
                      />
                    );
                  })}
                </LineChart>
              </ResponsiveContainer>
            </div>
            
            <div className="mt-6 flex flex-wrap gap-4 justify-center">
              {availablePlatforms.map((platform) => {
                const colors: Record<string, string> = { Blinkit: "bg-blue-500", Zepto: "bg-purple-500", Instamart: "bg-green-500", BigBasket: "bg-orange-500" };
                return (
                  <div key={platform} className="flex items-center gap-2">
                    <span className={`w-3 h-3 rounded-full ${colors[platform] || "bg-gray-500"}`}></span>
                    <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">{platform}</span>
                  </div>
                );
              })}
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center justify-center py-12 px-4 bg-gray-50 dark:bg-gray-800/50 rounded-2xl border border-dashed border-gray-200 dark:border-gray-700 text-center">
            <HistoryIcon size={48} className="text-gray-300 dark:text-gray-600 mb-4" />
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">No historical price data available yet.</h3>
            <p className="text-sm text-gray-500 mb-6 max-w-md">We'll start tracking this product after its first search.</p>
            <button 
              onClick={() => window.location.reload()}
              className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow-sm transition-colors"
            >
              Refresh Prices
            </button>
          </div>
        )}
      </section>

      {/* Similar Alternatives */}
      {data.similar_alternatives && data.similar_alternatives.length > 0 && (
        <section className="bg-white dark:bg-gray-900 p-6 md:p-8 rounded-3xl border border-gray-200 dark:border-gray-800 shadow-sm mt-8">
          <h2 className="text-xl font-bold mb-6 flex items-center gap-2 text-gray-900 dark:text-white font-display">
            <TrendingUp size={22} className="text-blue-600" /> Similar Alternatives
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {data.similar_alternatives.map((alt, idx) => (
              <div key={idx} className="border border-gray-200 dark:border-gray-800 rounded-2xl p-5 hover:border-blue-400 transition-colors flex flex-col">
                <div className="flex gap-4 items-start mb-4">
                  <div className="w-16 h-16 shrink-0 bg-gray-50 dark:bg-gray-800 rounded-xl p-2 flex items-center justify-center">
                    {alt.product.image ? (
                      <img src={alt.product.image} className="w-full h-full object-contain mix-blend-multiply dark:mix-blend-normal" alt="" />
                    ) : (
                      <Box size={24} className="text-gray-400" />
                    )}
                  </div>
                  <div>
                    <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1">{alt.product.brand || "Generic"}</div>
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-white line-clamp-2">{alt.product.name}</h3>
                    <div className="text-xs text-gray-500 mt-1">{alt.product.quantity}</div>
                  </div>
                </div>
                
                <div className="mt-auto pt-4 border-t border-gray-100 dark:border-gray-800">
                  <div className="flex justify-between items-end mb-3">
                    <span className="text-sm font-medium text-gray-500">Starting at</span>
                    <span className="text-lg font-bold text-gray-900 dark:text-white">{formatCurrency(alt.product.price, "INR")}</span>
                  </div>
                  
                  <div className="bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 text-xs px-3 py-2 rounded-lg font-medium mb-4">
                    {alt.evaluation.reason}
                  </div>
                  
                  <Link
                    to={`/comparison/${actualSearchId}/product/${encodeURIComponent(alt.product.normalized_id)}`}
                    className="flex w-full items-center justify-center gap-2 rounded-xl bg-gray-100 dark:bg-gray-800 py-2.5 text-sm font-bold text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                  >
                    Compare Alternative
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
