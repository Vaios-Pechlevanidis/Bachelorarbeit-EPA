# Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
# Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
# (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
# nach dem Annotationsprotokoll (Abschnitt 3.6.1)

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from services.evidence_sources import SOURCE_EQS, eqs_search_companies, throttle  # noqa: E402


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Einmalige Suche der EQS-companyUUID zu einem Firmennamen (Inkrement 4, Schritt 5).", formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("names", nargs="+", help="Suchwörter, z. B. Firmenname ohne Rechtsform")
    args = parser.parse_args(argv)
    for name in args.names:
        throttle(SOURCE_EQS)
        try:
            hits = eqs_search_companies(name)
        except Exception as exc:  # noqa: BLE001
            print(f"{name}: Suche fehlgeschlagen ({type(exc).__name__}: {exc})")
            continue
        print(f"{name}: {len(hits)} Treffer")
        for h in hits:
            print(f"  {h['company_name']}  uuid={h['uuid']}  isin={h['isin']}  land={h['country']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
