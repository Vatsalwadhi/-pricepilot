import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import ProviderStatusCard, { type ProviderStatus } from './ProviderStatusCard';
import { PLATFORMS } from '../lib/constants';

interface SearchLoadingStateProps {
  query: string;
}

export default function SearchLoadingState({ query }: SearchLoadingStateProps) {
  const [statuses, setStatuses] = useState<Record<string, ProviderStatus>>({
    blinkit: 'searching',
    zepto: 'searching',
    swiggy_instamart: 'searching',
    bigbasket: 'searching'
  });

  // Simulate staggered progress for the UI effect
  useEffect(() => {
    const timers: NodeJS.Timeout[] = [];
    
    const platforms = Object.keys(PLATFORMS);
    
    platforms.forEach((platform, index) => {
      // Simulate completion between 1s and 3.5s
      const delay = 1000 + (Math.random() * 2500) + (index * 500);
      
      const timer = setTimeout(() => {
        setStatuses(prev => ({
          ...prev,
          [platform]: Math.random() > 0.1 ? 'completed' : 'not_serviceable'
        }));
      }, delay);
      
      timers.push(timer);
    });

    return () => {
      timers.forEach(clearTimeout);
    };
  }, []);

  return (
    <div className="w-full max-w-5xl mx-auto space-y-8 animate-fade-in">
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Searching for "{query}"
        </h2>
        <p className="text-gray-500 dark:text-gray-400">
          Comparing prices across all platforms...
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Object.keys(PLATFORMS).map((key) => (
          <ProviderStatusCard 
            key={key} 
            providerKey={key} 
            status={statuses[key]} 
            productCount={statuses[key] === 'completed' ? Math.floor(Math.random() * 10) + 1 : 0}
          />
        ))}
      </div>

      <div className="mt-12 space-y-4">
        <div className="h-8 bg-gray-200 dark:bg-gray-800 rounded-lg w-1/4 animate-pulse"></div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4, 5, 6, 7, 8].map(n => (
            <div key={n} className="card p-4 animate-pulse h-80">
              <div className="w-full h-40 bg-gray-200 dark:bg-gray-800 rounded-xl mb-4"></div>
              <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-3/4 mb-2"></div>
              <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-1/2 mb-4"></div>
              <div className="flex justify-between items-end mt-auto">
                <div className="h-6 bg-gray-200 dark:bg-gray-800 rounded w-1/3"></div>
                <div className="h-8 bg-gray-200 dark:bg-gray-800 rounded-lg w-1/4"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
