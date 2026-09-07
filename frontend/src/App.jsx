import React, { useState } from 'react'
import { motion } from 'framer-motion'
import Header from './components/Header'
import Guests from './pages/Guests'
import DNR from './pages/DNR'
import Settings from './pages/Settings'

export default function App() {
  const [tab, setTab] = useState('guests')
  React.useEffect(() => {
    try {
      const v = localStorage.getItem('dark_mode')
      const on = v ? v === 'true' : true
      document.documentElement.classList.toggle('dark', on)
    } catch {}
  }, [])
  return (
    <div className="min-h-screen bg-white text-slate-900 dark:bg-slate-900 dark:text-slate-100">
      <Header tab={tab} setTab={setTab} />
      <main className="container mx-auto p-4">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}>
          {tab === 'guests' && <Guests />}
          {tab === 'dnr' && <DNR />}
          {tab === 'settings' && <Settings />}
        </motion.div>
      </main>
    </div>
  )
}