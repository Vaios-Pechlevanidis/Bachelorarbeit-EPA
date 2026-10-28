// Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
// Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
// (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
// nach dem Annotationsprotokoll (Abschnitt 3.6.1)

import { AlertTriangle } from "lucide-react"

const TONE_TEXT = {
    good: "text-emerald-700",
    bad: "text-rose-700",
    warn: "text-amber-700",
    neutral: "text-slate-900",
}

export function Headline({ value, unit = null, tone = "neutral", chip = null, sub = null }) {
    return (
        <div className="min-w-0">
            <div className="flex items-baseline gap-x-2 gap-y-1 flex-wrap min-w-0">
                <span className={`text-[28px] leading-8 font-semibold tracking-tight ${TONE_TEXT[tone] ?? TONE_TEXT.neutral}`}>{value}</span>
                {unit && <span className="text-[13px] text-slate-600">{unit}</span>}
                {chip}
            </div>
            {sub && <p className="m-0 mt-0.5 text-[11.5px] leading-4 text-slate-500 truncate" title={typeof sub === "string" ? sub : undefined}>{sub}</p>}
        </div>
    )
}

export function PreviewLabel({ children, className = "" }) {
    return <p className={`m-0 mt-3 mb-1.5 font-mono text-[10px] tracking-[0.06em] uppercase text-slate-500 leading-none ${className}`}>{children}</p>
}

export function ShiftBars({ rows }) {
    const max = Math.max(...rows.map((r) => Math.abs(r.value ?? 0)), 0.0001)
    return (
        <ul className="m-0 p-0 list-none space-y-1.5">
            {rows.map((r) => {
                const share = Math.abs(r.value ?? 0) / max
                return (
                    <li key={r.label} className="grid grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)_auto] items-center gap-2 text-[12px] leading-4">
                        <span className="truncate text-slate-700" title={r.label}>{r.label}</span>
                        <span className="h-2.5 rounded-[4px] bg-slate-100 overflow-hidden" aria-hidden="true">
                            {share > 0 && <span className="block h-full bg-blue-500 rounded-r-[4px]" style={{ width: `${share * 100}%` }} />}
                        </span>
                        <span className="text-right tnum font-semibold text-slate-900 whitespace-nowrap">{r.text}</span>
                    </li>
                )
            })}
        </ul>
    )
}

const pct0 = (share) => `${Math.round((share ?? 0) * 100)}`

export function SentimentRows({ rows }) {
    return (
        <ul className="m-0 p-0 list-none space-y-1.5">
            {rows.map((r) => {
                const s = r.sentiment
                const empty = !s?.n
                return (
                    <li key={r.label} className="grid grid-cols-[52px_minmax(0,1fr)_auto] items-center gap-2 text-[11.5px] leading-4">
                        <span className="text-slate-500 truncate" title={r.label}>{r.label}</span>
                        {empty ? (
                            <span className="col-span-2 text-slate-400">keine Freitexte</span>
                        ) : (
                            <>
                                <span className="flex h-2.5 gap-[2px] min-w-0" aria-hidden="true">
                                    <span className="bg-emerald-500 rounded-l-[4px]" style={{ width: `${(s.positive ?? 0) * 100}%` }} />
                                    <span className="bg-slate-300" style={{ width: `${(s.neutral ?? 0) * 100}%` }} />
                                    <span className="bg-rose-500 rounded-r-[4px]" style={{ width: `${(s.negative ?? 0) * 100}%` }} />
                                </span>
                                <span className="tnum text-slate-700 whitespace-nowrap" title={`positiv ${pct0(s.positive)} %, neutral ${pct0(s.neutral)} %, negativ ${pct0(s.negative)} % (n = ${s.n})`}>
                                    {pct0(s.positive)} % pos. · {pct0(s.negative)} % neg.
                                </span>
                            </>
                        )}
                    </li>
                )
            })}
        </ul>
    )
}

export function FigureRow({ items }) {
    return (
        <div className="flex flex-wrap gap-x-5 gap-y-1.5">
            {items.map((it) => (
                <div key={it.label} className="min-w-0">
                    <p className="m-0 text-[16px] leading-5 font-semibold text-slate-900 tnum">{it.value}</p>
                    <p className="m-0 text-[10.5px] leading-3 text-slate-500">{it.label}</p>
                </div>
            ))}
        </div>
    )
}

export function Warn({ children, title, className = "" }) {
    return (
        <p className={`m-0 inline-flex items-start gap-1 text-[11.5px] leading-4 text-amber-700 ${className}`} title={title}>
            <AlertTriangle className="w-3 h-3 flex-none mt-0.5" aria-hidden="true" />
            <span className="min-w-0">{children}</span>
        </p>
    )
}

export function PreviewStatus({ children, spinner = false }) {
    return (
        <div className="flex items-start gap-2 py-0.5">
            {spinner && <div className="animate-spin rounded-full h-3.5 w-3.5 mt-px flex-none border-2 border-slate-200 border-t-slate-600" />}
            <p className="m-0 text-[12px] leading-4 text-slate-500">{children}</p>
        </div>
    )
}
