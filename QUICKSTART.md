# Quickstart

> **Hinweis:** Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt. Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume nach dem Annotationsprotokoll (Abschnitt 3.6.1)

> Vollständige Anleitung: [INSTALLATION.md](INSTALLATION.md)

---

## Voraussetzungen installieren

```bash
# uv (Python-Paketmanager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Node.js 20+ prüfen
node --version   # muss v20+ sein → sonst: https://nodejs.org/
```

---

## 1 — Repository klonen

```bash
git clone https://github.com/Vaios-Pechlevanidis/EPA-Bachelorarbeit.git
cd EPA-Bachelorarbeit
```

---

## 2 — Abhängigkeiten installieren

```bash
# Backend
cd backend && uv sync && cd ..

# Frontend
cd frontend && npm install && cd ..
```

---

## 3 — Umgebungsvariablen setzen

```bash
cp backend/.env.example backend/.env
```

Öffne `backend/.env` und trage ein:

```env
SUPABASE_URL=https://dein-projekt.supabase.co
SUPABASE_SERVICE_KEY=dein-service-role-key
SUPABASE_KEY=dein-anon-key
```

> Zugangsdaten: [supabase.com](https://supabase.com) → Projekt → **Settings → API**. Das Backend nutzt `SUPABASE_SERVICE_KEY` (Schreibzugriff) und fällt auf `SUPABASE_KEY` zurück.
>
> Ohne Zugangsdaten startet das Backend trotzdem: Es arbeitet dann mit einem Speicher im Arbeitsspeicher und drei erfundenen Unternehmen (Demo 1–3).

---

## 4 — Projekt starten

**Terminal 1 — Backend:**

```bash
cd backend
uv run uvicorn main:app --reload
```

**Terminal 2 — Frontend:**

```bash
cd frontend
npm run dev
```

| Dienst   | URL                          |
| -------- | ---------------------------- |
| Frontend | http://localhost:5173        |
| Backend  | http://localhost:8000        |
| API-Docs | http://localhost:8000/docs   |

---

## 5 — LDA-Modell trainieren (einmalig)

Das Backend muss laufen. Dann in einem neuen Terminal:

```bash
curl -X POST http://localhost:8000/api/topics/train \
  -H "Content-Type: application/json" \
  -d '{"source": "both", "num_topics": 5}'
```

---

## Schnellreferenz

```bash
cd backend && uv run uvicorn main:app --reload   # Backend starten
cd frontend && npm run dev                        # Frontend starten
cd backend && uv run pytest -q                    # Backend-Tests
cd frontend && npm test                           # Frontend-Tests
cd frontend && npm run lint                       # Codeprüfung Frontend
```

Die letzten Ergebnisse stehen in [docs/testergebnisse.md](docs/testergebnisse.md).

## Häufige Fehler

| Fehler | Lösung |
| ------ | ------ |
| `uv: command not found` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` dann Terminal neu starten |
| Port 8000 belegt | `lsof -ti:8000 \| xargs kill -9` |
| Nur Demo 1–3 sichtbar | `backend/.env` fehlt oder ist leer → Schritt 3 wiederholen |
| `ModuleNotFoundError` | `cd backend && uv sync` |
| Frontend-Pakete fehlen | `cd frontend && rm -rf node_modules && npm install` |
