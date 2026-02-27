import { useState, useEffect } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || ''

export default function CompareModal({ plans, userProfile, onClose }) {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    const run = async () => {
      setLoading(true)
      setError('')
      try {
        const res = await fetch(`${API_BASE}/api/compare`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            plan_names: plans.map((p) => p.plan_name),
            user_profile: userProfile,
          }),
        })
        if (!res.ok) throw new Error((await res.json()).detail || 'Compare failed')
        setResult(await res.json())
      } catch (e) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    }
    run()
  }, [])

  return (
    <div
      className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-2xl max-w-3xl w-full max-h-[88vh] overflow-y-auto animate-fadeIn"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 p-6 text-white sticky top-0 z-10">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-bold">⚖️ Side-by-Side Comparison</h2>
              <p className="text-white/70 text-sm mt-0.5">
                {plans.map((p) => p.plan_name).join(' vs ')}
              </p>
            </div>
            <button onClick={onClose} className="text-white/70 hover:text-white text-3xl leading-none">
              ×
            </button>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {loading && (
            <div className="text-center py-14">
              <div className="animate-spin w-12 h-12 border-4 border-indigo-600 border-t-transparent rounded-full mx-auto mb-4" />
              <p className="text-gray-500 font-medium">Comparing plans…</p>
              <p className="text-gray-400 text-sm mt-1">This may take a few seconds</p>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-4">
              ⚠️ {error}
            </div>
          )}

          {result && (
            <>
              {/* Verdict banner */}
              <div className="bg-gradient-to-br from-indigo-50 to-purple-50 border border-indigo-200 rounded-2xl p-5">
                <p className="text-xs font-semibold text-indigo-500 uppercase tracking-widest mb-2">
                  Verdict
                </p>
                <div className="flex items-center gap-3 mb-3">
                  <span className="text-3xl">🏆</span>
                  <div>
                    <p className="text-xs text-indigo-500">Winner</p>
                    <p className="font-extrabold text-xl text-indigo-900">{result.winner}</p>
                  </div>
                </div>
                <p className="text-gray-700 text-sm leading-relaxed">{result.verdict}</p>
              </div>

              {/* Comparison table */}
              {result.comparison_table?.length > 0 && (
                <div>
                  <h3 className="font-bold text-gray-800 mb-3 text-lg">Feature-by-Feature</h3>
                  <div className="overflow-x-auto rounded-xl border border-gray-200 shadow-sm">
                    <table className="min-w-full text-sm">
                      <thead className="bg-gray-50 text-gray-500 text-xs uppercase tracking-wide">
                        <tr>
                          <th className="px-4 py-3 text-left min-w-[120px]">Aspect</th>
                          {plans.map((p) => (
                            <th key={p.plan_name} className="px-4 py-3 text-center">
                              {p.plan_name}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100 bg-white">
                        {result.comparison_table.map((row, i) => (
                          <tr key={i} className="hover:bg-gray-50 transition">
                            <td className="px-4 py-3 font-medium text-gray-700">
                              <div>{row.aspect}</div>
                              {row.why && (
                                <div className="text-xs text-gray-400 mt-0.5">{row.why}</div>
                              )}
                            </td>
                            {plans.map((p) => (
                              <td
                                key={p.plan_name}
                                className={`px-4 py-3 text-center ${
                                  row.winner_plan === p.plan_name
                                    ? 'font-bold text-green-700 bg-green-50'
                                    : 'text-gray-600'
                                }`}
                              >
                                {(() => {
                                  if (row.values?.[p.plan_name]) return row.values[p.plan_name]
                                  const lower = p.plan_name.toLowerCase()
                                  const ci = Object.entries(row.values || {}).find(
                                    ([k]) => k.toLowerCase() === lower
                                  )
                                  if (ci) return ci[1]
                                  const words = new Set(p.plan_name.toLowerCase().split(' '))
                                  const best = Object.entries(row.values || {}).reduce(
                                    (acc, [k, v]) => {
                                      const kw = new Set(k.toLowerCase().split(' '))
                                      const overlap = [...words].filter(w => kw.has(w)).length /
                                        Math.max(new Set([...words, ...kw]).size, 1)
                                      return overlap > acc.score ? { score: overlap, val: v } : acc
                                    },
                                    { score: 0, val: null }
                                  )
                                  return best.score > 0.25 ? best.val : '—'
                                })()}
                                {row.winner_plan === p.plan_name && (
                                  <span className="ml-1 text-green-500">✓</span>
                                )}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Detailed per-plan breakdown */}
              {result.detailed_comparison?.length > 0 && (
                <div>
                  <h3 className="font-bold text-gray-800 mb-3 text-lg">Detailed Breakdown</h3>
                  <div
                    className={`grid gap-4 ${
                      result.detailed_comparison.length >= 2 ? 'md:grid-cols-2' : ''
                    }`}
                  >
                    {result.detailed_comparison.map((plan, i) => (
                      <div key={i} className="border border-gray-200 rounded-xl p-5 bg-gray-50">
                        <div className="flex items-center gap-2 mb-3">
                          {result.winner === plan.plan_name && (
                            <span className="text-xl">🏆</span>
                          )}
                          <h4 className="font-bold text-gray-800">{plan.plan_name}</h4>
                        </div>
                        <p className="text-xs text-gray-500 mb-3">
                          Best for:{' '}
                          <span className="text-blue-600 font-semibold">{plan.best_for}</span>
                        </p>
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <p className="text-xs font-bold text-green-700 mb-1">✅ Strengths</p>
                            <ul className="space-y-1">
                              {plan.strengths?.map((s, j) => (
                                <li key={j} className="text-xs text-gray-600">
                                  • {s}
                                </li>
                              ))}
                            </ul>
                          </div>
                          <div>
                            <p className="text-xs font-bold text-red-600 mb-1">⚠️ Weaknesses</p>
                            <ul className="space-y-1">
                              {plan.weaknesses?.map((w, j) => (
                                <li key={j} className="text-xs text-gray-600">
                                  • {w}
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
