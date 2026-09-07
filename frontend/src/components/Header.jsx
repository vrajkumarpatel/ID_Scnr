import React from 'react'

const tabs = [
  { key: 'guests', label: "Today's Check-Ins" },
  { key: 'dnr', label: 'Do Not Rent' },
  { key: 'settings', label: 'Settings' },
]

export default function Header({ tab, setTab }) {
  return (
    <header className="sticky top-0 z-10 bg-white/80 dark:bg-slate-900/70 backdrop-blur border-b border-slate-200 dark:border-slate-700">
      <div className="container mx-auto px-4 py-3 flex items-center justify-between">
        <h1 className="text-xl font-semibold tracking-tight">IDscnr — by Vraj</h1>
        <nav className="flex gap-2 items-center" aria-label="Primary">
          {tabs.map(t => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`btn ${tab === t.key ? 'btn-primary' : 'btn-outline'}`}
              aria-current={tab === t.key ? 'page' : undefined}
            >
              {t.label}
            </button>
          ))}
          
        </nav>
      </div>
      <div className="h-[3px] bg-gradient-to-r from-emerald-400 via-cyan-400 to-indigo-400" />
    </header>
  )
}