import React from 'react';
import { motion } from 'framer-motion';

export type EmptyStateVariant = 'no-results' | 'no-location' | 'provider-error' | 'empty-favorites' | 'empty-cart' | 'default';

type EmptyStateProps = {
  title: string;
  message: string;
  variant?: EmptyStateVariant;
  action?: React.ReactNode;
};

export default function EmptyState({ title, message, variant = 'default', action }: EmptyStateProps) {
  const getEmoji = () => {
    switch (variant) {
      case 'no-results': return '🔍';
      case 'no-location': return '📍';
      case 'provider-error': return '⚠️';
      case 'empty-favorites': return '🤍';
      case 'empty-cart': return '🛒';
      default: return '✨';
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="rounded-3xl border border-dashed border-gray-200 dark:border-gray-800 bg-white/50 dark:bg-gray-900/50 backdrop-blur-sm px-6 py-16 text-center max-w-2xl mx-auto my-8"
    >
      <div className="text-6xl mb-6 select-none opacity-80 filter drop-shadow-md">{getEmoji()}</div>
      <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">{title}</h2>
      <p className="text-gray-500 dark:text-gray-400 mb-6 max-w-md mx-auto leading-relaxed">{message}</p>
      {action && (
        <div className="flex justify-center">
          {action}
        </div>
      )}
    </motion.div>
  );
}
