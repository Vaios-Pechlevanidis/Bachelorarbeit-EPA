from gensim import corpora
from gensim.models import LdaModel, Phrases
from gensim.parsing.preprocessing import (
    preprocess_string,
    strip_punctuation,
    strip_numeric,
    remove_stopwords,
    strip_short,
    stem_text
)
from typing import List, Dict, Any, Tuple, Optional
import pickle
import os
from datetime import datetime
import re


class LDATopicAnalyzer:
    @staticmethod
    def get_rating_criteria_keywords() -> set:
        candidate_criteria = [
            'erklaerung_der_weiteren_schritte', 'zufriedenstellende_reaktion',
            'vollstaendigkeit_der_infos', 'zufriedenstellende_antworten',
            'angenehme_atmosphaere', 'professionalitaet_des_gespraechs',
            'wertschaetzende_behandlung', 'erwartbarkeit_des_prozesses',
            'zeitgerechte_zu_oder_absage', 'schnelle_antwort'
        ]
        
        employee_criteria = [
            'arbeitsatmosphaere', 'image', 'work_life_balance',
            'karriere_weiterbildung', 'gehalt_sozialleistungen',
            'kollegenzusammenhalt', 'umwelt_sozialbewusstsein',
            'vorgesetztenverhalten', 'kommunikation', 'interessante_aufgaben',
            'umgang_mit_aelteren_kollegen', 'arbeitsbedingungen',
            'gleichberechtigung'
        ]
        
        keywords = set()
        for criteria in candidate_criteria + employee_criteria:
            parts = criteria.split('_')
            keywords.update(parts)
            keywords.add(criteria)
            keywords.add(criteria.replace('_', ''))
        
        keywords = {k for k in keywords if len(k) > 3 and k not in {'oder', 'der', 'des', 'mit'}}
        
        return keywords
    
    def __init__(self, num_topics: int = 12, passes: int = 25, iterations: int = 600):
        self.num_topics = num_topics
        self.passes = passes
        self.iterations = iterations
        self.dictionary = None
        self.corpus = None
        self.lda_model = None
        self.documents = []
        self.bigram_model = None
        self.trigram_model = None
        
        self.employee_type_weights = {
            'Employee': 1.0,      
            'Manager': 1.0,       
            'Student': 1.0,       
            'Nicht-Employee': 1.0, 
            'default': 1.0        
        }
        
        self.document_metadata = []
        
        self.german_stopwords = set([
            'der', 'die', 'das', 'den', 'dem', 'des', 'ein', 'eine', 'eines', 'einem', 'einen',
            'ich', 'du', 'er', 'sie', 'es', 'wir', 'ihr', 'mich', 'mir', 'sich', 'uns', 'euch',
            'dieser', 'diese', 'dieses', 'jener', 'jene', 'jenes', 'welcher', 'welche', 'welches',
            'mein', 'dein', 'sein', 'unser', 'euer',
            
            'und', 'oder', 'aber', 'wenn', 'als', 'wie', 'bei', 'nach', 'von', 'zu', 'mit',
            'auf', 'für', 'an', 'am', 'im', 'um', 'bis', 'gegen', 'ohne', 'durch', 'über',
            'unter', 'während', 'wegen', 'trotz', 'seit', 'vor', 'hinter', 'neben',
            
            'ist', 'sind', 'war', 'waren', 'sein', 'haben', 'hat', 'hatte', 'hatten',
            'werden', 'wird', 'wurde', 'wurden', 'worden', 'gewesen', 'geworden',
            'können', 'kann', 'konnte', 'konnten', 'könnte', 'könnten',
            'müssen', 'muss', 'musste', 'mussten', 'müsste', 'müssten',
            'sollen', 'soll', 'sollte', 'sollten',
            'wollen', 'will', 'wollte', 'wollten', 'würde', 'würden',
            'dürfen', 'darf', 'durfte', 'durften',
            'mögen', 'mag', 'mochte', 'mochten', 'möchte', 'möchten',
            
            'nicht', 'kein', 'keine', 'keines', 'keinem', 'keinen', 'nie', 'niemals', 'nichts',
            'alle', 'alles', 'allem', 'allen', 'jeder', 'jede', 'jedes', 'jedem', 'jeden',
            'einige', 'einigen', 'manche', 'manchen', 'viele', 'vielen', 'wenige', 'wenigen',
            'mehrere', 'mehreren', 'etliche', 'etlichen',
            
            'nur', 'noch', 'auch', 'sehr', 'mehr', 'weniger', 'gut', 'schlecht', 'besser',
            'schlechter', 'beste', 'schlechteste', 'groß', 'klein', 'größer', 'kleiner',
            'neu', 'alt', 'jung', 'so', 'dann', 'dort', 'hier', 'da', 'heute', 'gestern',
            'morgen', 'immer', 'oft', 'manchmal', 'selten', 'ganz', 'halb', 'teil',
            
            'dass', 'ob', 'wer', 'was', 'wo', 'wann', 'warum', 'weshalb', 'wieso', 'wohin',
            'woher', 'womit', 'wofür', 'worüber', 'wodurch',
            
            'eben', 'halt', 'eigentlich', 'irgendwie', 'sozusagen', 'quasi', 'praktisch',
            'echt', 'wirklich', 'ziemlich', 'eher', 'etwa', 'ungefähr', 'circa',
            'bzw', 'usw', 'etc', 'inkl', 'ggf', 'evtl',
            
            'mal', 'schon', 'erst', 'nun', 'jetzt', 'gerade', 'bereits', 'bald',
            
            'gibt', 'geben', 'machen', 'macht', 'gemacht', 'tun', 'tut', 'getan',
            'lassen', 'lässt', 'ließ', 'gelassen', 'sagen', 'sagt', 'sagte', 'gesagt',
            'gehen', 'geht', 'ging', 'gegangen', 'kommen', 'kommt', 'kam', 'gekommen',
            'sehen', 'sieht', 'sah', 'gesehen', 'finden', 'findet', 'fand', 'gefunden',
            'denken', 'denkt', 'dachte', 'gedacht', 'wissen', 'weiß', 'wusste', 'gewusst',
            'nehmen', 'nimmt', 'nahm', 'genommen', 'geben', 'gibt', 'gab', 'gegeben',
            
            'liegen', 'stehen', 'sitzen', 'etwas', 'nichts', 'alles', 'manches',
            'beide', 'beides', 'anderen', 'andere', 'anderer', 'weiteren', 'weitere',
            'vieles', 'weniges', 'meisten', 'meist', 'zwar', 'doch', 'jedoch', 'dennoch',
        ])
        
        self.domain_stopwords = set([
            'gehen', 'kommen', 'sein', 'haben', 'werden', 'machen', 'sehen', 'lassen',
            'stehen', 'liegen', 'sitzen', 'laufen', 'fahren', 'fliegen', 'essen', 'trinken',
            
            'ding', 'dinge', 'sache', 'sachen', 'fall', 'fälle', 'mal', 'zeit', 'tag', 'tage',
            'jahr', 'jahre', 'monat', 'monate', 'woche', 'wochen', 'stunde', 'stunden',
            'minute', 'minuten', 'moment', 'momente',
            
            'art', 'weise', 'form', 'grund', 'gründe', 'zweck', 'ziel', 'ende', 'anfang',
            'mitte', 'teil', 'teile', 'seite', 'seiten', 'punkt', 'punkte',
            
            'mensch', 'menschen', 'person', 'personen', 'leute', 'mann', 'männer',
            'frau', 'frauen', 'kind', 'kinder', 'name', 'namen',
            
            'man', 'viel', 'viele', 'vielen', 'wenig', 'wenige', 'wenigen',
            'dabei', 'damit', 'dadurch', 'dafür', 'dagegen', 'darauf', 'darin',
            'oben', 'unten', 'innen', 'außen', 'vorne', 'hinten', 'links', 'rechts',
            'zur', 'zum', 'beim', 'vom', 'zur', 'ans', 'ins', 'durchs', 'fürs',
            'habe', 'hatte', 'gehabt', 'bin', 'bist', 'war', 'warst', 'gewesen',
            'einfach', 'einfache', 'einfachen', 'einfacher', 'einfaches',
            'nett', 'nette', 'netten', 'netter', 'nettes',
            'okay', 'ok', 'super', 'toll', 'prima', 'klasse',
            'leider', 'bestimmt', 'sicher', 'wahrscheinlich', 'vielleicht',
            'meine', 'meinen', 'meiner', 'meines', 'deine', 'deinen', 'seiner', 'ihrer',
            'zwischen', 'neuen', 'neue', 'neuer', 'neues', 'alten', 'alte', 'alter', 'altes',
            'sondern', 'anstatt', 'statt', 'anstelle',
            'fuer', 'ueber', 'durch', 'ohne', 'gegen', 'seit', 'waehrend',
            'einer', 'eines', 'einem', 'denen', 'dessen', 'deren',
            'student', 'studenten',
        ])
        
        self.all_stopwords = self.german_stopwords.union(self.domain_stopwords)
        
        rating_keywords = self.get_rating_criteria_keywords()
        
        self.work_related_keywords = set([
            'arbeitsatmosphäre', 'atmosphäre', 'betriebsklima', 'klima',
            'image', 'ruf', 'reputation', 'ansehen',
            'work_life_balance', 'worklifebalance', 'balance', 'work', 'life',
            'karriere', 'weiterbildung', 'entwicklung', 'aufstieg', 'aufstiegsmöglichkeiten',
            'gehalt', 'sozialleistungen', 'vergütung', 'bezahlung', 'lohn', 'entlohnung',
            'kollegenzusammenhalt', 'kollegen', 'zusammenhalt', 'team', 'teamwork',
            'umwelt', 'sozialbewusstsein', 'nachhaltigkeit', 'sozial',
            'vorgesetztenverhalten', 'vorgesetzter', 'vorgesetzte', 'führung', 'leitung', 'management',
            'kommunikation', 'information', 'austausch', 'feedback',
            'aufgaben', 'tätigkeiten', 'arbeit', 'arbeitsinhalt',
            'umgang', 'kollegen', 'älteren', 'aelteren',
            'arbeitsbedingungen', 'bedingungen', 'arbeitsumfeld', 'umfeld',
            'gleichberechtigung', 'fairness', 'gerechtigkeit', 'chancengleichheit',
            
            'schritte', 'prozess', 'ablauf', 'verfahren',
            'reaktion', 'rückmeldung', 'antwort', 'response',
            'vollständigkeit', 'vollstaendigkeit', 'informationen', 'infos',
            'antworten', 'erklärungen', 'erklaerungen',
            'atmosphäre', 'atmosphaere', 'stimmung',
            'professionalität', 'professionalitaet', 'professionell',
            'wertschätzung', 'wertschaetzung', 'respekt', 'behandlung',
            'erwartbarkeit', 'transparenz', 'klarheit',
            'zeitgerecht', 'pünktlich', 'puenktlich', 'zeitnah',
            'zusage', 'absage', 'rückmeldung', 'rueckmeldung',
            'schnell', 'schnelle', 'zügig', 'zuegig',
            
            'homeoffice', 'remote', 'mobil', 'flexibel', 'flexible', 'flexibilität',
            'arbeitszeit', 'arbeitszeiten', 'gleitzeit', 'teilzeit', 'vollzeit',
            'urlaub', 'freizeit', 'erholung', 'pause', 'pausen',
            'projekt', 'projekte', 'aufgabe', 'aufgaben', 'verantwortung',
            'weiterbildung', 'schulung', 'training', 'fortbildung',
            'gehalt', 'bonus', 'prämie', 'praemie', 'benefits',
            'kultur', 'unternehmenskultur', 'werte', 'vision',
            'hierarchie', 'struktur', 'organisation', 'firma', 'unternehmen',
            'bewerbung', 'interview', 'gespräch', 'gespraech', 'vorstellung',
            'mitarbeiter', 'arbeitnehmer', 'arbeitgeber', 'angestellte',
            'stelle', 'position', 'job', 'beschäftigung', 'anstellung',
        ])
        
        self.work_related_keywords.update(rating_keywords)
    
    def preprocess_text(self, text: str) -> List[str]:
        if not text or not isinstance(text, str):
            return []
        
        text = text.lower()
        
        text = text.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
        
        text = re.sub(r'\bma\b|\bm\.a\.\b', 'mitarbeiter', text)
        text = re.sub(r'\bag\b', 'arbeitgeber', text)
        text = re.sub(r'\ban\b', 'arbeitnehmer', text)
        text = re.sub(r'\bgf\b', 'geschaeftsfuehrung', text)
        text = re.sub(r'\bvl\b', 'vorgesetzter', text)
        text = re.sub(r'\bwlb\b', 'work_life_balance', text)
        text = re.sub(r'\bho\b', 'homeoffice', text)
        text = re.sub(r'\bhome.?office\b', 'homeoffice', text)
        
        text = re.sub(r'work.?life.?balance', 'work_life_balance', text)
        text = re.sub(r'arbeits.?atmosphaere|betriebsklima', 'arbeitsatmosphaere', text)
        text = re.sub(r'kollegenzusammenhalt|team.?work', 'teamzusammenhalt', text)
        text = re.sub(r'vorgesetztenverhalten|fuehrungskraft', 'fuehrungsverhalten', text)
        text = re.sub(r'gehalt.*sozialleistungen|verguetung', 'verguetung', text)
        text = re.sub(r'karriere.*weiterbildung|entwicklung', 'karriereentwicklung', text)
        text = re.sub(r'umwelt.*sozial|nachhaltigkeit', 'nachhaltigkeit', text)
        text = re.sub(r'arbeits.?bedingungen', 'arbeitsbedingungen', text)
        text = re.sub(r'umgang.*aelteren', 'umgang_aeltere', text)
        
        custom_filters = [
            strip_punctuation,
            strip_numeric,
            remove_stopwords,
            strip_short,
        ]
        
        tokens = preprocess_string(text, custom_filters)
        
        tokens = [
            token for token in tokens 
            if token not in self.all_stopwords or token in self.work_related_keywords
        ]
        
        tokens = [
            token for token in tokens 
            if len(token) >= 3 or token in self.work_related_keywords
        ]
        
        tokens = [token for token in tokens if re.search(r'[a-z]', token)]
        
        exclude_tokens = {'aus', 'amp', 'fast', 'abs', 'bzw', 'zzgl', 'inkl', 'ggf', 'evtl', 
                         'usw', 'etc', 'inkl', 'exkl', 'bzw', 'ggfs', 'bzw', 'uvm',
                         'fuer', 'ueber', 'durch', 'ohne', 'gegen', 'seit', 'waehrend',
                         'einer', 'eines', 'einem', 'denen', 'dessen', 'deren'}
        tokens = [
            token for token in tokens 
            if token not in exclude_tokens or token in self.work_related_keywords
        ]
        
        return tokens
    
    def get_employee_type_weight(self, status: Optional[str]) -> float:
        if not status:
            return self.employee_type_weights['default']
        
        status_str = str(status).strip().lower()
        
        numeric_mappings = {
            '0': 'Student',
            '0.0': 'Student',
            '1': 'Employee',
            '1.0': 'Employee',
            '2': 'Manager',
            '2.0': 'Manager',
            '3': 'Nicht-Employee',
            '3.0': 'Nicht-Employee',
        }
        
        if status_str in numeric_mappings:
            mapped_type = numeric_mappings[status_str]
            return self.employee_type_weights[mapped_type]
        
        if any(keyword in status_str for keyword in ['nicht-employee', 'nicht employee', 'nichtemployee', 'ex-employee', 'ex employee', 'ehemaliger', 'ehemalige']):
            return self.employee_type_weights['Nicht-Employee']
        
        if any(keyword in status_str for keyword in ['manager', 'führungskraft', 'fuehrungskraft', 'leitung']):
            return self.employee_type_weights['Manager']
        
        if any(keyword in status_str for keyword in ['student', 'studentin', 'praktikant', 'praktikantin']):
            return self.employee_type_weights['Student']
        
        if any(keyword in status_str for keyword in ['employee', 'angestellter', 'angestellte', 'mitarbeiter', 'mitarbeiterin']):
            return self.employee_type_weights['Employee']
        
        return self.employee_type_weights['default']
    
    def prepare_documents(self, texts: List[str], metadata: Optional[List[Dict[str, Any]]] = None) -> Tuple[corpora.Dictionary, List[List[Tuple[int, int]]]]:
        self.documents = [self.preprocess_text(text) for text in texts]
        
        if metadata:
            self.document_metadata = metadata
        else:
            self.document_metadata = [{'status': None} for _ in texts]
        
        filtered_docs = []
        filtered_metadata = []
        for i, doc in enumerate(self.documents):
            if doc:
                filtered_docs.append(doc)
                if i < len(self.document_metadata):
                    filtered_metadata.append(self.document_metadata[i])
                else:
                    filtered_metadata.append({'status': None})
        
        self.documents = filtered_docs
        self.document_metadata = filtered_metadata
        
        if not self.documents:
            raise ValueError("No valid documents found after preprocessing")
        
        bigram = Phrases(self.documents, min_count=3, threshold=10, delimiter='_')
        self.bigram_model = bigram
        
        bigram_docs = [bigram[doc] for doc in self.documents]
        
        trigram = Phrases(bigram_docs, min_count=2, threshold=10, delimiter='_')
        self.trigram_model = trigram
        
        self.documents = [trigram[bigram_doc] for bigram_doc in bigram_docs]
        
        self.dictionary = corpora.Dictionary(self.documents)
        
        self.dictionary.filter_extremes(no_below=2, no_above=0.6, keep_n=2000)
        
        self.corpus = []
        for i, doc in enumerate(self.documents):
            bow = self.dictionary.doc2bow(doc)
            
            if i < len(self.document_metadata):
                weight = self.get_employee_type_weight(self.document_metadata[i].get('status'))
                weighted_bow = [(word_id, int(freq * weight)) for word_id, freq in bow]
                self.corpus.append(weighted_bow)
            else:
                self.corpus.append(bow)
        
        return self.dictionary, self.corpus
    
    def train_model(self, texts: List[str], metadata: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        if not texts:
            raise ValueError("No texts provided for training")
        
        self.prepare_documents(texts, metadata)
        
        weight_stats = {}
        if self.document_metadata:
            for meta in self.document_metadata:
                status = meta.get('status', 'unknown')
                weight = self.get_employee_type_weight(status)
                if status not in weight_stats:
                    weight_stats[status] = {'count': 0, 'weight': weight}
                weight_stats[status]['count'] += 1
        
        self.lda_model = LdaModel(
            corpus=self.corpus,
            id2word=self.dictionary,
            num_topics=self.num_topics,
            random_state=42,
            passes=self.passes,
            iterations=self.iterations,
            per_word_topics=True,
            alpha='auto',
            eta='auto',
            minimum_probability=0.005,
            chunksize=100,
            update_every=1,
            eval_every=10
        )
        
        topics = self.get_topics()
        
        return {
            "status": "success",
            "num_topics": self.num_topics,
            "num_documents": len(texts),
            "vocabulary_size": len(self.dictionary),
            "topics": topics,
            "employee_type_weights": self.employee_type_weights,
            "weight_statistics": weight_stats,
            "trained_at": datetime.now().isoformat()
        }
    
    def get_topics(self, num_words: int = 10) -> List[Dict[str, Any]]:
        if not self.lda_model:
            raise ValueError("Model not trained yet")
        
        topics = []
        for topic_id in range(self.num_topics):
            topic_words = self.lda_model.show_topic(topic_id, num_words)
            topics.append({
                "topic_id": topic_id,
                "words": [
                    {"word": word, "weight": float(weight)}
                    for word, weight in topic_words
                ]
            })
        
        return topics
    
    def predict_topics(self, text: str, threshold: float = 0.1, include_sentiment: bool = False, sentiment_mode: str = "lexicon") -> List[Dict[str, Any]]:
        if not self.lda_model or not self.dictionary:
            raise ValueError("Model not trained yet")
        
        tokens = self.preprocess_text(text)
        
        if not tokens:
            return []
        
        if self.bigram_model:
            tokens = self.bigram_model[tokens]
        if self.trigram_model:
            tokens = self.trigram_model[tokens]
        
        bow = self.dictionary.doc2bow(tokens)
        
        topic_distribution = self.lda_model.get_document_topics(bow)
        
        results = [
            {
                "topic_id": topic_id,
                "probability": float(prob)
            }
            for topic_id, prob in topic_distribution
            if prob >= threshold
        ]
        
        if include_sentiment and text:
            from models.sentiment_analyzer import SentimentAnalyzer
            sentiment_analyzer = SentimentAnalyzer(mode=sentiment_mode)
            sentiment = sentiment_analyzer.analyze_sentiment(text)
            for result in results:
                result["sentiment"] = sentiment
        
        results.sort(key=lambda x: x["probability"], reverse=True)
        
        return results
    
    def analyze_topics_with_sentiment(self, texts: List[str]) -> List[Dict[str, Any]]:
        if not self.lda_model or not self.dictionary:
            raise ValueError("Model not trained yet")
        
        from models.sentiment_analyzer import SentimentAnalyzer
        sentiment_analyzer = SentimentAnalyzer(mode="lexicon")
        
        results = []
        for idx, text in enumerate(texts):
            if not text or not text.strip():
                continue
                
            topics = self.predict_topics(text, threshold=0.1)
            
            sentiment = sentiment_analyzer.analyze_sentiment(text)
            
            results.append({
                "text_index": idx,
                "text_preview": text[:100] + "..." if len(text) > 100 else text,
                "topics": topics,
                "sentiment": sentiment,
                "dominant_topic": topics[0]["topic_id"] if topics else None,
                "dominant_topic_probability": topics[0]["probability"] if topics else 0.0
            })
        
        return results
    
    def save_model(self, model_dir: str = "models/saved_models") -> str:
        if not self.lda_model:
            raise ValueError("No model to save")
        
        os.makedirs(model_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = os.path.join(model_dir, f"lda_model_{timestamp}")
        
        self.lda_model.save(f"{model_path}.model")
        
        self.dictionary.save(f"{model_path}.dict")
        
        if self.bigram_model:
            with open(f"{model_path}.bigram", "wb") as f:
                pickle.dump(self.bigram_model, f)
        
        if self.trigram_model:
            with open(f"{model_path}.trigram", "wb") as f:
                pickle.dump(self.trigram_model, f)
        
        metadata = {
            "num_topics": self.num_topics,
            "passes": self.passes,
            "iterations": self.iterations,
            "vocabulary_size": len(self.dictionary),
            "num_documents": len(self.documents),
            "has_bigrams": self.bigram_model is not None,
            "has_trigrams": self.trigram_model is not None,
            "trained_at": timestamp
        }
        
        with open(f"{model_path}.meta", "wb") as f:
            pickle.dump(metadata, f)
        
        return model_path
    
    def load_model(self, model_path: str) -> Dict[str, Any]:
        self.lda_model = LdaModel.load(f"{model_path}.model")
        
        self.dictionary = corpora.Dictionary.load(f"{model_path}.dict")
        
        bigram_path = f"{model_path}.bigram"
        if os.path.exists(bigram_path):
            with open(bigram_path, "rb") as f:
                self.bigram_model = pickle.load(f)
        
        trigram_path = f"{model_path}.trigram"
        if os.path.exists(trigram_path):
            with open(trigram_path, "rb") as f:
                self.trigram_model = pickle.load(f)
        
        with open(f"{model_path}.meta", "rb") as f:
            metadata = pickle.load(f)
        
        self.num_topics = metadata["num_topics"]
        self.passes = metadata["passes"]
        self.iterations = metadata["iterations"]
        
        return metadata
    
    def get_model_info(self) -> Dict[str, Any]:
        if not self.lda_model:
            return {"status": "not_trained", "message": "Model not trained yet"}
        
        return {
            "status": "trained",
            "num_topics": self.num_topics,
            "vocabulary_size": len(self.dictionary) if self.dictionary else 0,
            "num_documents": len(self.documents),
            "passes": self.passes,
            "iterations": self.iterations
        }
    
    def calculate_topic_similarity(self, topic_id1: int, topic_id2: int, top_n: int = 20) -> float:
        if not self.lda_model:
            raise ValueError("Model not trained yet")
        
        words1 = set([word for word, _ in self.lda_model.show_topic(topic_id1, top_n)])
        words2 = set([word for word, _ in self.lda_model.show_topic(topic_id2, top_n)])
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def find_similar_topics(self, similarity_threshold: float = 0.3, top_n: int = 20) -> List[Tuple[int, int, float]]:
        if not self.lda_model:
            raise ValueError("Model not trained yet")
        
        similar_pairs = []
        
        for i in range(self.num_topics):
            for j in range(i + 1, self.num_topics):
                similarity = self.calculate_topic_similarity(i, j, top_n)
                if similarity >= similarity_threshold:
                    similar_pairs.append((i, j, similarity))
        
        similar_pairs.sort(key=lambda x: x[2], reverse=True)
        
        return similar_pairs
    
    def merge_similar_topics(
        self, 
        similarity_threshold: float = 0.3,
        max_merges: int = None,
        verbose: bool = True
    ) -> Dict[str, Any]:
        if not self.lda_model:
            raise ValueError("Model not trained yet")
        
        similar_pairs = self.find_similar_topics(similarity_threshold)
        
        if not similar_pairs:
            return {
                "status": "no_merges_needed",
                "similar_pairs": [],
                "topic_mapping": {i: i for i in range(self.num_topics)},
                "topic_groups": {i: [i] for i in range(self.num_topics)},
                "original_num_topics": self.num_topics,
                "merged_num_topics": self.num_topics,
                "reduction": 0
            }
        
        if max_merges:
            similar_pairs = similar_pairs[:max_merges]
        
        topic_groups = {}
        topic_to_group = {}
        
        for topic in range(self.num_topics):
            topic_groups[topic] = [topic]
            topic_to_group[topic] = topic
        
        for topic1, topic2, similarity in similar_pairs:
            rep1 = topic_to_group[topic1]
            rep2 = topic_to_group[topic2]
            
            if rep1 != rep2:
                if len(topic_groups[rep1]) >= len(topic_groups[rep2]):
                    for topic in topic_groups[rep2]:
                        topic_to_group[topic] = rep1
                        topic_groups[rep1].append(topic)
                    del topic_groups[rep2]
                else:
                    for topic in topic_groups[rep1]:
                        topic_to_group[topic] = rep2
                        topic_groups[rep2].append(topic)
                    del topic_groups[rep1]
        
        topic_mapping = {topic: rep for topic, rep in topic_to_group.items()}
        merged_num_topics = len(topic_groups)
        
        if verbose:
            print(f"\n{'='*80}")
            print(f"🔄 TOPIC MERGING RESULTS")
            print(f"{'='*80}")
            print(f"Original topics: {self.num_topics}")
            print(f"Merged topics: {merged_num_topics}")
            print(f"Reduction: {self.num_topics - merged_num_topics} topics")
            print(f"\nMerged Groups:")
            print("-" * 80)
            
            for rep, group in sorted(topic_groups.items()):
                if len(group) > 1:
                    print(f"\n📊 Representative Topic {rep}:")
                    top_words = [word for word, _ in self.lda_model.show_topic(rep, 5)]
                    print(f"   Words: {', '.join(top_words)}")
                    print(f"   Merged with: {[t for t in group if t != rep]}")
        
        self.topic_mapping = topic_mapping
        self.merged_num_topics = merged_num_topics
        
        return {
            "status": "success",
            "similar_pairs": [
                {"topic1": t1, "topic2": t2, "similarity": sim}
                for t1, t2, sim in similar_pairs
            ],
            "topic_mapping": topic_mapping,
            "topic_groups": {rep: group for rep, group in topic_groups.items()},
            "original_num_topics": self.num_topics,
            "merged_num_topics": merged_num_topics,
            "reduction": self.num_topics - merged_num_topics
        }
    
    def predict_topics_merged(
        self, 
        text: str, 
        threshold: float = 0.1,
        include_sentiment: bool = False,
        sentiment_mode: str = "lexicon"
    ) -> List[Dict[str, Any]]:
        original_predictions = self.predict_topics(text, threshold, include_sentiment, sentiment_mode)
        
        if not hasattr(self, 'topic_mapping'):
            return original_predictions
        
        merged_predictions = {}
        
        for pred in original_predictions:
            topic_id = pred["topic_id"]
            merged_id = self.topic_mapping[topic_id]
            probability = pred["probability"]
            
            if merged_id in merged_predictions:
                merged_predictions[merged_id]["probability"] += probability
                merged_predictions[merged_id]["source_topics"].append(topic_id)
            else:
                merged_predictions[merged_id] = {
                    "topic_id": merged_id,
                    "probability": probability,
                    "source_topics": [topic_id],
                    "is_merged": topic_id != merged_id
                }
                
                if "sentiment" in pred:
                    merged_predictions[merged_id]["sentiment"] = pred["sentiment"]
        
        results = list(merged_predictions.values())
        results.sort(key=lambda x: x["probability"], reverse=True)
        
        return results
