# Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
# Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
# (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
# nach dem Annotationsprotokoll (Abschnitt 3.6.1)

import pytest

import services.explanation_service as es
from models.sentiment_analyzer import SentimentAnalyzer

GEHALT = "Gehalt & Sozialleistungen"
KOMM = "Kommunikation"
WLB = "Work-Life Balance"


def _rows(n, *, start_id, text="Alles in Ordnung hier.", rating=3.0, day="2023-01-15", status="Angestellt"):
    return [
        {
            "id": start_id + i,
            "datum": day,
            "durchschnittsbewertung": rating,
            "status": status,
            "titel": "Titel",
            "gut_am_arbeitgeber_finde_ich": text,
            "schlecht_am_arbeitgeber_finde_ich": "",
            "verbesserungsvorschlaege": "",
        }
        for i in range(n)
    ]


class StubAnalyzer:
    mode = "lexicon"

    def __init__(self, sentiment="positive", polarity=0.5):
        self.calls = []
        self.sentiment, self.polarity = sentiment, polarity

    def analyze_sentiment(self, text, star_rating=None):
        self.calls.append((text, star_rating))
        return {"sentiment": self.sentiment, "polarity": self.polarity}


@pytest.fixture(autouse=True)
def _empty_cache():
    es.set_sentiment_analyzer(None)
    yield
    es.set_sentiment_analyzer(None)


def _topic(result, name):
    return next(t for t in result["topics"] if t["topic"] == name)


class TestComparisonWindows:

    def test_default_six_months(self):
        w = es.comparison_windows({"date": "2023-01", "before_from": "2020-01", "after_to": "2025-12"})
        assert w["window_months"] == 6
        assert (w["before"]["from"], w["before"]["to"], w["before"]["start"], w["before"]["end"]) == ("2022-07", "2022-12", "2022-07-01", "2022-12-31")
        assert (w["after"]["from"], w["after"]["to"], w["after"]["start"], w["after"]["end"]) == ("2023-01", "2023-06", "2023-01-01", "2023-06-30")
        assert w["before"]["months"] == w["after"]["months"] == 6

    def test_clamped_by_neighbouring_segments(self):
        w = es.comparison_windows({"date": "2023-01", "before_from": "2022-10", "after_to": "2023-02"})
        assert (w["before"]["from"], w["before"]["to"], w["before"]["months"]) == ("2022-10", "2022-12", 3)
        assert (w["after"]["from"], w["after"]["to"], w["after"]["months"]) == ("2023-01", "2023-02", 2)

    def test_window_months_and_leap_year(self):
        w = es.comparison_windows({"date": "2024-03", "before_from": "2020-01", "after_to": "2025-01"}, window_months=1)
        assert w["before"]["end"] == "2024-02-29" and w["after"]["end"] == "2024-03-31"

    def test_invalid_window_months(self):
        with pytest.raises(ValueError):
            es.comparison_windows({"date": "2023-01"}, window_months=0)

    def test_split_rows_by_window(self):
        w = es.comparison_windows({"date": "2023-01", "before_from": "2020-01", "after_to": "2025-12"})
        rows = [{"datum": "2022-06-30"}, {"datum": "2022-07-01T00:00:00+00:00"}, {"datum": "2023-01-01"},
                {"datum": "2023-06-30"}, {"datum": "2023-07-01"}, {"datum": None}]
        split = es.split_rows_by_window(rows, w)
        assert [r["datum"] for r in split["before"]] == ["2022-07-01T00:00:00+00:00"]
        assert [r["datum"] for r in split["after"]] == ["2023-01-01", "2023-06-30"]


class TestShares:

    @pytest.fixture
    def result(self):
        before = _rows(5, start_id=1, text="Das Gehalt ist gut") + _rows(15, start_id=100)
        after = (_rows(2, start_id=200, text="Das Gehalt ist gut") + _rows(10, start_id=300, text="Die Kommunikation ist schlecht")
                 + _rows(8, start_id=400))
        return es.compare_windows(before, after, "employee", analyzer=SentimentAnalyzer(mode="lexicon"))

    def test_counts_and_mean_rating(self, result):
        assert result["before"]["n_reviews"] == 20 and result["after"]["n_reviews"] == 20
        assert result["before"]["mean_rating"] == 3.0 and result["rating_shift"] == 0.0

    def test_share_and_shift(self, result):
        g, k = _topic(result, GEHALT), _topic(result, KOMM)
        assert (g["before"]["mentions"], g["before"]["share"], g["after"]["share"]) == (5, 0.25, 0.1)
        assert g["share_shift_pp"] == pytest.approx(-15.0)
        assert (k["before"]["share"], k["after"]["share"], k["share_shift_pp"]) == (0.0, 0.5, 50.0)

    def test_sorted_by_magnitude(self, result):
        shifts = [abs(t["share_shift_pp"]) for t in result["topics"]]
        assert shifts == sorted(shifts, reverse=True)
        assert [t["topic"] for t in result["topics"][:2]] == [KOMM, GEHALT]
        assert len(result["topics"]) == 13

    def test_topic_sentiment(self, result):
        k = _topic(result, KOMM)
        assert k["before"]["sentiment"]["n"] == 0 and k["before"]["sentiment"]["mean_polarity"] is None
        assert k["after"]["sentiment"]["n"] == 10 and k["after"]["sentiment"]["negative"] == 1.0
        assert k["polarity_shift"] is None
        assert _topic(result, GEHALT)["after"]["sentiment"]["positive"] == 1.0

    def test_window_sentiment_shares_sum_to_one(self, result):
        s = result["after"]["sentiment"]
        assert s["positive"] + s["neutral"] + s["negative"] == pytest.approx(1.0)
        assert -1.0 <= s["mean_polarity"] <= 1.0

    def test_value_column(self):
        before = [{**r, "sternebewertung_kommunikation": 4.0} for r in _rows(10, start_id=1)]
        after = [{**r, "sternebewertung_kommunikation": 2.5} for r in _rows(10, start_id=50)]
        res = es.compare_windows(before, after, "employee", analyzer=StubAnalyzer(), value_column="sternebewertung_kommunikation")
        assert res["before"]["mean_value"] == 4.0 and res["value_shift"] == -1.5


class TestLowBasis:

    def test_small_window_marks_everything(self):
        res = es.compare_windows(_rows(9, start_id=1, text="Gehalt"), _rows(30, start_id=100, text="Gehalt"), "employee", analyzer=StubAnalyzer())
        assert res["low_basis"] is True
        assert all(t["low_basis"] for t in res["topics"])

    def test_few_mentions_mark_topic(self):
        before = _rows(2, start_id=1, text="Gehalt") + _rows(10, start_id=10)
        after = _rows(2, start_id=100, text="Gehalt") + _rows(3, start_id=110, text="Kommunikation") + _rows(10, start_id=120)
        res = es.compare_windows(before, after, "employee", analyzer=StubAnalyzer())
        assert res["low_basis"] is False
        assert _topic(res, GEHALT)["low_basis"] is True
        assert _topic(res, KOMM)["low_basis"] is True
        before += _rows(1, start_id=50, text="Gehalt")
        res = es.compare_windows(before, after, "employee", analyzer=StubAnalyzer())
        assert _topic(res, GEHALT)["low_basis"] is False
        assert res["low_basis_rule"] == {"min_reviews_per_window": 10, "min_mentions_per_topic": 5}

    def test_empty_window(self):
        res = es.compare_windows([], _rows(12, start_id=1, text="Gehalt"), "employee", analyzer=StubAnalyzer())
        g = _topic(res, GEHALT)
        assert g["before"]["share"] is None and g["share_shift_pp"] is None and res["low_basis"] is True


class TestSentiment:

    def test_sample_newest_with_text(self):
        before = [
            *_rows(1, start_id=1, text="alt", day="2022-01-01"),
            *_rows(1, start_id=2, text="neu", day="2022-03-01"),
            *_rows(1, start_id=3, text="mittel", day="2022-02-01"),
            *_rows(2, start_id=4, text="", day="2022-04-01"),
        ]
        stub = StubAnalyzer()
        res = es.compare_windows(before, [], "employee", analyzer=stub, sample_limit=2)
        assert res["sentiment_sample"]["limit"] == 2
        assert res["sentiment_sample"]["before"] == {"with_text": 3, "analyzed": 2, "limited": True}
        assert res["sentiment_sample"]["after"] == {"with_text": 0, "analyzed": 0, "limited": False}
        assert [t for t, _ in stub.calls] == ["neu", "mittel"]
        assert res["before"]["sentiment"]["n"] == 2

    def test_counts_reviews_without_text_per_window(self):
        before = [*_rows(3, start_id=1, text="Gehalt passt"), *_rows(2, start_id=10, text="")]
        after = _rows(4, start_id=20, text="-")
        res = es.compare_windows(before, after, "employee", analyzer=StubAnalyzer())
        assert res["before"]["n_reviews"] == 5
        assert (res["before"]["n_with_text"], res["before"]["n_without_text"]) == (3, 2)
        assert (res["after"]["n_with_text"], res["after"]["n_without_text"]) == (0, 4)
        assert res["after"]["sentiment"]["n"] == 0

    def test_star_rating_is_passed_as_hint(self):
        stub = StubAnalyzer()
        es.compare_windows(_rows(1, start_id=1, rating=1.5), [], "employee", analyzer=stub)
        assert stub.calls[0][1] == 1.5

    def test_default_limit_is_300(self):
        stub = StubAnalyzer()
        res = es.compare_windows(_rows(301, start_id=1), [], "employee", analyzer=stub)
        assert len(stub.calls) == 300 and res["sentiment_sample"]["before"]["limited"] is True

    def test_results_are_cached_per_review_id(self):
        stub = StubAnalyzer()
        rows = _rows(12, start_id=1)
        es.compare_windows(rows, rows, "employee", analyzer=stub)
        assert len(stub.calls) == 12
        es.compare_windows(rows, [], "employee", analyzer=stub)
        assert len(stub.calls) == 12

    def test_cache_is_per_source(self):
        stub = StubAnalyzer()
        rows = _rows(3, start_id=1)
        es.compare_windows(rows, [], "employee", analyzer=stub)
        es.compare_windows([{**r, "stellenbeschreibung": "Text"} for r in rows], [], "candidates", analyzer=stub)
        assert len(stub.calls) == 6

    def test_mode_lexicon(self):
        res = es.compare_windows(_rows(10, start_id=1), [], "employee", analyzer=SentimentAnalyzer(mode="lexicon"))
        assert res["sentiment_mode"] == "lexicon"

    def test_mode_transformer_only_when_model_loaded(self):
        class NoModel(StubAnalyzer):
            mode = "transformer"
            _transformer_available = False

        class WithModel(StubAnalyzer):
            mode = "transformer"
            _transformer_available = True

        assert es.sentiment_mode(NoModel()) == "lexicon"
        assert es.sentiment_mode(WithModel()) == "transformer"

    def test_one_analyzer_per_process(self):
        es.set_sentiment_analyzer(StubAnalyzer())
        assert es.get_sentiment_analyzer() is es.get_sentiment_analyzer()


def test_parse_anomaly_id():
    assert es.parse_anomaly_id("employee:durchschnittsbewertung:2023-01") == {
        "source": "employee", "dimension": "durchschnittsbewertung", "date": "2023-01",
    }
    assert es.parse_anomaly_id("quatsch") is None and es.parse_anomaly_id("a::b") is None
