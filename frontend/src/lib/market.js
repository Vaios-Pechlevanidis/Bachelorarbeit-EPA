// Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
// Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
// (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
// nach dem Annotationsprotokoll (Abschnitt 3.6.1)

export function fmtPrice(v) {
  if (v == null) return "–"
  const digits = Math.abs(v) >= 1000 ? 0 : 2
  return Number(v).toLocaleString("de-DE", { minimumFractionDigits: digits, maximumFractionDigits: digits })
}

export function fmtPriceTick(v) {
  return v == null ? "" : Number(v).toLocaleString("de-DE", { maximumFractionDigits: 2 })
}

export const PRICE_PARAM = "kurs"
export const PRICE_OFF = "aus"
export const PRICE_ON = "an"

export function fmtAmount(v, unit) {
  if (v == null) return "–"
  const abs = Math.abs(v)
  const [div, suffix] = abs >= 1e12 ? [1e12, " Bio."] : abs >= 1e9 ? [1e9, " Mrd."] : abs >= 1e6 ? [1e6, " Mio."] : [1, ""]
  const num = (v / div).toLocaleString("de-DE", { maximumFractionDigits: div === 1 ? 0 : 1 })
  return `${num}${suffix}${unit ? ` ${unit}` : ""}`
}

export function fmtDay(day) {
  if (!day) return "–"
  const [y, m, d] = String(day).split("-")
  return `${d}.${m}.${y}`
}

export function fiscalYearLabel(end) {
  const [y, m] = String(end).split("-")
  return m === "12" ? `GJ ${y}` : `GJ bis ${m}/${y}`
}

export const MARKET_DISCLAIMER_LEAD = "Einordnung, keine Erklärung."
export const MARKET_DISCLAIMER_TEXT = "Der Kurs zeigt das Marktumfeld; ein Zusammenhang mit den Bewertungen wird nicht behauptet."

export const PARENT_SCOPE = "Konzernmutter"
export const GROUP_COMPANY_SCOPE = "Konzerngesellschaft"

export function noPriceText(reason) {
  if (!reason) return "Kein Aktienkurs."
  return reason.startsWith("Kein Aktienkurs") ? reason : `Kein Aktienkurs: ${reason}`
}

export const PRICE_RANGES = [
  { key: "1y", label: "1 J.", months: 12 },
  { key: "3y", label: "3 J.", months: 36 },
  { key: "5y", label: "5 J.", months: 60 },
  { key: "10y", label: "10 J.", months: 120 },
  { key: "max", label: "Max.", months: null },
]
export const DEFAULT_PRICE_RANGE = "5y"

export function isPriceRangeKey(key) {
  return PRICE_RANGES.some((r) => r.key === key)
}

export function pricesInRange(prices, rangeKey) {
  const range = PRICE_RANGES.find((r) => r.key === rangeKey)
  const list = prices ?? []
  return range?.months ? list.slice(-range.months) : list
}

export const RATING_LEVELS = [
  { key: "strong_buy", label: "Stark kaufen", color: "var(--rating-strong-buy)" },
  { key: "buy", label: "Kaufen", color: "var(--rating-buy)" },
  { key: "hold", label: "Halten", color: "var(--rating-hold)" },
  { key: "sell", label: "Verkaufen", color: "var(--rating-sell)" },
  { key: "strong_sell", label: "Stark verkaufen", color: "var(--rating-strong-sell)" },
]

export function fmtMonth(period) {
  const [y, m] = String(period).split("-").map(Number)
  return new Date(y, m - 1, 1).toLocaleDateString("de-DE", { month: "short", year: "numeric" })
}

export function quarterLabel(end) {
  const [y, m] = String(end).split("-").map(Number)
  return `Q${Math.ceil(m / 3)} ${y}`
}

export function fmtPercent(v) {
  if (v == null || !Number.isFinite(v)) return "–"
  const sign = v > 0 ? "+" : v < 0 ? "−" : ""
  return `${sign}${Math.abs(v).toLocaleString("de-DE", { minimumFractionDigits: 1, maximumFractionDigits: 1 })} %`
}
