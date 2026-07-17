import { Link } from "react-router-dom";
import { Heart, Search } from "lucide-react";
import EmptyState from "../components/EmptyState";

export default function FavoritesPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 animate-fade-in">
      <div className="flex items-center gap-3 border-b border-gray-200 dark:border-gray-800 pb-6">
        <div className="p-3 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-2xl">
          <Heart size={28} />
        </div>
        <div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-900 dark:text-white tracking-tight font-display">Favorites</h1>
        </div>
      </div>
      <EmptyState 
        title="Favorites Upgrades" 
        message="The favorites page is currently being upgraded for the new Google Shopping-style comparison engine. Stay tuned!" 
        variant="no-results"
        action={
          <Link to="/" className="btn-primary mt-4">
            <Search size={18} /> Discover Products
          </Link>
        }
      />
    </div>
  );
}
