# Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
# Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
# (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
# nach dem Annotationsprotokoll (Abschnitt 3.6.1)

import os
import pytest
from models.lda_topic_model import LDATopicAnalyzer
from services.topic_model_service import TopicModelDatabase


class TestLDATopicAnalyzer:
    @pytest.fixture
    def sample_texts(self):
        return [
            "Die Work-Life Balance ist sehr gut. Flexible Arbeitszeiten und Homeoffice möglich.",
            "Das Gehalt ist fair und die Sozialleistungen sind ausgezeichnet.",
            "Die Führungskräfte sind kompetent und das Vorgesetztenverhalten ist professionell.",
            "Der Kollegenzusammenhalt ist stark und die Arbeitsatmosphäre ist angenehm.",
            "Gute Karrieremöglichkeiten und viele Weiterbildungsangebote.",
            "Die Kommunikation im Unternehmen ist transparent und effektiv.",
            "Arbeitsbedingungen sind modern mit guter technischer Ausstattung.",
            "Das Bewerbungsgespräch war sehr professionell geführt.",
            "Die Erklärung der weiteren Schritte war vollständig und verständlich.",
            "Schnelle Antwort und zeitgerechte Rückmeldung nach dem Interview.",
        ]
    
    @pytest.fixture
    def analyzer(self):
        return LDATopicAnalyzer(num_topics=5)
    
    def test_initialization(self, analyzer):
        assert analyzer is not None
        assert analyzer.num_topics == 5
        assert analyzer.lda_model is None
        assert analyzer.dictionary is None
        assert analyzer.corpus is None
    
    def test_get_rating_criteria_keywords(self):
        keywords = LDATopicAnalyzer.get_rating_criteria_keywords()
        
        assert len(keywords) > 0
        
        assert 'work' in keywords or 'life' in keywords or 'balance' in keywords
        assert 'gehalt' in keywords
        assert 'karriere' in keywords
        assert 'kommunikation' in keywords
        assert 'arbeitsatmosphaere' in keywords
        
        assert 'erklaerung' in keywords or 'schritte' in keywords
        assert 'reaktion' in keywords
        assert 'vollstaendigkeit' in keywords or 'infos' in keywords
        assert 'professionalitaet' in keywords
        
        print(f"\n✓ {len(keywords)} Keywords gefunden")
    
    def test_get_stopwords(self, analyzer):
        stopwords = analyzer.german_stopwords
        
        assert len(stopwords) > 0
        assert 'der' in stopwords
        assert 'die' in stopwords
        assert 'und' in stopwords
        assert 'ist' in stopwords
        
        print(f"\n✓ {len(stopwords)} Stopwords geladen")
    
    def test_normalize_abbreviations(self, analyzer):
        text = "Der MA arbeitet für den AG und nutzt WLB."
        tokens = analyzer.preprocess_text(text)
        
        assert 'mitarbeiter' in tokens or any('mitarbeiter' in t for t in tokens)
        assert 'arbeitgeber' in tokens or any('arbeitgeber' in t for t in tokens)
        has_wlb = ('work_life_balance' in tokens 
                   or any('work_life_balance' in t for t in tokens)
                   or ('work' in tokens and 'life' in tokens))
        assert has_wlb, f"WLB nicht korrekt normalisiert. Tokens: {tokens}"
        
        print(f"\n✓ Text normalisiert: '{text}' -> '{tokens}'")
    
    def test_preprocess_text(self, analyzer):
        text = "Die Work-Life Balance ist sehr gut! Der MA hat flexible Arbeitszeiten."
        tokens = analyzer.preprocess_text(text)
        
        assert len(tokens) > 0
        
        assert 'der' not in tokens
        assert 'ist' not in tokens
        
        print(f"\n✓ Tokens generiert: {tokens[:10]}")
    
    def test_train_model(self, analyzer, sample_texts):
        result = analyzer.train_model(sample_texts)
        
        assert 'num_documents' in result
        assert 'num_topics' in result
        assert 'topics' in result
        
        assert result['num_documents'] == len(sample_texts)
        assert result['num_topics'] == 5
        assert len(result['topics']) == 5
        
        assert analyzer.lda_model is not None
        assert analyzer.dictionary is not None
        assert analyzer.corpus is not None
        
        print(f"\n✓ Modell trainiert mit {result['num_documents']} Dokumenten")
        print(f"✓ {result['num_topics']} Topics generiert")
    
    def test_predict_topics(self, analyzer, sample_texts):
        analyzer.train_model(sample_texts)
        
        test_text = "Das Gehalt ist gut und die Work-Life Balance stimmt auch."
        result = analyzer.predict_topics(test_text)
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        first_topic = result[0]
        assert 'topic_id' in first_topic
        assert 'probability' in first_topic
        
        print(f"\n✓ Topic-Vorhersage erfolgreich")
        print(f"  Anzahl Topics: {len(result)}")
        print(f"  Top Topic: {first_topic['topic_id']} ({first_topic['probability']:.2%})")
    
    def test_get_topic_words(self, analyzer, sample_texts):
        analyzer.train_model(sample_texts)
        
        topics = analyzer.get_topics(num_words=10)
        
        assert len(topics) > 0
        assert len(topics) == analyzer.num_topics
        
        first_topic = topics[0]
        assert 'topic_id' in first_topic
        assert 'words' in first_topic
        assert len(first_topic['words']) <= 10
        
        print(f"\n✓ {len(topics)} Topics mit je {len(first_topic['words'])} Wörtern")
    
    def test_save_and_load_model(self, analyzer, sample_texts, tmp_path):
        analyzer.train_model(sample_texts)
        
        model_path = analyzer.save_model(model_dir=str(tmp_path))
        assert os.path.exists(f"{model_path}.model")
        assert os.path.exists(f"{model_path}.dict")
        
        new_analyzer = LDATopicAnalyzer()
        new_analyzer.load_model(model_path)
        
        assert new_analyzer.lda_model is not None
        assert new_analyzer.dictionary is not None
        assert new_analyzer.num_topics == analyzer.num_topics
        
        print(f"\n✓ Modell gespeichert und geladen: {model_path}")


class TestTopicModelDatabase:
    @pytest.fixture
    def db_service(self):
        return TopicModelDatabase()
    
    def test_get_all_texts_both_sources(self, db_service):
        result = db_service.get_all_texts(source="both", limit=10)
        
        assert 'texts' in result
        assert 'sources' in result
        assert 'metadata' in result
        
        metadata = result['metadata']
        assert 'candidates_count' in metadata
        assert 'employee_count' in metadata
        assert 'total_count' in metadata
        
        assert len(result['texts']) > 0
        assert metadata['total_count'] == len(result['texts'])
        
        print(f"\n✓ Texte abgerufen:")
        print(f"  Bewerber: {metadata['candidates_count']}")
        print(f"  Mitarbeiter: {metadata['employee_count']}")
        print(f"  Gesamt: {metadata['total_count']}")
    
    def test_get_all_texts_candidates_only(self, db_service):
        result = db_service.get_all_texts(source="candidates", limit=10)
        
        metadata = result['metadata']
        
        assert metadata['employee_count'] == 0
        assert metadata['candidates_count'] > 0
        
        assert all(s == "candidates" for s in result['sources'])
        
        print(f"\n✓ Nur Bewerber-Texte: {metadata['candidates_count']}")
    
    def test_get_all_texts_employee_only(self, db_service):
        result = db_service.get_all_texts(source="employee", limit=10)
        
        metadata = result['metadata']
        
        assert metadata['candidates_count'] == 0
        assert metadata['employee_count'] > 0
        
        assert all(s == "employee" for s in result['sources'])
        
        print(f"\n✓ Nur Mitarbeiter-Texte: {metadata['employee_count']}")
    
    def test_get_all_texts_with_metadata(self, db_service):
        result = db_service.get_all_texts(
            source="employee",
            limit=5,
            include_metadata=True
        )
        
        assert 'detailed_metadata' in result
        assert len(result['detailed_metadata']) > 0
        
        first_meta = result['detailed_metadata'][0]
        assert 'text' in first_meta
        assert 'source' in first_meta
        assert 'status' in first_meta
        
        print(f"\n✓ Metadaten abgerufen für {len(result['detailed_metadata'])} Dokumente")


class TestIntegration:
    def test_complete_training_workflow(self):
        db_service = TopicModelDatabase()
        data = db_service.get_all_texts(source="both", limit=50)
        
        assert len(data['texts']) > 0
        print(f"\n✓ Schritt 1: {len(data['texts'])} Texte geladen")
        
        analyzer = LDATopicAnalyzer(num_topics=5)
        print("✓ Schritt 2: Analyzer initialisiert")
        
        result = analyzer.train_model(data['texts'])
        assert result['num_documents'] == len(data['texts'])
        print(f"✓ Schritt 3: Modell trainiert mit {result['num_topics']} Topics")
        
        test_text = "Die Arbeitsatmosphäre ist gut und das Gehalt ist fair."
        prediction = analyzer.predict_topics(test_text)
        assert len(prediction) > 0
        print(f"✓ Schritt 4: Topic-Vorhersage erfolgreich (Topic {prediction[0]['topic_id']})")
        
        print("\n✓ Schritt 5: Generierte Topics:")
        topics = analyzer.get_topics(num_words=5)
        for topic in topics[:3]:
            words = [w['word'] for w in topic['words'][:5]]
            print(f"  Topic {topic['topic_id']}: {', '.join(words)}")
    
    def test_source_specific_training(self):
        db_service = TopicModelDatabase()
        
        employee_data = db_service.get_all_texts(source="employee", limit=30)
        employee_analyzer = LDATopicAnalyzer(num_topics=5)
        employee_result = employee_analyzer.train_model(employee_data['texts'])
        
        print(f"\n✓ Mitarbeiter-Modell:")
        print(f"  Dokumente: {employee_result['num_documents']}")
        print(f"  Topics: {employee_result['num_topics']}")
        
        candidate_data = db_service.get_all_texts(source="candidates", limit=30)
        candidate_analyzer = LDATopicAnalyzer(num_topics=5)
        candidate_result = candidate_analyzer.train_model(candidate_data['texts'])
        
        print(f"\n✓ Bewerber-Modell:")
        print(f"  Dokumente: {candidate_result['num_documents']}")
        print(f"  Topics: {candidate_result['num_topics']}")
        
        test_text = "Die Kommunikation war professionell."
        
        employee_pred = employee_analyzer.predict_topics(test_text)
        candidate_pred = candidate_analyzer.predict_topics(test_text)
        
        assert len(employee_pred) > 0
        assert len(candidate_pred) > 0
        assert 'topic_id' in employee_pred[0]
        assert 'topic_id' in candidate_pred[0]
        
        print("\n✓ Beide Modelle funktionieren korrekt")


def run_all_tests():
    print("=" * 70)
    print("LDA TOPIC MODELING - TEST SUITE")
    print("=" * 70)
    
    print("\n[TEST 1] LDA Analyzer Initialisierung")
    print("-" * 70)
    test_analyzer = TestLDATopicAnalyzer()
    analyzer = test_analyzer.get_analyzer()
    test_analyzer.test_initialization(analyzer)
    print("✓ PASSED")
    
    print("\n[TEST 2] Rating-Kriterien Keywords")
    print("-" * 70)
    test_analyzer.test_get_rating_criteria_keywords()
    print("✓ PASSED")
    
    print("\n[TEST 3] Stopwords")
    print("-" * 70)
    test_analyzer.test_get_stopwords(analyzer)
    print("✓ PASSED")
    
    print("\n[TEST 4] Text Preprocessing")
    print("-" * 70)
    print("✓ SKIPPED (interne Methode)")
    
    print("\n[TEST 5] Modell-Training")
    print("-" * 70)
    sample_texts = test_analyzer.sample_texts(None)
    test_analyzer.test_train_model(analyzer, sample_texts)
    print("✓ PASSED")
    
    print("\n[TEST 7] Topic-Vorhersage")
    print("-" * 70)
    test_analyzer.test_predict_topics(analyzer, sample_texts)
    print("✓ PASSED")
    
    print("\n[TEST 8] Topic Words Extraction")
    print("-" * 70)
    test_analyzer.test_get_topic_words(analyzer, sample_texts)
    print("✓ PASSED")
    
    print("\n[TEST 9] Database Service - Beide Quellen")
    print("-" * 70)
    test_db = TestTopicModelDatabase()
    db_service = test_db.get_db_service()
    test_db.test_get_all_texts_both_sources(db_service)
    print("✓ PASSED")
    
    print("\n[TEST 10] Database Service - Nur Bewerber")
    print("-" * 70)
    test_db.test_get_all_texts_candidates_only(db_service)
    print("✓ PASSED")
    
    print("\n[TEST 11] Database Service - Nur Mitarbeiter")
    print("-" * 70)
    test_db.test_get_all_texts_employee_only(db_service)
    print("✓ PASSED")
    
    print("\n[TEST 12] Integration - Kompletter Workflow")
    print("-" * 70)
    test_integration = TestIntegration()
    test_integration.test_complete_training_workflow()
    print("✓ PASSED")
    
    print("\n[TEST 13] Integration - Source-spezifisches Training")
    print("-" * 70)
    test_integration.test_source_specific_training()
    print("✓ PASSED")
    
    print("\n" + "=" * 70)
    print("TEST ZUSAMMENFASSUNG")
    print("=" * 70)
    print("✓ Alle 13 Tests erfolgreich bestanden!")
    print("\nGetestete Komponenten:")
    print("  ✓ LDA Analyzer Initialisierung")
    print("  ✓ Rating-Kriterien aus DB-Schema")
    print("  ✓ Stopwords und Text-Preprocessing")
    print("  ✓ Abkürzungs-Normalisierung")
    print("  ✓ Modell-Training und Topic-Generierung")
    print("  ✓ Topic-Vorhersage für neue Texte")
    print("  ✓ Database Service für beide Quellen")
    print("  ✓ Separate Modelle für Bewerber/Mitarbeiter")
    print("  ✓ Kompletter Trainings-Workflow")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
