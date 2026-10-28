// Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
// Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
// (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
// nach dem Annotationsprotokoll (Abschnitt 3.6.1)

import { OVERALL_DIMENSION, dimensionLabel } from "./ratingCategories"

export function isSingleDimension(key) {
    return Boolean(key) && key !== OVERALL_DIMENSION.key
}

const plural = (n, one, many) => `${n} ${n === 1 ? one : many}`

export function reviewScopeText(highlight, dimension) {
    if (!highlight?.dimension_only) return null
    const n = highlight.n_dimension ?? 0
    const all = highlight.n_all ?? n
    return `${n} von ${plural(all, "Bewertung", "Bewertungen")} zur Dimension ${dimensionLabel(dimension)}`
}

export function evidenceScopeText(scope) {
    if (!scope) return null
    const n = scope.n_dimension ?? 0
    const all = scope.n_all ?? n
    return `nur zur Dimension ${dimensionLabel(scope.dimension)}: ${n} von ${plural(all, "Beleg", "Belegen")}`
}

export function dimensionScopeNote(dimension) {
    const label = dimensionLabel(dimension)
    return `Dimension ${label} gewählt: Die Bewertungen des Zeitraums und die externen Berichte unten zeigen nur, was zu dieser Dimension gehört (Bewertungen mit Kommentar zur Kategorie oder einem Schlüsselwort ihres Themas; Meldungen mit einem Schlüsselwort im Titel oder einer zugeordneten Ereignisart). „Gesamtbewertung“ zeigt wieder alles.`
}

export function reviewScopeEmptyText(dimension) {
    return `Keine Bewertung dieses Zeitraums gehört zur Dimension ${dimensionLabel(dimension)}: kein Kommentar zur Kategorie und kein Schlüsselwort ihres Themas.`
}

export function evidenceScopeEmptyText(scope) {
    const label = dimensionLabel(scope?.dimension)
    const all = scope?.n_all ?? 0
    if (!all) return `Kein Beleg im Fenster, also auch keiner zur Dimension ${label}.`
    return `Kein Beleg zur Dimension ${label} im Fenster. ${plural(all, "Beleg", "Belege")} im Fenster ${all === 1 ? "gehört" : "gehören"} nicht dazu: kein Schlüsselwort des Themas im Titel und keine zugeordnete Ereignisart.`
}

export function evidenceMatchText(match) {
    if (!match) return null
    const parts = [
        match.terms?.length ? `Schlüsselwort ${match.terms.map((t) => `‚${t}‘`).join(", ")}` : null,
        match.terms_in_text?.length ? `Schlüsselwort im Text ${match.terms_in_text.map((t) => `‚${t}‘`).join(", ")}` : null,
        match.category ? `Ereignisart ${match.category}` : null,
    ].filter(Boolean)
    return parts.length ? `Bezug zur Dimension: ${parts.join(" · ")}` : null
}
