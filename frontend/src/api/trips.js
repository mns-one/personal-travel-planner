const API_BASE_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')
const OWNER_ID_KEY = 'wanderwise-owner-id'

function getOwnerId() {
  let ownerId = localStorage.getItem(OWNER_ID_KEY)
  if (!ownerId) {
    ownerId = crypto.randomUUID()
    localStorage.setItem(OWNER_ID_KEY, ownerId)
  }
  return ownerId
}

function ownerHeaders() {
  return { 'X-Owner-ID': getOwnerId() }
}

async function send(path, data, method = 'POST') {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json', ...ownerHeaders() },
    body: JSON.stringify(data),
  })
  const result = await response.json()
  if (!response.ok) {
    const message = Array.isArray(result.detail)
      ? result.detail.map((issue) => issue.msg).join(', ')
      : result.detail || 'Something went wrong. Please try again.'
    throw new Error(message)
  }
  return result
}

export const tripsAPI = {
  create: (trip) => send('/api/trips', trip),
  list: async () => {
    const response = await fetch(`${API_BASE_URL}/api/trips`, { headers: ownerHeaders() })
    if (!response.ok) throw new Error('Could not load trips.')
    return response.json()
  },
  get: async (tripId) => {
    const response = await fetch(`${API_BASE_URL}/api/trips/${tripId}`, { headers: ownerHeaders() })
    const result = await response.json()
    if (!response.ok) throw new Error(result.detail || 'Could not load this trip.')
    return result
  },
  update: (tripId, fields) => send(`/api/trips/${tripId}`, fields, 'PATCH'),
  remove: async (tripId) => {
    const response = await fetch(`${API_BASE_URL}/api/trips/${tripId}`, { method: 'DELETE', headers: ownerHeaders() })
    if (!response.ok) throw new Error('Could not delete trip.')
  },
  recommend: async (tripId) => {
    const response = await fetch(`${API_BASE_URL}/api/trips/${tripId}/recommendations`, { method: 'POST', headers: ownerHeaders() })
    const result = await response.json()
    if (!response.ok) throw new Error(result.detail || 'Could not load recommendations.')
    return result
  },
  generateItinerary: (tripId) => send('/api/itineraries/generate', { trip_id: tripId }),
  refineItinerary: (tripId, itinerary, instruction, day = null) => send(
    `/api/trips/${tripId}/itinerary/refine`,
    { itinerary, instruction, day },
  ),
}

