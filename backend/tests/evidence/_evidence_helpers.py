# Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
# Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
# (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
# nach dem Annotationsprotokoll (Abschnitt 3.6.1)

from datetime import datetime
from email.utils import format_datetime


def rss(entries):
    items = []
    for title, url, day, publisher in entries:
        pub = format_datetime(datetime.fromisoformat(day + "T10:00:00+00:00"))
        items.append(f"<item><title>{title} - {publisher}</title><link>{url}</link><pubDate>{pub}</pubDate>"
                     f"<source url=\"https://{publisher.lower()}.example\">{publisher}</source></item>")
    return ("<?xml version=\"1.0\"?><rss version=\"2.0\"><channel><title>t</title><language>de</language>"
            + "".join(items) + "</channel></rss>").encode("utf-8")


class FakeRss:
    def __init__(self, by_month=None, fail=()):
        self.by_month = by_month or {}
        self.fail = set(fail)
        self.queries = []

    def __call__(self, query):
        self.queries.append(query)
        month = query.split("after:")[1][:7]
        if month in self.fail:
            raise OSError("Netz weg")
        return rss(self.by_month.get(month, []))
