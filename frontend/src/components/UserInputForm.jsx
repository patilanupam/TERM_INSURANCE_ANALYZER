import { useState } from 'react'

const DEFAULTS = {
  age: 30,
  sum_assured: 100,
  premium_budget: 15000,
  policy_term: 30,
  min_csr: 97,
}

export default function UserInputForm({ onSubmit, loading }) {
  const [form, setForm] = useState(DEFAULTS)

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: parseFloat(value) || value }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit(form)
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-lg p-8">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Your Profile</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Age */}
        <div>
          <label className="block text-sm font-semibold text-gray-600 mb-1">
            Age <span className="text-gray-400 font-normal">(years)</span>
          </label>
          <input
            type="number"
            name="age"
            min={18}
            max={70}
            value={form.age}
            onChange={handleChange}
            required
            className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-800"
          />
          <p className="text-xs text-gray-400 mt-1">Between 18 – 70 years</p>
        </div>

        {/* Sum Assured */}
        <div>
          <label className="block text-sm font-semibold text-gray-600 mb-1">
            Sum Assured <span className="text-gray-400 font-normal">(₹ Lakhs)</span>
          </label>
          <input
            type="number"
            name="sum_assured"
            min={5}
            max={10000}
            value={form.sum_assured}
            onChange={handleChange}
            required
            className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-800"
          />
          <p className="text-xs text-gray-400 mt-1">Recommended: 10–20× annual income</p>
        </div>

        {/* Premium Budget */}
        <div>
          <label className="block text-sm font-semibold text-gray-600 mb-1">
            Premium Budget <span className="text-gray-400 font-normal">(₹/year)</span>
          </label>
          <input
            type="number"
            name="premium_budget"
            min={1000}
            value={form.premium_budget}
            onChange={handleChange}
            required
            className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-800"
          />
        </div>

        {/* Policy Term */}
        <div>
          <label className="block text-sm font-semibold text-gray-600 mb-1">
            Policy Term <span className="text-gray-400 font-normal">(years)</span>
          </label>
          <input
            type="number"
            name="policy_term"
            min={5}
            max={50}
            value={form.policy_term}
            onChange={handleChange}
            required
            className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-800"
          />
        </div>

        {/* Min CSR */}
        <div className="md:col-span-2">
          <label className="block text-sm font-semibold text-gray-600 mb-1">
            Minimum Claim Settlement Ratio:{' '}
            <span className="text-blue-600 font-bold">{form.min_csr}%</span>
          </label>
          <input
            type="range"
            name="min_csr"
            min={90}
            max={100}
            step={0.5}
            value={form.min_csr}
            onChange={handleChange}
            className="w-full accent-blue-600"
          />
          <div className="flex justify-between text-xs text-gray-400 mt-1">
            <span>90%</span>
            <span>95%</span>
            <span>100%</span>
          </div>
        </div>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="mt-8 w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-bold py-3 px-6 rounded-xl transition-colors text-lg flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
            Analyzing…
          </>
        ) : (
          '🔍 Find Best Plans for Me'
        )}
      </button>
    </form>
  )
}
