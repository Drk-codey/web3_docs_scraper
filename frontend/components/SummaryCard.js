export default function SummaryCard({ title, content }) {
  return (
    <div className="bg-gray-900 text-white p-6 rounded-2xl shadow-lg border border-gray-700 hover:border-indigo-500 transition">
      <h2 className="text-xl font-bold mb-3">{title}</h2>
      <p className="text-gray-300 whitespace-pre-wrap leading-relaxed">
        {content.slice(0, 800)}...
      </p>
    </div>
  );
}
