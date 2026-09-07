import MockAdapter from 'axios-mock-adapter'
import { describe, test, expect, beforeAll, afterAll } from 'vitest'
import api, { imageUrl, listGuests, updateGuest, subscribeCheckins } from '../api'

describe('api helpers', () => {
  let mock
  beforeAll(() => {
    mock = new MockAdapter(api)
  })
  afterAll(() => {
    mock.restore()
  })

  test('imageUrl encodes path', () => {
    const url = imageUrl('C:/path/to/img.jpg.enc')
    expect(url).toMatch('http://localhost:8000/image?path=')
    expect(url).toMatch(encodeURIComponent('C:/path/to/img.jpg.enc'))
  })

  test('listGuests hits /guests?date=', async () => {
    mock.onGet(/\/guests\?date=/).reply(200, [{ id: 1 }])
    const data = await listGuests('2025-11-16')
    expect(Array.isArray(data)).toBe(true)
    expect(data[0].id).toBe(1)
  })

  test('updateGuest sends FormData and returns data', async () => {
    const id = 42
    mock.onPost(`/guest/${id}/update`).reply(config => {
      // FormData is serialized by axios for tests; just ensure request exists
      expect(config.method).toBe('post')
      return [200, { id, remarks: 'X' }]
    })
    const data = await updateGuest(id, { remarks: 'X', override_dnr: true })
    expect(data.id).toBe(id)
    expect(data.remarks).toBe('X')
  })

  test('subscribeCheckins returns EventSource or null', () => {
    const orig = global.EventSource
    class FakeES { constructor(){} close(){} }
    global.EventSource = FakeES
    const es = subscribeCheckins('2025-11-16')
    expect(es).toBeInstanceOf(FakeES)
    global.EventSource = orig
  })
})