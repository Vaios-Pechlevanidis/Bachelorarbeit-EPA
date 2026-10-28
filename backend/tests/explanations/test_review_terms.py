# Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
# Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
# (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
# nach dem Annotationsprotokoll (Abschnitt 3.6.1)

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

import services.review_terms as rt  # noqa: E402


def _rows(n, text, start_id=1, field="schlecht_am_arbeitgeber_finde_ich"):
    return [{"id": start_id + i, "datum": "2023-01-15", field: text} for i in range(n)]


class TestTokens:

    def test_lowercase_umlauts_and_short_words(self):
        assert rt.tokens("Kündigungen 2024: Büro zu, AG weg.") == ["kündigungen", "büro"]

    def test_stopwords_and_review_words_removed(self):
        assert rt.tokens("Der Arbeitgeber ist sehr gut und the team is nice, the strike is over") == ["strike"]

    def test_empty_and_non_string(self):
        assert rt.tokens("") == [] and rt.tokens(None) == [] and rt.tokens(42) == []

    def test_sharp_s_is_kept(self):
        assert rt.tokens("Außenstelle geschlossen") == ["außenstelle", "geschlossen"]

    def test_review_terms_over_text_fields_with_html(self):
        row = {"titel": "Stellenabbau angekündigt", "gut_am_arbeitgeber_finde_ich": "Homeoffice<br/>Homeoffice",
               "schlecht_am_arbeitgeber_finde_ich": None, "jobbeschreibung": "Werkstudent Vertrieb", "status": "Angestellt"}
        assert rt.review_terms(row) == {"stellenabbau", "angekündigt", "homeoffice"}
        assert rt.review_terms(row, exclude={"homeoffice"}) == {"stellenabbau", "angekündigt"}
        assert rt.review_terms(row, source="candidates") == {"stellenabbau", "angekündigt"}, "Bewerbende: Vorschläge und Titel"

    def test_company_prefix_excluded(self):
        row = {"titel": "Die deutschen Standorte der Telekoms", "gut_am_arbeitgeber_finde_ich": ""}
        assert rt.review_terms(row, exclude=rt.company_terms("Telekom", '"Deutsche Telekom"')) == {"standorte"}


class TestCompanyTerms:

    def test_name_search_term_and_joined_forms(self):
        assert rt.company_terms("E.ON SE", '"E.ON" OR Eon') == {"eon"}
        terms = rt.company_terms("Universität Duisburg-Essen", '"Universität Duisburg-Essen" OR "Uni Duisburg-Essen"')
        assert terms == {"universität", "duisburg", "essen", "duisburgessen", "uni"}

    def test_empty(self):
        assert rt.company_terms(None) == set() and rt.company_terms("", "") == set()


class TestDistinctiveTerms:

    def test_term_only_after(self):
        before = _rows(10, "Alles ruhig im Büro")
        after = _rows(4, "Der Stellenabbau macht Angst", start_id=100) + _rows(6, "Alles ruhig im Büro", start_id=200)
        terms = rt.distinctive_terms(before, after)
        assert [t["term"] for t in terms] == ["angst", "stellenabbau"]
        top = terms[1]
        assert (top["before"], top["after"], top["n_before"], top["n_after"]) == (0, 4, 10, 10)
        assert top["after_share"] == 0.4 and top["before_share"] == 0.0 and top["ratio"] is None

    def test_minimum_reviews_after(self):
        after = _rows(2, "Stellenabbau droht", start_id=100) + _rows(8, "Alles ruhig", start_id=200)
        assert rt.distinctive_terms(_rows(10, "Alles ruhig"), after) == []

    def test_share_ratio_with_different_window_sizes(self):
        before = _rows(2, "Die Umstrukturierung läuft") + _rows(18, "Alles ruhig", start_id=50)
        after = _rows(3, "Die Umstrukturierung läuft", start_id=100) + _rows(7, "Alles ruhig", start_id=200)
        terms = rt.distinctive_terms(before, after)
        assert [t["term"] for t in terms] == ["läuft", "umstrukturierung"]
        assert all(t["ratio"] == 3.0 and t["before"] == 2 and t["after"] == 3 for t in terms)

    def test_equal_shares_not_distinctive(self):
        before = _rows(5, "Streik im Werk") + _rows(5, "Alles ruhig", start_id=50)
        after = _rows(5, "Streik im Werk", start_id=100) + _rows(5, "Alles ruhig", start_id=200)
        assert rt.distinctive_terms(before, after) == []

    def test_sorted_by_share_shift_and_capped(self):
        after = (_rows(6, "Kündigung", start_id=100) + _rows(4, "Streik", start_id=200)
                 + _rows(4, "Abfindung", start_id=300) + _rows(3, "Umzug", start_id=400))
        terms = rt.distinctive_terms(_rows(10, "Alles ruhig"), after)
        assert [t["term"] for t in terms] == ["kündigung", "abfindung", "streik", "umzug"]
        assert [t["term"] for t in rt.distinctive_terms(_rows(10, "Alles ruhig"), after, max_terms=2)] == ["kündigung", "abfindung"]

    def test_company_name_and_stopwords_excluded(self):
        after = _rows(10, "Bei Beispielwerk ist der Chef neu", start_id=100)
        terms = rt.distinctive_terms(_rows(10, "Alles ruhig"), after, exclude=rt.company_terms("Beispielwerk GmbH"))
        assert [t["term"] for t in terms] == ["chef"]

    def test_small_basis_gives_no_terms(self):
        after = _rows(9, "Streik im Werk", start_id=100)
        assert rt.distinctive_terms(_rows(10, "Alles ruhig"), after) == []
        assert rt.distinctive_terms(_rows(9, "Alles ruhig"), _rows(10, "Streik im Werk", start_id=100)) == []
        assert rt.distinctive_terms(_rows(10, "Alles ruhig"), _rows(10, "Streik im Werk", start_id=100))

    def test_minimum_share_after(self):
        quiet = _rows(10, "Alles ruhig")
        assert rt.distinctive_terms(quiet, _rows(3, "Streik", start_id=100) + _rows(197, "Alles ruhig", start_id=200)) == []
        terms = rt.distinctive_terms(quiet, _rows(6, "Streik", start_id=100) + _rows(194, "Alles ruhig", start_id=200))
        assert [t["term"] for t in terms] == ["streik"]

    def test_empty_windows(self):
        assert rt.distinctive_terms([], []) == []
        assert rt.distinctive_terms([], _rows(12, "Streik im Werk")) == [] and rt.distinctive_terms(_rows(12, "Streik"), []) == []

    def test_each_review_counts_once(self):
        after = _rows(3, "Streik Streik Streik", start_id=100) + _rows(7, "Alles ruhig", start_id=200)
        assert rt.distinctive_terms(_rows(10, "Alles ruhig"), after)[0]["after"] == 3


class TestMatchTerms:

    TERMS = [{"term": "stellenabbau", "after": 5}, {"term": "entlassung", "after": 4}, {"term": "neu", "after": 3},
             {"term": "büro", "after": 3}]

    def test_exact_and_prefix_matches(self):
        matched = rt.match_terms("Konzern plant Stellenabbauprogramm und Entlassungen, Büro neuer", self.TERMS)
        assert [(m["term"], m["word"]) for m in matched] == [
            ("stellenabbau", "stellenabbauprogramm"), ("entlassung", "entlassungen"), ("büro", "büro")]

    def test_short_term_does_not_match_prefix(self):
        assert rt.match_terms("Neuer Standort", [{"term": "neu"}]) == []
        assert [m["term"] for m in rt.match_terms("Alles neu", [{"term": "neu"}])] == ["neu"]

    def test_title_word_as_prefix_of_term(self):
        assert [m["term"] for m in rt.match_terms("Kündigung angekündigt", [{"term": "kündigungen"}])] == ["kündigungen"]

    @pytest.mark.parametrize("title", ["", None, "   ", "AG SE"])
    def test_empty_title(self, title):
        assert rt.match_terms(title, self.TERMS) == []

    def test_no_terms(self):
        assert rt.match_terms("Stellenabbau", []) == []
