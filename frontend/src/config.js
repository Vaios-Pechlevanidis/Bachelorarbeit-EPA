// Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
// Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
// (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
// nach dem Annotationsprotokoll (Abschnitt 3.6.1)

export const API_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000") + "/api";

export const SHOW_FINANCE_EXTRAS = !["false", "0"].includes(
  String(import.meta.env.VITE_SHOW_FINANCE_EXTRAS ?? "").trim().toLowerCase(),
);

export const SHOW_FORECAST = !["false", "0"].includes(
  String(import.meta.env.VITE_SHOW_FORECAST ?? "").trim().toLowerCase(),
);

export const SHOW_OUTLIER_MONTHS = !["false", "0"].includes(
  String(import.meta.env.VITE_SHOW_OUTLIER_MONTHS ?? "").trim().toLowerCase(),
);

export const OUTLIER_UNVALIDATED_NOTE = "Ungeprüft: in der Simulation etwa so häufig wie bei reinem Zufall";
