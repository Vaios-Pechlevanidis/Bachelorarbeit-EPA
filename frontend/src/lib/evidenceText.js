// Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
// Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
// (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
// nach dem Annotationsprotokoll (Abschnitt 3.6.1)

import { fmtPeriod } from "./anomalySeries"
import { evidenceScopeText } from "./dimensionScope"

export const NO_CATEGORY = "__none__"

export function countsText(total, counts) {
    if (!total) return "kein Beleg"
    const parts = [
        counts?.news ? `${counts.news} ${counts.news === 1 ? "Meldung" : "Meldungen"}` : null,
        counts?.adhoc ? `${counts.adhoc} EQS` : null,
        counts?.global ? `${counts.global} ${counts.global === 1 ? "allgemeines Ereignis" : "allgemeine Ereignisse"}` : null,
    ].filter(Boolean)
    return `${total} ${total === 1 ? "Beleg" : "Belege"}${parts.length ? `: ${parts.join(", ")}` : ""}`
}

export function windowText(window) {
    if (!window) return ""
    const span = window.from === window.to ? fmtPeriod(window.from) : `${fmtPeriod(window.from)} – ${fmtPeriod(window.to)}`
    const ref = window.kind === "auswahl" ? "um die Auswahl" : window.kind === "einzelmonat" ? "um den Monat" : "um den Übergang"
    return `${span} (${window.months} ${window.months === 1 ? "Monat" : "Monate"}: ${window.window_before} davor, ${window.window_after} danach, ${ref})`
}

export function evidenceSubtitle(evidence, listNote = "", { short = false } = {}) {
    const data = evidence.data
    if (evidence.loading) return "Lade Belege…"
    if (evidence.error) return "Belege konnten nicht geladen werden"
    if (!data) return ""
    if (short) return countsText(data.total, data.counts)
    const scope = evidenceScopeText(data.scope)
    return `Ereignisfenster ${windowText(data.window)} · ${countsText(data.total, data.counts)}${scope ? ` · ${scope}` : ""}${listNote ? ` · ${listNote}` : ""}`
}
