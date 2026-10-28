// Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
// Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
// (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
// nach dem Annotationsprotokoll (Abschnitt 3.6.1)

import { useEffect, useState, useCallback } from "react"

const STORAGE_KEY = "agb.theme"

export function useTheme() {
  const getInitial = () => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved === "dark" || saved === "light") return saved
    } catch {}
    if (typeof window !== "undefined" && window.matchMedia?.("(prefers-color-scheme: dark)").matches) {
      return "dark"
    }
    return "light"
  }

  const [theme, setTheme] = useState(getInitial)

  useEffect(() => {
    const root = document.documentElement
    root.setAttribute("data-theme", theme)
    if (theme === "dark") root.classList.add("dark")
    else root.classList.remove("dark")
    try { localStorage.setItem(STORAGE_KEY, theme) } catch {}
  }, [theme])

  const toggle = useCallback(() => {
    setTheme((t) => (t === "dark" ? "light" : "dark"))
  }, [])

  return { theme, setTheme, toggle, isDark: theme === "dark" }
}
