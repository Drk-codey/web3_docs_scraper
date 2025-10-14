import { useState } from "react";
import { X, Sparkles } from "lucide-react";

export default function ScrapeModal({ onClose, onScrape }) {
  const [url, setUrl] = useState("");
  const [maxPages, setMaxPages] = useState(5);
  const [maxDepth, setMaxDepth] = useState(2);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url) return;

    setLoading(true);
    try {
      await onScrape(url, maxPages, maxDepth);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 rounded-2xl max-w-lg w-full p-8 border border-gray-700 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="bg-indigo-600/20 p-2 rounded-lg">
              <Sparkles className="w-6 h-6 text-indigo-400" />
            </div>
            <h2 className="text-2xl font-bold text-white">New Scraping Job</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* URL Input */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Documentation URL
            </label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://docs.example.com"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition"
              required
            />
            <p className="text-xs text-gray-500 mt-2">
              Enter the URL of the documentation you want to scrape
            </p>
          </div>

          {/* Max Pages */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Max Pages: {maxPages}
            </label>
            <input
              type="range"
              min="1"
              max="20"
              value={maxPages}
              onChange={(e) => setMaxPages(parseInt(e.target.value))}
              className="w-full accent-indigo-600"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>1 page</span>
              <span>20 pages</span>
            </div>
          </div>

          {/* Max Depth */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Crawl Depth: {maxDepth}
            </label>
            <input
              type="range"
              min="1"
              max="5"
              value={maxDepth}
              onChange={(e) => setMaxDepth(parseInt(e.target.value))}
              className="w-full accent-indigo-600"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>1 level</span>
              <span>5 levels</span>
            </div>
          </div>

          {/* Info Box */}
          <div className="bg-indigo-500/10 border border-indigo-500/30 rounded-lg p-4">
            <p className="text-sm text-indigo-400">
              <strong>Note:</strong> Larger values will take longer to process
              but provide more comprehensive summaries.
            </p>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-700 hover:bg-gray-600 text-white px-4 py-3 rounded-lg transition font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !url}
              className="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-3 rounded-lg transition font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Starting..." : "Start Scraping"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}