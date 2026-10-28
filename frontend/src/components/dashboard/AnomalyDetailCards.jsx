// Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
// Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
// (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
// nach dem Annotationsprotokoll (Abschnitt 3.6.1)

import { useState } from "react"
import { ArrowDownRight, ArrowUpRight, GitCompareArrows, Layers, Lightbulb, MessageSquareText, Newspaper, X } from "lucide-react"
import { ExpandableCard } from "./ExpandableCard"
import { AnomalyComparison } from "./AnomalyComparison"
import { ExplanationContent, ExplanationPreview } from "./ExplanationPanel"
import { EvidenceContent, EvidencePreview, ListControls } from "./EvidenceSection"
import { Headline, PreviewLabel, PreviewStatus, SentimentRows, ShiftBars, Warn } from "./CardPreview"
import { PeriodReviewList, ReviewListControls, WindowSideToggle } from "./PeriodReviews"
import { Delta } from "../ui/primitives"
import { selectionLabel } from "@/lib/anomalySeries"
import { useEvidence, useEvidenceList } from "@/hooks/useEvidence"
import { evidenceSubtitle } from "@/lib/evidenceText"
import { explanationSubtitle } from "@/lib/explanationText"
import { dimensionLabel } from "@/lib/ratingCategories"

const HINT = "Karte anklicken öffnet Detailansicht"
const TOP_SHIFTS = 3

export function DimensionFilterChip({ dimension, onClear = null }) {
    if (!dimension) return null
    const label = dimensionLabel(dimension)
    return (
        <span
            className="inline-flex items-center gap-1.5 h-7 pl-2 pr-1 rounded-md border border-amber-300 bg-amber-50 text-[12px] text-slate-800"
            title={`Nur zur Dimension ${label}: Bewertungen mit Kommentar zur Kategorie oder Schlüsselwort ihres Themas, Meldungen mit Schlüsselwort im Titel oder zugeordneter Ereignisart`}
        >
            <Layers className="w-3.5 h-3.5 text-amber-700" aria-hidden="true" />
            <span>Dimension: <span className="font-medium">{label}</span></span>
            {onClear ? (
                <button
                    type="button"
                    onClick={onClear}
                    aria-label={`Filter aufheben: Dimension ${label} abwählen`}
                    title="Filter aufheben: zur Gesamtbewertung wechseln, der Zeitraum bleibt"
                    className="inline-flex items-center justify-center w-5 h-5 rounded text-slate-500 hover:bg-amber-100 hover:text-slate-900"
                >
                    <X className="w-3.5 h-3.5" aria-hidden="true" />
                </button>
            ) : null}
        </span>
    )
}

const num = (v, digits = 2) =>
    v == null ? "–" : Number(v).toLocaleString("de-DE", { minimumFractionDigits: digits, maximumFractionDigits: digits })
const signed = (v, digits = 2) => (v == null ? "–" : (v > 0 ? "+" : v < 0 ? "−" : "±") + num(Math.abs(v), digits))

const ratingTone = (v) => {
    const n = Number(v)
    if (!Number.isFinite(n)) return "neu"
    return n >= 3.5 ? "pos" : n >= 2.5 ? "warn" : "neg"
}

const shortLabels = (labels) => ({ before: "davor", after: labels.after === "Auswahl" ? "Auswahl" : "danach" })

function ComparisonPreview({ comparison, intro = null }) {
    if (comparison.loading) return <PreviewStatus spinner>Vergleich wird berechnet; die Stimmungsanalyse kann beim ersten Aufruf dauern…</PreviewStatus>
    if (comparison.error) return <PreviewStatus>Vergleich konnte nicht geladen werden: {comparison.error}</PreviewStatus>
    const data = comparison.data
    if (!data) return null
    const { before, after, rating_shift, value_shift, low_basis, low_basis_rule, topics = [] } = data.comparison
    const dir = rating_shift > 0 ? "rise" : rating_shift < 0 ? "fall" : "flat"
    const tone = dir === "fall" ? "bad" : dir === "rise" ? "good" : "neutral"
    const chip = (
        <Delta
            tone={dir === "fall" ? "neg" : dir === "rise" ? "pos" : "neu"}
            icon={dir === "fall" ? <ArrowDownRight className="w-3 h-3" /> : dir === "rise" ? <ArrowUpRight className="w-3 h-3" /> : null}
        >
            {dir === "fall" ? "Abfall" : dir === "rise" ? "Anstieg" : "stabil"}
        </Delta>
    )
    const top = topics.slice(0, TOP_SHIFTS)
    const noText = (before.n_without_text ?? 0) > 0 || (after.n_without_text ?? 0) > 0
        ? ` · ohne Freitext ${before.n_without_text ?? 0} → ${after.n_without_text ?? 0}`
        : ""
    return (
        <div>
            {intro && <Warn className="mb-2">{intro}</Warn>}
            <Headline
                value={signed(rating_shift)}
                unit="Sterne"
                tone={tone}
                chip={chip}
                sub={`Ø ${num(before.mean_rating)} → ${num(after.mean_rating)} · ${before.n_reviews} → ${after.n_reviews} Bewertungen${noText}${value_shift !== undefined ? ` · Dimension ${signed(value_shift)}` : ""}`}
            />
            {top.length > 0 && (
                <>
                    <PreviewLabel>Stärkste Verschiebungen je Thema</PreviewLabel>
                    <ShiftBars rows={top.map((t) => ({ label: t.topic, value: t.share_shift_pp, text: `${signed(t.share_shift_pp, 1)} Pp.` }))} />
                </>
            )}
            {low_basis && (
                <Warn className="mt-2" title={`Mindestens ein Fenster hat weniger als ${low_basis_rule?.min_reviews_per_window} Bewertungen; Anteile und Stimmung schwanken dann stark`}>
                    Kleine Basis: ein Fenster hat weniger als {low_basis_rule?.min_reviews_per_window} Bewertungen.
                </Warn>
            )}
        </div>
    )
}

export function ComparisonCard({ eyebrow, title, subtitle, comparison, labels, intro = null, introText = null, onDrill = null, open = undefined, onOpenChange = null }) {
    return (
        <ExpandableCard
            icon={<GitCompareArrows />}
            eyebrow={eyebrow}
            title={title}
            subtitle={({ modal }) => (modal ? subtitle.full : subtitle.short)}
            basis={["stars", "text"]}
            accent="bg-slate-500"
            hint={HINT}
            open={open}
            onOpenChange={onOpenChange}
        >
            {({ modal }) => (modal ? (
                <>
                    {introText && <p className="m-0 mb-3 text-[12px] text-slate-600">{introText}</p>}
                    <AnomalyComparison data={comparison.data} loading={comparison.loading} error={comparison.error} labels={labels} onDrill={onDrill} />
                </>
            ) : (
                <ComparisonPreview comparison={comparison} intro={intro} />
            ))}
        </ExpandableCard>
    )
}

function ReviewsPreview({ pages, comparison, side, labels, span, filterTopic, dimension = null }) {
    if (pages.loading) return <PreviewStatus spinner>Lade Bewertungen…</PreviewStatus>
    if (pages.error && !pages.items.length) return <PreviewStatus>Bewertungen konnten nicht geladen werden: {pages.error}</PreviewStatus>
    const topic = pages.highlight?.topic ?? null
    const mentions = pages.highlight?.mentions
    const scope = dimension && pages.highlight?.dimension_only ? pages.highlight : null
    const stats = comparison.data?.comparison ?? null
    const meanRating = filterTopic ? null : scope ? scope.dimension_mean ?? null : stats?.[side]?.mean_rating ?? null
    const short = shortLabels(labels)
    const sub = `${labels[side]} · ${span}${filterTopic
        ? ` · nur Bewertungen, die ${filterTopic} nennen`
        : scope
            ? ` · zur Dimension ${dimensionLabel(dimension)}, von ${scope.n_all} insgesamt`
            : topic && mentions != null ? ` · ${mentions} ${mentions === 1 ? "nennt" : "nennen"} ${topic}` : ""}`
    return (
        <div>
            <Headline
                value={pages.total}
                unit={pages.total === 1 ? "Bewertung" : "Bewertungen"}
                chip={meanRating != null ? <Delta tone={ratingTone(meanRating)}>{scope ? "Ø Dimension" : "Ø"} {num(meanRating)}</Delta> : null}
                sub={sub}
            />
            <PreviewLabel>Stimmung der Freitexte</PreviewLabel>
            {comparison.loading ? (
                <PreviewStatus spinner>wird berechnet…</PreviewStatus>
            ) : stats ? (
                <SentimentRows rows={[{ label: short.before, sentiment: stats.before.sentiment }, { label: short.after, sentiment: stats.after.sentiment }]} />
            ) : (
                <PreviewStatus>nicht verfügbar</PreviewStatus>
            )}
        </div>
    )
}

export function ReviewsCard({ eyebrow, title, subtitle, pages, comparison, side, onSide, labels, window, topic, order, onOrder, listKey, emptyText, footnote, dimension = null, onClearDimension = null, open = undefined, onOpenChange = null }) {
    const span = window ? selectionLabel(window) : ""
    const withoutTopic = pages.topicCounts?.withoutTopic
    return (
        <ExpandableCard
            icon={<MessageSquareText />}
            eyebrow={eyebrow}
            title={title}
            subtitle={({ modal }) => (modal ? subtitle.full : subtitle.short)}
            basis={["stars", "text"]}
            accent="bg-slate-500"
            hint={HINT}
            open={open}
            onOpenChange={onOpenChange}
            actions={({ modal }) => (modal ? (
                <>
                    <DimensionFilterChip dimension={dimension} onClear={onClearDimension} />
                    <WindowSideToggle value={side} onChange={onSide} labels={labels} />
                    <ReviewListControls order={order} onOrder={onOrder} topics={pages.topicCounts} value={topic.value} onTopic={topic.onChange} dimension={dimension} />
                </>
            ) : null)}
        >
            {({ modal }) => (modal ? (
                <>
                    <PeriodReviewList key={listKey} pages={pages} emptyText={emptyText} dimension={dimension} />
                    <p className="m-0 mt-3 text-[11px] text-slate-400">{footnote}</p>
                    {dimension && pages.highlight?.note && (
                        <p className="m-0 mt-1 text-[11px] text-slate-400">
                            Dimension {dimensionLabel(dimension)} als Filter: {pages.highlight.note} Je Zeile stehen die Sterne der Dimension und, wenn vorhanden, der Kommentar zur Kategorie.
                        </p>
                    )}
                    <p className="m-0 mt-1 text-[11px] text-slate-400">
                        Themen: die Schlüsselwort-Themen der Themenübersicht, erkannt an Schlüsselwörtern in Titel, Freitexten und
                        Kategorie-Kommentaren; eine Bewertung kann mehrere oder keines nennen
                        {withoutTopic != null ? ` (in diesem Zeitraum ${withoutTopic} ohne erkanntes Thema)` : ""}. Keine Textanalyse durch ein Modell.
                    </p>
                </>
            ) : (
                <ReviewsPreview pages={pages} comparison={comparison} side={side} labels={labels} span={span} filterTopic={topic.value} dimension={dimension} />
            ))}
        </ExpandableCard>
    )
}

export function ExplanationCard({ eyebrow, subtitle, comparison, onSelectPeriod = null, userEvents = null }) {
    return (
        <ExpandableCard
            icon={<Lightbulb />}
            eyebrow={eyebrow}
            title="Mögliche Zusammenhänge"
            subtitle={({ modal }) => (modal ? explanationSubtitle(comparison) : subtitle)}
            basis={["external", "text"]}
            accent="bg-slate-500"
            hint={HINT}
        >
            {({ modal }) => (modal
                ? <ExplanationContent data={comparison.data} loading={comparison.loading} error={comparison.error} onSelectPeriod={onSelectPeriod} userEvents={userEvents} />
                : <ExplanationPreview data={comparison.data} loading={comparison.loading} error={comparison.error} userEvents={userEvents} />)}
        </ExpandableCard>
    )
}

export function EvidenceCard({ eyebrow, subtitle, companyId, anomalyId = null, selection = null, group = {}, scores = null, rules = null, dimensionOnly = false, onClearDimension = null }) {
    const evidence = useEvidence(companyId, { anomalyId, selection, ...group, dimensionOnly })
    const [sort, setSort] = useState("date")
    const [category, setCategory] = useState("")
    const list = useEvidenceList(evidence, scores, { sort, category })
    const showControls = !evidence.loading && !evidence.error && evidence.total > 0
    return (
        <ExpandableCard
            icon={<Newspaper />}
            eyebrow={eyebrow}
            title="Externe Berichte im Ereignisfenster"
            subtitle={({ modal }) => (modal ? evidenceSubtitle(evidence, list.listNote) : subtitle)}
            basis="external"
            accent="bg-slate-500"
            hint={HINT}
            actions={({ modal }) => (modal ? (
                <>
                    {dimensionOnly && <DimensionFilterChip dimension={group.dimension} onClear={onClearDimension} />}
                    {showControls && (
                        <ListControls sort={sort} onSort={setSort} category={category} onCategory={setCategory} categories={list.categories} enabled={Boolean(scores)} dimension={dimensionOnly ? group.dimension ?? null : null} />
                    )}
                </>
            ) : null)}
        >
            {({ modal }) => (modal
                ? <EvidenceContent evidence={evidence} items={list.items} needAll={list.needAll} sort={sort} category={category} scores={scores} rules={rules} />
                : <EvidencePreview evidence={evidence} />)}
        </ExpandableCard>
    )
}
