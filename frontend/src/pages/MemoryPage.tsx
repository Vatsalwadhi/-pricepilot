import { useState } from 'react';
import { Settings, Save, CheckCircle, BrainCircuit } from 'lucide-react';
import { motion } from 'framer-motion';
import { useMemory } from '../contexts/MemoryContext';

export default function MemoryPage() {
  const { memory, updateMemory } = useMemory();
  const [diet, setDiet] = useState(memory.diet);
  const [budget, setBudget] = useState(memory.budget);
  const [delivery, setDelivery] = useState(memory.deliverySpeedPreference);
  const [customNotes, setCustomNotes] = useState(memory.customNotes);
  const [isSaved, setIsSaved] = useState(false);

  const handleSave = () => {
    updateMemory({
      diet,
      budget,
      deliverySpeedPreference: delivery,
      customNotes
    });
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 3000);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 animate-fade-in">
      <div className="flex items-center gap-3 border-b border-gray-200 dark:border-gray-800 pb-6 mb-8">
        <div className="p-3 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 rounded-2xl">
          <BrainCircuit size={28} />
        </div>
        <div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-900 dark:text-white tracking-tight font-display">Shopping Memory</h1>
          <p className="text-gray-500 mt-1">Teach the AI Assistant about your preferences.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="bg-white dark:bg-gray-900 rounded-3xl p-6 md:p-8 border border-gray-200 dark:border-gray-800 shadow-sm">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
            <Settings size={20} className="text-blue-500" /> Preferences
          </h2>
          
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">Dietary Preferences</label>
              <input 
                type="text" 
                value={diet}
                onChange={(e) => setDiet(e.target.value)}
                placeholder="e.g. Vegan, Gluten-free, Keto" 
                className="w-full bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-blue-500/50 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">Typical Budget Constraint</label>
              <input 
                type="text" 
                value={budget}
                onChange={(e) => setBudget(e.target.value)}
                placeholder="e.g. Under ₹500, Premium brands only" 
                className="w-full bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-blue-500/50 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">Delivery Speed Priority</label>
              <select 
                value={delivery}
                onChange={(e) => setDelivery(e.target.value)}
                className="w-full bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-blue-500/50 dark:text-white"
              >
                <option value="Fastest">Fastest (10 mins)</option>
                <option value="Cheapest">Cheapest (don't care about time)</option>
                <option value="Balanced">Balanced</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">Custom Instructions</label>
              <textarea 
                value={customNotes}
                onChange={(e) => setCustomNotes(e.target.value)}
                placeholder="e.g. I always want Amul milk. Never suggest Swiggy Instamart." 
                className="w-full h-32 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-blue-500/50 resize-none dark:text-white"
              />
            </div>

            <button 
              onClick={handleSave}
              className="w-full flex items-center justify-center gap-2 bg-indigo-600 text-white font-bold py-3.5 rounded-xl hover:bg-indigo-700 transition-colors shadow-lg shadow-indigo-500/30"
            >
              {isSaved ? <CheckCircle size={18} /> : <Save size={18} />}
              {isSaved ? "Saved to Memory" : "Save Preferences"}
            </button>
          </div>
        </div>

        <div className="hidden md:flex flex-col items-center justify-center bg-indigo-50 dark:bg-indigo-900/10 rounded-3xl border border-indigo-100 dark:border-indigo-900/30 p-8 text-center relative overflow-hidden">
           <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
           <BrainCircuit size={64} className="text-indigo-300 dark:text-indigo-800 mb-6" />
           <h3 className="text-2xl font-bold text-indigo-900 dark:text-indigo-300 mb-3">AI Personalization</h3>
           <p className="text-indigo-700 dark:text-indigo-400 font-medium">
             The information you save here is injected directly into the AI's prompt as context. When you ask the chatbot a question, it will automatically consider your diet, budget, and brand loyalties to give you the perfect recommendation.
           </p>
        </div>
      </div>
    </div>
  );
}
