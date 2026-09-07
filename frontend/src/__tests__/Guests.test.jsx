import { describe, test, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import React from 'react'
import Guests from '../pages/Guests'

vi.mock('../api', () => ({
  listGuests: vi.fn(async () => ([{ id: 1, first_name: 'John', last_name: 'Doe', created_at: new Date().toISOString() }])),
  statsMtd: vi.fn(async () => 1),
  subscribeCheckins: vi.fn(() => null),
  getGuest: vi.fn(async (id) => ({ id, first_name: 'John', last_name: 'Doe', image_front_path: 'C:/project/IDscnr/backend/temp/temp_front_test.jpg.enc' })),
  getGuestHistory: vi.fn(async () => []),
  getGuestSummary: vi.fn(async () => ({ total_checkins: 1 })),
  updateGuest: vi.fn(async (id, payload) => ({ id, ...payload })),
  writePMS: vi.fn(async () => ({ status: 'ok' })),
  addDNR: vi.fn(async () => ({ status: 'ok' })),
  dnrMatch: vi.fn(async () => ({ tier: 0 })),
  scanIngest: vi.fn(async () => ({ id: 2, first_name: 'Jane', last_name: 'Smith', created_at: new Date().toISOString() })),
  uploadGuestImage: vi.fn(async () => ({ status: 'ok' })),
  scanDuplex: vi.fn(async () => ({ id: 3, first_name: 'Zed', last_name: 'Lee', created_at: new Date().toISOString() })),
  imageUrl: (p) => 'http://localhost:8000/image?path=' + encodeURIComponent(p),
}))

describe('Guests page', () => {
  test('renders controls and a guest item', async () => {
    render(<Guests />)
    expect(await screen.findByPlaceholderText('Search name, room, ID')).toBeTruthy()
    expect(await screen.findByText('John Doe')).toBeTruthy()
  })

  test('shows fallback when image fails to load', async () => {
    render(<Guests />)
    const name = await screen.findByText('John Doe')
    expect(name).toBeTruthy()
    const img = await screen.findByAltText('Front')
    fireEvent.error(img)
    expect(await screen.findByText('Image unavailable')).toBeTruthy()
  })
})