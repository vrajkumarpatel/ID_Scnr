import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Guests from '../pages/Guests.jsx'

vi.mock('../api', () => ({
  listGuests: async () => [{ id: 1, first_name: 'Test', last_name: 'User', created_at: new Date().toISOString(), room_number: '101' }],
  statsMtd: async () => 0,
  subscribeCheckins: () => null,
  dnrMatch: async () => ({ hit: null, score: 0, tier: 0 }),
  getGuest: async (id) => ({ id, first_name: 'Test', last_name: 'User', created_at: new Date().toISOString(), room_number: '101' }),
}))

describe('PIN validation', () => {
  it('shows error for invalid PIN', async () => {
    render(<Guests />)
    const rows = await screen.findAllByRole('row')
    await userEvent.click(rows[1])
    await screen.findByRole('button', { name: /Save/ })
    const toggleBtn = await screen.findByRole('button', { name: /DNR Status/ })
    await userEvent.click(toggleBtn)
    const pinInput = await screen.findByLabelText('Admin PIN')
    await userEvent.type(pinInput, '12')
    const submit = await screen.findByRole('button', { name: /Submit/ })
    await userEvent.click(submit)
    const err = await screen.findByText(/PIN must be 4-6 digits/)
    expect(err).toBeInTheDocument()
  })
})