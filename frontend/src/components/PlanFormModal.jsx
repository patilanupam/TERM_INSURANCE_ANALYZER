import { useState } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || ""
const EMPTY_FORM = {
  plan_name: '',
  provider: '',
  sum_assured_min: 50,
  sum_assured_max: 10000,
  premium_annual: '',
  policy_term_min: 10,
  policy_term_max: 40,
  age_min: 18,
  age_max: 65,
  claim_settlement_ratio: '',
  key_features: '',
  source_url: '',
}

export default function PlanFormModal({ plan, onClose, onSaved }) {
  const isEdit = Boolean(plan)
  const [form, setForm] = useState(
    isEdit
      ? {
          plan_name: plan.plan_name,
          provider: plan.provider,
          sum_assured_min: plan.sum_assured_min,
          sum_assured_max: plan.sum_assured_max,
          premium_annual: plan.premium_annual,
          policy_term_min: plan.policy_term_min,
          policy_term_max: plan.policy_term_max,
          age_min: plan.age_min,
          age_max: plan.age_max,
          claim_settlement_ratio: plan.claim_settlement_ratio,
          key_features: plan.key_features,
          source_url: plan.source_url,
        }
      : EMPTY_FORM
  )
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    // Coerce numeric fields
    const payload = {
      ...form,
      sum_assured_min: parseFloat(form.sum_assured_min),
      sum_assured_max: parseFloat(form.sum_assured_max),
      premium_annual: parseFloat(form.premium_annual),
      policy_term_min: parseInt(form.policy_term_min),
      policy_term_max: parseInt(form.policy_term_max),
      age_min: parseInt(form.age_min),
      age_max: parseInt(form.age_max),
      claim_settlement_ratio: parseFloat(form.claim_settlement_ratio),
    }

    try {
      const url = isEdit ? `${API_BASE}/api/plans/${plan.id}` : `${API_BASE}/api/plans`
      const method = isEdit ? 'PUT' : 'POST'
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Failed to save plan')
      }
      const saved = await res.json()
      onSaved(saved)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const fields = [
    { name: 'plan_name', label: 'Plan Name', type: 'text', required: true, colSpan: 2 },
    { name: 'provider', label: 'Insurance Provider', type: 'text', required: true, colSpan: 2 },
    { name: 'premium_annual', label: 'Annual Premium (₹)', type: 'number', required: true },
    { name: 'claim_settlement_ratio', label: 'Claim Settlement Ratio (%)', type: 'number', required: true, step: '0.01', min: 0, max: 100 },
    { name: 'sum_assured_min', label: 'Min Sum Assured (Lakhs)', type: 'number', required: true },
    { name: 'sum_assured_max', label: 'Max Sum Assured (Lakhs)', type: 'number', required: true },
    { name: 'policy_term_min', label: 'Min Policy Term (years)', type: 'number', required: true },
    { name: 'policy_term_max', label: 'Max Policy Term (years)', type: 'number', required: true },
    { name: 'age_min', label: 'Min Entry Age', type: 'number', required: true },
    { name: 'age_max', label: 'Max Entry Age', type: 'number', required: true },
    { name: 'key_features', label: 'Key Features (pipe-separated: Feature 1|Feature 2)', type: 'text', colSpan: 2 },
    { name: 'source_url', label: 'Official Plan URL', type: 'url', colSpan: 2 },
  ]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-xl font-bold text-gray-800">
            {isEdit ? '✏️ Edit Plan' : '➕ Add New Plan'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {fields.map((f) => (
              <div key={f.name} className={f.colSpan === 2 ? 'md:col-span-2' : ''}>
                <label className="block text-sm font-semibold text-gray-600 mb-1">
                  {f.label} {f.required && <span className="text-red-500">*</span>}
                </label>
                <input
                  type={f.type}
                  name={f.name}
                  value={form[f.name]}
                  onChange={handleChange}
                  required={f.required}
                  step={f.step}
                  min={f.min}
                  max={f.max}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-800"
                  placeholder={f.type === 'url' ? 'https://...' : ''}
                />
              </div>
            ))}
          </div>

          {error && (
            <p className="text-red-600 text-sm bg-red-50 p-3 rounded-lg">⚠️ {error}</p>
          )}

          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-bold py-2.5 rounded-xl transition"
            >
              {loading ? 'Saving…' : isEdit ? 'Save Changes' : 'Add Plan'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold py-2.5 rounded-xl transition"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
