// Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
// Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
// (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
// nach dem Annotationsprotokoll (Abschnitt 3.6.1)

export function HighlightedText({ text, spans, title }) {
    if (!text) return null
    if (!spans?.length) return text
    const parts = []
    let pos = 0
    spans.forEach(([start, end], i) => {
        if (start > pos) parts.push(text.slice(pos, start))
        parts.push(
            <mark key={i} title={title} className="bg-amber-100 text-inherit rounded-[2px] px-0.5 -mx-0.5 font-medium">
                {text.slice(start, end)}
            </mark>,
        )
        pos = Math.max(pos, end)
    })
    if (pos < text.length) parts.push(text.slice(pos))
    return parts
}
