import { useState } from "react"
import UserInputForm from "./components/UserInputForm"
import PlanCard from "./components/PlanCard"
import AIRecommendation from "./components/AIRecommendation"

export default function App() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [scraping, setScraping] = useState(false)

  const handleRecommend = async (formData) => {
    setLoading(true)
    setError("")
    setResult(null)
    try {
      const res = await fetch("/api/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || "Something went wrong")
      }
      const data = await res.json()
      setResult(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleScrape = async () => {
    setScraping(true)
    try {
      await fetch("/api/scrape", { method: "POST" })
      setTimeout(() => setScraping(false), 3000)
    } catch {
      setScraping(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Hero */}
      <header className="bg-white shadow-sm">
        <div className="max-w-5xl mx-auto px-4 py-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-3xl">🛡️</span>
            <div>
              <h1 className="text-xl font-extrabold text-gray-900 leading-tight">
                Term Insurance Analyzer
              </h1>
              <p className="text-xs text-gray-500">
                AI-powered • PolicyBazaar & InsuranceDekho data
              </p>
            </div>
          </div>
          <button
            onClick={handleScrape}
            disabled={scraping}
            className="text-sm bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded-lg transition disabled:opacity-50"
          >
            {scraping ? "⟳ Refreshing..." : "↺ Refresh Plans"}
          </button>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8 space-y-8">
        {/* Tagline */}
        <div className="text-center">
          <h2 className="text-3xl font-extrabold text-gray-800">
            Find the <span className="text-blue-600">Best Term Insurance</span> for You
          </h2>
          <p className="text-gray-500 mt-2">
            Enter your details and let Gemini AI analyze plans across top insurers
          </p>
        </div>

        {/* Form */}
        <UserInputForm onSubmit={handleRecommend} loading={loading} />

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700">
            ⚠️ {error}
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="space-y-6">
            <AIRecommendation
              summary={result.overall_summary}
              topPick={result.top_pick}
              totalAnalyzed={result.total_plans_analyzed}
            />

            <div>
              <h3 className="text-xl font-bold text-gray-800 mb-4">
                All Plans Ranked
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {result.ranked_plans.map((plan) => (
                  <PlanCard key={`${plan.rank}-${plan.plan_name}`} plan={plan} />
                ))}
              </div>
            </div>
          </div>
        )}
      </main>

      <footer className="text-center text-xs text-gray-400 py-6">
        Data sourced from PolicyBazaar & InsuranceDekho • AI by Gemini 1.5 Flash
      </footer>
    </div>
  )
}
