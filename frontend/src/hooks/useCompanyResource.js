// Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
// Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
// (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
// nach dem Annotationsprotokoll (Abschnitt 3.6.1)

import { useEffect, useState } from "react"
import { API_URL } from "../config"

export function useCompanyResource(companyId, path) {
  const requestKey = companyId ? `${companyId}/${path}` : null
  const [result, setResult] = useState({ key: null, data: null, error: "" })

  useEffect(() => {
    if (!requestKey) return undefined
    const controller = new AbortController()
    fetch(`${API_URL}/analytics/company/${requestKey}`, { signal: controller.signal })
      .then(async (res) => {
        const json = await res.json().catch(() => ({}))
        if (!res.ok) throw new Error(typeof json.detail === "string" ? json.detail : `HTTP ${res.status}`)
        setResult({ key: requestKey, data: json, error: "" })
      })
      .catch((e) => {
        if (e.name !== "AbortError") setResult({ key: requestKey, data: null, error: e.message })
      })
    return () => controller.abort()
  }, [requestKey])

  const current = result.key === requestKey ? result : null
  return {
    loading: Boolean(requestKey) && !current,
    error: current?.error ?? "",
    data: current?.data ?? null,
  }
}
