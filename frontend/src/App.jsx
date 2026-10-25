import { useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import {
  ArrowLeft, ArrowRight, CalendarDays, Check, Compass, Copy, Download, MapPin,
  Share2, Sparkles, Users, Wallet,
} from 'lucide-react'
import { tripsAPI } from './api/trips.js'

const steps = ['Destination', 'Dates & budget', 'Your style']
const interestOptions = ['Food', 'Nature', 'Culture', 'History', 'Adventure', 'Shopping']
const paceOptions = [
  { value: 'relaxed', label: 'Slow & easy', note: 'Plenty of downtime' },
  { value: 'balanced', label: 'A little of both', note: 'A few plans each day' },
  { value: 'active', label: 'Pack it in', note: 'See as much as possible' },
]

const blankTrip = {
  destination: '', start_date: '', end_date: '', budget: '', travelers: 1,
  interests: [], dietary_needs: [], mobility_needs: [], travel_pace: 'balanced', travel_style: 'comfort',
}

function downloadFile(filename, contents, contentType) {
  const file = new Blob([contents], { type: contentType })
  const url = URL.createObjectURL(file)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

function itineraryMarkdown(trip, itinerary) {
  const lines = [
    `# ${itinerary.destination} Trip Plan`,
    '',
    `**Dates:** ${trip.start_date} to ${trip.end_date}  `,
    `**Travelers:** ${trip.travelers}  `,
    `**Budget:** ${trip.budget}  `,
    `**Style:** ${trip.travel_style} · **Pace:** ${trip.travel_pace}`,
    '',
  ]
  itinerary.days.forEach((day) => {
    lines.push(`## Day ${day.day}: ${day.title} (${day.date})`, '')
    for (const [slot, activities] of [['Morning', day.morning], ['Afternoon', day.afternoon], ['Evening', day.evening]]) {
      if (activities.length) {
        lines.push(`### ${slot}`)
        activities.forEach((activity) => lines.push(`- ${activity}`))
        lines.push('')
      }
    }
    if (day.notes.length) lines.push(`**Notes:** ${day.notes.join(' ')}`, '')
  })
  lines.push(`---`, '', itinerary.note)
  return lines.join('\n')
}

function App() {
  const [step, setStep] = useState(0)
  const [trip, setTrip] = useState(blankTrip)
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [recommendations, setRecommendations] = useState(null)
  const [tripId, setTripId] = useState(null)
  const [refinement, setRefinement] = useState('')
  const [refineDay, setRefineDay] = useState('')
  const [refining, setRefining] = useState(false)
  const [refineMessage, setRefineMessage] = useState('')
  const [apiError, setApiError] = useState('')
  const [savedTrips, setSavedTrips] = useState([])
  const [historyError, setHistoryError] = useState('')
  const [shareMessage, setShareMessage] = useState('')
  const [isSharedView, setIsSharedView] = useState(false)

  useEffect(() => {
    document.title = result ? `Your ${trip.destination} itinerary — Wanderwise` : 'Wanderwise — your trip, your way'
  }, [result, trip.destination])

  function update(field, value) {
    setTrip((current) => ({ ...current, [field]: value }))
    setErrors((current) => ({ ...current, [field]: '' }))
  }

  useEffect(() => {
    tripsAPI.list().then(setSavedTrips).catch((error) => setHistoryError(error.message))
  }, [])

  useEffect(() => {
    const sharedTripId = new URLSearchParams(window.location.search).get('trip')
    if (!sharedTripId) return
    setIsSharedView(true)
    tripsAPI.get(sharedTripId).then((sharedTrip) => {
      if (!sharedTrip.itinerary) throw new Error('This trip does not have a saved itinerary to share yet.')
      setTripId(sharedTrip.id)
      setTrip({ ...sharedTrip, budget: String(sharedTrip.budget) })
      setResult(sharedTrip.itinerary)
    }).catch((error) => setHistoryError(error.message))
  }, [])

  async function refreshTrips() {
    try {
      setSavedTrips(await tripsAPI.list())
      setHistoryError('')
    } catch (error) {
      setHistoryError(error.message)
    }
  }

  async function openSavedTrip(savedTrip) {
    setTripId(savedTrip.id)
    setTrip({ ...savedTrip, budget: String(savedTrip.budget) })
    setRecommendations(null)
    setApiError('')
    try {
      const itinerary = savedTrip.itinerary || await tripsAPI.generateItinerary(savedTrip.id)
      setResult(itinerary)
    } catch (error) {
      setApiError(error.message)
    }
  }

  async function renameSavedTrip(savedTrip) {
    const destination = window.prompt('Update trip destination:', savedTrip.destination)
    if (!destination || destination.trim() === savedTrip.destination) return
    try {
      await tripsAPI.update(savedTrip.id, { destination: destination.trim() })
      await refreshTrips()
    } catch (error) {
      setHistoryError(error.message)
    }
  }

  async function deleteSavedTrip(savedTrip) {
    if (!window.confirm(`Delete your trip to ${savedTrip.destination}? This also deletes its saved itinerary.`)) return
    try {
      await tripsAPI.remove(savedTrip.id)
      await refreshTrips()
      if (tripId === savedTrip.id) {
        setTripId(null)
        setResult(null)
        setRecommendations(null)
      }
    } catch (error) {
      setHistoryError(error.message)
    }
  }

  function toggleInterest(interest) {
    const selected = trip.interests.includes(interest)
    if (!selected && trip.interests.length >= 10) return
    update('interests', selected
      ? trip.interests.filter((item) => item !== interest)
      : [...trip.interests, interest])
  }

  function validateStep() {
    const nextErrors = {}
    if (step === 0 && trip.destination.trim().length < 2) nextErrors.destination = 'Add a destination with at least 2 characters.'
    if (step === 1) {
      if (!trip.start_date) nextErrors.start_date = 'Choose your first day.'
      if (!trip.end_date) nextErrors.end_date = 'Choose your last day.'
      if (trip.start_date && trip.end_date && trip.end_date < trip.start_date) nextErrors.end_date = 'The last day must be after the first day.'
      if (trip.start_date && trip.end_date && (new Date(`${trip.end_date}T00:00:00`) - new Date(`${trip.start_date}T00:00:00`)) / 86400000 > 30) nextErrors.end_date = 'Trips can be up to 31 days in this version.'
      if (!trip.budget || Number(trip.budget) <= 0) nextErrors.budget = 'Enter a budget greater than zero.'
      if (!Number.isInteger(Number(trip.travelers)) || Number(trip.travelers) < 1 || Number(trip.travelers) > 20) nextErrors.travelers = 'Choose 1 to 20 travelers.'
    }
    setErrors(nextErrors)
    return Object.keys(nextErrors).length === 0
  }

  async function submitTrip() {
    if (!validateStep()) return
    setLoading(true)
    setApiError('')
    try {
      const created = await tripsAPI.create({ ...trip, budget: Number(trip.budget), travelers: Number(trip.travelers) })
      setTripId(created.id)
      await refreshTrips()
      const suggested = await tripsAPI.recommend(created.id)
      setRecommendations(suggested)
      const itinerary = await tripsAPI.generateItinerary(created.id)
      setResult(itinerary)
      await refreshTrips()
    } catch (error) {
      setApiError(`${error.message} Is the FastAPI server running?`)
    } finally {
      setLoading(false)
    }
  }

  async function submitRefinement(event) {
    event.preventDefault()
    if (!refinement.trim() || !tripId || !result) return
    setRefining(true)
    setRefineMessage('')
    try {
      const updated = await tripsAPI.refineItinerary(tripId, result, refinement.trim(), refineDay ? Number(refineDay) : null)
      setResult(updated.itinerary)
      setRefineMessage(`${updated.assistant_message} (${updated.source === 'ai' ? 'AI updated' : 'saved as a note'})`)
      setRefinement('')
    } catch (error) {
      setRefineMessage(error.message)
    } finally {
      setRefining(false)
    }
  }

  async function copyShareLink() {
    const shareUrl = new URL(window.location.href)
    shareUrl.search = `?trip=${tripId}`
    try {
      await navigator.clipboard.writeText(shareUrl.toString())
      setShareMessage('Share link copied. Anyone with this link can view the trip.')
    } catch {
      setShareMessage(shareUrl.toString())
    }
  }

  function exportMarkdown() {
    const slug = result.destination.toLowerCase().replace(/[^a-z0-9]+/g, '-')
    downloadFile(`${slug}-itinerary.md`, itineraryMarkdown(trip, result), 'text/markdown;charset=utf-8')
  }

  function exportJson() {
    const exportedTrip = { ...trip }
    delete exportedTrip.id
    delete exportedTrip.status
    delete exportedTrip.itinerary
    downloadFile(
      `${result.destination.toLowerCase().replace(/[^a-z0-9]+/g, '-')}-itinerary.json`,
      JSON.stringify({ trip: exportedTrip, itinerary: result }, null, 2),
      'application/json;charset=utf-8',
    )
  }

  const progress = ((step + 1) / steps.length) * 100

  return (
    <main className="page-shell">
      <header className="topbar">
        <a className="brand" href="#home" aria-label="Wanderwise home"><span className="brand-mark"><Compass size={20} /></span> wanderwise<span className="brand-period">.</span></a>
        <span className="topbar-note">A little more you in every journey</span>
        <div className="topbar-tag"><span /> YOUR TRIP STUDIO</div>
      </header>

      <div className="main-layout" id="home">
        <section className="form-column">
          {!isSharedView && <section className="saved-trips">
            <div className="saved-trips-heading"><div><span className="small-label">YOUR TRAVEL HISTORY</span><h2>Saved trips <span>{savedTrips.length}</span></h2></div><button className="text-button" type="button" onClick={refreshTrips}>Refresh</button></div>
            {historyError && <p className="history-error">{historyError}</p>}
            {savedTrips.length === 0 && !historyError && <p className="history-empty">Your saved trips will show up here.</p>}
            {savedTrips.slice(0, 4).map((savedTrip) => <article className="saved-trip-row" key={savedTrip.id}><button type="button" className="saved-trip-open" onClick={() => openSavedTrip(savedTrip)}><span><b>{savedTrip.destination}</b><small>{savedTrip.start_date} — {savedTrip.end_date}{savedTrip.itinerary ? ' · itinerary saved' : ''}</small></span><ArrowRight size={15} /></button><button type="button" className="text-button" onClick={() => renameSavedTrip(savedTrip)} aria-label={`Edit ${savedTrip.destination}`}>Edit</button><button type="button" className="text-button delete-trip" onClick={() => deleteSavedTrip(savedTrip)} aria-label={`Delete ${savedTrip.destination}`}>Delete</button></article>)}
          </section>}
          {!result ? (
            <>
              <div className="eyebrow"><span className="eyebrow-line" /> THE ART OF GOING YOUR OWN WAY</div>
              <h1>Travel should<br />feel like <em>you.</em></h1>
              <p className="intro">Tell us what makes a trip yours. We’ll help you turn it into a plan worth looking forward to.</p>

              <div className="form-card">
                <div className="step-meta"><span>LET’S PLAN YOUR TRIP</span><span>STEP 0{step + 1} <i>/ 03</i></span></div>
                <div className="progress-track"><motion.div className="progress-fill" animate={{ width: `${progress}%` }} transition={{ duration: 0.35 }} /></div>
                <div className="step-labels">{steps.map((label, index) => <span key={label} className={index <= step ? 'active' : ''}>{label}</span>)}</div>

                <AnimatePresence mode="wait">
                  <motion.div key={step} className="step-content" initial={{ opacity: 0, y: 9 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -7 }} transition={{ duration: 0.2 }}>
                    {step === 0 && <>
                      <label className="field-label" htmlFor="destination">Where are you headed?</label>
                      <p className="field-help">Pick a place that’s been on your mind.</p>
                      <div className={`input-wrap ${errors.destination ? 'has-error' : ''}`}><MapPin size={18} /><input id="destination" autoFocus placeholder="e.g. Kyoto, Japan" value={trip.destination} onChange={(event) => update('destination', event.target.value)} onKeyDown={(event) => event.key === 'Enter' && validateStep() && setStep(1)} /></div>
                      {errors.destination && <p className="error-text">{errors.destination}</p>}
                      <div className="suggestion-row"><span>POPULAR RIGHT NOW</span>{['Lisbon', 'Marrakech', 'Bali'].map((place) => <button type="button" key={place} className="suggestion" onClick={() => update('destination', place)}>{place}</button>)}</div>
                    </>}

                    {step === 1 && <>
                      <label className="field-label">When are you going?</label><p className="field-help">Pick your dates and what you’d like to spend.</p>
                      <div className="two-fields">
                        <div><label className="small-label" htmlFor="start_date">FROM</label><div className={`input-wrap ${errors.start_date ? 'has-error' : ''}`}><CalendarDays size={17} /><input id="start_date" type="date" value={trip.start_date} onChange={(event) => update('start_date', event.target.value)} /></div>{errors.start_date && <p className="error-text">{errors.start_date}</p>}</div>
                        <div><label className="small-label" htmlFor="end_date">TO</label><div className={`input-wrap ${errors.end_date ? 'has-error' : ''}`}><CalendarDays size={17} /><input id="end_date" type="date" min={trip.start_date || undefined} value={trip.end_date} onChange={(event) => update('end_date', event.target.value)} /></div>{errors.end_date && <p className="error-text">{errors.end_date}</p>}</div>
                      </div>
                      <div className="two-fields second-row">
                        <div><label className="small-label" htmlFor="budget">TOTAL BUDGET</label><div className={`input-wrap ${errors.budget ? 'has-error' : ''}`}><Wallet size={17} /><span className="currency">$</span><input id="budget" type="number" min="1" placeholder="2,500" value={trip.budget} onChange={(event) => update('budget', event.target.value)} /></div>{errors.budget && <p className="error-text">{errors.budget}</p>}</div>
                        <div><label className="small-label" htmlFor="travelers">TRAVELERS</label><div className={`input-wrap ${errors.travelers ? 'has-error' : ''}`}><Users size={17} /><input id="travelers" type="number" min="1" max="20" value={trip.travelers} onChange={(event) => update('travelers', event.target.value)} /></div>{errors.travelers && <p className="error-text">{errors.travelers}</p>}</div>
                      </div>
                      <label className="small-label dietary-label" htmlFor="dietary">DIETARY NEEDS <span>OPTIONAL · SEPARATE WITH COMMAS</span></label>
                      <input className="plain-input" id="dietary" placeholder="e.g. vegetarian, gluten-free" value={trip.dietary_needs.join(', ')} onChange={(event) => update('dietary_needs', event.target.value.split(',').map((item) => item.trim()).filter(Boolean).slice(0, 10))} />
                      <label className="small-label dietary-label" htmlFor="mobility">MOBILITY NEEDS <span>OPTIONAL · SEPARATE WITH COMMAS</span></label>
                      <input className="plain-input" id="mobility" placeholder="e.g. step-free routes, wheelchair access" value={trip.mobility_needs.join(', ')} onChange={(event) => update('mobility_needs', event.target.value.split(',').map((item) => item.trim()).filter(Boolean).slice(0, 10))} />
                    </>}

                    {step === 2 && <>
                      <label className="field-label">What do you love doing?</label><p className="field-help">Choose a few things that make a trip memorable.</p>
                      <div className="interest-grid">{interestOptions.map((interest) => <button type="button" key={interest} className={`interest-chip ${trip.interests.includes(interest) ? 'selected' : ''}`} onClick={() => toggleInterest(interest)}>{trip.interests.includes(interest) && <Check size={14} />}{interest}</button>)}</div>
                      <label className="field-label pace-heading">What’s your travel pace?</label>
                      <div className="pace-options">{paceOptions.map((option) => <button type="button" key={option.value} className={`pace-option ${trip.travel_pace === option.value ? 'selected' : ''}`} onClick={() => update('travel_pace', option.value)}><span className="radio-dot" /><span><b>{option.label}</b><small>{option.note}</small></span></button>)}</div>
                      <label className="small-label style-label" htmlFor="travel_style">TRAVEL STYLE</label>
                      <select className="plain-input" id="travel_style" value={trip.travel_style} onChange={(event) => update('travel_style', event.target.value)}><option value="budget">Budget friendly</option><option value="comfort">Comfortable</option><option value="luxury">A little luxury</option></select>
                    </>}
                  </motion.div>
                </AnimatePresence>

                {apiError && <p className="api-error" role="alert">{apiError}</p>}
                <div className="form-actions">
                  {step > 0 ? <button className="back-button" type="button" onClick={() => { setErrors({}); setStep(step - 1) }}><ArrowLeft size={16} /> Back</button> : <span className="secure-note"><Sparkles size={14} /> MADE AROUND YOU</span>}
                  {step < 2 ? <button className="primary-button" type="button" onClick={() => validateStep() && setStep(step + 1)}>Continue <ArrowRight size={16} /></button> : <button className="primary-button" type="button" disabled={loading} onClick={submitTrip}>{loading ? 'Building your plan…' : 'Create my itinerary'} <Sparkles size={16} /></button>}
                </div>
              </div>
              <p className="privacy-note"><span className="tiny-lock">✳</span> Your details stay yours. We only use them to shape your trip.</p>
            </>
          ) : (
            <motion.section className="result-panel" initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }}>
              <div className="eyebrow"><span className="eyebrow-line" /> YOUR NEXT CHAPTER</div>
              <h1>Your trip,<br /><em>taking shape.</em></h1>
              <p className="intro">A first draft for {result.destination}, made around what you love. Your trip has {result.days.length} {result.days.length === 1 ? 'day' : 'days'} planned.</p>
              <p className="optimization-label"><span>✳</span> DAYS ORDERED BY TIME AND NEARBY AREA HINTS</p>
              <section className="share-export-card"><div><span className="small-label">TAKE YOUR PLAN WITH YOU</span><p>Share a view-only link or download a copy.</p></div><div className="share-export-actions"><button type="button" className="secondary-button" onClick={copyShareLink}><Share2 size={14} /> Share link</button><button type="button" className="secondary-button" onClick={exportMarkdown}><Download size={14} /> Markdown</button><button type="button" className="secondary-button" onClick={exportJson}><Download size={14} /> JSON</button></div>{shareMessage && <p className="share-message" role="status"><Copy size={12} />{shareMessage}</p>}</section>
              {recommendations && <section className="recommendations-section"><div className="recommendation-heading"><div><span className="small-label">CURATED FOR YOUR TRIP</span><h2>Ideas to make it yours</h2></div><span className={`source-badge ${recommendations.source}`}>{recommendations.source === 'ai' ? 'AI SUGGESTIONS' : 'STARTER IDEAS'}</span></div><div className="recommendation-grid">{recommendations.recommendations.map((item) => <article className="recommendation-card" key={`${item.category}-${item.name}`}><div className="recommendation-top"><span className="category-label">{item.category}</span><span className="cost-label">{item.estimated_cost} cost</span></div><h3>{item.name}</h3><p>{item.description}</p><p className="match-note">{item.why_it_matches}</p></article>)}</div><p className="recommendation-note">{recommendations.note}</p></section>}
              <div className="itinerary-list">{result.days.map((day) => <article className="day-card" key={day.day}><div className="day-number">DAY <b>{String(day.day).padStart(2, '0')}</b><small>{day.date}</small></div><div><h2>{day.title}</h2>{[['Morning', day.morning], ['Afternoon', day.afternoon], ['Evening', day.evening]].map(([slot, activities]) => activities.length > 0 && <div className="time-slot" key={slot}><b>{slot}</b><ul>{activities.map((activity) => <li key={activity}>{activity}</li>)}</ul></div>)}{day.notes.length > 0 && <p className="day-notes">{day.notes.join(' ')}</p>}</div></article>)}</div>
              <p className="result-note">{result.note}</p>
              {!isSharedView && <form className="refine-card" onSubmit={submitRefinement}>
                <label className="field-label" htmlFor="refine-request">Want to change something?</label>
                <p className="field-help">Ask for a different pace, more food stops, or a change to one day.</p>
                <textarea id="refine-request" maxLength={500} placeholder="e.g. Make day 2 more relaxed and add a museum" value={refinement} onChange={(event) => setRefinement(event.target.value)} />
                <div className="refine-actions"><label className="small-label" htmlFor="refine-day">APPLY TO</label><select id="refine-day" className="plain-input" value={refineDay} onChange={(event) => setRefineDay(event.target.value)}><option value="">Whole itinerary</option>{result.days.map((day) => <option key={day.day} value={day.day}>Day {day.day}</option>)}</select><button className="primary-button" type="submit" disabled={refining || !refinement.trim()}>{refining ? 'Updating…' : 'Refine plan'} <Sparkles size={15} /></button></div>
                {refineMessage && <p className="refine-message" role="status">{refineMessage}</p>}
              </form>}
              {!isSharedView && <button className="back-button plan-again" type="button" onClick={() => { setResult(null); setRecommendations(null); setTripId(null); setRefineMessage(''); setStep(0); setTrip(blankTrip) }}><ArrowLeft size={16} /> Plan another trip</button>}
            </motion.section>
          )}
        </section>

        <aside className="visual-column" aria-label="Travel inspiration">
          <div className="photo-card"><div className="photo-wash" /><div className="photo-sun" /><div className="photo-mountain back-mountain" /><div className="photo-mountain front-mountain" /><div className="photo-water" /><div className="photo-plant plant-one">✳</div><div className="photo-plant plant-two">✳</div>
            <div className="photo-caption"><span>THE WORLD IS YOURS TO WANDER</span><h2>Somewhere<br />new is calling.</h2><div className="caption-rule" /><p>Take the long way.<br />Find your kind of nowhere.</p></div>
            <div className="photo-index"><span>01</span><i /> 04</div>
          </div>
          <div className="quote-card"><span className="quote-mark">“</span><div><p>We travel not to escape life, but for life not to escape us.</p><span>— ROBIN YOUNG</span></div><div className="quote-spark">✳</div></div>
          <div className="side-footer"><span>36° 10′ 30″ N &nbsp; 115° 08′ 11″ W</span><span>MADE FOR THE MOMENTS IN BETWEEN</span></div>
        </aside>
      </div>
      <footer className="page-footer"><span>© 2026 WANDERWISE TRAVEL CO.</span><span>GO SOMEWHERE THAT MOVES YOU <i>✳</i></span><span>TAKE THE SCENIC ROUTE ↗</span></footer>
    </main>
  )
}

export default App

