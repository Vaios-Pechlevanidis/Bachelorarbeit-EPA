// Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
// Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
// (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
// nach dem Annotationsprotokoll (Abschnitt 3.6.1)

export const SCORE_HINT =
  "Ø Score: Mittel der Gesamtnote aller Bewertungen von Mitarbeitenden im gewählten Zeitraum, ungewichtet. " +
  "Kununu berechnet seinen Score anders (laut Experteninterviews ohne Bewerbende und mit geringerem Gewicht " +
  "für ältere Bewertungen); der Wert kann deshalb von der Anzeige auf Kununu abweichen."

export const CATEGORY_MEAN_TITLE = "Kategorienmittel"
export const CATEGORY_MEAN_NOTE =
  "Mittel der einzelnen Kategorien (Sternebewertung je Kategorie, Mitarbeitende). Ihr Mittel kann von der " +
  "Gesamtnote abweichen: Die Gesamtnote ist eine eigene Angabe je Bewertung, und nicht jede Bewertung enthält " +
  "jede Kategorie."

export { CRITICAL_LABEL } from "./labels"
export const CRITICAL_NOTE = "niedrigstes Kategorienmittel, Mitarbeitende"

const fmtN = (n) => (n == null ? "–" : Number(n).toLocaleString("de-DE"))

export function scoreUncertaintyText(ci) {
  if (ci == null || !Number.isFinite(Number(ci))) return ""
  return `95-%-Intervall ±${Number(ci).toFixed(2).replace(".", ",")}`
}

export const UNCERTAINTY_NOTE =
  "Die Intervalle (95 %) sind aus den Bewertungen gerechnet (t-Verteilung bzw. Welch für Differenzen) und setzen " +
  "unabhängige Bewertungen voraus; Mehrfachbewertungen derselben Person sind in den Daten nicht erkennbar. " +
  "Kununu-Bewertungen sind freiwillig und selektiv; die Intervalle beschreiben die Streuung im Datensatz, keine Repräsentativität."

export function scoreCountText(n) {
  return n == null ? "Mitarbeitende" : `n = ${fmtN(n)} ${n === 1 ? "Bewertung" : "Bewertungen"} mit Gesamtnote, Mitarbeitende`
}

const fmtMonth = (p) => {
  if (!p) return "–"
  const [y, m] = String(p).split("-")
  return m && y ? `${m}/${y}` : "–"
}

export function scoreTrendWindowsText(trend) {
  if (!trend?.current || !trend?.previous) return "keine datierten Bewertungen mit Gesamtnote"
  return `${fmtMonth(trend.current.from)} – ${fmtMonth(trend.current.to)} (n = ${fmtN(trend.current.n)}) vs. ` +
    `${fmtMonth(trend.previous.from)} – ${fmtMonth(trend.previous.to)} (n = ${fmtN(trend.previous.n)})`
}
