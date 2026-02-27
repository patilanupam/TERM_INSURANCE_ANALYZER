import { useState } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || ''

function SliderField({ label, name, value, min, max, step = 1, format, onChange }) {
  const pct = ((value - min) / (max - min)) * 100
  return (
    <div>
      <div className="flex justify-between items-center mb-1">
        <label className="text-sm font-semibold text-gray-600">{label}</label>
        <span className="text-xl font-extrabold text-blue-600">{format ? format(value) : value}</span>
      </div>
      <input
        type="range"
        name={name}
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={onChange}
        className="w-full h-2 rounded-lg appearance-none cursor-pointer accent-blue-600"
        style={{ background: `linear-gradient(to right, #2563eb ${pct}%, #e2e8f0 ${pct}%)` }}
      />
      <div className="flex justify-between text-xs text-gray-400 mt-1">
        <span>{format ? format(min) : min}</span>
        <span>{format ? format(max) : max}</span>
      </div>
    </div>
  )
}

export default function PremiumCalculator() {
  const [form, setForm] = useState({ age: 30, sum_assured: 100, policy_term: 30 })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: parseFloat(value) }))
    setResult(null)
  }

  const estimate = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await fetch(`${API_BASE}/api/premium-estimate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      if (!res.ok) throw new Error('Estimation failed')
      setResult(await res.json())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-3xl font-extrabold text-gray-800">
          💰 Premium <span className="text-blue-600">Calculator</span>
        </h2>
        <p className="text-gray-500 mt-2">
          Get an instant estimate of your annual premium
        </p>
      </div>

      <div className="max-w-xl mx-auto bg-white rounded-2xl shadow-lg p-8 space-y-6">
        <SliderField
          label="Your Age"
          name="age"
          value={form.age}
          min={18}
          max={65}
          format={(v) => `${v} yrs`}
          onChange={handleChange}
        />
        <SliderField
          label="Sum Assured"
          name="sum_assured"
          value={form.sum_assured}
          min={25}
          max={1000}
          step={25}
          format={(v) => `₹${v}L`}
          onChange={handleChange}
        />
        <SliderField
          label="Policy Term"
          name="policy_term"
          value={form.policy_term}
          min={10}
          max={50}
          format={(v) => `${v} yrs`}
          onChange={handleChange}
        />

        {/* Input summary */}
        <div className="flex gap-3 text-center">
          {[
            { label: 'Age', value: `${form.age} yrs`, icon: '👤' },
            { label: 'Coverage', value: `₹${form.sum_assured}L`, icon: '🛡️' },
            { label: 'Term', value: `${form.policy_term} yrs`, icon: '📅' },
          ].map((item) => (
            <div
              key={item.label}
              className="flex-1 bg-blue-50 border border-blue-100 rounded-xl p-3"
            >
              <div className="text-xl mb-1">{item.icon}</div>
              <p className="text-xs text-gray-500">{item.label}</p>
              <p className="font-bold text-blue-600 text-sm">{item.value}</p>
            </div>
          ))}
        </div>

        <button
          onClick={estimate}
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-bold py-3.5 rounded-xl transition flex items-center justify-center gap-2 text-lg"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Estimating…
            </>
          ) : (
            '⚡ Estimate My Premium'
          )}
        </button>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-4 text-sm">
            ⚠️ {error}
          </div>
        )}

        {result && (
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-2xl p-6 space-y-5 animate-fadeIn">
            <p className="font-extrabold text-gray-800 text-xl text-center">
              Your Estimated Annual Premium
            </p>

            {/* Min / Typical / Max */}
            <div className="grid grid-cols-3 gap-3 text-center">
              <div className="bg-white rounded-xl p-4 border border-gray-100 shadow-sm">
                <p className="text-xs text-gray-400 mb-1">Minimum</p>
                <p className="text-lg font-bold text-green-600">
                  ₹{result.min_premium?.toLocaleString()}
                </p>
              </div>
              <div className="bg-blue-600 rounded-xl p-4 shadow-md">
                <p className="text-xs text-blue-100 mb-1">Typical</p>
                <p className="text-2xl font-extrabold text-white">
                  ₹{result.typical_premium?.toLocaleString()}
                </p>
              </div>
              <div className="bg-white rounded-xl p-4 border border-gray-100 shadow-sm">
                <p className="text-xs text-gray-400 mb-1">Maximum</p>
                <p className="text-lg font-bold text-orange-500">
                  ₹{result.max_premium?.toLocaleString()}
                </p>
              </div>
            </div>

            {/* Monthly equivalent */}
            <p className="text-center text-sm text-gray-500">
              Monthly equivalent: ≈{' '}
              <span className="font-bold text-gray-700">
                ₹{Math.round(result.typical_premium / 12).toLocaleString()}
              </span>
              /month
            </p>

            {/* Factors */}
            {result.factors?.length > 0 && (
              <div className="space-y-1.5">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  Factors considered
                </p>
                {result.factors.map((f, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm text-gray-600">
                    <span className="text-blue-500 font-bold">•</span> {f}
                  </div>
                ))}
              </div>
            )}

            {/* Tip */}
            {result.tip && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 text-sm text-yellow-800 flex gap-2">
                <span className="text-lg flex-shrink-0">💡</span>
                <span>{result.tip}</span>
              </div>
            )}

            <p className="text-xs text-gray-400 text-center">
              * Estimates are indicative. Actual premiums vary by insurer, health, and lifestyle.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
