// Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
// Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
// (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
// nach dem Annotationsprotokoll (Abschnitt 3.6.1)

import { periodIndex } from "./anomalySeries"
import { MIN_REVIEWS_PER_MONTH, MIN_REVIEWS_PER_WINDOW } from "./dataBasis"
import { dataQualityNotes, fmtN } from "./dataStatusText"
import { CRITICAL_LABEL } from "./labels"

export const COMPARE_RULES = {
  tieSpread: 0.1,
  sharedWeakness: 3.0,
  maxGaps: 3,
  countRatio: 5,
  goodRating: 3.5,
  weakRating: 2.5,
  maxSteps: 3,
}

const num = (v, digits = 2) =>
  v == null || !Number.isFinite(Number(v)) ? "–" : Number(v).toFixed(digits).replace(".", ",")

const signed = (v, digits = 2) =>
  v == null || !Number.isFinite(Number(v)) ? "–" : `${v > 0 ? "+" : v < 0 ? "-" : "±"}${num(Math.abs(v), digits)}`

const finite = (v) => v != null && Number.isFinite(Number(v))
const trendDelta = (trend) => (trend?.avgDelta != null ? parseFloat(trend.avgDelta) : NaN)
const smallBasis = (n, context = "") =>
  n != null && n < MIN_REVIEWS_PER_WINDOW ? `kleine Basis (${fmtN(n)} Bewertungen${context ? ` ${context}` : ""}, unter ${MIN_REVIEWS_PER_WINDOW})` : null

export function categoryRows(companies, categories) {
  return (categories ?? []).map(({ key, label }) => {
    const values = companies.map((c) => (finite(c.categoryRatings?.[key]) ? Number(c.categoryRatings[key]) : null))
    const counts = companies.map((c) => c.categoryCounts?.[key] ?? null)
    const valid = values.filter((v) => v != null)
    const max = valid.length ? Math.max(...valid) : null
    const min = valid.length ? Math.min(...valid) : null
    return { key, label, values, counts, max, min, spread: valid.length >= 2 ? max - min : null }
  })
}

export function bestCategory(rows, index) {
  let best = null
  for (const r of rows) {
    const v = r.values[index]
    if (v != null && (best == null || v > best.value)) best = { label: r.label, value: v, n: r.counts[index] }
  }
  return best
}

export function biggestGaps(rows, rules = COMPARE_RULES) {
  return rows.filter((r) => r.spread > 0).sort((a, b) => b.spread - a.spread).slice(0, rules.maxGaps)
}

export function sharedWeaknesses(rows, rules = COMPARE_RULES) {
  return rows.filter((r) => r.values.length > 0 && r.values.every((v) => v != null && v < rules.sharedWeakness))
}

export function scoreRanking(companies, rules = COMPARE_RULES) {
  const scored = companies.filter((c) => finite(c.score)).map((c) => ({ ...c, score: Number(c.score) }))
  if (scored.length < 2) return { state: "missing", text: "Ø Score nicht für mindestens zwei Firmen vorhanden; keine Rangfolge." }
  const sorted = [...scored].sort((a, b) => b.score - a.score)
  const top = sorted[0]
  const low = sorted[sorted.length - 1]
  const spread = top.score - low.score
  const tied = sorted.filter((c) => c.score === top.score).length >= 2 && spread <= rules.tieSpread
  return {
    state: tied ? "tied" : "ok",
    top,
    low,
    spread,
    text: tied
      ? `Mehrere Firmen gleichauf beim Ø Score (${num(top.score)}); Spanne ${num(spread)} Sterne.`
      : `Höchster Ø Score: ${top.name} (${num(top.score)}), niedrigster: ${low.name} (${num(low.score)}); Spanne ${num(spread)} Sterne.`,
  }
}

export function trendSentence(companies) {
  const months = companies.find((c) => c.trend?.windowMonths)?.trend.windowMonths
  const parts = companies.map((c) => {
    const tv = trendDelta(c.trend)
    if (!Number.isFinite(tv)) return `${c.name} –`
    const word = c.trend.sign === "up" ? "steigend" : c.trend.sign === "down" ? "sinkend" : "stabil"
    return `${c.name} ${signed(tv)} (${word})`
  })
  return `Trend der Gesamtnote${months ? ` (${months} volle Monate gegen die ${months} davor)` : ""}: ${parts.join(" · ")}.`
}

export function compareCells(companies, rules = COMPARE_RULES) {
  return companies.map((c) => {
    const score = finite(c.score) ? Number(c.score) : NaN
    return {
      label: c.name,
      value: Number.isFinite(score) ? num(score) : "–",
      sub: c.scoreN != null
        ? `von 5 · n = ${fmtN(c.scoreN)}${c.scoreCi95 != null ? ` · ±${num(c.scoreCi95)} (95 %)` : ""}`
        : "von 5 · Gesamtnote, Mitarbeitende",
      tone: !Number.isFinite(score) ? "neutral" : score >= rules.goodRating ? "good" : score >= rules.weakRating ? "warn" : "bad",
    }
  })
}

function trendItem(company) {
  const trend = company.trend
  if (trend?.sign !== "up" && trend?.sign !== "down") return null
  const tv = trendDelta(trend)
  const months = trend.windowMonths
  const nMin = Math.min(trend.nReviews?.current ?? Infinity, trend.nReviews?.previous ?? Infinity)
  const ci = trend.raw?.difference_ci95
  const warnings = []
  if (Number.isFinite(nMin)) {
    const small = smallBasis(nMin, "in einem Fenster")
    if (small) warnings.push(small)
  }
  if (ci != null && Number.isFinite(tv) && Math.abs(tv) <= ci) warnings.push("statistisch nicht von 0 unterscheidbar (95 %)")
  return {
    title: `${company.name}: Gesamtnote ${trend.sign === "up" ? "steigt" : "sinkt"}`,
    detail: `${signed(tv)} Sterne${ci != null ? ` (±${num(ci)}, 95 %)` : ""}${months ? `, ${months} volle Monate gegenüber den ${months} Monaten davor` : ""}`,
    warning: warnings[0] ?? null,
    basis: "stars",
    up: trend.sign === "up",
  }
}

export function compareColumns(companies, rows, rules = COMPARE_RULES) {
  const strengths = []
  const issues = []
  const shared = sharedWeaknesses(rows, rules)
  if (shared.length) {
    issues.push({
      title: `${shared.length === 1 ? "Gemeinsame Schwäche" : `${shared.length} gemeinsame Schwächen`} (alle unter ${num(rules.sharedWeakness, 1)})`,
      detail: shared.map((r) => `${r.label}: ${companies.map((c, i) => `${c.name} ${num(r.values[i])}`).join(" · ")}`).join("; "),
      warning: null,
      basis: "stars",
    })
  }
  companies.forEach((c, i) => {
    const best = bestCategory(rows, i)
    if (best) {
      strengths.push({
        title: `${c.name}: ${best.label}`,
        detail: `Ø ${num(best.value)} von 5, höchstes Kategorienmittel der Firma${best.n != null ? `, n = ${fmtN(best.n)}` : ""}`,
        warning: smallBasis(best.n),
        basis: "stars",
      })
    }
    const mc = c.mostCritical
    if (mc?.topicName && finite(mc.score)) {
      issues.push({
        title: `${c.name}: ${mc.topicName}`,
        detail: `Ø ${num(mc.score)} von 5, ${CRITICAL_LABEL} (niedrigstes Kategorienmittel der Firma)${mc.n != null ? `, n = ${fmtN(mc.n)}` : ""}`,
        warning: smallBasis(mc.n),
        basis: "stars",
      })
    }
  })
  companies.forEach((c) => {
    const item = trendItem(c)
    if (!item) return
    const { up, ...rest } = item
    if (up) strengths.push(rest)
    else issues.push(rest)
  })
  return { strengths, issues }
}

export function compareWarnings(companies, rows, rules = COMPARE_RULES) {
  const out = []
  companies.forEach((c, i) => {
    dataQualityNotes(c.dataStatus).forEach((t) => out.push(`${c.name}, ${t}.`))
    if (!finite(c.score)) out.push(`${c.name}: kein Ø Score (keine Bewertungen mit Gesamtnote).`)
    else if (c.scoreN != null && c.scoreN < MIN_REVIEWS_PER_WINDOW) {
      out.push(`${c.name}: kleine Basis beim Ø Score (${fmtN(c.scoreN)} Bewertungen mit Gesamtnote, unter ${MIN_REVIEWS_PER_WINDOW}).`)
    }
    const trend = c.trend
    const nMin = Math.min(trend?.nReviews?.current ?? Infinity, trend?.nReviews?.previous ?? Infinity)
    if (Number.isFinite(nMin) && nMin < MIN_REVIEWS_PER_WINDOW) {
      out.push(`${c.name}: Trend mit kleiner Basis (${fmtN(nMin)} Bewertungen in einem Fenster, unter ${MIN_REVIEWS_PER_WINDOW}).`)
    }
    const tv = trendDelta(trend)
    const ci = trend?.raw?.difference_ci95
    if (trend?.sign && trend.sign !== "flat" && ci != null && Number.isFinite(tv) && Math.abs(tv) <= ci) {
      out.push(`${c.name}: Die Trend-Differenz ${signed(tv)} liegt innerhalb ihres 95-%-Intervalls (±${num(ci)}); sie ist statistisch nicht von 0 unterscheidbar.`)
    }
    const missing = rows.filter((r) => r.values[i] == null).length
    if (rows.length && missing) out.push(`${c.name}: keine Werte in ${missing} von ${rows.length} Kategorien.`)
    if (!(c.timeline ?? []).some((p) => !p.is_forecast && finite(p.score))) {
      out.push(`${c.name}: keine datierten Bewertungen im Bewertungsverlauf (letzte fünf Jahre).`)
    }
  })

  const counted = companies.filter((c) => c.scoreN > 0)
  if (counted.length >= 2) {
    const most = counted.reduce((a, b) => (b.scoreN > a.scoreN ? b : a))
    const least = counted.reduce((a, b) => (b.scoreN < a.scoreN ? b : a))
    if (most.scoreN / least.scoreN >= rules.countRatio) {
      out.push(`Sehr unterschiedliche Basis: ${most.name} ${fmtN(most.scoreN)} gegenüber ${least.name} ${fmtN(least.scoreN)} Bewertungen mit Gesamtnote; das Mittel der kleineren Firma schwankt stärker.`)
    }
  }

  const ranked = companies.filter((c) => finite(c.score) && finite(c.scoreCi95)).sort((a, b) => b.score - a.score)
  if (ranked.length >= 2) {
    const [a, b] = ranked
    if (a.score - b.score <= a.scoreCi95 + b.scoreCi95) {
      out.push(`Ø Score: ${a.name} und ${b.name} liegen ${num(a.score - b.score)} Sterne auseinander, ihre 95-%-Intervalle (±${num(a.scoreCi95)} / ±${num(b.scoreCi95)}) überschneiden sich; die Reihenfolge ist im Datensatz nicht gesichert.`)
    }
  }
  return out
}

export function compareNextSteps(companies, rows, rules = COMPARE_RULES) {
  const out = []
  const gap = biggestGaps(rows, rules)[0]
  if (gap) {
    const hi = companies[gap.values.indexOf(gap.max)]
    const lo = companies[gap.values.indexOf(gap.min)]
    out.push(`Kategorie ${gap.label} (Spanne ${num(gap.spread)}): Verlauf der Kategorie und Freitexte von ${hi.name} und ${lo.name} in den Einzelanalysen vergleichen; prüfen, ob der Abstand über die Jahre besteht.`)
  }
  const shared = sharedWeaknesses(rows, rules)[0]
  if (shared) {
    out.push(`Gemeinsame Schwäche ${shared.label}: weitere Firmen derselben Branche hinzunehmen, um zu prüfen, ob der niedrige Wert branchentypisch ist.`)
  }
  const ups = companies.filter((c) => c.trend?.sign === "up").map((c) => c.name)
  const downs = companies.filter((c) => c.trend?.sign === "down").map((c) => c.name)
  if (ups.length && downs.length) {
    out.push(`Gegenläufige Trends (${ups.join(", ")} steigend, ${downs.join(", ")} sinkend): Monatsverlauf im selben Zeitfenster vergleichen und prüfen, ob einzelne Monate mit kleiner Basis den Trend tragen.`)
  } else if (downs.length) {
    out.push(`Sinkende Gesamtnote bei ${downs.join(", ")}: in der Einzelanalyse prüfen, ob der Rückgang von einzelnen Monaten mit kleiner Basis oder von einer Statusgruppe getragen wird (Zeitverlauf, Anomalien).`)
  }
  return out.slice(0, rules.maxSteps)
}

export function timelineStats(timeline, minReviews = MIN_REVIEWS_PER_MONTH) {
  const pts = (timeline ?? [])
    .filter((p) => p?.date && !p.is_forecast && finite(p.score))
    .sort((a, b) => periodIndex(a.date) - periodIndex(b.date))
  if (!pts.length) return null
  const scores = pts.map((p) => Number(p.score))
  const low = pts.reduce((a, b) => (Number(b.score) < Number(a.score) ? b : a))
  const high = pts.reduce((a, b) => (Number(b.score) > Number(a.score) ? b : a))
  const first = pts[0].date
  const last = pts[pts.length - 1].date
  const spanMonths = periodIndex(last) - periodIndex(first) + 1
  return {
    months: pts.length,
    spanMonths,
    gaps: spanMonths - pts.length,
    first,
    last,
    mean: scores.reduce((s, v) => s + v, 0) / scores.length,
    low,
    high,
    thin: pts.filter((p) => p.count != null && p.count < minReviews).length,
    minReviews,
  }
}

export function compareLimitLines() {
  return [
    "Der Vergleich stellt Mittel nebeneinander; ob die Firmen vergleichbar sind (Größe, Standorte, Anteil der Bewertungen an den Beschäftigten), zeigt er nicht. Die Branche laut Kununu-Profil ist ein Hinweis, kein Nachweis.",
    "Kununu-Bewertungen sind freiwillig und selektiv; der Datensatz ist keine Stichprobe aller Beschäftigten und erlaubt keine Aussage über Repräsentativität.",
    "Unterschiede zwischen den Firmen sind nicht auf Signifikanz geprüft; nur Ø Score und Trend tragen ein 95-%-Intervall. Intervalle setzen unabhängige Bewertungen voraus; Mehrfachbewertungen derselben Person sind nicht erkennbar.",
    "Der Bericht beschreibt, wo sich die Bewertungen unterscheiden; er belegt keine Ursachen.",
  ]
}

export function compareRulesText(rules = COMPARE_RULES) {
  return (
    `Regeln dieses Berichts (wie die Zusammenfassung der Vergleichsseite, Setzungen): Die Rangfolge folgt dem Ø Score; gleichauf heißt, mehrere Firmen teilen den höchsten Wert und die Spanne beträgt höchstens ${num(rules.tieSpread, 1)} Sterne. ` +
    `Stärke je Firma ist das höchste, Schwäche das niedrigste Kategorienmittel (${CRITICAL_LABEL}); dazu kommt ein steigender bzw. sinkender Trend der Gesamtnote (Änderung über ±0,05 Sterne). Die Einträge sind relativ zur Firma, keine absolute Bewertung. ` +
    `Größte Unterschiede: die ${rules.maxGaps} Kategorien mit der größten Spanne (höchster minus niedrigster Wert der Firmen). Gemeinsame Schwäche: eine Kategorie, die bei allen Firmen unter ${num(rules.sharedWeakness, 1)} liegt. ` +
    `Warnungen bei weniger als ${MIN_REVIEWS_PER_WINDOW} Bewertungen, bei sich überschneidenden 95-%-Intervallen der beiden höchsten Ø Scores und wenn die Zahl der Bewertungen um den Faktor ${rules.countRatio} oder mehr auseinanderliegt. ` +
    `Die nächsten Schritte sind Vorschläge für Untersuchungsfragen, keine Maßnahmen. ` +
    `Der Bericht nennt, wo sich die Bewertungen unterscheiden, nicht warum: keine Aussage über Ursachen.`
  )
}

export function buildCompareReport({ companies = [], categories = [] }, rules = COMPARE_RULES) {
  const rows = categoryRows(companies, categories)
  return {
    rows,
    cells: compareCells(companies, rules),
    ranking: scoreRanking(companies, rules),
    trends: trendSentence(companies),
    gaps: biggestGaps(rows, rules),
    shared: sharedWeaknesses(rows, rules),
    ...compareColumns(companies, rows, rules),
    warnings: compareWarnings(companies, rows, rules),
    nextSteps: compareNextSteps(companies, rows, rules),
    limits: compareLimitLines(),
    rules: compareRulesText(rules),
  }
}
