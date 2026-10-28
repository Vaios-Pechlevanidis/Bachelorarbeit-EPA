// Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
// Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
// (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
// nach dem Annotationsprotokoll (Abschnitt 3.6.1)

import { describe, expect, it } from "vitest"
import { sameSectorCompanies, sectorOf } from "../companies"

const list = [
  { id: "1", name: "Alpha", sector: "IT", review_count: 50 },
  { id: "2", name: "Beta", sector: "IT", review_count: 200 },
  { id: "3", name: "Gamma", sector: "Energie", review_count: 90 },
  { id: "4", name: "Delta", sector: "IT", review_count: 200 },
  { id: "5", name: "Epsilon", sector: " ", review_count: 10 },
  { id: "6", name: "Zeta", sector: null, review_count: 10 },
]

describe("sectorOf", () => {
  it("liefert die Branche getrimmt, sonst null", () => {
    expect(sectorOf({ sector: " IT " })).toBe("IT")
    expect(sectorOf({ sector: " " })).toBeNull()
    expect(sectorOf({ sector: null })).toBeNull()
    expect(sectorOf(null)).toBeNull()
  })
})

describe("sameSectorCompanies", () => {
  it("findet Firmen derselben Branche ohne die Bezugsfirma, nach Bewertungen und Name", () => {
    expect(sameSectorCompanies(list, list[0]).map((c) => c.name)).toEqual(["Beta", "Delta"])
    expect(sameSectorCompanies(list, list[1]).map((c) => c.name)).toEqual(["Delta", "Alpha"])
  })
  it("lässt bereits gewählte Firmen aus", () => {
    expect(sameSectorCompanies(list, list[0], [2]).map((c) => c.name)).toEqual(["Delta"])
  })
  it("ist leer ohne Branche, ohne Liste oder ohne zweite Firma der Branche", () => {
    expect(sameSectorCompanies(list, list[4])).toEqual([])
    expect(sameSectorCompanies(list, list[5])).toEqual([])
    expect(sameSectorCompanies(list, list[2])).toEqual([])
    expect(sameSectorCompanies(null, list[0])).toEqual([])
  })
})
