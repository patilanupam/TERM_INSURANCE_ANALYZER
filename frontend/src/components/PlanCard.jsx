const RANK_STYLE = {
  1: 'border-yellow-400 bg-yellow-50',
  2: 'border-gray-300 bg-gray-50',
  3: 'border-orange-300 bg-orange-50',
}

const MEDAL = { 1: '🥇', 2: '🥈', 3: '🥉' }

function ScoreRing({ score }) {
  const radius = 26
  const circumference = 2 * Math.PI * radius
  const filled = (score / 100) * circumference
  const color = score >= 80 ? '#16a34a' : score >= 60 ? '#2563eb' : '#d97706'
  return (
    <div className="relative w-14 h-14 flex-shrink-0">
      <svg className="w-14 h-14 -rotate-90" viewBox="0 0 64 64">
        <circle cx="32" cy="32" r={radius} fill="none" stroke="#e2e8f0" strokeWidth="5" />
        <circle
          cx="32"
          cy="32"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="5"
          strokeDasharray={circumference}
          strokeDashoffset={circumference - filled}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 1s ease' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-sm font-extrabold text-gray-800 leading-none">{score}</span>
        <span className="text-[9px] text-gray-400 leading-none">/100</span>
      </div>
    </div>
  )
}

export default function PlanCard({ plan, onToggleCompare, compareSelected }) {
  const {
    rank,
    plan_name,
    provider,
    score,
    reason,
    pros = [],
    cons = [],
    within_budget,
    claim_settlement_ratio,
  } = plan

  const borderClass = RANK_STYLE[rank] || 'border-blue-100 bg-white'

  return (
    <div
      className={`border-2 rounded-2xl p-5 transition-all hover:shadow-lg ${borderClass} ${
        compareSelected ? 'ring-2 ring-offset-1 ring-indigo-500' : ''
      }`}
    >
      {/* Header row */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-2xl flex-shrink-0">{MEDAL[rank] || `#${rank}`}</span>
          <div className="min-w-0">
            <h3 className="font-bold text-gray-800 text-base leading-tight truncate">
              {plan_name}
            </h3>
            <p className="text-sm text-gray-500 truncate">{provider}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {onToggleCompare && (
            <label className="flex items-center gap-1 cursor-pointer text-xs text-gray-500 hover:text-indigo-600 transition">
              <input
                type="checkbox"
                checked={compareSelected}
                onChange={() => onToggleCompare(plan)}
                className="w-3.5 h-3.5 accent-indigo-600"
              />
              <span>Compare</span>
            </label>
          )}
          <ScoreRing score={score} />
        </div>
      </div>

      {/* Badges */}
      <div className="flex flex-wrap gap-2 mb-3">
        <span
          className={`text-xs px-2.5 py-0.5 rounded-full font-semibold ${
            within_budget ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'
          }`}
        >
          {within_budget ? '✓ Within Budget' : '✗ Exceeds Budget'}
        </span>
        <span className="text-xs px-2.5 py-0.5 rounded-full font-semibold bg-blue-100 text-blue-700">
          CSR: {claim_settlement_ratio}%
        </span>
      </div>

      {/* Reason */}
      <p className="text-sm text-gray-700 mb-4 leading-relaxed">{reason}</p>

      {/* Pros & Cons */}
      <div className="grid grid-cols-2 gap-3 pt-3 border-t border-gray-100">
        <div>
          <p className="text-xs font-bold text-green-700 mb-1.5">✅ Pros</p>
          <ul className="space-y-1">
            {pros.map((p, i) => (
              <li key={i} className="text-xs text-gray-600 leading-relaxed">
                • {p}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="text-xs font-bold text-red-600 mb-1.5">⚠️ Cons</p>
          <ul className="space-y-1">
            {cons.map((c, i) => (
              <li key={i} className="text-xs text-gray-600 leading-relaxed">
                • {c}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
