async function send(path, data) {
  const response = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
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
    const response = await fetch('/api/trips')
    if (!response.ok) throw new Error('Could not load trips.')
    return response.json()
  },
  recommend: async (tripId) => {
    const response = await fetch(`/api/trips/${tripId}/recommendations`, { method: 'POST' })
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

