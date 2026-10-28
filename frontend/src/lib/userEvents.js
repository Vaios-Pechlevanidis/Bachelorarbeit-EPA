// Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
// Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
// (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
// nach dem Annotationsprotokoll (Abschnitt 3.6.1)

import { fmtPeriod, isPeriod, periodFromIndex, periodIndex } from "./anomalySeries"

export const TITLE_MAX = 120
export const NOTE_MAX = 1000

export const USER_EVENT_NOTE =
  "Eigene Ereignisse sind von Nutzerinnen und Nutzern eingetragene Zeiträume zur Einordnung. Sie sind keine Aussage über Ursachen und gehen nicht in Erkennung, Rangfolge oder Belege ein; bei den Erklärungsansätzen stehen sie nur nach zeitlicher Nähe als möglicher Zusammenhang."

export const USER_EVENT_EXPLANATION_NOTE =
  "Eigene Ereignisse haben keine Quelle und keine Stufe; sie stehen hier, weil ihr Zeitraum das Ereignisfenster berührt. Möglicher Zusammenhang, keine Ursache."

export const EVENT_WINDOW_BEFORE = 3
export const EVENT_WINDOW_AFTER = 1

export function changeEventWindow(anomaly, before = EVENT_WINDOW_BEFORE, after = EVENT_WINDOW_AFTER) {
  if (!anomaly || !isPeriod(anomaly.date)) return null
  const transitionFrom = isPeriod(anomaly.previous_period) ? periodIndex(anomaly.previous_period) + 1 : periodIndex(anomaly.date)
  return { from: periodFromIndex(transitionFrom - before), to: periodFromIndex(periodIndex(anomaly.date) + after) }
}

export function eventWindowPhrase(event, window) {
  const f = periodIndex(event.date_from), t = periodIndex(event.date_to)
  const wf = periodIndex(window.from), wt = periodIndex(window.to)
  if (f < wf && t > wt) return "umfasst das Ereignisfenster"
  if (f < wf) return "beginnt vor dem Ereignisfenster"
  if (t > wt) return "reicht über das Ereignisfenster hinaus"
  return "im Ereignisfenster"
}

export function userEventsInWindow(events, window) {
  if (!Array.isArray(events) || !window || !isPeriod(window.from) || !isPeriod(window.to)) return []
  const wf = periodIndex(window.from), wt = periodIndex(window.to)
  return sortUserEvents(events.filter((e) => isPeriod(e.date_from) && isPeriod(e.date_to) && periodIndex(e.date_to) >= wf && periodIndex(e.date_from) <= wt))
    .map((e) => ({ ...e, time_phrase: eventWindowPhrase(e, window) }))
}

export function sortUserEvents(events) {
  return [...events].sort((a, b) =>
    periodIndex(a.date_from) - periodIndex(b.date_from)
    || periodIndex(a.date_to) - periodIndex(b.date_to)
    || (a.id ?? 0) - (b.id ?? 0))
}

export function eventSpanLabel(event) {
  if (!event) return ""
  return event.date_from === event.date_to ? fmtPeriod(event.date_from) : `${fmtPeriod(event.date_from)} – ${fmtPeriod(event.date_to)}`
}

export function eventMonths(event) {
  return periodIndex(event.date_to) - periodIndex(event.date_from) + 1
}

export function eventCoversPeriod(event, period) {
  const i = periodIndex(period)
  return periodIndex(event.date_from) <= i && i <= periodIndex(event.date_to)
}

export function validateUserEventInput({ title, from, to, note }) {
  const t = String(title ?? "").trim()
  if (!t) throw new Error("Bitte einen Titel angeben.")
  if (t.length > TITLE_MAX) throw new Error(`Der Titel darf höchstens ${TITLE_MAX} Zeichen haben.`)
  if (!isPeriod(from)) throw new Error("Bitte einen Startmonat wählen.")
  const end = to || from
  if (!isPeriod(end)) throw new Error("Bitte einen Endmonat wählen.")
  if (periodIndex(end) < periodIndex(from)) throw new Error("Der Endmonat darf nicht vor dem Startmonat liegen.")
  const n = String(note ?? "").trim()
  if (n.length > NOTE_MAX) throw new Error(`Der Vermerk darf höchstens ${NOTE_MAX} Zeichen haben.`)
  return { title: t, date_from: from, date_to: end, note: n || null }
}
