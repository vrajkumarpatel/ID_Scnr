import axios from 'axios'

const baseURL = import.meta.env?.VITE_API_URL || 'http://localhost:8000'
const api = axios.create({ baseURL })

export async function listGuests(date) {
  const qs = date ? `?date=${encodeURIComponent(date)}` : ''
  const { data } = await api.get(`/guests${qs}`)
  return data
}

export async function statsMtd(date) {
  const qs = date ? `?date=${encodeURIComponent(date)}` : ''
  const { data } = await api.get(`/stats/mtd${qs}`)
  return data?.mtd ?? null
}

export async function statsDnr(month) {
  const qs = month ? `?month=${encodeURIComponent(month)}` : ''
  const { data } = await api.get(`/stats/dnr${qs}`)
  return data
}

export async function getGuest(id) {
  const { data } = await api.get(`/guest/${id}`)
  return data
}

export async function getGuestHistory(id) {
  const { data } = await api.get(`/guest/${id}/history`)
  return data
}

export async function getGuestSummary(id) {
  const { data } = await api.get(`/guest/${id}/summary`)
  return data
}

export async function uploadGuestImage(id, side, file) {
  const form = new FormData()
  form.append('side', side)
  form.append('file', file)
  const { data } = await api.post(`/guest/${id}/upload-image`, form)
  return data
}

export async function scanIngest(frontFile, backFile) {
  const form = new FormData()
  if (frontFile) form.append('front', frontFile)
  if (backFile) form.append('back', backFile)
  const { data } = await api.post('/scan/ingest', form)
  return data
}

export async function processGuestImages(id, overwrite = true) {
  const { data } = await api.post(`/guest/${id}/process-images?overwrite=${overwrite ? 'true' : 'false'}`)
  return data
}

export async function scanDuplex() {
  const { data } = await api.post('/scan/duplex')
  return data
}

export async function updateGuest(id, payload = {}, adminPin) {
  const form = new FormData()
  Object.entries(payload).forEach(([k, v]) => {
    if (v !== undefined && v !== null) form.append(k, String(v))
  })
  form.append('override_dnr', String(Boolean(payload.override_dnr)))
  if (adminPin) form.append('admin_pin', adminPin)
  const { data } = await api.post(`/guest/${id}/update`, form)
  return data
}

export const imageUrl = (path) => `${baseURL}/image?path=${encodeURIComponent(path)}`

export async function writePMS(guestId, opts = {}) {
  const qs = new URLSearchParams({ guest_id: String(guestId) })
  if (opts.override_dnr) qs.set('override_dnr', 'true')
  if (opts.adminPin) qs.set('admin_pin', String(opts.adminPin))
  if (opts.overrideReason) qs.set('override_reason', String(opts.overrideReason))
  const { data } = await api.post('/pms/write?' + qs.toString())
  return data
}

export async function autofillPMS(guestId) {
  const { data } = await api.post('/pms/autofill?guest_id=' + String(guestId))
  return data
}

export async function getScannerDevices() {
  const { data } = await api.get('/scan/devices')
  return data.devices || []
}

export async function settingsGet() {
  const { data } = await api.get('/settings/get')
  return data
}

export function subscribeCheckins(date) {
  const qs = date ? `?date=${encodeURIComponent(date)}` : ''
  const url = `${baseURL}/checkins/stream${qs}`
  try {
    const es = new EventSource(url)
    return es
  } catch (e) {
    console.warn('EventSource not available', e)
    return null
  }
}

export async function settingsUpdate(payload) {
  const form = new FormData()
  Object.entries(payload || {}).forEach(([k, v]) => {
    if (v !== undefined && v !== null) form.append(k, String(v))
  })
  const token = localStorage.getItem('jwt_token') || ''
  const { data } = await api.post('/settings/update', form, { headers: authHeaders(token) })
  return data
}

export async function adminPinUpdate(currentPin, newPin) {
  const form = new FormData()
  form.append('current_pin', currentPin)
  form.append('new_pin', newPin)
  const token = localStorage.getItem('jwt_token') || ''
  const { data } = await api.post('/admin/pin/update', form, { headers: authHeaders(token) })
  return data
}

export default api

// --- Auth helpers ---
export async function authLoginWithPin(pin) {
  const form = new FormData()
  form.append('pin', pin)
  const { data } = await api.post('/auth/login', form)
  return data // { access_token, token_type, role }
}

function authHeaders(token) {
  return token ? { Authorization: `Bearer ${token}` } : {}
}

// --- DNR helpers ---
export async function listDNR() {
  const { data } = await api.get('/dnr')
  return data
}

export async function addDNR(entry) {
  const form = new FormData()
  Object.entries(entry || {}).forEach(([k, v]) => {
    if (v !== undefined && v !== null) form.append(k, String(v))
  })
  const { data } = await api.post('/dnr', form)
  return data
}

export async function dnrMatch(guestId) {
  const { data } = await api.get('/dnr/match?guest_id=' + guestId)
  return data
}

export async function fetchImage(path) {
  const token = localStorage.getItem('jwt_token') || ''
  const resp = await api.get(`/image?path=${encodeURIComponent(path)}`,{ responseType: 'blob', headers: authHeaders(token) })
  return resp.data
}
export async function searchDNR(q) {
  const { data } = await api.get('/dnr?q=' + encodeURIComponent(q || ''))
  return data
}

export async function deleteDNR(id) {
  await api.delete('/dnr/' + String(id))
  return true
}

export async function setGuestDNR(guestId, opts = {}) {
  const form = new FormData()
  form.append('set', String(Boolean(opts.set)))
  if (opts.adminPin) form.append('admin_pin', String(opts.adminPin))
  const { data } = await api.post(`/guest/${guestId}/dnr`, form)
  return data
}

export async function listOverrides(limit = 50) {
  const token = localStorage.getItem('jwt_token') || ''
  const { data } = await api.get('/admin/overrides?limit=' + String(limit), { headers: authHeaders(token) })
  return data
}
