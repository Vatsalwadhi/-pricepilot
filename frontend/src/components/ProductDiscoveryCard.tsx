import { motion } from "framer-motion";
import { ChevronRight } from "lucide-react";
import { Link } from "react-router-dom";
import type { ProductDiscovery } from "../types";
import { formatCurrency } from "../services/format";

type ProductDiscoveryCardProps = {
  product: ProductDiscovery;
  searchId: string | number;
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 }
};

export default function ProductDiscoveryCard({ product, searchId }: ProductDiscoveryCardProps) {
  const hasMultipleOffers = product.offers_count > 1;
  const isRange = hasMultipleOffers && product.lowest_price !== product.highest_price;

  return (
    <motion.div
      variants={item}
      className="group relative flex flex-col overflow-hidden rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 transition-all duration-300 hover:shadow-xl hover:shadow-blue-500/10 hover:border-blue-200 dark:hover:border-blue-800"
    >
      <div className="relative aspect-[4/3] w-full bg-white p-6 flex items-center justify-center border-b border-gray-100 dark:border-gray-800">
        {product.image ? (
          <img
            src={product.image}
            alt={product.display_name}
            className="h-full w-full object-contain mix-blend-multiply drop-shadow-sm transition-transform duration-500 group-hover:scale-105"
            loading="lazy"
            referrerPolicy="no-referrer"
          />
        ) : (
          <div className="flex h-full items-center justify-center text-gray-300">
            <span className="text-sm font-medium">No image</span>
          </div>
        )}
      </div>

      <div className="flex flex-1 flex-col p-5">
        <div className="flex justify-between items-start mb-2">
          <div className="text-[11px] font-bold text-gray-400 uppercase tracking-wider line-clamp-1 mr-2">
            {product.brand || "Generic"}
          </div>
        </div>
        
        <h3 className="line-clamp-2 text-base font-semibold text-gray-900 dark:text-gray-100 flex-1 leading-snug">
          {product.display_name}
        </h3>

        <div className="mt-2 text-sm font-medium text-gray-500 dark:text-gray-400">
          {product.quantity || "-"}
        </div>

        <div className="mt-4 mb-4">
          <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">
            {isRange ? "Price range" : "Best price"}
          </div>
          <div className="flex items-end gap-2">
            <span className="text-2xl font-bold text-gray-900 dark:text-white leading-none">
              {formatCurrency(product.lowest_price, "INR")}
            </span>
            {isRange && (
              <span className="text-sm font-medium text-gray-500 dark:text-gray-400 pb-0.5">
                - {formatCurrency(product.highest_price, "INR")}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-1.5 mb-5 flex-wrap">
          {product.available_platforms.map((p, i) => (
            <div key={i} className="flex items-center justify-center bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md p-1" title={p.name}>
              {p.logo_url ? (
                <img src={p.logo_url} alt={p.name} className="w-4 h-4 object-contain rounded-sm" />
              ) : (
                <span className="text-[10px] px-1 font-bold">{p.name[0]}</span>
              )}
            </div>
          ))}
          <span className="text-xs text-gray-500 ml-1">
            {product.offers_count} {product.offers_count === 1 ? "offer" : "offers"}
          </span>
        </div>

        <Link
          to={`/comparison/${searchId}/product/${encodeURIComponent(product.normalized_id)}`}
          className="mt-auto flex items-center justify-center gap-2 rounded-xl bg-blue-600 py-3 text-sm font-bold text-white transition-all hover:bg-blue-700 shadow-sm shadow-blue-500/20 active:scale-[0.98]"
        >
          Compare Prices
          <ChevronRight size={16} />
        </Link>
      </div>
    </motion.div>
  );
}
