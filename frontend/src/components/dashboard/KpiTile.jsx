// Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
// Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
// (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
// nach dem Annotationsprotokoll (Abschnitt 3.6.1)

export function KpiTile({ label, value, note, tone }) {
    return (
        <div className="bg-white border border-slate-200 rounded-lg px-3.5 py-2 min-w-0 shadow-xs">
            <p className="m-0 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 leading-none truncate">{label}</p>
            <p className="m-0 mt-1 text-[16px] leading-6 font-semibold text-slate-900 tnum truncate" style={tone ? { color: tone } : undefined}>{value}</p>
            <p className="m-0 text-[11px] text-slate-500 leading-4 truncate" title={note}>{note}</p>
        </div>
    )
}
