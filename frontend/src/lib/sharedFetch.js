// Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
// Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
// (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
// nach dem Annotationsprotokoll (Abschnitt 3.6.1)

export const SHARED_TTL = 30 * 1000

const entries = new Map()

export function fetchJsonShared(url) {
  const hit = entries.get(url)
  if (!hit || (hit.done && Date.now() - hit.at >= SHARED_TTL)) {
    const entry = { at: Date.now(), done: false, promise: null }
    entry.promise = fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error(`API Error: ${res.status}`)
        return res.json()
      })
      .then(
        (json) => {
          entry.done = true
          entry.at = Date.now()
          return json
        },
        (error) => {
          if (entries.get(url) === entry) entries.delete(url)
          throw error
        },
      )
    entries.set(url, entry)
  }
  return entries.get(url).promise.then((json) => structuredClone(json))
}

export function invalidateSharedFetches() {
  entries.clear()
}
