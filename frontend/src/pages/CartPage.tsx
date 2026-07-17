import { useState } from 'react';
import { ShoppingCart, Search, FileText, Loader2, Sparkles, ExternalLink, Package } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link } from 'react-router-dom';
import EmptyState from '../components/EmptyState';
import { request } from '../services/api';
import { formatCurrency } from '../services/format';
import { useLocationStore } from '../contexts/LocationContext';

export default function CartPage() {
  const { location } = useLocationStore();
  
  const [listText, setListText] = useState("");
  const [isParsing, setIsParsing] = useState(false);
  const [isOptimizing, setIsOptimizing] = useState(false);
  
  const [parsedItems, setParsedItems] = useState<any[] | null>(null);
  const [cartResult, setCartResult] = useState<any | null>(null);
  const [error, setError] = useState("");

  const handleProcessList = async () => {
    if (!listText.trim()) return;
    setError("");
    setIsParsing(true);
    setParsedItems(null);
    setCartResult(null);

    try {
      const response = await request<{items: any[]}>("/assistant/parse-list", {
        method: "POST",
        body: JSON.stringify({ text: listText })
      });
      
      setParsedItems(response.items);
      setIsParsing(false);
    } catch (e: any) {
      setError(e.message || "Failed to parse list.");
      setIsParsing(false);
    }
  };

  const handleOptimizeCart = async (items: any[]) => {
    setIsParsing(false);
    setIsOptimizing(true);
    
    try {
      const response = await request<any>("/cart/optimize", {
        method: "POST",
        body: JSON.stringify({
          items,
          strategy: "cheapest",
          lat: location?.lat,
          lon: location?.lon
        })
      });
      setCartResult(response);
    } catch (e: any) {
      setError(e.message || "Failed to optimize cart.");
    } finally {
      setIsOptimizing(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 animate-fade-in">
      <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-800 pb-6 mb-8">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-2xl">
            <Sparkles size={28} />
          </div>
          <div>
            <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-900 dark:text-white tracking-tight font-display">Smart Cart Optimizer</h1>
            <p className="text-gray-500 mt-1">Paste your shopping list and let AI build the cheapest cart across apps.</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Input Column */}
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-white dark:bg-gray-900 p-6 rounded-3xl border border-gray-200 dark:border-gray-800 shadow-sm">
            <label className="flex items-center gap-2 font-bold text-gray-700 dark:text-gray-300 mb-4">
              <FileText size={18} /> Paste your list here
            </label>
            <textarea
              className="w-full h-48 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl p-4 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 resize-none dark:text-white"
              placeholder="e.g.&#10;2 litres milk&#10;1 kg sugar&#10;brown bread&#10;dozen eggs"
              value={listText}
              onChange={(e) => setListText(e.target.value)}
            />
            <button 
              onClick={handleProcessList}
              disabled={isParsing || isOptimizing || !listText.trim()}
              className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold py-4 px-6 rounded-2xl transition-all disabled:opacity-50 transform hover:scale-[1.02] shadow-lg shadow-blue-500/25"
            >
              {isParsing ? <Loader2 size={20} className="animate-spin" /> : <Sparkles size={20} />}
              {isParsing ? "Parsing List..." : "Parse Shopping List"}
            </button>
            {error && <p className="text-red-500 text-sm mt-3 font-medium">{error}</p>}
          </div>

          {parsedItems && !isOptimizing && !cartResult && (
            <div className="bg-white dark:bg-gray-900 p-6 rounded-3xl border border-gray-200 dark:border-gray-800 shadow-sm mt-6">
              <h3 className="font-bold text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
                <Package size={18} /> Verify Your List
              </h3>
              <ul className="space-y-3 mb-6">
                {parsedItems.map((item, idx) => (
                  <li key={idx} className="flex justify-between items-center gap-2 text-sm p-3 bg-gray-50 dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700">
                    <input 
                      type="text" 
                      className="flex-1 bg-transparent font-medium dark:text-white outline-none" 
                      value={item.name}
                      onChange={(e) => {
                        const newItems = [...parsedItems];
                        newItems[idx].name = e.target.value;
                        setParsedItems(newItems);
                      }}
                    />
                    <input 
                      type="text"
                      className="w-20 text-gray-500 font-bold bg-white dark:bg-gray-900 px-2 py-1 rounded-md outline-none border border-transparent focus:border-blue-500"
                      value={item.quantity || ""}
                      placeholder="Qty"
                      onChange={(e) => {
                        const newItems = [...parsedItems];
                        newItems[idx].quantity = e.target.value;
                        setParsedItems(newItems);
                      }}
                    />
                    <button 
                      className="text-red-500 hover:text-red-600 p-1"
                      onClick={() => setParsedItems(parsedItems.filter((_, i) => i !== idx))}
                    >
                      &times;
                    </button>
                  </li>
                ))}
              </ul>
              
              <button
                onClick={() => {
                  const newItems = [...parsedItems, { name: "", quantity: "" }];
                  setParsedItems(newItems);
                }}
                className="w-full mb-4 py-2 border-2 border-dashed border-gray-300 dark:border-gray-700 text-gray-500 rounded-xl hover:border-gray-400 dark:hover:border-gray-500 transition-colors"
              >
                + Add Item
              </button>

              <button
                onClick={() => handleOptimizeCart(parsedItems.filter(i => i.name.trim()))}
                className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-bold py-4 px-6 rounded-2xl transition-all transform hover:scale-[1.02] shadow-lg shadow-green-500/25"
              >
                <Sparkles size={20} />
                Confirm & Find Best Prices
              </button>
            </div>
          )}
        </div>

        {/* Results Column */}
        <div className="lg:col-span-2">
          {!cartResult && !isOptimizing && !isParsing && (
             <EmptyState 
                title="Ready to save?" 
                message="Paste your list on the left to see how much you can save by splitting your order optimally." 
                variant="empty-cart"
             />
          )}

          {(isParsing || isOptimizing) && (
            <div className="h-full flex flex-col items-center justify-center bg-white/50 dark:bg-gray-900/50 rounded-3xl border border-dashed border-gray-300 dark:border-gray-700 p-12 text-center">
              <Loader2 size={48} className="animate-spin text-blue-500 mb-6" />
              <h3 className="text-xl font-bold dark:text-white">{isParsing ? "AI is reading your list..." : "Running optimization algorithms..."}</h3>
              <p className="text-gray-500 mt-2">Checking millions of products across providers for the best deal.</p>
            </div>
          )}

          {cartResult && (
            <AnimatePresence>
              <motion.div initial={{opacity:0, y:20}} animate={{opacity:1, y:0}} className="space-y-6">
                
                {/* Summary Card */}
                <div className="bg-gradient-to-br from-green-500 to-emerald-600 rounded-3xl p-6 md:p-8 text-white shadow-lg shadow-green-500/20">
                  <h2 className="text-xl font-bold text-green-50 mb-6 flex items-center gap-2"><Sparkles size={20}/> Optimal Split Found</h2>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <p className="text-green-100 text-sm font-medium">Grand Total</p>
                      <p className="text-3xl font-extrabold">{formatCurrency(cartResult.grand_total)}</p>
                    </div>
                    <div>
                      <p className="text-green-100 text-sm font-medium">Items Total</p>
                      <p className="text-xl font-bold mt-2">{formatCurrency(cartResult.total_items_cost)}</p>
                    </div>
                    <div>
                      <p className="text-green-100 text-sm font-medium">Delivery Fees</p>
                      <p className="text-xl font-bold mt-2">{formatCurrency(cartResult.total_delivery)}</p>
                    </div>
                    <div>
                      <p className="text-green-100 text-sm font-medium">Apps Used</p>
                      <p className="text-xl font-bold mt-2">{cartResult.splits.length}</p>
                    </div>
                  </div>
                </div>

                {/* Splits */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {cartResult.splits.map((split: any, idx: number) => (
                    <div key={idx} className="bg-white dark:bg-gray-900 rounded-3xl p-6 border border-gray-200 dark:border-gray-800 shadow-sm relative overflow-hidden">
                      <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 rounded-full blur-2xl -translate-y-1/2 translate-x-1/3"></div>
                      
                      <div className="flex justify-between items-center mb-6">
                        <h3 className="text-xl font-bold dark:text-white capitalize">{split.platform}</h3>
                        <div className="text-right">
                          <p className="text-xl font-extrabold text-blue-600">{formatCurrency(split.subtotal)}</p>
                          <p className="text-xs text-gray-500 font-medium">incl. {formatCurrency(split.delivery_charge)} delivery</p>
                        </div>
                      </div>

                      <ul className="space-y-4 mb-6">
                        {split.items.map((item: any, i: number) => (
                          <li key={i} className="flex gap-4 items-center">
                            {item.image ? (
                              <div className="w-12 h-12 rounded-xl bg-gray-50 border border-gray-100 p-1 flex-shrink-0">
                                <img src={item.image} alt="" className="w-full h-full object-contain mix-blend-multiply" />
                              </div>
                            ) : (
                               <div className="w-12 h-12 rounded-xl bg-gray-50 border border-gray-100 flex items-center justify-center flex-shrink-0 text-gray-300"><Package size={20}/></div>
                            )}
                            <div className="flex-1 min-w-0">
                              <p className="text-xs text-gray-500 font-bold uppercase truncate">{item.original_query}</p>
                              <p className="text-sm font-medium dark:text-white line-clamp-1">{item.matched_name}</p>
                            </div>
                            <div className="font-bold dark:text-white">
                              {formatCurrency(item.price)}
                            </div>
                          </li>
                        ))}
                      </ul>

                      <button 
                        onClick={() => {
                          split.items.forEach((item: any) => {
                            if (item.product_url) {
                              window.open(item.product_url, '_blank');
                            }
                          });
                        }}
                        className="w-full flex items-center justify-center gap-2 bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-900 dark:text-white font-bold py-3 rounded-xl transition-colors border border-gray-200 dark:border-gray-700"
                      >
                        Buy on {split.platform} <ExternalLink size={16}/>
                      </button>
                    </div>
                  ))}
                </div>

                {/* Unavailable Items */}
                {cartResult.unavailable?.length > 0 && (
                   <div className="bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-900/30 rounded-3xl p-6">
                      <h3 className="text-red-700 dark:text-red-400 font-bold mb-4 flex items-center gap-2">⚠️ Out of Stock</h3>
                      <div className="flex flex-wrap gap-2">
                         {cartResult.unavailable.map((item: any, i: number) => (
                           <span key={i} className="bg-white dark:bg-red-900/20 text-red-600 dark:text-red-300 px-3 py-1.5 rounded-lg text-sm font-medium border border-red-100 dark:border-red-900/50">
                             {item.original_query}
                           </span>
                         ))}
                      </div>
                   </div>
                )}
                
              </motion.div>
            </AnimatePresence>
          )}
        </div>
      </div>
    </div>
  );
}
