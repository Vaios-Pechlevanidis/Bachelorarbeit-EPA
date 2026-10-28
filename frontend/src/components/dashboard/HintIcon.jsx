// Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
// Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
// (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
// nach dem Annotationsprotokoll (Abschnitt 3.6.1)

import { CircleHelp } from "lucide-react"

export function HintIcon({ text, label = "Erklärung", className = "" }) {
    return (
        <span className={`relative inline-flex group align-middle ${className}`}>
            <button
                type="button"
                aria-label={label}
                className="inline-flex items-center justify-center w-4 h-4 rounded-full text-slate-400 hover:text-slate-700 focus:outline-none focus-visible:ring-1 focus-visible:ring-slate-400"
                onClick={(e) => e.stopPropagation()}
            >
                <CircleHelp className="w-3.5 h-3.5" aria-hidden="true" />
            </button>
            <span
                role="tooltip"
                className="pointer-events-none absolute left-0 top-full z-20 mt-1 hidden w-[280px] max-w-[80vw] rounded-md border border-slate-200 bg-white px-2.5 py-2 text-left text-[11px] font-normal normal-case tracking-normal leading-4 text-slate-700 shadow-md group-hover:block group-focus-within:block"
            >
                {text}
            </span>
        </span>
    )
}
