import { useState } from 'react'

const STEPS = [
  { id: 1, title: 'About You', icon: '👤' },
  { id: 2, title: 'Coverage', icon: '🛡️' },
  { id: 3, title: 'Budget', icon: '💰' },
]

const DEFAULTS = {
  age: 30,
  sum_assured: 100,
  premium_budget: 15000,
  policy_term: 30,
  min_csr: 97,
}

function SliderInput({ label, name, value, min, max, step = 1, format, hint, onChange }) {
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
        style={{ background: `linear-gradient(to right, #2563eb ${((value - min) / (max - min)) * 100}%, #e2e8f0 ${((value - min) / (max - min)) * 100}%)` }}
      />
      <div className="flex justify-between text-xs text-gray-400 mt-1">
        <span>{format ? format(min) : min}</span>
        <span>{format ? format(max) : max}</span>
      </div>
      {hint && <p className="text-xs text-blue-500 mt-1">💡 {hint}</p>}
    </div>
  )
}

export default function WizardForm({ onSubmit, loading }) {
  const [step, setStep] = useState(1)
  const [form, setForm] = useState(DEFAULTS)

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: parseFloat(value) || value }))
  }

  const next = () => setStep((s) => Math.min(s + 1, 3))
  const prev = () => setStep((s) => Math.max(s - 1, 1))

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit(form)
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
      {/* Progress header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-6">
        <div className="flex justify-between items-start mb-5">
          {STEPS.map((s) => (
            <div key={s.id} className="flex flex-col items-center gap-1.5 flex-1">
              <div
                className={`w-11 h-11 rounded-full flex items-center justify-center text-lg font-bold transition-all duration-300 ${
                  step > s.id
                    ? 'bg-green-400 text-white shadow-lg'
                    : step === s.id
                    ? 'bg-white text-blue-600 shadow-xl scale-110'
                    : 'bg-white/20 text-white/50'
                }`}
              >
                {step > s.id ? '✓' : s.icon}
              </div>
              <span className={`text-xs font-semibold ${step === s.id ? 'text-white' : 'text-white/50'}`}>
                {s.title}
              </span>
            </div>
          ))}
        </div>
        <div className="w-full bg-white/20 rounded-full h-1.5">
          <div
            className="bg-white h-1.5 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${((step - 1) / 2) * 100}%` }}
          />
        </div>
        <p className="text-white/70 text-xs mt-2 text-right">Step {step} of 3</p>
      </div>

      <form onSubmit={handleSubmit} className="p-8">
        {/* ── Step 1: About You ── */}
        {step === 1 && (
          <div className="space-y-6 animate-fadeIn">
            <div>
              <h3 className="text-xl font-bold text-gray-800">Tell us about yourself</h3>
              <p className="text-sm text-gray-500 mt-1">Your age is the biggest factor in determining premiums</p>
            </div>
            <SliderInput
              label="Your Age"
              name="age"
              value={form.age}
              min={18}
              max={70}
              format={(v) => `${v} yrs`}
              hint={`Coverage till age ${form.age + 30} if you pick a 30-year term`}
              onChange={handleChange}
            />
            <div
              className={`rounded-xl p-4 text-sm font-medium border ${
                form.age <= 30
                  ? 'bg-green-50 text-green-700 border-green-200'
                  : form.age <= 45
                  ? 'bg-yellow-50 text-yellow-700 border-yellow-200'
                  : 'bg-orange-50 text-orange-700 border-orange-200'
              }`}
            >
              {form.age <= 30 && '🟢 Excellent! You\'re in the best age bracket — lowest premiums available.'}
              {form.age > 30 && form.age <= 45 && '🟡 Good time to buy. Premiums are still reasonable at your age.'}
              {form.age > 45 && '🟠 Act quickly — premiums rise sharply after 50. Buy without delay.'}
            </div>
            <div className="flex justify-end">
              <button
                type="button"
                onClick={next}
                className="bg-blue-600 text-white px-8 py-3 rounded-xl font-bold hover:bg-blue-700 transition flex items-center gap-2"
              >
                Next <span>→</span>
              </button>
            </div>
          </div>
        )}

        {/* ── Step 2: Coverage ── */}
        {step === 2 && (
          <div className="space-y-6 animate-fadeIn">
            <div>
              <h3 className="text-xl font-bold text-gray-800">Your Coverage Needs</h3>
              <p className="text-sm text-gray-500 mt-1">How much protection does your family need?</p>
            </div>
            <SliderInput
              label="Sum Assured"
              name="sum_assured"
              value={form.sum_assured}
              min={25}
              max={1000}
              step={25}
              format={(v) => `₹${v}L`}
              hint={`Experts recommend 10–15× annual income. For ₹${form.sum_assured}L, that implies ₹${Math.round(form.sum_assured / 12.5)}L–₹${Math.round(form.sum_assured / 10)}L annual income.`}
              onChange={handleChange}
            />
            <SliderInput
              label="Policy Term"
              name="policy_term"
              value={form.policy_term}
              min={10}
              max={50}
              format={(v) => `${v} yrs`}
              hint={`You'll be covered until age ${form.age + form.policy_term}`}
              onChange={handleChange}
            />
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-sm text-blue-700">
              💡 Cover yourself at least until your <strong>retirement age</strong> (60–65) to protect your family during peak earning years.
              Your current selection covers until age <strong>{form.age + form.policy_term}</strong>.
            </div>
            <div className="flex justify-between">
              <button type="button" onClick={prev} className="text-gray-600 px-6 py-3 rounded-xl font-bold hover:bg-gray-100 transition">
                ← Back
              </button>
              <button type="button" onClick={next} className="bg-blue-600 text-white px-8 py-3 rounded-xl font-bold hover:bg-blue-700 transition">
                Next →
              </button>
            </div>
          </div>
        )}

        {/* ── Step 3: Budget ── */}
        {step === 3 && (
          <div className="space-y-6 animate-fadeIn">
            <div>
              <h3 className="text-xl font-bold text-gray-800">Budget & Quality Filter</h3>
              <p className="text-sm text-gray-500 mt-1">Set your premium limit and minimum claim reliability</p>
            </div>
            <SliderInput
              label="Annual Premium Budget"
              name="premium_budget"
              value={form.premium_budget}
              min={3000}
              max={100000}
              step={500}
              format={(v) => `₹${v.toLocaleString()}`}
              hint={`Monthly: ≈ ₹${Math.round(form.premium_budget / 12).toLocaleString()}`}
              onChange={handleChange}
            />
            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="text-sm font-semibold text-gray-600">Min. Claim Settlement Ratio</label>
                <span
                  className={`text-xl font-extrabold ${
                    form.min_csr >= 98 ? 'text-green-600' : form.min_csr >= 95 ? 'text-blue-600' : 'text-orange-500'
                  }`}
                >
                  {form.min_csr}%
                </span>
              </div>
              <input
                type="range"
                name="min_csr"
                min={90}
                max={100}
                step={0.5}
                value={form.min_csr}
                onChange={handleChange}
                className="w-full h-2 rounded-lg appearance-none cursor-pointer accent-blue-600"
                style={{
                  background: `linear-gradient(to right, #2563eb ${((form.min_csr - 90) / 10) * 100}%, #e2e8f0 ${((form.min_csr - 90) / 10) * 100}%)`,
                }}
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>90% (Lenient)</span>
                <span>95%</span>
                <span>100% (Strict)</span>
              </div>
              <p className="text-xs text-blue-500 mt-1">💡 97%+ is excellent. This means 97 out of 100 claims get settled.</p>
            </div>

            {/* Summary card */}
            <div className="bg-gradient-to-br from-indigo-50 to-blue-50 border border-blue-200 rounded-xl p-5">
              <p className="font-bold text-gray-800 mb-3">📋 Your Profile Summary</p>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">👤</span>
                  <div>
                    <p className="text-xs text-gray-500">Age</p>
                    <p className="font-bold text-gray-800">{form.age} years</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-2xl">🛡️</span>
                  <div>
                    <p className="text-xs text-gray-500">Sum Assured</p>
                    <p className="font-bold text-gray-800">₹{form.sum_assured}L</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-2xl">💰</span>
                  <div>
                    <p className="text-xs text-gray-500">Budget</p>
                    <p className="font-bold text-gray-800">₹{form.premium_budget.toLocaleString()}/yr</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-2xl">📅</span>
                  <div>
                    <p className="text-xs text-gray-500">Policy Term</p>
                    <p className="font-bold text-gray-800">{form.policy_term} years</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-between">
              <button type="button" onClick={prev} className="text-gray-600 px-6 py-3 rounded-xl font-bold hover:bg-gray-100 transition">
                ← Back
              </button>
              <button
                type="submit"
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-bold py-3 px-8 rounded-xl transition flex items-center gap-2 text-lg"
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
                  '🔍 Find Best Plans'
                )}
              </button>
            </div>
          </div>
        )}
      </form>
    </div>
  )
}
