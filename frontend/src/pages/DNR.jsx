import React, { useEffect, useState } from 'react'
import { listDNR, searchDNR } from '../api'

export default function DNR() {
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [q, setQ] = useState('')

  const refresh = async () => {
    setLoading(true)
    setError('')
    try {
      const data = q ? await searchDNR(q) : await listDNR()
      setEntries(Array.isArray(data) ? data : [])
    } catch (e) {
      setError('Failed to load DNR list')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { refresh() }, [])

  const adminLogin = async () => {}

  return (
    <div className="glass p-6 rounded-xl">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Do Not Rent</h2>
        <div className="flex items-center gap-2">
          <input className="input" placeholder="Search name / ID" aria-label="Search DNR" value={q} onChange={e => setQ(e.target.value)} />
          <button className="btn btn-outline" onClick={refresh}>Refresh</button>
        </div>
      </div>
      {loading && (
        <div className="space-y-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-8 bg-slate-200 dark:bg-slate-700 animate-pulse rounded" />
          ))}
        </div>
      )}
      {error && <div className="text-red-400 text-sm mb-2" role="alert" aria-live="polite">{error}</div>}
      <div className="overflow-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
            <tr>
              <th className="text-left px-4 py-2">Name</th>
              <th className="text-left px-4 py-2">DOB</th>
              <th className="text-left px-4 py-2">ID Number</th>
              <th className="text-left px-4 py-2">Notes</th>
              <th className="text-left px-4 py-2">Created</th>
            </tr>
          </thead>
          <tbody>
            {entries.length === 0 && !loading && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-slate-400">No DNR entries.</td>
              </tr>
            )}
            {entries.map(e => (
              <tr key={e.id} className="border-t border-slate-200 dark:border-slate-700">
                <td className="px-4 py-2">{[e.first_name, e.last_name].filter(Boolean).join(' ') || '—'}</td>
                <td className="px-4 py-2">{e.dob || '—'}</td>
                <td className="px-4 py-2">{e.id_number || '—'}</td>
                <td className="px-4 py-2">{e.notes || '—'}</td>
                <td className="px-4 py-2">{e.created_at ? new Date(e.created_at).toLocaleString() : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}