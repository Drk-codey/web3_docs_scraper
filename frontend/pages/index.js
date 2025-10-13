import { useState, useEffect } from "react";
import axios from "axios";
import SummaryCard from "../components/SummaryCard";

export default function Home() {
  const [summaries, setSummaries] = useState([]);
  const [loading, setLoading] = useState(true);
  // const backendURL = "http://127.0.0.1:8000";
  const backendURL = "http://localhost:8000/";

  useEffect(() => {
    axios.get(`${backendURL}/summaries`).then((res) => {
      setSummaries(res.data);
      setLoading(false);
    });
  }, []);

  const handleScrape = async () => {
    setLoading(true);
    await axios.post(`${backendURL}/scrape`);
    const res = await axios.get(`${backendURL}/summaries`);
    setSummaries(res.data);
    setLoading(false);
  };

  return (
    <main className="min-h-screen bg-black text-white p-10">
      <div className="max-w-5xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">⚡ Web3 Docs Scraper Dashboard</h1>
          <button
            onClick={handleScrape}
            className="bg-indigo-600 px-4 py-2 rounded-xl hover:bg-indigo-500 transition"
          >
            {loading ? "Scraping..." : "Scrape Latest Docs"}
          </button>
        </div>

        {loading ? (
          <p className="text-gray-400">Loading summaries...</p>
        ) : summaries.length === 0 ? (
          <p className="text-gray-400">No summaries found yet.</p>
        ) : (
          <div className="grid md:grid-cols-2 gap-6">
            {summaries.map((s, i) => (
              <SummaryCard
                key={i}
                title={s.filename.replace(".md", "")}
                content={s.content}
              />
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
