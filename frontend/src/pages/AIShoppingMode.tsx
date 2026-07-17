import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Bot, User, Loader2, BrainCircuit, Sparkles, ShoppingBag, CheckCircle, ArrowRight } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { cn } from '../lib/cn';
import { useMemory } from '../contexts/MemoryContext';

type Message = {
  role: 'user' | 'model';
  content: string;
};

export default function AIShoppingMode() {
  const { memory } = useMemory();
  const [messages, setMessages] = useState<Message[]>([
    { role: 'model', content: "Hi! I'm your AI Grocery Copilot. Tell me what you're trying to achieve (e.g. 'Feed a family of 4 for ₹1500 this week', 'Plan a high-protein keto diet')." }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  
  // Dashboard state
  const [shoppingList, setShoppingList] = useState<any[] | null>(null);
  const [optimizationResult, setOptimizationResult] = useState<any | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSend = async (text: string = input) => {
    if (!text.trim()) return;
    
    const userMsg: Message = { role: 'user', content: text };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput('');
    setIsTyping(true);

    try {
      const context = {
        currentPage: window.location.pathname,
        time: new Date().toISOString(),
        userPreferences: memory,
        activeShoppingList: shoppingList
      };
      
      const response = await fetch('http://127.0.0.1:8000/api/assistant/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: newMessages, context })
      });
      
      if (!response.body) throw new Error("No body returned");
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      
      let botResponse = "";
      setMessages([...newMessages, { role: 'model', content: "" }]);
      setIsTyping(false);

      let buffer = "";
      let streamBuffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        streamBuffer += decoder.decode(value, { stream: true });
        const lines = streamBuffer.split("\n");
        streamBuffer = lines.pop() || "";
        
        for (const line of lines) {
            if (line.startsWith("data: ")) {
                const dataStr = line.slice(6);
                if (dataStr === "[DONE]") {
                    break;
                }
                try {
                    const data = JSON.parse(dataStr);
                    if (data.content) {
                        buffer += data.content;
                        
                        // Check for state updates in the buffer
                        const stateUpdateRegex = /<<<STATE_UPDATE>>>(.*?)<<<END_STATE_UPDATE>>>/gs;
                        let match;
                        while ((match = stateUpdateRegex.exec(buffer)) !== null) {
                            try {
                                const stateUpdate = JSON.parse(match[1]);
                                if (stateUpdate.type === "shopping_plan_generated") {
                                    setShoppingList(stateUpdate.items);
                                } else if (stateUpdate.type === "cart_optimized") {
                                    setOptimizationResult(stateUpdate.result);
                                }
                            } catch (e) {
                                console.error("Error parsing state update JSON", e);
                            }
                        }
                        
                        // Remove state updates from what the user sees
                        const cleanContent = buffer.replace(/<<<STATE_UPDATE>>>.*?<<<END_STATE_UPDATE>>>/gs, "");
                        botResponse = cleanContent;
                        
                        setMessages([...newMessages, { role: 'model', content: botResponse }]);
                    }
                } catch (err) {}
            }
        }
      }
      
    } catch (e) {
      setMessages([...newMessages, { role: 'model', content: "I'm having trouble connecting right now. Please try again." }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 h-[calc(100vh-80px)] flex flex-col md:flex-row gap-6">
      
      {/* Left Panel: Chat Interface */}
      <div className="w-full md:w-1/2 flex flex-col bg-white dark:bg-gray-900 rounded-3xl shadow-xl overflow-hidden border border-gray-100 dark:border-gray-800">
        <div className="p-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white flex items-center gap-3">
          <BrainCircuit size={24} />
          <div>
            <h2 className="font-bold text-lg">AI Grocery Copilot</h2>
            <p className="text-xs text-blue-100">Plan, compare, and optimize in natural language</p>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg, idx) => (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              key={idx}
              className={cn(
                "flex max-w-[85%]",
                msg.role === 'user' ? "ml-auto" : "mr-auto"
              )}
            >
              {msg.role === 'model' && (
                <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400 mr-2 flex-shrink-0 mt-1">
                  <Bot size={16} />
                </div>
              )}
              <div
                className={cn(
                  "p-3 rounded-2xl shadow-sm text-sm overflow-hidden",
                  msg.role === 'user' 
                    ? "bg-blue-600 text-white rounded-tr-sm" 
                    : "bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 rounded-tl-sm"
                )}
              >
                {msg.role === 'model' ? (
                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    <ReactMarkdown>{msg.content || '...'}</ReactMarkdown>
                  </div>
                ) : (
                  msg.content
                )}
              </div>
            </motion.div>
          ))}
          
          {isTyping && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex mr-auto max-w-[85%]">
              <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400 mr-2">
                <Bot size={16} />
              </div>
              <div className="p-4 bg-gray-100 dark:bg-gray-800 rounded-2xl rounded-tl-sm flex gap-1.5 items-center">
                <div className="w-2 h-2 rounded-full bg-blue-500 animate-bounce" />
                <div className="w-2 h-2 rounded-full bg-blue-500 animate-bounce" style={{ animationDelay: '0.2s' }} />
                <div className="w-2 h-2 rounded-full bg-blue-500 animate-bounce" style={{ animationDelay: '0.4s' }} />
              </div>
            </motion.div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Suggestion Chips */}
        {messages.length === 1 && (
          <div className="px-4 pb-2 flex flex-wrap gap-2">
            {[
              "Feed 4 people for ₹1500 this week",
              "Plan a high-protein keto diet",
              "Healthy breakfast shopping list",
              "Vegetarian groceries for 7 days"
            ].map(prompt => (
              <button
                key={prompt}
                onClick={() => handleSend(prompt)}
                className="text-xs bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 py-1.5 px-3 rounded-full transition-colors"
              >
                {prompt}
              </button>
            ))}
          </div>
        )}

        <div className="p-4 border-t border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-950/50">
          <form
            onSubmit={(e) => { e.preventDefault(); handleSend(); }}
            className="flex gap-2 relative"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask the AI Copilot..."
              className="flex-1 rounded-full pl-5 pr-12 py-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500/50 dark:text-white shadow-sm"
            />
            <button
              type="submit"
              disabled={!input.trim() || isTyping}
              className="absolute right-1.5 top-1.5 bottom-1.5 w-10 bg-blue-600 hover:bg-blue-700 text-white rounded-full flex items-center justify-center transition-colors disabled:opacity-50 disabled:hover:bg-blue-600"
            >
              <Send size={16} />
            </button>
          </form>
        </div>
      </div>

      {/* Right Panel: Shopping Plan Dashboard */}
      <div className="w-full md:w-1/2 flex flex-col gap-6 overflow-y-auto">
        
        {/* Placeholder if nothing generated */}
        {!shoppingList && !optimizationResult && (
            <div className="flex-1 flex flex-col items-center justify-center text-gray-400 dark:text-gray-600 border-2 border-dashed border-gray-200 dark:border-gray-800 rounded-3xl p-8">
                <Sparkles size={48} className="mb-4 opacity-50" />
                <h3 className="text-xl font-medium text-gray-700 dark:text-gray-300 mb-2">No Active Plan</h3>
                <p className="text-center text-sm max-w-sm">
                    Tell the AI what you want to achieve, and your generated shopping plan, cost estimates, and optimization results will appear here.
                </p>
            </div>
        )}

        {/* Shopping List view */}
        {shoppingList && (
            <div className="shrink-0 bg-white dark:bg-gray-900 rounded-3xl shadow-sm border border-gray-200 dark:border-gray-800 overflow-hidden">
                <div className="p-4 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between">
                    <h3 className="font-bold flex items-center gap-2">
                        <ShoppingBag size={18} className="text-blue-500" />
                        Generated Grocery List
                    </h3>
                    <span className="text-xs font-medium px-2.5 py-1 bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 rounded-full">
                        {shoppingList.length} items
                    </span>
                </div>
                <div className="p-0">
                    <ul className="divide-y divide-gray-100 dark:divide-gray-800">
                        {shoppingList.map((item, idx) => (
                            <li key={idx} className="flex items-center justify-between p-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                                <span className="font-medium text-gray-900 dark:text-gray-100">{item.name}</span>
                                <span className="text-sm bg-gray-100 dark:bg-gray-800 px-3 py-1 rounded-lg text-gray-600 dark:text-gray-400 font-medium">
                                    {item.quantity}
                                </span>
                            </li>
                        ))}
                    </ul>
                </div>

                <div className="p-4 bg-gray-50 dark:bg-gray-950 border-t border-gray-200 dark:border-gray-800">
                    {!optimizationResult ? (
                        <button 
                            onClick={() => handleSend("Optimize this cart for me across providers to find the cheapest prices.")}
                            disabled={isTyping}
                            className="w-full py-3 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white rounded-xl font-bold flex items-center justify-center gap-2 transition-all shadow-md hover:shadow-lg disabled:opacity-50"
                        >
                            <Sparkles size={18} />
                            Optimize Cart Prices
                        </button>
                    ) : (
                        <button 
                            onClick={() => { setOptimizationResult(null); handleSend("Re-optimize this cart to find better prices."); }}
                            disabled={isTyping}
                            className="w-full py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-xl font-medium flex items-center justify-center gap-2 transition-all"
                        >
                            Re-optimize Cart
                        </button>
                    )}
                </div>
            </div>
        )}

        {/* Optimization Dashboard */}
        {optimizationResult && (
            <div className="shrink-0 bg-white dark:bg-gray-900 rounded-3xl shadow-sm border border-gray-200 dark:border-gray-800 overflow-hidden flex flex-col">
                <div className="p-5 border-b border-gray-200 dark:border-gray-800 bg-gradient-to-r from-emerald-500/10 to-teal-500/10">
                    <h3 className="font-bold flex items-center gap-2 text-emerald-700 dark:text-emerald-400 mb-4">
                        <CheckCircle size={18} />
                        Optimization Complete
                    </h3>
                    
                    <div className="grid grid-cols-2 gap-4">
                        <div className="bg-white dark:bg-gray-950 p-4 rounded-2xl shadow-sm border border-emerald-100 dark:border-emerald-900/30">
                            <p className="text-xs text-gray-500 uppercase font-bold tracking-wider mb-1">Estimated Total</p>
                            <p className="text-2xl font-black text-gray-900 dark:text-white">₹{optimizationResult.grand_total}</p>
                        </div>
                        <div className="bg-gradient-to-br from-emerald-500 to-emerald-600 p-4 rounded-2xl shadow-md text-white">
                            <p className="text-xs text-emerald-100 uppercase font-bold tracking-wider mb-1">Total Savings</p>
                            <p className="text-2xl font-black">₹{optimizationResult.total_savings || 0}</p>
                        </div>
                    </div>
                </div>
                
                <div className="p-5 space-y-4">
                    <h4 className="text-sm font-bold text-gray-900 dark:text-gray-100 uppercase tracking-wider">Optimal Split</h4>
                    {optimizationResult.splits.map((split: any, idx: number) => (
                        <div key={idx} className="bg-gray-50 dark:bg-gray-800/50 rounded-2xl p-4 border border-gray-100 dark:border-gray-700">
                            <div className="flex justify-between items-center mb-3">
                                <span className="font-bold text-lg">{split.platform}</span>
                                <span className="font-bold text-emerald-600 dark:text-emerald-400">₹{split.subtotal}</span>
                            </div>
                            <ul className="space-y-2">
                                {split.items.map((item: any, i: number) => (
                                    <li key={i} className="flex justify-between text-sm items-center">
                                        {item.product_url ? (
                                            <a href={item.product_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 dark:text-blue-400 hover:underline truncate max-w-[70%] flex items-center gap-1">
                                                {item.matched_name || item.original_query}
                                            </a>
                                        ) : (
                                            <span className="text-gray-600 dark:text-gray-300 truncate max-w-[70%]">
                                                {item.matched_name || item.original_query}
                                            </span>
                                        )}
                                        <span className="font-medium">₹{item.price}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    ))}
                    
                    {optimizationResult.unavailable && optimizationResult.unavailable.length > 0 && (
                        <div className="bg-red-50 dark:bg-red-900/20 rounded-2xl p-4 border border-red-100 dark:border-red-800/30 mt-4">
                            <div className="flex justify-between items-center mb-3">
                                <span className="font-bold text-lg text-red-700 dark:text-red-400">Unavailable Items</span>
                            </div>
                            <ul className="space-y-2">
                                {optimizationResult.unavailable.map((item: any, i: number) => (
                                    <li key={i} className="flex justify-between text-sm items-center">
                                        <span className="text-red-600 dark:text-red-300 truncate max-w-[70%] line-through opacity-70">
                                            {item.original_query}
                                        </span>
                                        <span className="font-medium text-red-700 dark:text-red-400 text-xs uppercase tracking-wider">Out of stock</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            </div>
        )}

      </div>
    </div>
  );
}
