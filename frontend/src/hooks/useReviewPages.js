// Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
// Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
// (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
// nach dem Annotationsprotokoll (Abschnitt 3.6.1)

import { useCallback, useEffect, useRef, useState } from "react"
import { API_URL } from "../config"

export const REVIEW_PAGE_SIZE = 25

export function useReviewPages(companyId, { source = "employee", status = null, start, end, dimension = null, dimensionOnly = false, topicOnly = false, topic = null, order = "desc" } = {}) {
  const scoped = Boolean(dimension) && dimensionOnly
  const requestKey = companyId && start && end ? `${companyId}:${source}:${status ?? ""}:${start}:${end}:${dimension ?? ""}:${scoped}:${topicOnly}:${topic ?? ""}:${order}` : null
  const countsKey = companyId && start && end ? `${companyId}:${source}:${status ?? ""}:${start}:${end}:${scoped ? dimension : ""}` : null
  const [result, setResult] = useState({ key: null, items: [], total: 0, highlight: null, markedTopic: null, error: "", loadingMore: false })
  const [topicCounts, setTopicCounts] = useState({ key: null, counts: [], withoutTopic: 0 })
  const controllerRef = useRef(null)

  const fetchPage = useCallback(
    (offset, signal) => {
      const params = new URLSearchParams({ source, start, end, offset: String(offset), limit: String(REVIEW_PAGE_SIZE), format: "full", order })
      if (status) params.set("status", status)
      if (dimension) params.set("dimension", dimension)
      if (scoped) params.set("dimension_only", "true")
      if (dimension && topicOnly) params.set("topic_only", "true")
      else if (topic) params.set("topic", topic)
      return fetch(`${API_URL}/analytics/company/${companyId}/reviews?${params}`, { signal }).then(async (res) => {
        const json = await res.json().catch(() => ({}))
        if (!res.ok) throw new Error(typeof json.detail === "string" ? json.detail : `HTTP ${res.status}`)
        return json
      })
    },
    [companyId, source, status, start, end, dimension, scoped, topicOnly, topic, order],
  )

  useEffect(() => {
    if (!requestKey) return undefined
    const controller = new AbortController()
    controllerRef.current = controller
    fetchPage(0, controller.signal)
      .then((json) => {
        setResult({
          key: requestKey, items: json.reviews ?? [], total: json.total ?? 0, highlight: json.highlight ?? null,
          markedTopic: json.topic_summary?.marked ?? null, error: "", loadingMore: false,
        })
        setTopicCounts({ key: countsKey, counts: json.topic_summary?.counts ?? [], withoutTopic: json.topic_summary?.without_topic ?? 0 })
      })
      .catch((e) => {
        if (e.name !== "AbortError") setResult({ key: requestKey, items: [], total: 0, highlight: null, markedTopic: null, error: e.message, loadingMore: false })
      })
    return () => controller.abort()
  }, [requestKey, countsKey, fetchPage])

  const current = result.key === requestKey ? result : null

  const loadMore = useCallback(() => {
    if (!current || current.loadingMore || current.items.length >= current.total) return
    const signal = controllerRef.current?.signal
    setResult((r) => ({ ...r, loadingMore: true }))
    fetchPage(current.items.length, signal)
      .then((json) => setResult((r) => (r.key === requestKey
        ? { ...r, items: [...r.items, ...(json.reviews ?? [])], total: json.total ?? r.total, loadingMore: false }
        : r)))
      .catch((e) => {
        if (e.name !== "AbortError") setResult((r) => (r.key === requestKey ? { ...r, loadingMore: false, error: e.message } : r))
      })
  }, [current, fetchPage, requestKey])

  return {
    loading: Boolean(requestKey) && !current,
    loadingMore: current?.loadingMore ?? false,
    error: current?.error ?? "",
    items: current?.items ?? [],
    total: current?.total ?? 0,
    highlight: current?.highlight ?? null,
    markedTopic: current?.markedTopic ?? null,
    topicCounts: topicCounts.key === countsKey ? topicCounts : null,
    hasMore: Boolean(current) && current.items.length < current.total,
    loadMore,
  }
}
