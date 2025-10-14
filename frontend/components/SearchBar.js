import { Search, RefreshCw } from "lucide-react";

export default function SearchBar({ searchTerm, setSearchTerm, onRefresh, isRefreshing }) {
  return (
    <div className="flex gap-3 mt-6">
      <div className="flex-1 relative">
        <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search summaries..."
          className="w-full bg-gray-800 border border-gray-700 rounded-xl pl-12 pr-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition"
        />
      </div>
      <button
        onClick={onRefresh}
        disabled={isRefreshing}
        className="bg-gray-800 border border-gray-700 hover:border-gray-600 px-4 rounded-xl transition disabled:opacity-50"
      >
        <RefreshCw className={`w-5 h-5 text-gray-400 ${isRefreshing ? 'animate-spin' : ''}`} />
      </button>
    </div>
  );
}