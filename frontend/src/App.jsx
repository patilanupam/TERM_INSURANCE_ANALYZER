import { useState, useEffect } from 'react'
import WizardForm from './components/WizardForm'
import PlanCard from './components/PlanCard'
import AIRecommendation from './components/AIRecommendation'
import ManagePlans from './components/ManagePlans'
import ResultsChart from './components/ResultsChart'
import CompareModal from './components/CompareModal'
import ChatPanel from './components/ChatPanel'
import PremiumCalculator from './components/PremiumCalculator'

const API_BASE = import.meta.env.VITE_API_URL || ''

const TABS = [
  { id: 'analyzer', label: '🔍 Analyzer' },
  { id: 'calculator', label: '💰 Calculator' },
  { id: 'manage', label: '📋 Manage Plans' },
]

export default function App() {
  const [tab, setTab] = useState('analyzer')
  const [result, setResult] = useState(null)
  const [lastProfile, setLastProfile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [scraping, setScraping] = useState(false)
  const [compareList, setCompareList] = useState([])
  const [showCompare, setShowCompare] = useState(false)
  const [showChat, setShowChat] = useState(false)
  const [sortBy, setSortBy] = useState('rank')
  const [showChart, setShowChart] = useState(true)
  const [stats, setStats] = useState(null)

  // Load stats on mount
  useEffect(() => {
    fetch(`${API_BASE}/api/stats`)
      .then((r) => r.json())
      .then(setStats)
      .catch(() => {})
  }, [])

  const handleRecommend = async (formData) => {
    setLoading(true)
    setError('')
    setResult(null)
    setCompareList([])
    setLastProfile(formData)
    try {
      const res = await fetch(`${API_BASE}/api/recommend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Something went wrong')
      }
      const data = await res.json()
      setResult(data)
      setTimeout(() => document.getElementById('results')?.scrollIntoView({ behavior: 'smooth' }), 100)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleScrape = async () => {
    setScraping(true)
    try {
      await fetch(`${API_BASE}/api/scrape`, { method: 'POST' })
      setTimeout(() => {
        setScraping(false)
        fetch(`${API_BASE}/api/stats`).then((r) => r.json()).then(setStats).catch(() => {})
      }, 3500)
    } catch {
      setScraping(false)
    }
  }

  const toggleCompare = (plan) => {
    setCompareList((prev) => {
      const exists = prev.some((p) => p.plan_name === plan.plan_name)
      if (exists) return prev.filter((p) => p.plan_name !== plan.plan_name)
      if (prev.length >= 3) return prev
      return [...prev, plan]
    })
  }

  const getSortedPlans = () => {
    if (!result?.ranked_plans) return []
    const plans = [...result.ranked_plans]
    if (sortBy === 'rank') return plans.sort((a, b) => a.rank - b.rank)
    if (sortBy === 'score') return plans.sort((a, b) => b.score - a.score)
    if (sortBy === 'csr') return plans.sort((a, b) => b.claim_settlement_ratio - a.claim_settlement_ratio)
    if (sortBy === 'budget') return plans.filter((p) => p.within_budget)
    return plans
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* ── Header ── */}
      <header className="bg-white shadow-sm sticky top-0 z-40">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-3xl">🛡️</span>
            <div>
              <h1 className="text-xl font-extrabold text-gray-900 leading-tight">
                Term Insurance Analyzer
              </h1>
              <p className="text-xs text-gray-400">
                Smart plan comparison
                {stats && (
                  <span className="ml-2 text-blue-500 font-semibold">
                    • {stats.total_plans} plans
                  </span>
                )}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {result && (
              <button
                onClick={() => setShowChat((v) => !v)}
                className={`text-sm font-semibold px-3 py-2 rounded-lg transition flex items-center gap-1.5 ${
                  showChat
                    ? 'bg-indigo-600 text-white'
                    : 'bg-indigo-50 text-indigo-700 hover:bg-indigo-100'
                }`}
              >
                💬 Ask Advisor
              </button>
            )}
            <button
              onClick={handleScrape}
              disabled={scraping}
              className="text-sm bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-2 rounded-lg transition disabled:opacity-50 flex items-center gap-1"
            >
              {scraping ? (
                <>
                  <svg className="animate-spin h-3.5 w-3.5" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                  Refreshing…
                </>
              ) : (
                '↺ Refresh'
              )}
            </button>
          </div>
        </div>

        {/* Tab bar */}
        <div className="max-w-5xl mx-auto px-4 flex gap-1 border-t border-gray-100">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition ${
                tab === t.id
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8">
        {/* ── Analyzer Tab ── */}
        {tab === 'analyzer' && (
          <div className="space-y-8">
            {/* Hero */}
            <div className="text-center">
              <h2 className="text-3xl font-extrabold text-gray-800">
                Find the{' '}
                <span className="text-blue-600">Best Term Insurance</span> for You
              </h2>
              <p className="text-gray-500 mt-2">
                Answer 3 quick questions — we rank every plan for your profile
              </p>
            </div>

            {/* Wizard form */}
            <WizardForm onSubmit={handleRecommend} loading={loading} />

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 flex items-center gap-2">
                ⚠️ {error}
              </div>
            )}

            {/* ── Results ── */}
            {result && (
              <div id="results" className="space-y-6">
                <AIRecommendation
                  summary={result.overall_summary}
                  topPick={result.top_pick}
                  totalAnalyzed={result.total_plans_analyzed}
                />

                {/* Toolbar: sort + chart toggle */}
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <h3 className="text-xl font-bold text-gray-800">All Plans Ranked</h3>
                    <span className="text-sm text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">
                      {result.ranked_plans.length}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <select
                      value={sortBy}
                      onChange={(e) => setSortBy(e.target.value)}
                      className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-blue-400"
                    >
                      <option value="rank">Sort: Best Match</option>
                      <option value="score">Sort: Score ↓</option>
                      <option value="csr">Sort: CSR% ↓</option>
                      <option value="budget">Within Budget only</option>
                    </select>
                    <button
                      onClick={() => setShowChart((v) => !v)}
                      className={`text-sm px-3 py-1.5 rounded-lg border transition ${
                        showChart
                          ? 'bg-blue-600 text-white border-blue-600'
                          : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
                      }`}
                    >
                      📊 Chart
                    </button>
                  </div>
                </div>

                {/* Compare bar */}
                {compareList.length >= 2 && (
                  <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4 flex items-center justify-between gap-3 animate-fadeIn">
                    <p className="text-sm text-indigo-800 font-medium">
                      ⚖️ {compareList.map((p) => p.plan_name).join(' vs ')}
                    </p>
                    <button
                      onClick={() => setShowCompare(true)}
                      className="flex-shrink-0 bg-indigo-600 text-white text-sm font-bold px-4 py-2 rounded-lg hover:bg-indigo-700 transition"
                    >
                      Compare →
                    </button>
                  </div>
                )}
                {compareList.length === 1 && (
                  <p className="text-sm text-gray-400 text-center">
                    ☝️ Select 1 more plan (up to 3) to compare side-by-side
                  </p>
                )}

                {/* Chart */}
                {showChart && <ResultsChart plans={result.ranked_plans} />}

                {/* Plan cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {getSortedPlans().map((plan) => (
                    <PlanCard
                      key={`${plan.rank}-${plan.plan_name}`}
                      plan={plan}
                      onToggleCompare={toggleCompare}
                      compareSelected={compareList.some((p) => p.plan_name === plan.plan_name)}
                    />
                  ))}
                </div>

                {getSortedPlans().length === 0 && sortBy === 'budget' && (
                  <div className="text-center py-8 text-gray-400">
                    No plans within your budget. Try increasing the budget in the form above.
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* ── Calculator Tab ── */}
        {tab === 'calculator' && <PremiumCalculator />}

        {/* ── Manage Plans Tab ── */}
        {tab === 'manage' && <ManagePlans />}
      </main>

      <footer className="text-center text-xs text-gray-400 py-6 border-t border-gray-100 mt-8">
        Data sourced from multiple insurance portals • Smart plan analysis
        {stats?.avg_claim_settlement_ratio && (
          <span className="ml-2">• Avg CSR: {stats.avg_claim_settlement_ratio}%</span>
        )}
      </footer>

      {/* ── Compare Modal ── */}
      {showCompare && lastProfile && (
        <CompareModal
          plans={compareList}
          userProfile={lastProfile}
          onClose={() => setShowCompare(false)}
        />
      )}

      {/* ── Chat Panel ── */}
      {showChat && (
        <ChatPanel
          userProfile={lastProfile}
          topPlans={result?.ranked_plans?.slice(0, 3)}
          onClose={() => setShowChat(false)}
        />
      )}
    </div>
  )
}
