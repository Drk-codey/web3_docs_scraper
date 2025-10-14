import { Eye, Trash2, Calendar, Link as LinkIcon } from "lucide-react";
import { format } from "date-fns";

export default function SummaryCard({ summary, onView, onDelete }) {
  const formatDate = (dateString) => {
    try {
      return format(new Date(dateString), "MMM dd, yyyy HH:mm");
    } catch {
      return dateString;
    }
  };

  const truncateText = (text, maxLength = 200) => {
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength) + "...";
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "completed":
        return "bg-green-500/10 text-green-400 border-green-500/30";
      case "processing":
        return "bg-yellow-500/10 text-yellow-400 border-yellow-500/30";
      case "failed":
        return "bg-red-500/10 text-red-400 border-red-500/30";
      default:
        return "bg-gray-500/10 text-gray-400 border-gray-500/30";
    }
  };

  return (
    <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700 hover:border-indigo-500/50 transition-all duration-300 hover:shadow-xl hover:shadow-indigo-500/10 flex flex-col">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <h3 className="text-lg font-semibold text-white line-clamp-2 flex-1">
          {summary.title}
        </h3>
        <span
          className={`px-2 py-1 rounded-lg text-xs font-medium border ml-2 ${getStatusColor(
            summary.status
          )}`}
        >
          {summary.status}
        </span>
      </div>

      {/* URL */}
      <div className="flex items-center gap-2 mb-3 text-sm text-gray-400">
        <LinkIcon className="w-4 h-4 flex-shrink-0" />
        <a
          href={summary.url}
          target="_blank"
          rel="noopener noreferrer"
          className="truncate hover:text-indigo-400 transition"
        >
          {summary.url}
        </a>
      </div>

      {/* Date */}
      <div className="flex items-center gap-2 mb-4 text-sm text-gray-500">
        <Calendar className="w-4 h-4" />
        <span>{formatDate(summary.created_at)}</span>
      </div>

      {/* Summary Preview */}
      <p className="text-gray-300 text-sm leading-relaxed mb-6 flex-1">
        {truncateText(summary.summary)}
      </p>

      {/* Actions */}
      <div className="flex gap-3">
        <button
          onClick={() => onView(summary.id)}
          className="flex-1 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-400 px-4 py-2 rounded-lg transition flex items-center justify-center gap-2 border border-indigo-500/30"
        >
          <Eye className="w-4 h-4" />
          View Full
        </button>
        <button
          onClick={() => onDelete(summary.id)}
          className="bg-red-600/20 hover:bg-red-600/30 text-red-400 px-4 py-2 rounded-lg transition flex items-center justify-center border border-red-500/30"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}