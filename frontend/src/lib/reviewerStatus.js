// Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
// Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
// (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
// nach dem Annotationsprotokoll (Abschnitt 3.6.1)

import { sourceLabel } from "./ratingCategories"

const RAW_LABELS = {
  "1": "Angestellt",
  "1.0": "Angestellt",
  "true": "Angestellt",
  "0": "Ex-Angestellt",
  "0.0": "Ex-Angestellt",
  "false": "Ex-Angestellt",
  hired: "Eingestellt",
  offerdeclined: "Angebot abgelehnt",
  rejected: "Abgelehnt",
  deferred: "Zurückgestellt oder Absage",
}

export function statusLabel(status) {
  if (status == null) return null
  const s = String(status).trim()
  if (!s) return null
  const lower = s.toLowerCase()
  if (RAW_LABELS[lower]) return RAW_LABELS[lower]
  if (/^ex-?angestell/.test(lower.replace(/\s+/g, "-"))) return "Ex-Angestellt"
  return s
}

export const STATUS_OPTIONS_BY_SOURCE = {
  employee: [
    { key: null, label: "Alle" },
    { key: "angestellt", label: "Angestellt" },
    { key: "ex-angestellt", label: "Ex-Angestellt" },
    { key: "unbekannt", label: "ohne Angabe" },
  ],
  candidates: [
    { key: null, label: "Alle" },
    { key: "eingestellt", label: "Eingestellt" },
    { key: "angebot-abgelehnt", label: "Angebot abgelehnt" },
    { key: "abgelehnt", label: "Abgelehnt" },
    { key: "zurueckgestellt", label: "Zurückgestellt oder Absage" },
    { key: "unbekannt", label: "ohne Angabe" },
  ],
}

export function statusOptions(source) {
  return STATUS_OPTIONS_BY_SOURCE[source] ?? STATUS_OPTIONS_BY_SOURCE.employee
}

export function validStatus(source, key) {
  return key && statusOptions(source).some((o) => o.key === key) ? key : null
}

export function groupLabel(source, status) {
  const option = status ? statusOptions(source).find((o) => o.key === status) : null
  return option ? `${sourceLabel(source)} · ${option.label}` : sourceLabel(source)
}

export const STATUS_NO_DISTINCTION_HINT =
  "Für dieses Unternehmen liegt keine Unterscheidung zwischen aktuellen und ehemaligen Mitarbeitenden vor (Export ohne diesen Wert). „Angestellt“ heißt hier „Bewertung mit Typangabe“ und entspricht bis auf die Bewertungen ohne Angabe der Gruppe „Alle“."

export function statusDistinctionHint(source, sourceStatus) {
  if (source !== "employee" || !sourceStatus || sourceStatus.n_reviews === 0) return null
  return sourceStatus.status_distinction === false ? STATUS_NO_DISTINCTION_HINT : null
}
