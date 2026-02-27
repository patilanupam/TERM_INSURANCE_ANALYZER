export default function AIRecommendation({ summary, topPick, totalAnalyzed }) {
  return (
    <div className="bg-gradient-to-br from-blue-600 to-indigo-700 text-white rounded-2xl p-8 shadow-xl">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <div className="bg-white/20 rounded-full p-2">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.347.224A2 2 0 0113 18.56V20a2 2 0 01-2 2h-2a2 2 0 01-2-2v-1.44a2 2 0 00-.874-1.636l-.346-.225z"
            />
          </svg>
        </div>
        <div>
          <p className="text-white/70 text-sm">Plan Recommendation</p>
          <p className="font-bold text-lg">{totalAnalyzed} plans analyzed</p>
        </div>
      </div>

      {/* Top Pick */}
      <div className="bg-white/20 rounded-xl px-5 py-3 mb-5 flex items-center gap-3">
        <span className="text-3xl">🏆</span>
        <div>
          <p className="text-white/70 text-xs uppercase tracking-wide">Top Pick</p>
          <p className="font-bold text-xl">{topPick}</p>
        </div>
      </div>

      {/* Summary */}
      <p className="text-white/90 leading-relaxed">{summary}</p>
    </div>
  )
}
