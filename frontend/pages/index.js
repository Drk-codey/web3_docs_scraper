import { useState, useEffect } from "react";
import axios from "axios";
import SummaryCard from "../components/SummaryCard";
import ScrapeModal from "../components/ScrapeModal";
import SummaryDetailModal from "../components/SummaryDetailModal";
import SearchBar from "../components/SearchBar";
import StatsPanel from "../components/StatsPanel";
import { RefreshCw, TrendingUp } from "lucide-react";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";

// Add error handling for missing backend URL
if (!BACKEND_URL) {
  console.error('BACKEND_URL is not defined. Please check your environment variables.');
}

export default function Home() {
  const [summaries, setSummaries] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [showScrapeModal, setShowScrapeModal] = useState(false);
  const [selectedSummary, setSelectedSummary] = useState(null);
  const [pollingJobId, setPollingJobId] = useState(null);

  useEffect(() => {
    fetchSummaries();
    fetchStats();
  }, []);

  useEffect(() => {
    if (searchTerm) {
      const delayDebounceFn = setTimeout(() => {
        fetchSummaries(searchTerm);
      }, 500);
      return () => clearTimeout(delayDebounceFn);
    } else {
      fetchSummaries();
    }
  }, [searchTerm]);

  // Poll job status
  useEffect(() => {
    if (!pollingJobId) return;

    const interval = setInterval(async () => {
      try {
        const res = await axios.get(`${BACKEND_URL}/jobs/${pollingJobId}`);
        if (res.data.status === "completed") {
          setPollingJobId(null);
          fetchSummaries();
          fetchStats();
        } else if (res.data.status === "failed") {
          setPollingJobId(null);
          setError(res.data.error || "Scraping job failed");
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [pollingJobId]);

  const fetchSummaries = async (search = "") => {
    try {
      setLoading(true);
      setError(null);
      const params = search ? { search, limit: 20 } : { limit: 20 };
      const res = await axios.get(`${BACKEND_URL}/summaries`, { params });
      setSummaries(res.data);
    } catch (err) {
      setError("Failed to load summaries. Please check if the backend is running.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const res = await axios.get(`${BACKEND_URL}/stats`);
      setStats(res.data);
    } catch (err) {
      console.error("Failed to fetch stats:", err);
    }
  };

  const handleScrape = async (url, maxPages, maxDepth) => {
    try {
      setError(null);
      const res = await axios.post(`${BACKEND_URL}/scrape`, {
        url,
        max_pages: maxPages,
        max_depth: maxDepth,
      });
      setPollingJobId(res.data.job_id);
      setShowScrapeModal(false);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to start scraping job");
    }
  };

  const handleDelete = async (id) => {
    if (!confirm("Are you sure you want to delete this summary?")) return;
    
    try {
      await axios.delete(`${BACKEND_URL}/summaries/${id}`);
      fetchSummaries();
      fetchStats();
    } catch (err) {
      setError("Failed to delete summary");
    }
  };

  const handleViewDetails = async (id) => {
    try {
      const res = await axios.get(`${BACKEND_URL}/summaries/${id}`);
      setSelectedSummary(res.data);
    } catch (err) {
      setError("Failed to load summary details");
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {/* Header */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                ⚡ Web3 Docs Scraper
              </h1>
              <p className="text-gray-400 mt-2">
                AI-powered documentation summarization
              </p>
            </div>
            <button
              onClick={() => setShowScrapeModal(true)}
              className="bg-indigo-600 px-6 py-3 rounded-xl hover:bg-indigo-500 transition flex items-center gap-2 shadow-lg shadow-indigo-500/50"
            >
              <TrendingUp className="w-5 h-5" />
              New Scrape
            </button>
          </div>

          {/* Stats Panel */}
          {stats && <StatsPanel stats={stats} />}

          {/* Search Bar */}
          <SearchBar 
            searchTerm={searchTerm} 
            setSearchTerm={setSearchTerm}
            onRefresh={() => fetchSummaries(searchTerm)}
            isRefreshing={loading}
          />
        </div>

        {/* Polling Status */}
        {pollingJobId && (
          <div className="mb-6 bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4 flex items-center gap-3">
            <RefreshCw className="w-5 h-5 animate-spin text-yellow-500" />
            <div>
              <p className="font-medium text-yellow-500">Scraping in progress...</p>
              <p className="text-sm text-gray-400">Job ID: {pollingJobId}</p>
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-500/10 border border-red-500/30 rounded-xl p-4">
            <p className="text-red-400">{error}</p>
          </div>
        )}

        {/* Loading State */}
        {loading && !pollingJobId ? (
          <div className="flex items-center justify-center py-20">
            <div className="flex flex-col items-center gap-4">
              <RefreshCw className="w-12 h-12 animate-spin text-indigo-500" />
              <p className="text-gray-400">Loading summaries...</p>
            </div>
          </div>
        ) : summaries.length === 0 ? (
          <div className="text-center py-20">
            <div className="bg-gray-800/50 rounded-2xl p-12 max-w-md mx-auto">
              <TrendingUp className="w-16 h-16 mx-auto mb-4 text-gray-600" />
              <p className="text-gray-400 mb-4">
                {searchTerm ? "No summaries found matching your search." : "No summaries yet. Start by scraping a documentation site!"}
              </p>
              <button
                onClick={() => setShowScrapeModal(true)}
                className="bg-indigo-600 px-6 py-3 rounded-xl hover:bg-indigo-500 transition"
              >
                Create First Summary
              </button>
            </div>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {summaries.map((summary) => (
              <SummaryCard
                key={summary.id}
                summary={summary}
                onView={handleViewDetails}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}
      </div>

      {/* Modals */}
      {showScrapeModal && (
        <ScrapeModal
          onClose={() => setShowScrapeModal(false)}
          onScrape={handleScrape}
        />
      )}

      {selectedSummary && (
        <SummaryDetailModal
          summary={selectedSummary}
          onClose={() => setSelectedSummary(null)}
        />
      )}
    </main>
  );
}