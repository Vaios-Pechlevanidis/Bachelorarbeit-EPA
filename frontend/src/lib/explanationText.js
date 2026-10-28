// Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
// Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
// (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
// nach dem Annotationsprotokoll (Abschnitt 3.6.1)

const STAGE_LABELS = {
    hoch: "Wortbezug und Ereignisart",
    mittel: "Wortbezug oder Themenbezug",
    niedrig: "nur Ereignisart",
    keine: "kein Bezug",
}
const STAGE_ORDER = ["hoch", "mittel", "niedrig"]

export const stageLabel = (stage, rules = null) => rules?.stage_labels?.[stage] ?? STAGE_LABELS[stage] ?? stage

export function stageCounts(n, rules) {
    if (!n) return ""
    return STAGE_ORDER.filter((s) => n[s]).map((s) => `${stageLabel(s, rules)} ${n[s]}`).join(", ")
}

export const isStrict = (summary) => Boolean(summary?.selection?.strict ?? summary?.rules?.selection?.strict)

export function exclusionCounts(n) {
    if (!n) return ""
    return Object.entries(n).filter(([, count]) => count > 0).map(([reason, count]) => `${reason} ${count}`).join(", ")
}

export function selectionText(summary) {
    if (!isStrict(summary) || !summary?.n_items) return ""
    const counts = exclusionCounts(summary.n_excluded_by_reason)
    return `Strenge Auswahl: ${summary.n_selected} von ${summary.n_items} ${summary.n_items === 1 ? "Beleg" : "Belegen"} erfüllen alle vier Regeln, ${summary.n_excluded} ausgeschlossen${counts ? ` (${counts})` : ""}. Die Belegliste nennt je Meldung die nicht erfüllte Regel.`
}

export function signalCounts(n) {
    if (!n) return ""
    return Object.entries(n).sort((a, b) => b[1] - a[1]).map(([label, count]) => `${label} ${count}`).join(", ")
}

export function explanationSubtitle({ data, loading, error }, { short = false } = {}) {
    const summary = data?.explanation_summary ?? null
    const entries = data?.explanations ?? []
    const rules = summary?.rules ?? null
    if (loading) return "Erklärungsansätze werden berechnet…"
    if (error) return "Erklärungsansätze konnten nicht geladen werden"
    if (!summary) return ""
    const nGlobal = summary.global_events?.length ?? 0
    const globalText = nGlobal ? ` · ${nGlobal} ${nGlobal === 1 ? "allgemeines Ereignis" : "allgemeine Ereignisse"} (Hypothese)` : ""
    const strict = isStrict(summary)
    if (summary.state === "offen") {
        const why = strict ? "keiner erfüllt die strengen Auswahlregeln" : "keiner erreicht die Stufe niedrig"
        return short
            ? `offen · ${summary.n_items} ${summary.n_items === 1 ? "Beleg" : "Belege"} im Ereignisfenster`
            : `offen · ${summary.n_items} ${summary.n_items === 1 ? "Beleg" : "Belege"} im Ereignisfenster, ${why}${globalText}`
    }
    const head = `${entries.length} ${entries.length === 1 ? "Ansatz" : "Ansätze"} aus ${summary.n_items} Belegen`
    if (short) return head
    const selected = strict && summary.n_selected != null ? `${summary.n_selected} geeignet nach strenger Auswahl, ${summary.n_excluded} ausgeschlossen; ` : ""
    return `${head} (${selected}${summary.n_bundles} Bündel${summary.n_groups != null ? `, ${summary.n_groups} ${summary.n_groups === 1 ? "Gruppe" : "Gruppen"} nach Ereignisart` : ""})${signalCounts(summary.n_by_signal_label)
        ? ` · Bündel nach Signalen: ${signalCounts(summary.n_by_signal_label)}`
        : stageCounts(summary.n_by_stage, rules) ? ` · Bündel je Stufe: ${stageCounts(summary.n_by_stage, rules)}` : ""}${globalText}`
}
