// Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
// Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
// (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
// nach dem Annotationsprotokoll (Abschnitt 3.6.1)

export const BASIS = {
  stars: { label: "Sternebewertung", title: "Datenbasis: Sterne der Kununu-Bewertungen (Gesamtnote je Bewertung oder Kategorien)" },
  text: { label: "Freitextanalyse", title: "Datenbasis: Freitexte der Kununu-Bewertungen (Schlüsselwort-Themen, Stimmung, kennzeichnende Begriffe)" },
  external: { label: "Externe Meldungen", title: "Datenbasis: Meldungen externer Quellen (Google News RSS, EQS News, allgemeine Ereignisse); keine Aussage über Ursachen" },
  market: { label: "Marktdaten", title: "Datenbasis: Kurse und Kennzahlen von Yahoo Finance; Einordnung, kein Zusammenhang mit den Bewertungen behauptet" },
}

export const MIN_REVIEWS_PER_MONTH = 5
export const MIN_REVIEWS_PER_WINDOW = 10

export function basisLabel(key) {
  return BASIS[key]?.label ?? key
}
