// Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
// Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
// (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
// nach dem Annotationsprotokoll (Abschnitt 3.6.1)

import { fmtPeriod } from "./anomalySeries"

export const fmtN = (n) => (n == null ? "–" : Number(n).toLocaleString("de-DE"))

export const fmtDay = (value) => {
  if (!value) return "–"
  const [y, m, d] = String(value).slice(0, 10).split("-")
  return d && m && y ? `${d}.${m}.${y}` : "–"
}

export const fmtStamp = (value) => {
  if (!value) return "–"
  const s = String(value)
  return s.length >= 16 ? `${fmtDay(s)} ${s.slice(11, 16)}` : fmtDay(s)
}

export function sourceLine(s) {
  if (!s || !s.n_reviews) return "keine Bewertungen"
  const span = s.first_review && s.last_review ? `${fmtDay(s.first_review)} – ${fmtDay(s.last_review)}` : "ohne Datum"
  const eligible = s.eligible
    ? `${s.evaluated_months} bewertete Monate, geeignet für die Erkennung`
    : `${s.evaluated_months} bewertete ${s.evaluated_months === 1 ? "Monat" : "Monate"}, keine automatische Erkennung`
  return `${fmtN(s.n_reviews)} ${s.n_reviews === 1 ? "Bewertung" : "Bewertungen"} · ${span} · ${eligible}${
    s.n_undated ? ` · ${s.n_undated} ohne Datum` : ""}${
    s.n_without_value ? ` · ${s.n_without_value} ohne Gesamtnote` : ""}${
    s.n_duplicates ? ` · ${s.n_duplicates} exakte ${s.n_duplicates === 1 ? "Duplikat" : "Duplikate"} (gezählt, nicht entfernt)` : ""}`
}

export function dataQualityNotes(data) {
  const out = []
  for (const [key, label] of [["employee", "Mitarbeitende"], ["candidates", "Bewerbende"]]) {
    const s = data?.sources?.[key]
    if (!s) continue
    if (s.n_duplicates) out.push(`${label}: ${s.n_duplicates} exakte ${s.n_duplicates === 1 ? "Duplikat" : "Duplikate"} (gleiches Datum, Titel, Gesamtnote, Status) im Datensatz, in allen Mitteln enthalten`)
    if (s.n_undated) out.push(`${label}: ${s.n_undated} ${s.n_undated === 1 ? "Bewertung" : "Bewertungen"} ohne Datum, nicht in Zeitreihen und Fenstern`)
    if (s.n_without_value) out.push(`${label}: ${s.n_without_value} ${s.n_without_value === 1 ? "Bewertung" : "Bewertungen"} ohne Gesamtnote, in keinem Mittel`)
  }
  return out
}

export function summaryText(data) {
  const emp = data?.sources?.employee
  const cand = data?.sources?.candidates
  const counts = [
    emp?.n_reviews ? `${fmtN(emp.n_reviews)} Mitarbeitende` : null,
    cand?.n_reviews ? `${fmtN(cand.n_reviews)} Bewerbende` : null,
  ].filter(Boolean)
  const last = [emp?.last_review, cand?.last_review].filter(Boolean).sort().pop()
  return [
    counts.length ? `Bewertungen: ${counts.join(", ")}` : "keine Bewertungen",
    last ? `bis ${fmtDay(last)}` : null,
  ].filter(Boolean).join(" · ")
}

export function lastImportText(data) {
  return data?.last_import?.value
    ? `${fmtStamp(data.last_import.value)} (Datenbank; Abrufdatum bei Kununu nicht gespeichert)`
    : "unbekannt"
}

export function platformText(platform) {
  return platform?.available
    ? `${fmtN(platform.review_count)} Bewertungen am ${fmtDay(platform.count_date)} · im Datensatz ${fmtN(platform.dataset_count)} (${Math.round((platform.coverage_share ?? 0) * 100)} %)`
    : platform?.note ?? "–"
}

export function marketText(market) {
  if (market === null) return "kein Ticker"
  if (!market) return "–"
  return market.available
    ? `${market.ticker}${market.ticker_scope && market.ticker_scope !== "eigene Aktie" ? ` (${market.ticker_scope})` : ""} · ${fmtPeriod(market.first_month)} – ${fmtPeriod(market.last_month)} · abgerufen ${fmtDay(market.fetched_at)}`
    : `${market.ticker}: kein Zwischenspeicher`
}

export function evidenceText(evidence) {
  if (evidence === null || !evidence?.months) return "kein gespeicherter Monat"
  return `${Object.values(evidence.sources ?? {}).map((s) => `${s.label} ${s.months} ${s.months === 1 ? "Monat" : "Monate"}`).join(", ")} · ${fmtPeriod(evidence.first_month)} – ${fmtPeriod(evidence.last_month)} · abgerufen ${fmtDay(evidence.fetched_at)}`
}

export function thresholdsNote(thresholds) {
  const t = thresholds ?? { min_reviews_per_month: 5, min_evaluated_months: 12 }
  return `bewertet = Monat mit mindestens ${t.min_reviews_per_month} Bewertungen, geeignet = mindestens ${t.min_evaluated_months} bewertete Monate`
}

export function timestampCell(t) {
  return t?.n ? `${fmtStamp(t.min)} – ${fmtStamp(t.max)} (${fmtN(t.n)})` : "leer"
}
