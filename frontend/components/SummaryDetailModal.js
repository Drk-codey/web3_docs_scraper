import { X, Download, ExternalLink, Calendar } from "lucide-react";
import { format } from "date-fns";

export default function SummaryDetailModal({ summary, onClose }) {
  const formatDate = (dateString) => {
    try {
      return format(new Date(dateString), "MMMM dd, yyyy 'at' HH:mm");
    } catch {
      return dateString;
    }
  };

  const handleDownload = () => {
    const element = document.createElement("a");
    const file = new Blob([summary.summary], { type: "text/markdown" });
    element.href = URL.createObjectURL(file);
    element.download = `${summary.title.replace(/\s+/g, "_")}.md`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-gray-900 rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden border border-gray-700 shadow-2xl my-8">
        {/* Header */}
        <div className="sticky top-0 bg-gray-900 border-b border-gray-700 p-6 flex items-start justify-between z-10">
          <div className="flex-1 pr-4">
            <h2 className="text-2xl font-bold text-white mb-2">
              {summary.title}
            </h2>
            <div className="flex flex-wrap items-center gap-4 text-sm text-gray-400">
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                <span>{formatDate(summary.created_at)}</span>
              </div>
              <a
                href={summary.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 hover:text-indigo-400 transition"
              >
                <ExternalLink className="w-4 h-4" />
                <span className="truncate max-w-xs">View Source</span>
              </a>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition flex-shrink-0"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
          <div className="prose prose-invert prose-indigo max-w-none">
            <div
              className="text-gray-300 leading-relaxed whitespace-pre-wrap"
              dangerouslySetInnerHTML={{
                __html: formatMarkdown(summary.summary),
              }}
            />
          </div>
        </div>

        {/* Footer Actions */}
        <div className="sticky bottom-0 bg-gray-900 border-t border-gray-700 p-6 flex gap-3">
          <button
            onClick={handleDownload}
            className="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-3 rounded-lg transition flex items-center justify-center gap-2 font-medium"
          >
            <Download className="w-5 h-5" />
            Download Summary
          </button>
          <button
            onClick={onClose}
            className="bg-gray-700 hover:bg-gray-600 text-white px-6 py-3 rounded-lg transition font-medium"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

// Simple markdown formatter
function formatMarkdown(text) {
  return text
    // Headers
    .replace(/^### (.*$)/gim, '<h3 class="text-xl font-bold text-white mt-6 mb-3">$1</h3>')
    .replace(/^## (.*$)/gim, '<h2 class="text-2xl font-bold text-white mt-8 mb-4">$1</h2>')
    .replace(/^# (.*$)/gim, '<h1 class="text-3xl font-bold text-white mt-10 mb-5">$1</h1>')
    // Bold
    .replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>')
    // Italic
    .replace(/\*(.*?)\*/g, '<em class="italic">$1</em>')
    // Code blocks
    .replace(/```([\s\S]*?)```/g, '<pre class="bg-gray-800 p-4 rounded-lg overflow-x-auto my-4"><code class="text-sm text-gray-300">$1</code></pre>')
    // Inline code
    .replace(/`(.*?)`/g, '<code class="bg-gray-800 px-2 py-1 rounded text-indigo-400 text-sm">$1</code>')
    // Links
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-indigo-400 hover:text-indigo-300 underline">$1</a>')
    // Lists
    .replace(/^\- (.*$)/gim, '<li class="ml-4 mb-2">$1</li>')
    .replace(/^(\d+)\. (.*$)/gim, '<li class="ml-4 mb-2">$2</li>')
    // Paragraphs
    .replace(/\n\n/g, '</p><p class="mb-4">')
    .replace(/^(.+)$/gm, '<p class="mb-4">$1</p>');
}