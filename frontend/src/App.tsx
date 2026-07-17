import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";

import Layout from "./components/Layout";
import HistoryPage from "./pages/HistoryPage";
import HomePage from "./pages/HomePage";
import ComparisonPage from "./pages/ComparisonPage";
import ResultsPage from "./pages/ResultsPage";
import FavoritesPage from "./pages/FavoritesPage";
import CartPage from "./pages/CartPage";
import MemoryPage from "./pages/MemoryPage";
import AIShoppingMode from "./pages/AIShoppingMode";
import AIChatbot from "./components/AIChatbot";

function AnimatedRoutes() {
  const location = useLocation();
  
  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<HomePage />} />
        <Route path="/results/:id" element={<ResultsPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/favorites" element={<FavoritesPage />} />
        <Route path="/cart" element={<CartPage />} />
        <Route path="/memory" element={<MemoryPage />} />
        <Route path="/ai-shopping" element={<AIShoppingMode />} />
        <Route path="/comparison/:comparisonId/product/:normalizedProductId" element={<ComparisonPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AnimatePresence>
  );
}

export default function App() {
  return (
    <Layout>
      <AnimatedRoutes />
      <AIChatbot />
    </Layout>
  );
}
