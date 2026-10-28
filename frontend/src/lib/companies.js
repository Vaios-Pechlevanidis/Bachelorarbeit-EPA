// Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
// Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
// (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
// nach dem Annotationsprotokoll (Abschnitt 3.6.1)

import { API_URL } from "../config"

export const COMPANIES_TTL = 5 * 60 * 1000

let cache = null
let pending = null

export function cachedCompanies() {
  return cache && Date.now() - cache.at < COMPANIES_TTL ? cache.data : null
}

export function loadCompanies({ force = false } = {}) {
  const cached = force ? null : cachedCompanies()
  if (cached) return Promise.resolve(cached)
  if (pending && !force) return pending
  const request = fetch(`${API_URL}/companies`)
    .then((res) => {
      if (!res.ok) throw new Error(`Firmen konnten nicht geladen werden (HTTP ${res.status})`)
      return res.json()
    })
    .then((data) => {
      const list = Array.isArray(data) ? data : []
      if (pending === request) cache = { at: Date.now(), data: list }
      return list
    })
    .finally(() => {
      if (pending === request) pending = null
    })
  pending = request
  return request
}

export function invalidateCompanies() {
  cache = null
  pending = null
}

export async function loadCompany(companyId) {
  const list = await loadCompanies()
  return list.find((c) => String(c.id) === String(companyId)) ?? null
}

export async function loadCompanyName(companyId) {
  const company = await loadCompany(companyId)
  return company?.name?.trim() ?? ""
}

export function sectorOf(company) {
  const s = company?.sector
  return typeof s === "string" && s.trim() ? s.trim() : null
}

export function sameSectorCompanies(list, reference, excludeIds = []) {
  const sector = sectorOf(reference)
  if (!sector || !Array.isArray(list)) return []
  const excluded = new Set([String(reference.id), ...excludeIds.map(String)])
  return list
    .filter((c) => !excluded.has(String(c.id)) && sectorOf(c) === sector)
    .sort((a, b) => (b.review_count ?? 0) - (a.review_count ?? 0) || a.name.localeCompare(b.name, "de"))
}
