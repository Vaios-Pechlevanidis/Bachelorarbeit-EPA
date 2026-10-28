// Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
// Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
// (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
// nach dem Annotationsprotokoll (Abschnitt 3.6.1)

export const RATING_CATEGORIES = [
  { key: "arbeitsatmosphaere",         label: "Arbeitsatmosphäre" },
  { key: "image",                       label: "Image" },
  { key: "work_life_balance",           label: "Work-Life Balance" },
  { key: "karriere_weiterbildung",      label: "Karriere/Weiterbildung" },
  { key: "gehalt_sozialleistungen",     label: "Gehalt/Sozialleistungen" },
  { key: "kollegenzusammenhalt",        label: "Kollegenzusammenhalt" },
  { key: "umwelt_sozialbewusstsein",    label: "Umwelt-/Sozialbewusstsein" },
  { key: "vorgesetztenverhalten",       label: "Vorgesetztenverhalten" },
  { key: "kommunikation",               label: "Kommunikation" },
  { key: "interessante_aufgaben",       label: "Interessante Aufgaben" },
  { key: "umgang_mit_aelteren_kollegen", label: "Umgang mit älteren Kollegen" },
  { key: "arbeitsbedingungen",          label: "Arbeitsbedingungen" },
  { key: "gleichberechtigung",          label: "Gleichberechtigung" },
]

export const CANDIDATE_RATING_CATEGORIES = [
  { key: "erklaerung_der_weiteren_schritte",  label: "Erklärung der weiteren Schritte" },
  { key: "zufriedenstellende_reaktion",       label: "Zufriedenstellende Reaktion" },
  { key: "vollstaendigkeit_der_infos",        label: "Vollständigkeit der Infos" },
  { key: "zufriedenstellende_antworten",      label: "Zufriedenstellende Antworten" },
  { key: "angenehme_atmosphaere",             label: "Angenehme Atmosphäre" },
  { key: "professionalitaet_des_gespraechs",  label: "Professionalität des Gesprächs" },
  { key: "wertschaetzende_behandlung",        label: "Wertschätzende Behandlung" },
  { key: "erwartbarkeit_des_prozesses",       label: "Erwartbarkeit des Prozesses" },
  { key: "zeitgerechte_zu_oder_absage",       label: "Zeitgerechte Zu- oder Absage" },
  { key: "schnelle_antwort",                  label: "Schnelle Antwort" },
]

export const OVERALL_DIMENSION = { key: "durchschnittsbewertung", label: "Gesamtbewertung" }

export const EMPLOYEE_DIMENSIONS = [OVERALL_DIMENSION, ...RATING_CATEGORIES]
export const CANDIDATE_DIMENSIONS = [OVERALL_DIMENSION, ...CANDIDATE_RATING_CATEGORIES]
export const DIMENSIONS_BY_SOURCE = { employee: EMPLOYEE_DIMENSIONS, candidates: CANDIDATE_DIMENSIONS }

export const SOURCES = [
  { value: "employee",   label: "Mitarbeiter", color: "#3b82f6" },
  { value: "candidates", label: "Bewerber",    color: "#10b981" },
]
export const DEFAULT_SOURCE = "employee"

export function isSource(key) {
  return SOURCES.some((s) => s.value === key)
}

export function sourceLabel(key) {
  return SOURCES.find((s) => s.value === key)?.label ?? key
}

export function dimensionsFor(source = DEFAULT_SOURCE) {
  return DIMENSIONS_BY_SOURCE[source] ?? EMPLOYEE_DIMENSIONS
}

export function isDimensionOf(source, key) {
  return dimensionsFor(source).some((d) => d.key === key)
}

export function dimensionLabel(key) {
  return [...EMPLOYEE_DIMENSIONS, ...CANDIDATE_RATING_CATEGORIES].find((d) => d.key === key)?.label ?? key
}
