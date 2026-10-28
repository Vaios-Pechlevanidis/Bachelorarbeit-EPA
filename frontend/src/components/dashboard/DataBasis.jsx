// Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
// Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
// (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
// nach dem Annotationsprotokoll (Abschnitt 3.6.1)

import { AlertTriangle } from "lucide-react"
import { BASIS } from "@/lib/dataBasis"

export function DataBasisTag({ basis, small = false, className = "" }) {
  const b = BASIS[basis]
  if (!b) return null
  return (
    <span
      className={`inline-flex items-center rounded-full border border-slate-300 bg-slate-50 text-slate-600 font-sans normal-case tracking-normal ${small ? "px-1.5 py-px text-[9.5px]" : "px-1.5 py-0.5 text-[10px]"} ${className}`}
      title={b.title}
    >
      {b.label}
    </span>
  )
}

export function DataBasisTags({ basis, small = false, className = "" }) {
  const keys = Array.isArray(basis) ? basis : basis ? [basis] : []
  if (!keys.length) return null
  return (
    <span className={`inline-flex flex-wrap items-center gap-1 ${className}`} aria-label="Datenbasis">
      {keys.map((k) => <DataBasisTag key={k} basis={k} small={small} />)}
    </span>
  )
}

export function SmallBasisWarning({ n, min, unit = "Bewertungen", context = "", className = "" }) {
  if (n == null || min == null || n >= min) return null
  return (
    <span className={`inline-flex items-center gap-1 text-amber-700 ${className}`} title={`Kleine Basis: ${n} ${unit}${context ? ` ${context}` : ""}, Schwelle ${min}`}>
      <AlertTriangle className="w-3 h-3 flex-none" aria-hidden="true" />
      kleine Basis ({n} {unit}{context ? ` ${context}` : ""}, unter {min})
    </span>
  )
}
