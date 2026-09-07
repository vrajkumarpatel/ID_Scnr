import React, { useEffect, useMemo, useState } from 'react'
import { listGuests, statsMtd, fetchImage, getGuest, getGuestHistory, getGuestSummary, updateGuest, writePMS, subscribeCheckins, addDNR, dnrMatch, scanIngest, uploadGuestImage, scanDuplex, imageUrl } from '../api'

export default function Guests() {
  const [guests, setGuests] = useState([])
  const [q, setQ] = useState('')
  const [selectedDate, setSelectedDate] = useState(() => new Date().toISOString().slice(0, 10))
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [selectedGuestId, setSelectedGuestId] = useState(null)
  const [selectedGuest, setSelectedGuest] = useState(null)
  const [editRoom, setEditRoom] = useState('')
  const [editRemarks, setEditRemarks] = useState('')
  const [showBackImage, setShowBackImage] = useState(false)
  const [toast, setToast] = useState('')
  const [mtdCount, setMtdCount] = useState(null)
  const [frontSrc, setFrontSrc] = useState('')
  const [backSrc, setBackSrc] = useState('')
  const [imageErrorFront, setImageErrorFront] = useState(false)
  const [imageErrorBack, setImageErrorBack] = useState(false)
  const [dnrInfo, setDnrInfo] = useState(null)
  const [history, setHistory] = useState([])
  const [summary, setSummary] = useState(null)
  const [sortDesc, setSortDesc] = useState(true)
  const [nowStr, setNowStr] = useState(new Date().toLocaleTimeString())
  const fileFrontRef = React.useRef(null)
  const fileBackRef = React.useRef(null)
  const [uploadFront, setUploadFront] = useState(null)
  const [uploadBack, setUploadBack] = useState(null)
  const [dnrToggleOn, setDnrToggleOn] = useState(false)
  const [dnrBusy, setDnrBusy] = useState(false)
  const [adminPin, setAdminPin] = useState('')
  const [draftGuestId, setDraftGuestId] = useState(null)
  const draftRef = React.useRef(null)
  const [pinModalOpen, setPinModalOpen] = useState(false)
  const [pinAction, setPinAction] = useState('add')
  const [pinInput, setPinInput] = useState('')
  const [pinError, setPinError] = useState('')
  const [pinSubmitting, setPinSubmitting] = useState(false)
  const [pinAttempts, setPinAttempts] = useState([])
  const pinInputRef = React.useRef(null)
  const [lastActivityAt, setLastActivityAt] = useState(Date.now())
  

  const toISODate = (s) => {
    if (!s) return s
    const t = String(s).trim()
    let m
    m = t.match(/^([0-9]{4})-([0-9]{2})-([0-9]{2})$/)
    if (m) return t
    m = t.match(/^([0-9]{1,2})\/([0-9]{1,2})\/([0-9]{2,4})$/)
    if (m) {
      const a = parseInt(m[1], 10), b = parseInt(m[2], 10), yy = m[3]
      if (a > 12 && b >= 1 && b <= 12) {
        const y = parseInt(yy, 10)
        return `${y.toString().length===2 ? (y>=50?1900+y:2000+y):y}-${String(b).padStart(2,'0')}-${String(a).padStart(2,'0')}`
      }
      const y = parseInt(yy, 10)
      return `${y.toString().length===2 ? (y>=50?1900+y:2000+y):y}-${String(a).padStart(2,'0')}-${String(b).padStart(2,'0')}`
    }
    m = t.match(/^([A-Za-z]{3,9})\s+(\d{1,2}),\s*(\d{2,4})$/)
    if (m) {
      const months = {jan:1,feb:2,mar:3,apr:4,may:5,jun:6,jul:7,aug:8,sep:9,oct:10,nov:11,dec:12}
      const mm = months[m[1].toLowerCase().slice(0,3)]||0
      const dd = parseInt(m[2],10)
      const yy = m[3]
      const y = yy.length===2 ? (parseInt(yy,10)>=50?1900+parseInt(yy,10):2000+parseInt(yy,10)) : parseInt(yy,10)
      if (mm) return `${String(y).padStart(4,'0')}-${String(mm).padStart(2,'0')}-${String(dd).padStart(2,'0')}`
    }
    m = t.match(/^([0-9]{4})([0-9]{2})([0-9]{2})$/)
    if (m) return `${m[1]}-${m[2]}-${m[3]}`
    m = t.match(/^([0-9]{2})([0-9]{2})([0-9]{2})$/)
    if (m) {
      const yy = parseInt(m[1],10), mm = parseInt(m[2],10), dd = parseInt(m[3],10)
      const y = yy<=29 ? 2000+yy : 1900+yy
      return `${String(y).padStart(4,'0')}-${String(mm).padStart(2,'0')}-${String(dd).padStart(2,'0')}`
    }
    return t
  }

  const toMMDDYYYY = (s) => {
    if (!s) return ''
    const t = String(s).trim()
    let m
    m = t.match(/^([0-9]{4})-([0-9]{2})-([0-9]{2})$/)
    if (m) return `${m[2]}/${m[3]}/${m[1]}`
    m = t.match(/^([0-9]{1,2})\/([0-9]{1,2})\/([0-9]{2,4})$/)
    if (m) return `${String(m[1]).padStart(2,'0')}/${String(m[2]).padStart(2,'0')}/${String(m[3]).padStart(2,'0')}`
    m = t.match(/^([A-Za-z]{3,9})\s+(\d{1,2}),\s*(\d{2,4})$/)
    if (m) {
      const months = {jan:1,feb:2,mar:3,apr:4,may:5,jun:6,jul:7,aug:8,sep:9,oct:10,nov:11,dec:12}
      const mm = months[m[1].toLowerCase().slice(0,3)]||0
      const dd = parseInt(m[2],10)
      const yy = m[3]
      const y = yy.length===2 ? (parseInt(yy,10)>=50?1900+parseInt(yy,10):2000+parseInt(yy,10)) : parseInt(yy,10)
      if (mm) return `${String(mm).padStart(2,'0')}/${String(dd).padStart(2,'0')}/${String(y).padStart(2,'0')}`
    }
    return t
  }

  const fetchForDate = async (dateStr) => {
    setLoading(true)
    setError('')
    try {
      const data = await listGuests(dateStr)
      setGuests(Array.isArray(data) ? data : [])
      // Auto-select the most recent check-in when viewing today's date
      const todayStr = new Date().toISOString().slice(0, 10)
      if (dateStr === todayStr && (!selectedGuestId || !selectedGuest)) {
        const sorted = (Array.isArray(data) ? data : []).sort((a, b) => new Date(a.created_at || 0) - new Date(b.created_at || 0))
        const latest = sorted[sorted.length - 1]
        if (latest) {
          // Do not block UI; fire and forget
          selectGuest(latest)
        }
      }
    } catch (e) {
      setError('Failed to load guests')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let t
    fetchForDate(selectedDate)
    const es = subscribeCheckins(selectedDate)
    if (!es) {
      t = setInterval(() => fetchForDate(selectedDate), 10000)
    } else {
      es.onmessage = (evt) => {
        try {
          const g = JSON.parse(evt.data)
          if (draftRef.current && draftRef.current === g.id) return
          setGuests(prev => {
            const exists = prev.some(x => x.id === g.id)
            if (exists) return prev.map(x => (x.id === g.id ? g : x))
            return [...prev, g]
          })
          if (!selectedGuestId || selectedGuestId !== g.id) {
            selectGuest(g)
          }
        } catch {}
      }
      es.onerror = () => {
        try { es.close() } catch {}
      }
    }
    return () => {
      if (t) clearInterval(t)
      try { es && es.close() } catch {}
    }
  }, [selectedDate])

  // Removed duplicate SSE effect to prevent aborted connections

  // Fetch month-to-date total (simple aggregation by day)
  useEffect(() => {
    (async () => {
      try {
        const d = await statsMtd(selectedDate)
        setMtdCount(d)
      } catch {
        setMtdCount(null)
      }
    })()
  }, [selectedDate])

  const setDateOffset = (days) => {
    const d = new Date(selectedDate)
    d.setDate(d.getDate() + days)
    const next = d.toISOString().slice(0, 10)
    setSelectedDate(next)
  }

  const filtered = useMemo(() => {
    const sQ = q.trim().toLowerCase()
    const bySearch = (g) => {
      const parts = [g.first_name, g.last_name, g.room_number, g.id_number].filter(Boolean).map(v => String(v).toLowerCase())
      return sQ ? parts.some(p => p.includes(sQ)) : true
    }
    const byDate = (g) => (g.created_at || '').slice(0, 10) === selectedDate
    const asc = (a, b) => new Date(a.created_at || 0) - new Date(b.created_at || 0)
    const desc = (a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0)
    return guests.filter(g => byDate(g) && bySearch(g) && g.id !== draftGuestId).sort(sortDesc ? desc : asc)
  }, [guests, q, selectedDate, sortDesc])

  const checkinTime = (g) => {
    const t = g.created_at ? new Date(g.created_at) : null
    return t ? t.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '—'
  }

  // Select guest and load details
  const selectGuest = async (g) => {
    setSelectedGuestId(g.id)
    try {
      const full = await getGuest(g.id)
      setSelectedGuest(full)
      setEditRoom(full.room_number || '')
      setEditRemarks(full.remarks || '')
      setShowBackImage(false)
      setFrontSrc('')
      setBackSrc('')
      setImageErrorFront(false)
      setImageErrorBack(false)
      setDnrInfo(null)
      if (full.dnr_hit_id) {
        setDnrInfo({ hit: null, score: Number(full.dnr_match_score || 0) })
      } else {
        try {
          const info = await dnrMatch(g.id)
          setDnrInfo(info)
        } catch {}
      }
      try { setHistory(await getGuestHistory(g.id)) } catch { setHistory([]) }
      try { setSummary(await getGuestSummary(g.id)) } catch { setSummary(null) }
    } catch {
      setSelectedGuest(null)
    }
  }

  useEffect(() => {
    if (!selectedGuest) return
    try {
      setFrontSrc(selectedGuest.image_front_path ? imageUrl(selectedGuest.image_front_path) : '')
      setBackSrc(selectedGuest.image_back_path ? imageUrl(selectedGuest.image_back_path) : '')
    } catch {}
  }, [selectedGuest])

  useEffect(() => {
    const has = !!selectedGuest && Boolean(selectedGuest.dnr_hit_id)
    setDnrToggleOn(Boolean(has))
  }, [selectedGuest, dnrInfo])

  useEffect(() => {
    (async () => {
      if (!uploadFront && !uploadBack) return
      try {
        const g = await scanIngest(uploadFront, uploadBack)
        await selectGuest(g)
        setDraftGuestId(g.id)
        draftRef.current = g.id
        setToast('ID processed')
        setTimeout(() => setToast(''), 2000)
        setUploadFront(null); setUploadBack(null)
      } catch {
        setToast('Processing failed')
        setTimeout(() => setToast(''), 2000)
      }
    })()
  }, [uploadFront, uploadBack])

  const markGuestDNR = async () => {
    if (!selectedGuestId || !selectedGuest) return
    const current = String(editRemarks || selectedGuest.remarks || '').trim()
    const hasDNR = current.toLowerCase().includes('dnr')
    const newRemarks = hasDNR ? current : (current ? `DNR — ${current}` : 'DNR')
    try {
      const updated = await updateGuest(selectedGuestId, { remarks: newRemarks })
      setSelectedGuest(updated)
      setEditRemarks(updated.remarks || '')
      // Update list state so DNR tag appears
      setGuests(prev => prev.map(g => (g.id === updated.id ? updated : g)))
      try {
        await addDNR({
          first_name: updated.first_name,
          last_name: updated.last_name,
          dob: updated.dob,
          id_number: updated.id_number,
          notes: updated.remarks || 'Marked from Guests',
        })
      } catch {}
      setToast('Marked as DNR')
      setTimeout(() => setToast(''), 2500)
    } catch (e) {
      setToast('Failed to mark DNR')
      setTimeout(() => setToast(''), 2500)
    }
  }

  const applyDNRToHistory = async () => {
    if (!selectedGuest || !history || history.length === 0) return
    try {
      const tasks = history.filter(h => !String(h.remarks || '').toLowerCase().includes('dnr')).map(h => {
        const cur = String(h.remarks || '')
        const next = cur.toLowerCase().includes('dnr') ? cur : (cur ? `DNR — ${cur}` : 'DNR')
        return updateGuest(h.id, { remarks: next })
      })
      if (tasks.length > 0) await Promise.all(tasks)
      try { setHistory(await getGuestHistory(selectedGuest.id)) } catch {}
      setToast('Applied DNR to history')
      setTimeout(() => setToast(''), 2500)
    } catch {
      setToast('Failed to apply DNR')
      setTimeout(() => setToast(''), 2500)
    }
  }

  const stripDNR = (remarks) => {
    const t = String(remarks || '')
    const lowered = t.toLowerCase()
    if (!lowered.includes('dnr')) return t
    return t.replace(/^\s*dnr\s*—\s*/i, '').replace(/^\s*dnr\s*/i, '').trim()
  }

  const clearDNRFromHistory = async () => {
    if (!selectedGuest || !history) return
    const tasks = []
    const cur = String(editRemarks || selectedGuest.remarks || '')
    const nextCur = stripDNR(cur)
    if (nextCur !== cur) tasks.push(updateGuest(selectedGuest.id, { remarks: nextCur }))
    history.forEach(h => {
      const r = String(h.remarks || '')
      const next = stripDNR(r)
      if (next !== r) tasks.push(updateGuest(h.id, { remarks: next }))
    })
    if (tasks.length > 0) await Promise.all(tasks)
    try { setHistory(await getGuestHistory(selectedGuest.id)) } catch {}
  }

  const onToggleDNR = async (checked) => {
    if (!selectedGuest) return
    setDnrBusy(true)
    try {
      if (checked) {
        const { setGuestDNR } = await import('../api')
        await setGuestDNR(selectedGuest.id, { set: true })
        setToast('Marked as DNR')
        setTimeout(() => setToast(''), 2500)
      } else {
        if (!window.confirm('Remove DNR for this guest and all past records?')) { setDnrBusy(false); return }
        const pin = window.prompt('Enter admin PIN to confirm DNR removal')
        if (!pin) { setToast('Admin PIN required'); setTimeout(() => setToast(''), 2500); setDnrBusy(false); return }
        const { setGuestDNR } = await import('../api')
        await setGuestDNR(selectedGuest.id, { set: false, adminPin: pin })
        setToast('Removed DNR from all records')
        setTimeout(() => setToast(''), 2500)
      }
      try { setSelectedGuest(await getGuest(selectedGuest.id)) } catch {}
      fetchForDate(selectedDate)
    } catch {
      setToast('DNR update failed')
      setTimeout(() => setToast(''), 2500)
    } finally {
      setDnrBusy(false)
    }
  }

  const removeDnrWithPin = async () => {
    if (!selectedGuest) return
    if (!adminPin) { setToast('Admin PIN required'); setTimeout(() => setToast(''), 2500); return }
    setDnrBusy(true)
    try {
      const { setGuestDNR } = await import('../api')
      await setGuestDNR(selectedGuest.id, { set: false, adminPin })
      setToast('Removed DNR from all records')
      setTimeout(() => setToast(''), 2500)
      try { setSelectedGuest(await getGuest(selectedGuest.id)) } catch {}
      fetchForDate(selectedDate)
      setAdminPin('')
    } catch {
      setToast('DNR update failed')
      setTimeout(() => setToast(''), 2500)
    } finally {
      setDnrBusy(false)
    }
  }

  const markDnrQuick = async () => {
    if (!selectedGuest) return
    const ok = window.confirm('Mark this guest as Do Not Rent?')
    if (!ok) return
    setDnrBusy(true)
    try {
      const { setGuestDNR } = await import('../api')
      await setGuestDNR(selectedGuest.id, { set: true })
      setToast('Marked as DNR')
      setTimeout(() => setToast(''), 2500)
      try { setSelectedGuest(await getGuest(selectedGuest.id)) } catch {}
      fetchForDate(selectedDate)
    } catch {
      setToast('DNR update failed')
      setTimeout(() => setToast(''), 2500)
    } finally {
      setDnrBusy(false)
    }
  }

  // Save updates
  const onSave = async () => {
    if (!selectedGuestId || !selectedGuest) return
    const payload = {
      first_name: selectedGuest.first_name,
      middle_name: selectedGuest.middle_name,
      last_name: selectedGuest.last_name,
      dob: selectedGuest.dob,
      id_number: selectedGuest.id_number,
      expiration_date: selectedGuest.expiration_date,
      issue_date: selectedGuest.issue_date,
      address: selectedGuest.address,
      city: selectedGuest.city,
      state: selectedGuest.state,
      zip_code: selectedGuest.zip_code,
      nationality: selectedGuest.nationality,
      phone_country_code: selectedGuest.phone_country_code,
      phone_number: selectedGuest.phone_number,
      room_number: editRoom,
      remarks: editRemarks,
      override_dnr: false,
    }
    try {
      const updated = await updateGuest(selectedGuestId, payload)
      setToast('Saved')
      setTimeout(() => setToast(''), 2000)
      // Refresh list to reflect changes
      fetchForDate(selectedDate)
      setDraftGuestId(null)
      draftRef.current = null
      setSelectedGuestId(null)
      setSelectedGuest(null)
      setFrontSrc('')
      setBackSrc('')
      setShowBackImage(false)
    } catch (e) {
      setToast('Save failed')
      setTimeout(() => setToast(''), 2500)
    }
  }

  const onSaveAndWrite = async () => {
    await onSave()
    if (!selectedGuestId) return
    try {
      await writePMS(selectedGuestId)
      setToast('Written to PMS')
      setTimeout(() => setToast(''), 2500)
      // Clear selection to prepare for next scan
      setDraftGuestId(null)
      draftRef.current = null
      setSelectedGuestId(null)
      setSelectedGuest(null)
      setFrontSrc('')
      setBackSrc('')
      setShowBackImage(false)
    } catch (e) {
      const msg = String(e?.response?.data?.detail || e?.message || '')
      if (msg.toLowerCase().includes('dnr')) {
        try {
          await writePMS(selectedGuestId, { override_dnr: true })
          setToast('Overridden and written to PMS')
          setTimeout(() => setToast(''), 2500)
          setDraftGuestId(null)
          draftRef.current = null
          setSelectedGuestId(null)
          setSelectedGuest(null)
          setFrontSrc('')
          setBackSrc('')
          setShowBackImage(false)
          return
        } catch {}
      }
      setToast('PMS write failed')
      setTimeout(() => setToast(''), 2500)
    }
  }

  const onSaveFill = async () => {
    await onSave()
    if (!selectedGuestId) return
    try {
      await autofillPMS(selectedGuestId)
      setToast('Auto-filled PMS')
      setTimeout(() => setToast(''), 2500)
      setDraftGuestId(null)
      draftRef.current = null
    } catch {
      setToast('Auto-fill failed')
      setTimeout(() => setToast(''), 2500)
    }
  }

  // Keyboard shortcuts: Ctrl+D today, Ctrl+Left/Right navigate
  useEffect(() => {
    const onKey = (e) => {
      if (e.ctrlKey && e.key === 'd') {
        e.preventDefault()
        setSelectedDate(new Date().toISOString().slice(0, 10))
      }
      if (e.ctrlKey && e.key === 'ArrowLeft') {
        e.preventDefault(); setDateOffset(-1)
      }
      if (e.ctrlKey && e.key === 'ArrowRight') {
        e.preventDefault(); setDateOffset(1)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [selectedDate])

  useEffect(() => {
    const t = setInterval(() => setNowStr(new Date().toLocaleTimeString()), 1000)
    return () => clearInterval(t)
  }, [])

  useEffect(() => {
    const timer = setInterval(() => {
      if (Date.now() - lastActivityAt > 15 * 60 * 1000) {
        try { localStorage.removeItem('jwt_token') } catch {}
      }
    }, 30000)
    return () => clearInterval(timer)
  }, [lastActivityAt])

  useEffect(() => {
    ;(async () => {
      if (!selectedGuest || !dnrInfo || Number(dnrInfo.tier || 0) < 1) return
      const cur = String(selectedGuest.remarks || '')
      if (cur.toLowerCase().includes('dnr')) return
      const next = cur ? `DNR — ${cur}` : 'DNR'
      try {
        const updated = await updateGuest(selectedGuest.id, { remarks: next })
        setSelectedGuest(updated)
        setEditRemarks(updated.remarks || '')
        setGuests(prev => prev.map(g => (g.id === updated.id ? updated : g)))
      } catch {}
    })()
  }, [dnrInfo, selectedGuest])

  return (
    <div className="space-y-4">
      
      {/* Toast */}
      {toast && <div className="fixed top-4 right-4 bg-slate-900 text-white px-3 py-2 rounded shadow" role="status" aria-live="polite">{toast}</div>}
      {/* Controls: date picker, navigation, search */}
      <div className="glass p-3 rounded flex flex-wrap items-center gap-3">
        <button onClick={() => setDateOffset(-1)} className="btn btn-muted" aria-label="Previous day" title="Previous day">←</button>
        <input type="date" value={selectedDate} onChange={e => setSelectedDate(e.target.value)} className="input" />
        <button onClick={() => setDateOffset(1)} className="btn btn-muted" aria-label="Next day" title="Next day">→</button>
        <div className="flex items-center gap-2 ml-auto">
          <input placeholder="Search name, room, ID" aria-label="Search guests" value={q} onChange={e => setQ(e.target.value)} className="input w-64" />
          {q && <button className="btn btn-outline" onClick={() => setQ('')}>Clear</button>}
        </div>
        
        <button className="btn btn-outline" onClick={() => setSortDesc(s => !s)}>{sortDesc ? 'Newest first' : 'Oldest first'}</button>
        
        <input type="file" accept="image/*" className="hidden" id="uploadFrontGlobal" onChange={e => setUploadFront(e.target.files?.[0] || null)} />
        <input type="file" accept="image/*" className="hidden" id="uploadBackGlobal" onChange={e => setUploadBack(e.target.files?.[0] || null)} />
        <button className="btn btn-secondary" aria-label="Upload front ID image" title="Upload front ID image" onClick={() => document.getElementById('uploadFrontGlobal').click()}>Upload Front</button>
        <button className="btn btn-secondary" aria-label="Upload back ID image" title="Upload back ID image" onClick={() => document.getElementById('uploadBackGlobal').click()}>Upload Back</button>
        <button className="btn btn-primary" onClick={async () => {
          if (!uploadFront) { setToast('Select front image'); setTimeout(() => setToast(''), 2000); return }
          try {
            const g = await scanIngest(uploadFront, uploadBack)
            await selectGuest(g)
            fetchForDate(selectedDate)
            setToast('ID processed')
            setTimeout(() => setToast(''), 2000)
            setUploadFront(null); setUploadBack(null)
          } catch {
            setToast('Processing failed')
            setTimeout(() => setToast(''), 2000)
          }
        }}>Process ID</button>
        <button className="btn btn-primary" onClick={async () => {
          setLoading(true)
          setToast('Scanning... Please scan front side of ID')
          try {
            const g = await scanDuplex()
            if (g && g.id) {
              await selectGuest(g)
              fetchForDate(selectedDate)
              // Check if data was extracted
              if (!g.first_name && !g.last_name) {
                setToast('Scanned but no data extracted. Check OCR debug or manually enter.')
              } else {
                setToast(`Scanned & processed: ${g.first_name || ''} ${g.last_name || ''}`.trim() || 'Scanned & processed')
              }
              setTimeout(() => setToast(''), 3000)
            } else {
              setToast('Scan completed but no guest created')
              setTimeout(() => setToast(''), 2000)
            }
          } catch (e) {
            const errorMsg = e?.response?.data?.detail || e?.message || 'Scanner error'
            setToast(`Scanner error: ${errorMsg}`)
            setTimeout(() => setToast(''), 4000)
            console.error('Scan error:', e)
          } finally {
            setLoading(false)
          }
        }} disabled={loading}>
          {loading ? 'Scanning...' : 'Scan Duplex (Front & Back)'}
        </button>
      </div>

      {/* Summary */}
      <div className="text-slate-700 text-sm flex items-center gap-4">
        <span>{filtered.length} guests checked in on {new Date(selectedDate).toLocaleDateString()}</span>
        <span className="text-slate-700 bg-slate-100 rounded px-2 py-1 border border-slate-200">MTD {mtdCount ?? '—'}</span>
        <span className="ml-auto text-slate-400">Local time: {nowStr}</span>
      </div>

      {/* Loading and error */}
      {loading && <div className="text-slate-400 text-sm">Loading…</div>}
      {error && <div className="text-red-400 text-sm">{error}</div>}

      {/* Split panels */}
      <div className="grid gap-4 grid-cols-12">
        {/* Left: list */}
        <div className="glass rounded-xl overflow-hidden col-span-4 max-h-[65vh] overflow-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 sticky top-0 z-10">
              <tr>
                <th scope="col" className="text-left px-4 py-2">Room</th>
                <th scope="col" className="text-left px-4 py-2">Guest Name</th>
                <th scope="col" className="text-left px-4 py-2">Check-In Time</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={3} className="px-4 py-6 text-center text-slate-400">No check-ins for this date.</td>
                </tr>
              )}
              {loading && filtered.length === 0 && (
                Array.from({ length: 6 }).map((_, i) => (
                  <tr key={i} className="border-t border-slate-200">
                    <td className="px-4 py-2">
                      <div className="h-3 w-16 bg-slate-200 animate-pulse rounded" />
                    </td>
                    <td className="px-4 py-2">
                      <div className="h-3 w-32 bg-slate-200 animate-pulse rounded" />
                    </td>
                    <td className="px-4 py-2">
                      <div className="h-3 w-20 bg-slate-200 animate-pulse rounded" />
                    </td>
                  </tr>
                ))
              )}
              {filtered.map(g => {
                const timeStr = checkinTime(g)
                const isToday = selectedDate === new Date().toISOString().slice(0, 10)
                const activeDot = isToday ? 'bg-emerald-500' : 'bg-slate-500'
                const dnr = Boolean(g.dnr_hit_id)
                const isSelected = selectedGuestId === g.id
                return (
                  <tr key={g.id} className={(isSelected ? 'bg-indigo-50 dark:bg-indigo-900/20 ring-1 ring-emerald-400 ' : '') + 'border-t border-slate-200 dark:border-slate-700 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/50'} onClick={() => selectGuest(g)} tabIndex={0} aria-selected={isSelected} onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); selectGuest(g) } }}>
                    <td className="px-4 py-2">
                      <div className="flex items-center gap-2">
                        <span className={`inline-block w-2 h-2 rounded-full ${activeDot}`}></span>
                        <span>{g.room_number || '—'}</span>
                      </div>
                    </td>
                    <td className="px-4 py-2">
                      <div className="flex items-center gap-2">
                        <span>{[g.first_name, g.last_name].filter(Boolean).join(' ') || '—'}</span>
                        {dnr && <span className="text-xs px-2 py-0.5 bg-red-600 text-white rounded" title="Do Not Rent — guest is restricted">DNR</span>}
                      </div>
                    </td>
                    <td className="px-4 py-2">{timeStr}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        {/* Right: details */}
        <div className="glass rounded-xl p-6 col-span-8 min-h-[65vh]">
          {!selectedGuest && !loading && <div className="text-slate-400">Select a guest to view details.</div>}
          {!selectedGuest && loading && (
            <div className="grid grid-cols-2 gap-6">
              <div className="space-y-2">
                {Array.from({ length: 10 }).map((_, i) => (
                  <div key={i} className="h-8 bg-slate-700 animate-pulse rounded" />
                ))}
              </div>
              <div className="space-y-3">
                <div className="h-64 bg-slate-700 animate-pulse rounded" />
                <div className="h-8 bg-slate-700 animate-pulse rounded" />
              </div>
            </div>
          )}
          {selectedGuest && (
            <div className="grid grid-cols-2 gap-6">
              {/* Left column: text data */}
              <div className="space-y-2">
                {(selectedGuest?.dnr_hit_id || (dnrInfo && dnrInfo.hit)) && (
                  <div className="bg-red-50 border border-red-200 text-red-700 rounded px-3 py-2 flex items-center justify-between">
                    <div>
                      <span className="font-semibold">DNR Match</span>
                      
                    </div>
                    <div className="text-sm">
                      {dnrInfo.hit ? `${dnrInfo.hit.first_name || ''} ${dnrInfo.hit.last_name || ''} · ${dnrInfo.hit.dob || ''}` : 'Potential match'}
                    </div>
                  </div>
                )}
                
                {selectedGuest?.dnr_hit_id && (
                  <div className="text-xs text-red-700">Notes: {String(selectedGuest?.remarks || '')}</div>
                )}
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <div className="text-slate-500 text-xs">First Name</div>
                    <input aria-label="First Name" className="input w-full" value={selectedGuest.first_name || ''} onChange={e => setSelectedGuest(s => ({ ...s, first_name: e.target.value }))} disabled={dnrToggleOn} />
                  </div>
                  <div>
                    <div className="text-slate-500 text-xs">Last Name</div>
                    <input aria-label="Last Name" className="input w-full" value={selectedGuest.last_name || ''} onChange={e => setSelectedGuest(s => ({ ...s, last_name: e.target.value }))} disabled={dnrToggleOn} />
                  </div>
                </div>
                  <div>
                    <div className="text-slate-500 text-xs">Street Address</div>
                    <input aria-label="Street Address" className="input w-full" value={selectedGuest.address || ''} onChange={e => setSelectedGuest(s => ({ ...s, address: e.target.value }))} disabled={dnrToggleOn} />
                  </div>
                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <div className="text-slate-500 text-xs">City</div>
                    <input className="input w-full" value={selectedGuest.city || ''} onChange={e => setSelectedGuest(s => ({ ...s, city: e.target.value }))} disabled={dnrToggleOn} />
                  </div>
                  <div>
                    <div className="text-slate-500 text-xs">State</div>
                    <input className="bg-white border border-slate-300 rounded px-2 py-1 w-full" value={selectedGuest.state || ''} onChange={e => setSelectedGuest(s => ({ ...s, state: e.target.value }))} disabled={dnrToggleOn} />
                  </div>
                  <div>
                    <div className="text-slate-500 text-xs">ZIP</div>
                    <input className="bg-white border border-slate-300 rounded px-2 py-1 w-full" value={selectedGuest.zip_code || ''} onChange={e => setSelectedGuest(s => ({ ...s, zip_code: e.target.value }))} disabled={dnrToggleOn} />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <div className="text-slate-500 text-xs">Phone Country Code</div>
                    <input className="bg-white border border-slate-300 rounded px-2 py-1 w-full" value={selectedGuest.phone_country_code || ''} onChange={e => setSelectedGuest(s => ({ ...s, phone_country_code: e.target.value }))} disabled={dnrToggleOn} />
                  </div>
                  <div>
                    <div className="text-slate-500 text-xs">Phone Number</div>
                    <input className="bg-white border border-slate-300 rounded px-2 py-1 w-full" value={selectedGuest.phone_number || ''} onChange={e => setSelectedGuest(s => ({ ...s, phone_number: e.target.value }))} disabled={dnrToggleOn} />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <div className="text-slate-500 text-xs">ID Number</div>
                    <input aria-label="ID Number" className="input w-full" value={selectedGuest.id_number || ''} onChange={e => setSelectedGuest(s => ({ ...s, id_number: e.target.value }))} disabled={dnrToggleOn} />
                  </div>
                  <div>
                    <div className="text-slate-500 text-xs">Nationality</div>
                    <input aria-label="Nationality" className="input w-full" value={selectedGuest.nationality || ''} onChange={e => setSelectedGuest(s => ({ ...s, nationality: e.target.value }))} disabled={dnrToggleOn} />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <div className="text-slate-500 text-xs">Issued</div>
                    <input aria-label="Issue Date" className="input w-full" value={toMMDDYYYY(selectedGuest.issue_date || '')} onChange={e => setSelectedGuest(s => ({ ...s, issue_date: toISODate(e.target.value) }))} disabled={dnrToggleOn} />
                  </div>
                  <div>
                    <div className="text-slate-500 text-xs">Expires</div>
                    <input aria-label="Expiration Date" className="input w-full" value={toMMDDYYYY(selectedGuest.expiration_date || '')} onChange={e => setSelectedGuest(s => ({ ...s, expiration_date: toISODate(e.target.value) }))} disabled={dnrToggleOn} />
                  </div>
                  <div>
                    <div className="text-slate-500 text-xs">Date of Birth</div>
                    <input aria-label="Date of Birth" className="input w-full" value={toMMDDYYYY(selectedGuest.dob || '')} onChange={e => setSelectedGuest(s => ({ ...s, dob: toISODate(e.target.value) }))} disabled={dnrToggleOn} />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <div className="text-slate-500 text-xs">Room Number</div>
                    <input aria-label="Room Number" className="input w-full" value={editRoom} onChange={e => setEditRoom(e.target.value)} disabled={dnrToggleOn} />
                  </div>
                  <div>
                    <div className="text-slate-500 text-xs">Remarks / Notes</div>
                    <input aria-label="Remarks or Notes" className="input w-full" value={editRemarks} onChange={e => setEditRemarks(e.target.value)} disabled={dnrToggleOn} />
                  </div>
                </div>
                {/* Minimal action bar */}

                {/* Check-In Details table */}
                <div className="glass p-3 rounded mt-3">
                  <div className="text-slate-300 text-sm mb-2">Check-In Details</div>
                  <table className="w-full text-sm">
                    <thead className="text-slate-400">
                      <tr>
                        <th className="text-left py-1">Date</th>
                        <th className="text-left py-1">Time</th>
                        <th className="text-left py-1">Remark</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td className="py-1">{new Date(selectedGuest.created_at).toLocaleDateString()}</td>
                        <td className="py-1">{checkinTime(selectedGuest)}</td>
                        <td className="py-1">{selectedGuest.remarks || '—'}</td>
                      </tr>
                    </tbody>
                  </table>
                  <div className="mt-3 flex items-center gap-2">
                    <button className="btn btn-secondary" onClick={onSave} disabled={dnrBusy}>Save</button>
                    <button className="btn btn-primary" onClick={onSaveAndWrite} disabled={dnrBusy}>Save & Write to PMS</button>
                    <button
                      className={`btn ${dnrToggleOn ? 'btn-danger' : 'btn-success'}`}
                      aria-label="DNR Status"
                      title="DNR Status"
                      onClick={() => { setPinAction(dnrToggleOn ? 'remove' : 'add'); setPinModalOpen(true); setPinInput(''); setPinError(''); setTimeout(() => { try { pinInputRef.current && pinInputRef.current.focus() } catch {} }, 0) }}
                      disabled={dnrBusy}
                    >
                      {dnrToggleOn ? 'DNR Status: Active' : 'DNR Status: Inactive'}
                    </button>
                    <button className="btn btn-outline" onClick={() => selectGuest(selectedGuest)}>Cancel</button>
                  </div>
                </div>
                <div className="glass p-3 rounded mt-3">
                  <div className="text-slate-700 text-sm mb-2">Guest History</div>
                  {(!history || history.length === 0) && <div className="text-slate-600 text-sm">No previous check-ins.</div>}
                  {history && history.length > 0 && (
                    <table className="w-full text-sm">
                      <thead className="text-slate-600">
                        <tr>
                          <th className="text-left py-1">Date</th>
                          <th className="text-left py-1">Room</th>
                          <th className="text-left py-1">Notes</th>
                        </tr>
                      </thead>
                      <tbody>
                        {history.map(h => (
                          <tr key={h.id}>
                            <td className="py-1">{h.created_at ? new Date(h.created_at).toLocaleString() : '—'}</td>
                            <td className="py-1">{h.room_number || '—'}</td>
                            <td className="py-1">{h.remarks || '—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                  {summary && (
                    <div className="text-slate-600 text-xs mt-2">Total check-ins: {summary.total_checkins}</div>
                  )}
                </div>
              </div>

              {/* Right column: visuals */}
              <div className="space-y-3">
                {!showBackImage && frontSrc && !imageErrorFront && (
                  <img
                    src={frontSrc}
                    alt="Front"
                    className="w-full h-auto rounded"
                    loading="lazy"
                    onError={() => { console.error('Front image failed to load', { guestId: selectedGuest?.id, path: selectedGuest?.image_front_path }); setImageErrorFront(true) }}
                  />
                )}
                {showBackImage && backSrc && !imageErrorBack && (
                  <img
                    src={backSrc}
                    alt="Back"
                    className="w-full h-auto rounded"
                    loading="lazy"
                    onError={() => { console.error('Back image failed to load', { guestId: selectedGuest?.id, path: selectedGuest?.image_back_path }); setImageErrorBack(true) }}
                  />
                )}
                {!showBackImage && imageErrorFront && (
                  <div className="w-full h-64 bg-slate-100 border border-slate-200 rounded flex items-center justify-center text-slate-400">
                    Image unavailable
                  </div>
                )}
                {showBackImage && imageErrorBack && (
                  <div className="w-full h-64 bg-slate-100 border border-slate-200 rounded flex items-center justify-center text-slate-400">
                    Image unavailable
                  </div>
                )}
                <div>
                  <button className="btn btn-outline" title="Toggle ID side" aria-label="Toggle ID side" onClick={() => setShowBackImage(s => !s)}>
                    {showBackImage ? 'Show Front' : 'Show Back'}
                  </button>
                </div>
                <div className="flex items-center gap-2">
                  <input type="file" accept="image/*" ref={fileFrontRef} className="hidden" onChange={async e => {
                    const f = e.target.files?.[0]; if (!f || !selectedGuest) return
                    try {
                      await uploadGuestImage(selectedGuest.id, 'front', f)
                      const { processGuestImages } = await import('../api')
                      const g = await processGuestImages(selectedGuest.id, true)
                      await selectGuest(g)
                      setToast('Front processed')
                      setTimeout(() => setToast(''), 2000)
                    } catch {}
                  }} />
                  <input type="file" accept="image/*" ref={fileBackRef} className="hidden" onChange={async e => {
                    const f = e.target.files?.[0]; if (!f || !selectedGuest) return
                    try {
                      await uploadGuestImage(selectedGuest.id, 'back', f)
                      const { processGuestImages } = await import('../api')
                      const g = await processGuestImages(selectedGuest.id, true)
                      await selectGuest(g)
                      setToast('Back processed')
                      setTimeout(() => setToast(''), 2000)
                    } catch {}
                  }} />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    {pinModalOpen && (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" role="dialog" aria-modal="true" aria-labelledby="dnrPinTitle">
        <div className="glass rounded-xl p-4 w-[340px]" onKeyDown={e => { if (e.key === 'Escape') { setPinModalOpen(false) } }}>
          <div id="dnrPinTitle" className="text-lg font-semibold mb-2">Enter Admin PIN</div>
          <div className="space-y-2">
            <input ref={pinInputRef} className="input w-full" type="password" inputMode="numeric" pattern="[0-9]*" aria-label="Admin PIN" value={pinInput} onChange={e => setPinInput(e.target.value)} />
            {pinError && <div className="text-rose-600 text-sm" role="alert">{pinError}</div>}
          </div>
          <div className="mt-3 flex items-center gap-2 justify-end">
            <button className="btn btn-outline" onClick={() => { setPinModalOpen(false); setPinInput(''); setPinError('') }}>Cancel</button>
            <button className="btn btn-primary" onClick={async () => {
              setLastActivityAt(Date.now())
              const now = Date.now()
              const windowMs = 5 * 60 * 1000
              const maxAttempts = 5
              const recent = pinAttempts.filter(t => now - t < windowMs)
              if (recent.length >= maxAttempts) { setPinError('Too many attempts. Please wait.'); return }
              if (!/^\d{4,6}$/.test(pinInput)) { setPinError('PIN must be 4-6 digits'); return }
              setPinSubmitting(true)
              try {
                const { authLoginWithPin, setGuestDNR } = await import('../api')
                const resp = await authLoginWithPin(pinInput)
                try { localStorage.setItem('jwt_token', String(resp?.access_token || '')) } catch {}
                const setFlag = pinAction === 'add'
                await setGuestDNR(selectedGuest.id, { set: setFlag, adminPin: pinInput })
                setToast(setFlag ? 'Marked as DNR' : 'Removed DNR')
                setTimeout(() => setToast(''), 2500)
                try { setSelectedGuest(await getGuest(selectedGuest.id)) } catch {}
                fetchForDate(selectedDate)
                setDnrToggleOn(setFlag)
                setPinModalOpen(false)
                setPinInput('')
                setPinError('')
              } catch (e) {
                const msg = String(e?.response?.data?.detail || e?.message || 'Error')
                if (msg.toLowerCase().includes('invalid pin')) setPinError('Invalid PIN')
                else setPinError('Operation failed')
              } finally {
                setPinSubmitting(false)
                setPinAttempts(prev => [...prev.filter(t => now - t < windowMs), now])
              }
            }} disabled={pinSubmitting}>{pinSubmitting ? 'Submitting…' : 'Submit'}</button>
          </div>
        </div>
      </div>
    )}
    </div>
  )
}
