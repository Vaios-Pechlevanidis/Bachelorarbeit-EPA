// Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
// Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
// (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
// nach dem Annotationsprotokoll (Abschnitt 3.6.1)

const MONTHS = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]

export const fmtDe = (v, d = 2) => (v == null || !Number.isFinite(Number(v)) ? "–" : Number(v).toFixed(d).replace(".", ","))
export const fmtSigned = (v, d = 3) => (v == null ? "–" : `${Number(v) >= 0 ? "+" : "−"}${fmtDe(Math.abs(Number(v)), d)}`)

export const fmtMonthKey = (key) => {
  const [y, m] = String(key ?? "").split("-").map(Number)
  return y && m ? `${MONTHS[m - 1]} ${y}` : "–"
}
