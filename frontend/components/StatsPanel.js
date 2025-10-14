import { FileText, Activity, TrendingUp } from "lucide-react";

export default function StatsPanel({ stats }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <div className="bg-gradient-to-br from-indigo-900/30 to-indigo-800/10 border border-indigo-700/30 rounded-xl p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-400 text-sm">Total Summaries</p>
            <p className="text-3xl font-bold text-white mt-1">
              {stats.total_summaries}
            </p>
          </div>
          <div className="bg-indigo-600/20 p-3 rounded-lg">
            <FileText className="w-6 h-6 text-indigo-400" />
          </div>
        </div>
      </div>

      <div className="bg-gradient-to-br from-purple-900/30 to-purple-800/10 border border-purple-700/30 rounded-xl p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-400 text-sm">Total Jobs</p>
            <p className="text-3xl font-bold text-white mt-1">
              {stats.total_jobs}
            </p>
          </div>
          <div className="bg-purple-600/20 p-3 rounded-lg">
            <Activity className="w-6 h-6 text-purple-400" />
          </div>
        </div>
      </div>

      <div className="bg-gradient-to-br from-green-900/30 to-green-800/10 border border-green-700/30 rounded-xl p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-400 text-sm">Last 7 Days</p>
            <p className="text-3xl font-bold text-white mt-1">
              {stats.recent_summaries_7days}
            </p>
          </div>
          <div className="bg-green-600/20 p-3 rounded-lg">
            <TrendingUp className="w-6 h-6 text-green-400" />
          </div>
        </div>
      </div>
    </div>
  );
}