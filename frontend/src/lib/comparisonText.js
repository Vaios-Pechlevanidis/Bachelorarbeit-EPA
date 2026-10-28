// Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
// Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
// (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
// nach dem Annotationsprotokoll (Abschnitt 3.6.1)

export function withoutTextText(stats) {
  const n = stats?.n_without_text
  if (n == null || !stats?.n_reviews) return null
  if (n === 0) return "alle mit Freitext"
  return n === stats.n_reviews ? "keine mit Freitext" : `${n} ohne Freitext`
}
