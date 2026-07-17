import React from 'react';
import { motion } from 'framer-motion';
import { Loader2, CheckCircle2, XCircle, AlertCircle } from 'lucide-react';
import { PLATFORMS } from '../lib/constants';

export type ProviderStatus = 'searching' | 'completed' | 'failed' | 'not_serviceable';

interface ProviderStatusCardProps {
  providerKey: string;
  status: ProviderStatus;
  productCount?: number;
}

export default function ProviderStatusCard({ providerKey, status, productCount = 0 }: ProviderStatusCardProps) {
  const platform = PLATFORMS[providerKey as keyof typeof PLATFORMS] || {
    name: providerKey,
    color: '#6b7280',
    gradient: 'from-gray-400 to-gray-500',
    logo_url: ''
  };

  const getStatusContent = () => {
    switch (status) {
      case 'searching':
        return (
          <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400">
            <Loader2 size={16} className="animate-spin" />
            <span className="text-sm font-medium">Searching...</span>
          </div>
        );
      case 'completed':
        return (
          <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
            <CheckCircle2 size={16} />
            <span className="text-sm font-medium">{productCount} products</span>
          </div>
        );
      case 'failed':
        return (
          <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
            <XCircle size={16} />
            <span className="text-sm font-medium">Failed</span>
          </div>
        );
      case 'not_serviceable':
        return (
          <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
            <AlertCircle size={16} />
            <span className="text-sm font-medium">Not Serviceable</span>
          </div>
        );
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`relative overflow-hidden rounded-2xl bg-white dark:bg-gray-900 border ${
        status === 'searching' 
          ? 'border-blue-200 dark:border-blue-900/50 shadow-md shadow-blue-500/10' 
          : 'border-gray-200 dark:border-gray-800'
      } p-4 transition-all duration-300`}
    >
      {/* Top Accent Line */}
      <div 
        className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${platform.gradient}`} 
        style={status === 'searching' ? { animation: 'shimmer 2s infinite linear', backgroundSize: '200% 100%' } : {}}
      />
      
      <div className="flex items-center justify-between mt-1">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gray-50 dark:bg-gray-800 p-2 flex items-center justify-center border border-gray-100 dark:border-gray-700">
            {platform.logo_url ? (
              <img src={platform.logo_url} alt={platform.name} className="w-full h-full object-contain" />
            ) : (
              <div className="w-full h-full rounded-full" style={{ backgroundColor: platform.color }} />
            )}
          </div>
          <div>
            <h3 className="font-bold text-gray-900 dark:text-white text-sm">{platform.name}</h3>
            {getStatusContent()}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
