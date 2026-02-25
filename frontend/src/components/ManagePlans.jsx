import { useState, useEffect, useCallback } from 'react'
import PlanFormModal from './PlanFormModal'

const SOURCE_BADGE = {
  manual: 'bg-purple-100 text-purple-700',
  seed: 'bg-gray-100 text-gray-600',
  policybazaar: 'bg-orange-100 text-orange-700',
  insurancedekho: 'bg-green-100 text-green-700',
}

export default function ManagePlans() {
  const [plans, setPlans] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editPlan, setEditPlan] = useState(null)
  const [deletingId, setDeletingId] = useState(null)
  const [toast, setToast] = useState('')

  const showToast = (msg) => {
    setToast(msg)
    setTimeout(() => setToast(''), 3000)
  }

  const fetchPlans = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/plans')
      const data = await res.json()
      setPlans(data)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchPlans() }, [fetchPlans])

  const handleSaved = (saved) => {
    setPlans((prev) => {
      const idx = prev.findIndex((p) => p.id === saved.id)
      if (idx >= 0) {
        const next = [...prev]
        next[idx] = saved
        return next
      }
      return [saved, ...prev]
    })
    setShowModal(false)
    setEditPlan(null)
    showToast(editPlan ? '✅ Plan updated!' : '✅ Plan added!')
  }

  const handleDelete = async (plan) => {
    if (!window.confirm(`Delete "${plan.plan_name}" by ${plan.provider}?`)) return
    setDeletingId(plan.id)
    try {
      const res = await fetch(`/api/plans/${plan.id}`, { method: 'DELETE' })
      if (!res.ok) throw new Error('Delete failed')
      setPlans((prev) => prev.filter((p) => p.id !== plan.id))
      showToast('🗑️ Plan deleted')
    } catch {
      showToast('❌ Failed to delete plan')
    } finally {
      setDeletingId(null)
    }
  }

  const openAdd = () => { setEditPlan(null); setShowModal(true) }
  const openEdit = (plan) => { setEditPlan(plan); setShowModal(true) }

  return (
    <div className="space-y-4">
      {/* Toast */}
      {toast && (
        <div className="fixed top-4 right-4 z-50 bg-gray-900 text-white px-5 py-3 rounded-xl shadow-xl text-sm">
          {toast}
        </div>
      )}

      {/* Toolbar */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-800">Manage Plans</h2>
          <p className="text-sm text-gray-500">{plans.length} plans in database</p>
        </div>
        <button
          onClick={openAdd}
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold px-4 py-2 rounded-xl transition flex items-center gap-1"
        >
          + Add Plan
        </button>
      </div>

      {/* Table */}
      {loading ? (
        <div className="text-center py-12 text-gray-400">Loading plans…</div>
      ) : plans.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          No plans yet.{' '}
          <button onClick={openAdd} className="text-blue-600 underline">Add one</button>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-gray-200 shadow-sm">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 text-gray-600 text-xs uppercase tracking-wide">
              <tr>
                <th className="px-4 py-3 text-left">Plan / Provider</th>
                <th className="px-4 py-3 text-right">Premium/yr</th>
                <th className="px-4 py-3 text-right">CSR%</th>
                <th className="px-4 py-3 text-right">Sum Assured (L)</th>
                <th className="px-4 py-3 text-center">Term</th>
                <th className="px-4 py-3 text-center">Age</th>
                <th className="px-4 py-3 text-center">Source</th>
                <th className="px-4 py-3 text-center">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 bg-white">
              {plans.map((p) => (
                <tr key={p.id} className="hover:bg-gray-50 transition">
                  <td className="px-4 py-3">
                    <div className="font-semibold text-gray-800">{p.plan_name}</div>
                    <div className="text-gray-500 text-xs">{p.provider}</div>
                  </td>
                  <td className="px-4 py-3 text-right font-medium text-gray-700">
                    ₹{p.premium_annual.toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className={`font-bold ${p.claim_settlement_ratio >= 98 ? 'text-green-600' : p.claim_settlement_ratio >= 95 ? 'text-yellow-600' : 'text-red-500'}`}>
                      {p.claim_settlement_ratio}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right text-gray-600">
                    {p.sum_assured_min}–{p.sum_assured_max}
                  </td>
                  <td className="px-4 py-3 text-center text-gray-600">
                    {p.policy_term_min}–{p.policy_term_max} yrs
                  </td>
                  <td className="px-4 py-3 text-center text-gray-600">
                    {p.age_min}–{p.age_max}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${SOURCE_BADGE[p.source] || 'bg-gray-100 text-gray-600'}`}>
                      {p.source}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <div className="flex items-center justify-center gap-2">
                      <button
                        onClick={() => openEdit(p)}
                        className="text-blue-600 hover:text-blue-800 text-xs font-medium px-2 py-1 rounded hover:bg-blue-50 transition"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(p)}
                        disabled={deletingId === p.id}
                        className="text-red-500 hover:text-red-700 text-xs font-medium px-2 py-1 rounded hover:bg-red-50 transition disabled:opacity-40"
                      >
                        {deletingId === p.id ? '…' : 'Delete'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <PlanFormModal
          plan={editPlan}
          onClose={() => { setShowModal(false); setEditPlan(null) }}
          onSaved={handleSaved}
        />
      )}
    </div>
  )
}
