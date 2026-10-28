// Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
// Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
// (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
// nach dem Annotationsprotokoll (Abschnitt 3.6.1)

export const TIME_RANGES = [
  { key: "all", label: "Gesamt", months: null },
  { key: "5y", label: "5 Jahre", months: 60 },
  { key: "3y", label: "3 Jahre", months: 36 },
  { key: "1y", label: "12 Monate", months: 12 },
]

export const DEFAULT_TIME_RANGE = "all"

export function isTimeRangeKey(key) {
  return TIME_RANGES.some((r) => r.key === key)
}

export function fmtPeriod(period) {
  const [y, m] = String(period).split("-").map(Number)
  return new Date(y, m - 1, 1).toLocaleDateString("de-DE", { month: "short", year: "numeric" })
}

export function periodIndex(period) {
  const [y, m] = String(period).split("-").map(Number)
  return y * 12 + (m - 1)
}

export function periodFromIndex(index) {
  const y = Math.floor(index / 12)
  const m = (index % 12) + 1
  return `${y}-${String(m).padStart(2, "0")}`
}

export function trimToEvaluated(series) {
  const list = series ?? []
  const isValue = (m) => m.evaluated && m.mean != null
  const first = list.findIndex(isValue)
  if (first < 0) return { series: list, hiddenBefore: null, hiddenAfter: null }
  let last = list.length - 1
  while (!isValue(list[last])) last--
  const edge = (a, b) => (b >= a ? { from: list[a].period, to: list[b].period, months: b - a + 1 } : null)
  return {
    series: list.slice(first, last + 1),
    hiddenBefore: edge(0, first - 1),
    hiddenAfter: edge(last + 1, list.length - 1),
  }
}

export function timeWindow(series, rangeKey) {
  const range = TIME_RANGES.find((r) => r.key === rangeKey)
  if (!range?.months || !series?.length) return null
  const first = periodIndex(series[0].period)
  const last = periodIndex(series[series.length - 1].period)
  const from = Math.max(first, last - range.months + 1)
  if (from <= first) return null
  return { from: periodFromIndex(from), to: periodFromIndex(last) }
}

export function inWindow(period, win) {
  if (!win) return true
  const i = periodIndex(period)
  return i >= periodIndex(win.from) && i <= periodIndex(win.to)
}

export const INTERP_KEYS = ["interpA", "interpB"]

export function interpolateGaps(series) {
  const out = series.map(() => ({ interpA: null, interpB: null, interpolated: false }))
  const isValue = (m) => m.evaluated && m.mean != null
  let gapNo = 0
  let i = 0
  while (i < series.length) {
    if (isValue(series[i])) { i++; continue }
    const start = i
    while (i < series.length && !isValue(series[i])) i++
    const before = start - 1
    const after = i
    if (before >= 0 && after < series.length) {
      const key = INTERP_KEYS[gapNo % 2]
      const a = series[before].mean
      const b = series[after].mean
      const span = after - before
      out[before][key] = a
      out[after][key] = b
      for (let j = start; j < after; j++) {
        out[j][key] = +(a + ((j - before) / span) * (b - a)).toFixed(3)
        out[j].interpolated = true
      }
      gapNo++
    }
  }
  return out
}

export function levelsFromAnomalies(anomalies) {
  const levels = {}
  const fill = (from, to, value) => {
    for (let i = periodIndex(from); i <= periodIndex(to); i++) levels[periodFromIndex(i)] = value
  }
  const sorted = [...(anomalies ?? [])]
    .filter((a) => a.before_from && a.after_to)
    .sort((a, b) => periodIndex(a.date) - periodIndex(b.date))
  for (const a of sorted) {
    fill(a.before_from, periodFromIndex(periodIndex(a.date) - 1), a.before_mean)
    fill(a.date, a.after_to, a.after_mean)
  }
  return levels
}

export const DEFAULT_WINDOW_MONTHS = 6

function lastDayOfMonth(period) {
  const [y, m] = String(period).split("-").map(Number)
  const day = new Date(Date.UTC(y, m, 0)).getUTCDate()
  return `${period}-${String(day).padStart(2, "0")}`
}

function windowSpan(fromIndex, toIndex) {
  const from = periodFromIndex(fromIndex)
  const to = periodFromIndex(toIndex)
  return { from, to, start: `${from}-01`, end: lastDayOfMonth(to), months: toIndex - fromIndex + 1 }
}

export function comparisonWindows(anomaly, windowMonths = DEFAULT_WINDOW_MONTHS) {
  if (!anomaly?.date) return null
  const date = periodIndex(anomaly.date)
  const beforeFrom = anomaly.before_from ? periodIndex(anomaly.before_from) : date - windowMonths
  const afterTo = anomaly.after_to ? periodIndex(anomaly.after_to) : date + windowMonths - 1
  return {
    windowMonths,
    before: windowSpan(Math.max(date - windowMonths, beforeFrom), date - 1),
    after: windowSpan(date, Math.min(date + windowMonths - 1, afterTo)),
  }
}

export function outlierCountText(n) {
  return n ? ` · ${n} ${n === 1 ? "auffälliger Einzelmonat" : "auffällige Einzelmonate"}` : ""
}

export function monthSpan(period) {
  return windowSpan(periodIndex(period), periodIndex(period))
}

export const MIN_BASELINE_MONTHS = 6

export function periodWindows(from, to, minBaseline = MIN_BASELINE_MONTHS) {
  if (!from || !to) return null
  const first = Math.min(periodIndex(from), periodIndex(to))
  const last = Math.max(periodIndex(from), periodIndex(to))
  const baseline = Math.max(last - first + 1, minBaseline)
  return { windowMonths: baseline, before: windowSpan(first - baseline, first - 1), after: windowSpan(first, last) }
}

export function isPeriod(value) {
  return typeof value === "string" && /^\d{4}-(0[1-9]|1[0-2])$/.test(value)
}

export function selectionLabel(selection) {
  if (!selection) return ""
  return selection.from === selection.to ? fmtPeriod(selection.from) : `${fmtPeriod(selection.from)} – ${fmtPeriod(selection.to)}`
}
