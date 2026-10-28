// Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
// Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
// (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
// nach dem Annotationsprotokoll (Abschnitt 3.6.1)

export function saveImportHistory(companyId, entry) {
  if (!companyId) return
  const key = `import_history_${companyId}`
  const existing = JSON.parse(localStorage.getItem(key) || "[]")
  const updated = [entry, ...existing].slice(0, 10)
  localStorage.setItem(key, JSON.stringify(updated))
}

export function getImportHistory(companyId) {
  if (!companyId) return []
  return JSON.parse(localStorage.getItem(`import_history_${companyId}`) || "[]")
}
