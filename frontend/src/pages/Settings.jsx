import React, { useEffect, useState } from 'react'
import { getScannerDevices, settingsGet, settingsUpdate, statsMtd, statsDnr, listOverrides } from '../api'

export default function Settings() {
  const [devices, setDevices] = useState([])
  const [settings, setSettings] = useState({ ocr_provider: 'google', scan_device: '', auto_pms_write: false, dark_mode: true, pms_export_mode: 'json' })
  const [msg, setMsg] = useState('')
  const [mtd, setMtd] = useState(null)
  const [dnr, setDnr] = useState(null)
  const [overrides, setOverrides] = useState([])

  useEffect(() => {
    (async () => {
      try {
        const s = await settingsGet()
        setSettings(s)
      } catch (e) {
        console.error(e)
      }
      try {
        const ds = await getScannerDevices()
        setDevices(ds)
      } catch (e) {
        console.error(e)
      }
      try {
        const today = new Date().toISOString().slice(0, 10)
        const m = await statsMtd(today)
        setMtd(m)
        const month = today.slice(0, 7)
        const d = await statsDnr(month)
        setDnr(d)
      } catch (e) {
        setMtd(null); setDnr(null)
      }
      try {
        const rows = await listOverrides(50)
        setOverrides(Array.isArray(rows) ? rows : [])
      } catch {}
    })()
  }, [])

  const save = async () => {
    setMsg('')
    try {
      const resp = await settingsUpdate(settings)
      setSettings(resp.settings)
      setMsg('Settings saved')
    } catch (e) {
      setMsg('Failed to save settings')
    }
  }

  const toggleDarkMode = async () => {
    const next = !settings.dark_mode
    const newSettings = { ...settings, dark_mode: next }
    setSettings(newSettings)
    try { await settingsUpdate({ dark_mode: next }) } catch {}
    try {
      localStorage.setItem('dark_mode', String(next))
      document.documentElement.classList.toggle('dark', next)
    } catch {}
  }


  return (
    <div className="glass p-6 rounded-xl space-y-4">
      <h2 className="text-xl font-semibold">Settings</h2>
      <div className="grid grid-cols-3 gap-3">
        <div className="glass p-3 rounded">
          <div className="text-slate-400 text-xs">Month-to-date Check-ins</div>
          <div className="text-xl">{mtd ?? '—'}</div>
        </div>
        <div className="glass p-3 rounded">
          <div className="text-slate-400 text-xs">DNR Strong Hits (Month)</div>
          <div className="text-xl">{dnr?.strong_hits ?? '—'}</div>
        </div>
        <div className="glass p-3 rounded">
          <div className="text-slate-400 text-xs">DNR Overrides (Month)</div>
          <div className="text-xl">{dnr?.overrides ?? '—'}</div>
        </div>
      </div>
      {msg && <div className="text-sm text-emerald-500">{msg}</div>}
      <div className="grid grid-cols-2 gap-4">
        <Setting label="Scanner Device">
          <select className="input" value={settings.scan_device || ''} onChange={e => setSettings({ ...settings, scan_device: e.target.value })}>
            <option value="">Default</option>
            {devices.map((d, i) => <option key={i} value={d}>{d}</option>)}
          </select>
        </Setting>

        <Setting label="OCR Provider">
          <select className="input" value={settings.ocr_provider} onChange={e => setSettings({ ...settings, ocr_provider: e.target.value })}>
            <option value="google">Google Vision</option>
            <option value="tesseract">Tesseract</option>
          </select>
        </Setting>

        <Setting label="Google Vision API Key">
          <input
            className="input w-full"
            type="password"
            placeholder="Paste Google Vision API key"
            value={settings.google_api_key || ''}
            onChange={e => setSettings({ ...settings, google_api_key: e.target.value })}
          />
        </Setting>

        <Setting label="Auto PMS Write">
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={!!settings.auto_pms_write} onChange={e => setSettings({ ...settings, auto_pms_write: e.target.checked })} />
            <span>Automatically export to PMS on save</span>
          </label>
        </Setting>

        <Setting label="Dark Mode">
          <button className="btn" onClick={toggleDarkMode}>{settings.dark_mode ? 'Disable' : 'Enable'} Dark Mode</button>
        </Setting>

        

        <Setting label="PMS Export Mode">
          <select className="input" value={settings.pms_export_mode || 'json'} onChange={e => setSettings({ ...settings, pms_export_mode: e.target.value })}>
            <option value="json">JSON</option>
            <option value="csv">CSV</option>
            <option value="api">API POST</option>
          </select>
        </Setting>

        <Setting label="PMS Export Path">
          <input className="input w-full" value={settings.pms_export_path || ''} onChange={e => setSettings({ ...settings, pms_export_path: e.target.value })} />
        </Setting>

        <Setting label="PMS API URL">
          <input className="input w-full" value={settings.pms_api_url || ''} onChange={e => setSettings({ ...settings, pms_api_url: e.target.value })} />
        </Setting>

        <Setting label="PMS Window Title">
          <input className="input w-full" value={settings.pms_window_title || ''} onChange={e => setSettings({ ...settings, pms_window_title: e.target.value })} />
        </Setting>

        <Setting label="PMS Auto-Fill Tab Order">
          <input className="input w-full" value={Array.isArray(settings.pms_autofill_tab_order) ? settings.pms_autofill_tab_order.join(',') : (settings.pms_autofill_tab_order || '')} onChange={e => setSettings({ ...settings, pms_autofill_tab_order: e.target.value })} />
        </Setting>

        <Setting label="PMS Auto-Fill Delay (ms)">
          <input className="input w-full" type="number" min="0" value={String(settings.pms_autofill_delay_ms ?? 50)} onChange={e => setSettings({ ...settings, pms_autofill_delay_ms: e.target.value })} />
        </Setting>
      </div>

      <div className="pt-2">
        <button className="btn" onClick={save}>Save Settings</button>
      </div>

      <div className="glass p-6 rounded-xl mt-4">
        <div className="text-slate-200 font-semibold mb-2">Help</div>
        <div className="text-slate-300 text-sm space-y-1">
          <div>Ctrl+D — Jump to today</div>
          <div>Ctrl+←/→ — Previous/Next day</div>
          <div>Enter — Save guest</div>
          <div>Alt+W — Save & Write PMS</div>
          <div>Alt+F — Save & Fill PMS</div>
        </div>
      </div>

      <div className="glass p-6 rounded-xl mt-4">
        <div className="text-slate-200 font-semibold mb-2">Override Center</div>
        <div className="text-slate-400 text-xs mb-2">Recent DNR overrides</div>
        {!overrides || overrides.length === 0 ? (
          <div className="text-slate-400 text-sm">No overrides.</div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-slate-800 text-slate-300">
              <tr>
                <th className="text-left px-4 py-2">Date</th>
                <th className="text-left px-4 py-2">Guest</th>
                <th className="text-left px-4 py-2">Reason</th>
                <th className="text-left px-4 py-2">Actor</th>
              </tr>
            </thead>
            <tbody>
              {overrides.map(r => (
                <tr key={r.guest_id} className="border-t border-slate-700">
                  <td className="px-4 py-2">{r.at ? new Date(r.at).toLocaleString() : '—'}</td>
                  <td className="px-4 py-2">{[r.first_name, r.last_name].filter(Boolean).join(' ') || r.guest_id}</td>
                  <td className="px-4 py-2">{r.reason || '—'}</td>
                  <td className="px-4 py-2">{r.actor || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

function Setting({ label, children }) {
  return (
    <div className="glass p-4 rounded">
      <div className="text-slate-400 text-xs mb-1">{label}</div>
      <div>{children}</div>
    </div>
  )
}
