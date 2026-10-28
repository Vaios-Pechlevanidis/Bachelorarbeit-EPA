// Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
// Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
// (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
// nach dem Annotationsprotokoll (Abschnitt 3.6.1)

import { useEffect, useState } from "react"
import { API_URL } from "../config"

function useComparisonRequest(url) {
  const [result, setResult] = useState({ key: null, data: null, error: "" })

  useEffect(() => {
    if (!url) return undefined
    const controller = new AbortController()
    fetch(url, { signal: controller.signal })
      .then(async (res) => {
        const json = await res.json().catch(() => ({}))
        if (!res.ok) throw new Error(typeof json.detail === "string" ? json.detail : `HTTP ${res.status}`)
        setResult({ key: url, data: json, error: "" })
      })
      .catch((e) => {
        if (e.name !== "AbortError") setResult({ key: url, data: null, error: e.message })
      })
    return () => controller.abort()
  }, [url])

  const current = result.key === url ? result : null
  return {
    loading: Boolean(url) && !current,
    error: current?.error ?? "",
    data: current?.data ?? null,
  }
}

function groupParams({ source = "employee", dimension, status = null }) {
  const params = new URLSearchParams({ source })
  if (dimension) params.set("dimension", dimension)
  if (status) params.set("status", status)
  return params
}

export function useAnomalyComparison(companyId, anomalyId, options = {}) {
  const url = companyId && anomalyId
    ? `${API_URL}/analytics/company/${companyId}/anomalies/${encodeURIComponent(anomalyId)}/explanations?${groupParams(options)}`
    : null
  return useComparisonRequest(url)
}

export function usePeriodComparison(companyId, period, options = {}) {
  let url = null
  if (companyId && period?.from && period?.to) {
    const params = groupParams(options)
    params.set("from", period.from)
    params.set("to", period.to)
    url = `${API_URL}/analytics/company/${companyId}/compare?${params}`
  }
  return useComparisonRequest(url)
}
