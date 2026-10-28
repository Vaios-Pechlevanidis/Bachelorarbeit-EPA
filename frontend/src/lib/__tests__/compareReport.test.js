// Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
// Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
// (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
// nach dem Annotationsprotokoll (Abschnitt 3.6.1)

import { describe, expect, it } from "vitest"
import {
  bestCategory, biggestGaps, buildCompareReport, categoryRows, compareColumns, compareNextSteps, compareWarnings,
  scoreRanking, sharedWeaknesses, timelineStats, trendText,
} from "../compareReport"

const categories = [
  { key: "avg_gehalt", label: "Gehalt/Sozialleistungen" },
  { key: "avg_kollegen", label: "Kollegenzusammenhalt" },
  { key: "avg_image", label: "Image" },
]

const alpha = {
  name: "Alpha", score: 3.9, scoreN: 400, scoreCi95: 0.08,
  trend: { avgDelta: "0.20", sign: "up", windowMonths: 12, nReviews: { current: 80, previous: 70 }, raw: { difference_ci95: 0.15 } },
  mostCritical: { topicName: "Gehalt/Sozialleistungen", score: "2.80", n: 380 },
  categoryRatings: { avg_gehalt: 2.8, avg_kollegen: 4.3, avg_image: 3.6 },
  categoryCounts: { avg_gehalt: 380, avg_kollegen: 390, avg_image: 385 },
  timeline: [
    { date: "2024-01", score: 3.8, count: 12 },
    { date: "2024-03", score: 4.2, count: 3 },
    { date: "2024-02", score: 3.5, count: 9 },
  ],
}
const beta = {
  name: "Beta", score: 3.6, scoreN: 60, scoreCi95: 0.25,
  trend: { avgDelta: "-0.10", sign: "down", windowMonths: 12, nReviews: { current: 6, previous: 20 }, raw: { difference_ci95: 0.4 } },
  mostCritical: { topicName: "Gehalt/Sozialleistungen", score: "2.50", n: 8 },
  categoryRatings: { avg_gehalt: 2.5, avg_kollegen: 3.4, avg_image: null },
  categoryCounts: { avg_gehalt: 8, avg_kollegen: 55, avg_image: 0 },
  timeline: [],
}

describe("categoryRows", () => {
  it("richtet Werte und n je Firma aus und berechnet die Spanne nur bei mindestens zwei Werten", () => {
    const rows = categoryRows([alpha, beta], categories)
    expect(rows[0]).toMatchObject({ label: "Gehalt/Sozialleistungen", values: [2.8, 2.5], counts: [380, 8], max: 2.8, min: 2.5 })
    expect(rows[0].spread).toBeCloseTo(0.3)
    expect(rows[2].values).toEqual([3.6, null])
    expect(rows[2].spread).toBeNull()
  })
})

describe("Regeln der Zusammenfassung", () => {
  const rows = categoryRows([alpha, beta], categories)
  it("nennt die höchste Kategorie je Firma", () => {
    expect(bestCategory(rows, 0)).toEqual({ label: "Kollegenzusammenhalt", value: 4.3, n: 390 })
    expect(bestCategory(rows, 1).label).toBe("Kollegenzusammenhalt")
  })
  it("sortiert die größten Unterschiede nach Spanne und lässt Kategorien ohne Vergleich weg", () => {
    expect(biggestGaps(rows).map((r) => r.label)).toEqual(["Kollegenzusammenhalt", "Gehalt/Sozialleistungen"])
  })
  it("zählt eine Kategorie nur als gemeinsame Schwäche, wenn alle Firmen unter 3,0 liegen", () => {
    expect(sharedWeaknesses(rows).map((r) => r.label)).toEqual(["Gehalt/Sozialleistungen"])
  })
  it("erkennt Gleichstand nur bei gleichem Höchstwert und kleiner Spanne", () => {
    expect(scoreRanking([alpha, beta]).text).toBe("Höchster Ø Score: Alpha (3,90), niedrigster: Beta (3,60); Spanne 0,30 Sterne.")
    expect(scoreRanking([alpha, { ...beta, score: 3.9 }]).state).toBe("tied")
    expect(scoreRanking([alpha, { ...beta, score: null }]).state).toBe("missing")
  })
})

describe("compareColumns", () => {
  it("fasst gemeinsame Schwächen zusammen und ordnet Trends nach Richtung", () => {
    const rows = categoryRows([alpha, beta], categories)
    const { strengths, issues } = compareColumns([alpha, beta], rows)
    expect(strengths.map((s) => s.title)).toEqual(["Alpha: Kollegenzusammenhalt", "Beta: Kollegenzusammenhalt", "Alpha: Gesamtnote steigt"])
    expect(issues[0].title).toBe("Gemeinsame Schwäche (alle unter 3,0)")
    expect(issues[0].detail).toBe("Gehalt/Sozialleistungen: Alpha 2,80 · Beta 2,50")
    expect(issues.find((i) => i.title === "Beta: Gehalt/Sozialleistungen").warning).toBe("kleine Basis (8 Bewertungen, unter 10)")
    const down = issues.find((i) => i.title === "Beta: Gesamtnote sinkt")
    expect(down.warning).toBe("kleine Basis (6 Bewertungen in einem Fenster, unter 10) · statistisch nicht von 0 unterscheidbar (95 %)")
  })
})

describe("compareWarnings", () => {
  it("warnt bei kleiner Basis, fehlenden Werten, ungleicher Basis und überlappenden Intervallen", () => {
    const rows = categoryRows([alpha, beta], categories)
    const w = compareWarnings([alpha, beta], rows)
    expect(w).toContain("Beta: Trend mit kleiner Basis (6 Bewertungen in einem Fenster, unter 10).")
    expect(w).toContain("Beta: keine Werte in 1 von 3 Kategorien.")
    expect(w).toContain("Beta: keine datierten Bewertungen im Bewertungsverlauf (letzte fünf Jahre).")
    expect(w.some((t) => t.startsWith("Sehr unterschiedliche Basis: Alpha 400 gegenüber Beta 60"))).toBe(true)
    expect(w.some((t) => t.startsWith("Ø Score: Alpha und Beta liegen 0,30 Sterne auseinander"))).toBe(true)
  })
  it("schweigt bei getrennten Intervallen und ähnlicher Basis", () => {
    const b = { ...alpha, name: "Gamma", score: 3.2, scoreN: 300, scoreCi95: 0.1 }
    const w = compareWarnings([alpha, b], categoryRows([alpha, b], categories))
    expect(w.some((t) => t.startsWith("Ø Score:"))).toBe(false)
    expect(w.some((t) => t.startsWith("Sehr unterschiedliche Basis"))).toBe(false)
  })
})

describe("compareNextSteps", () => {
  it("schlägt höchstens drei Untersuchungsfragen vor", () => {
    const rows = categoryRows([alpha, beta], categories)
    const steps = compareNextSteps([alpha, beta], rows)
    expect(steps).toHaveLength(3)
    expect(steps[0]).toContain("Kategorie Kollegenzusammenhalt (Spanne 0,90)")
    expect(steps[1]).toContain("Gemeinsame Schwäche Gehalt/Sozialleistungen")
    expect(steps[2]).toContain("Gegenläufige Trends (Alpha steigend, Beta sinkend)")
  })
})

describe("timelineStats", () => {
  it("rechnet Monate, Lücken, Mittel und dünne Monate", () => {
    const s = timelineStats([...alpha.timeline, { date: "2024-05", score: 4, count: 6 }, { date: "2024-06", score: 9, is_forecast: true }])
    expect(s).toMatchObject({ months: 4, spanMonths: 5, gaps: 1, first: "2024-01", last: "2024-05", thin: 1 })
    expect(s.mean).toBeCloseTo(3.875)
    expect(s.low.date).toBe("2024-02")
    expect(s.high.date).toBe("2024-03")
    expect(timelineStats([])).toBeNull()
  })
})

describe("buildCompareReport", () => {
  it("liefert alle Teile des Kurzberichts", () => {
    const r = buildCompareReport({ companies: [alpha, beta], categories })
    expect(r.cells.map((c) => c.value)).toEqual(["3,90", "3,60"])
    expect(r.cells[0].sub).toBe("von 5 · n = 400 · ±0,08 (95 %)")
    expect(r.limits.length).toBeGreaterThan(0)
    expect(r.rules).toContain("keine Aussage über Ursachen")
    expect(trendText(alpha.trend)).toBe("+0,20 (12 M)")
    expect(trendText(null)).toBe("–")
  })
})
