const BADGE_COLOR = {
  policybazaar: 'bg-orange-100 text-orange-700',
  insurancedekho: 'bg-green-100 text-green-700',
  seed: 'bg-gray-100 text-gray-600',
}

const RANK_STYLE = {
  1: 'border-yellow-400 bg-yellow-50',
  2: 'border-gray-300 bg-gray-50',
  3: 'border-orange-300 bg-orange-50',
}

const MEDAL = { 1: '🥇', 2: '🥈', 3: '🥉' }

export default function PlanCard({ plan }) {
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
    <div className={`border-2 rounded-2xl p-6 transition-shadow hover:shadow-md ${borderClass}`}>
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{MEDAL[rank] || `#${rank}`}</span>
          <div>
            <h3 className="font-bold text-gray-800 text-lg leading-tight">{plan_name}</h3>
            <p className="text-sm text-gray-500">{provider}</p>
          </div>
        </div>
        <div className="text-right flex-shrink-0">
          <div className="text-3xl font-extrabold text-blue-600">{score}</div>
          <div className="text-xs text-gray-400">/ 100</div>
        </div>
      </div>

      {/* Badges */}
      <div className="flex flex-wrap gap-2 mb-3">
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${within_budget ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'}`}>
          {within_budget ? '✓ Within Budget' : '✗ Exceeds Budget'}
        </span>
        <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-blue-100 text-blue-700">
          CSR: {claim_settlement_ratio}%
        </span>
      </div>

      {/* Reason */}
      <p className="text-sm text-gray-700 mb-4">{reason}</p>

      {/* Pros & Cons */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <p className="text-xs font-semibold text-green-700 mb-1">✅ Pros</p>
          <ul className="space-y-1">
            {pros.map((p, i) => (
              <li key={i} className="text-xs text-gray-600">• {p}</li>
            ))}
          </ul>
        </div>
        <div>
          <p className="text-xs font-semibold text-red-600 mb-1">⚠️ Cons</p>
          <ul className="space-y-1">
            {cons.map((c, i) => (
              <li key={i} className="text-xs text-gray-600">• {c}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
