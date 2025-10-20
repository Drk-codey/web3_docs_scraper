import { useRouter } from 'next/router';
import { ExternalLink, FileText, Calendar, ArrowRight } from 'lucide-react';

export default function SummaryCard({ summary, onDelete }) {
  const router = useRouter();

  const handleViewDetails = () => {
    router.push(`/summary/${summary.id}`);
  };

  return (
    <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700 hover:border-indigo-500/30 transition-all duration-300 hover:shadow-2xl hover:shadow-indigo-500/10">
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-xl font-bold text-white line-clamp-2 flex-1">
          {summary.title}
        </h3>
        <button
          onClick={handleViewDetails}
          className="ml-2 bg-indigo-600 hover:bg-indigo-500 transition p-2 rounded-lg"
          title="View full details"
        >
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      <p className="text-gray-400 text-sm mb-4 line-clamp-3">
        {summary.summary.substring(0, 150)}...
      </p>

      <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1">
            <Calendar className="w-4 h-4" />
            <span>{new Date(summary.created_at).toLocaleDateString()}</span>
          </div>
          <div className="flex items-center gap-1">
            <FileText className="w-4 h-4" />
            <span>ID: {summary.id}</span>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <a
          href={summary.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-indigo-400 hover:text-indigo-300 transition flex items-center gap-1 text-sm"
        >
          <ExternalLink className="w-4 h-4" />
          Visit Source
        </a>

        <button
          onClick={() => onDelete(summary.id)}
          className="text-red-400 hover:text-red-300 transition text-sm"
        >
          Delete
        </button>
      </div>

      <button
        onClick={handleViewDetails}
        className="w-full mt-4 bg-indigo-600 hover:bg-indigo-500 transition text-white py-2 rounded-lg flex items-center justify-center gap-2"
      >
        View Full Summary
        <ArrowRight className="w-4 h-4" />
      </button>
    </div>
  );
}