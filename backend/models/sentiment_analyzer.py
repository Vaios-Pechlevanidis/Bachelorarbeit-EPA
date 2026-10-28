from typing import Dict, Any, List, Optional
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    def __init__(self, mode: str = "transformer"):
        self.mode = mode
        self._transformer_pipeline = None
        self._transformer_available = False
        
        self._init_lexicon()
        
        if mode == "transformer":
            try:
                self._init_transformer()
                self._transformer_available = True
                logger.info("Transformer mode initialized as primary analyzer.")
            except Exception as e:
                logger.warning(
                    f"Could not initialize transformer mode: {e}. "
                    "Falling back to lexicon (reserve) mode."
                )
                self.mode = "lexicon"
        else:
            logger.info("Using lexicon (reserve) mode explicitly.")
    
    def _init_lexicon(self):
        self.positive_words = {
            'gut', 'super', 'toll', 'ausgezeichnet', 'hervorragend', 'wunderbar',
            'großartig', 'perfekt', 'prima', 'klasse', 'spitze', 'fantastisch',
            'exzellent', 'positiv', 'freundlich', 'hilfsbereit', 'nett', 'angenehm',
            'zufrieden', 'glücklich', 'erfreut', 'begeistert', 'motiviert',
            'professionell', 'kompetent', 'effizient', 'flexibel', 'modern',
            'innovativ', 'kreativ', 'dynamisch', 'fair', 'transparent', 'offen',
            'wertschätzend', 'respektvoll', 'unterstützend', 'fördernd',
            'beste', 'besten', 'besser', 'hervorragend', 'empfehlenswert',
            'liebe', 'mögen', 'gefällt', 'schätzen', 'loben', 'dankbar',
            'weiterbildung', 'weiterbildungsmöglichkeiten', 'karrierechancen', 
            'aufstiegsmöglichkeiten', 'entwicklungsmöglichkeiten', 'perspektive',
            'teamgeist', 'teamwork', 'kollegial', 'kooperativ', 'zusammenhalt',
            'ausgewogen', 'balance', 'familienfreundlich', 'vereinbarkeit',
            'wertschätzung', 'anerkennung', 'lob', 'förderung', 'unterstützung',
            'eigenverantwortung', 'selbstständig', 'gestaltungsspielraum',
            'spannend', 'interessant', 'abwechslungsreich', 'vielfältig',
            'strukturiert', 'organisiert', 'verlässlich', 'pünktlich',
            'kommunikativ', 'partizipativ', 'mitbestimmung', 'einbindung'
        }
        
        self.negative_words = {
            'schlecht', 'schlechtes', 'schlechte', 'mies', 'katastrophal', 
            'furchtbar', 'schrecklich', 'grausam', 'schlimm', 'übel', 'negativ',
            'unzufrieden', 'enttäuscht', 'frustriert', 'ärgerlich', 'stressig',
            'chaotisch', 'unprofessionell', 'inkompetent', 'ineffizient',
            'unfreundlich', 'unhöflich', 'respektlos', 'unfair', 'intransparent',
            'mangelhaft', 'ungenügend', 'unzureichend', 'problematisch',
            'schwierig', 'kompliziert', 'langsam', 'veraltet', 'altmodisch',
            'niedrig', 'gering', 'wenig', 'kaum', 'nicht', 'nie', 'kein',
            'fehlt', 'fehlen', 'vermissen', 'mangel', 'problem', 'probleme',
            'kritik', 'kritisch', 'beschwerde', 'ärger', 'hassen', 'hasse',
            'burnout', 'überlastung', 'überstunden', 'überarbeitet', 
            'unterbezahlt', 'ausbeutung', 'ausbeuten', 'unterbezahlung',
            'unorganisiert', 'desorganisiert', 'planlos', 'chaotisch',
            'perspektivlos', 'aussichtslos', 'stagnation', 'stillstand',
            'eintönig', 'monoton', 'langweilig', 'routiniert',
            'hierarchisch', 'autoritär', 'bevormundend', 'kontrollierend',
            'bürokratisch', 'umständlich', 'starr', 'unflexibel', 'rigid',
            'mikromanagement', 'misstrauisch', 'kontrollwahn',
            'mobbing', 'ausgrenzung', 'diskriminierung', 'benachteiligung',
            'befristet', 'unsicher', 'instabil', 'wackelig',
            'intransparent', 'undurchsichtig', 'verschlossen', 'geheimniskrämerei'
        }
        
        self.intensifiers = {
            'sehr': 1.5,
            'extrem': 2.0,
            'total': 1.8,
            'absolut': 1.8,
            'wirklich': 1.3,
            'ziemlich': 1.2,
            'besonders': 1.5,
            'außerordentlich': 2.0,
            'unglaublich': 1.8
        }
        
        self.negations = {
            'nicht', 'kein', 'keine', 'keiner', 'keines', 'nie', 'niemals',
            'nimmer', 'nirgends', 'nichts', 'kaum', 'wenig'
        }
        
        self._neutral_patterns = [
            r'\bnicht\s+schlecht\b',
            r'\bnicht\s+besonders\b',
            r'\bes\s+ist\s+okay\b',
            r'\bgeht\s+so\b',
            r'\bnichts\s+besonderes\b',
            r'\bnichts\s+besonders\b',
            r'\bkönnte\s+besser\b',
            r'\bkönnte\s+schlimmer\b',
            r'\bganz\s+okay\b',
            r'\bganz\s+in\s+ordnung\b',
            r'\bmal\s+so\s+mal\s+so\b',
            r'\bdurchschnitt',
            r'\bmittelmäßig\b',
            r'\bin\s+ordnung\b',
            r'\bnaja\b',
            r'\bsolide\b',
            r'\bakzeptabel\b',
        ]
        self._compiled_neutral_patterns = [
            re.compile(p, re.IGNORECASE) for p in self._neutral_patterns
        ]
        
        self._negated_negative_patterns = [
            r'\bnicht\s+schlecht\b',
            r'\bnicht\s+schlimm\b',
            r'\bnicht\s+übel\b',
            r'\bkein\w*\s+problem\b',
            r'\bkein\w*\s+beschwerde\b',
        ]
        self._compiled_negated_negative = [
            re.compile(p, re.IGNORECASE) for p in self._negated_negative_patterns
        ]
    
    def _init_transformer(self):
        try:
            from transformers import pipeline
            logger.info("Loading German sentiment analysis model...")
            
            model_options = [
                "oliverguhr/german-sentiment-bert",
                "cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual"
            ]
            
            loaded = False
            for model_name in model_options:
                try:
                    logger.info(f"Attempting to load: {model_name}")
                    self._transformer_pipeline = pipeline(
                        "sentiment-analysis",
                        model=model_name,
                        top_k=None
                    )
                    logger.info(f"✅ Transformer model loaded: {model_name}")
                    self._model_name = model_name
                    loaded = True
                    break
                except Exception as e:
                    logger.warning(f"Could not load {model_name}: {e}")
                    continue
            
            if not loaded:
                raise RuntimeError("Could not load any sentiment model")
            
        except ImportError:
            logger.error(
                "transformers library not found. "
                "Install with: pip install transformers torch"
            )
            raise ImportError(
                "Please install transformers: pip install transformers torch"
            )
        except Exception as e:
            logger.error(f"Error loading transformer model: {e}")
            raise
    
    def _has_neutral_indicators(self, text: str) -> bool:
        for pattern in self._compiled_neutral_patterns:
            if pattern.search(text):
                return True
        return False
    
    def _has_negated_negative(self, text: str) -> bool:
        for pattern in self._compiled_negated_negative:
            if pattern.search(text):
                return True
        return False
    
    def _analyze_with_transformer(self, text: str, star_rating: Optional[float] = None) -> Dict[str, Any]:
        if not self._transformer_pipeline:
            raise RuntimeError("Transformer model not initialized")
        
        if not text or not isinstance(text, str) or not text.strip():
            return {
                "polarity": 0.0,
                "sentiment": "neutral",
                "subjectivity": 0.0,
                "confidence": 0.0
            }
        
        try:
            results = self._transformer_pipeline(text[:512])[0]
            
            best_result = max(results, key=lambda x: x['score'])
            label = best_result['label'].lower()
            confidence = best_result['score']
            
            score_map = {r['label'].lower(): r['score'] for r in results}
            pos_score = score_map.get('positive', 0.0)
            neg_score = score_map.get('negative', 0.0)
            neu_score = score_map.get('neutral', 0.0)
            
            sentiment_map = {
                'positive': ('positive', 1.0),
                'neutral': ('neutral', 0.0),
                'negative': ('negative', -1.0)
            }
            
            sentiment, polarity_base = sentiment_map.get(
                label, 
                ('neutral', 0.0)
            )
            polarity = polarity_base * confidence
            
            has_neutral_phrases = self._has_neutral_indicators(text)
            has_negated_neg = self._has_negated_negative(text)
            
            lexicon_result = self._analyze_with_lexicon(text)
            lexicon_sentiment = lexicon_result['sentiment']
            lexicon_polarity = lexicon_result['polarity']
            
            if has_neutral_phrases:
                sentiment = 'neutral'
                polarity = 0.0
                confidence = max(confidence * 0.8, neu_score, 0.6)
                logger.debug(f"Neutral indicator override: '{text[:40]}...'")
            
            elif has_negated_neg and sentiment == 'negative':
                sentiment = 'neutral'
                polarity = 0.0
                confidence = max(confidence * 0.7, 0.5)
                logger.debug(f"Negated-negative override: '{text[:40]}...'")

            elif sentiment == 'positive' and lexicon_sentiment == 'negative' and lexicon_result['confidence'] > 0.3:
                sentiment = 'negative'
                polarity = lexicon_polarity * 0.6
                confidence = confidence * 0.6
                logger.debug(f"Case F reversal (positive→negative): '{text[:40]}...'")

            elif confidence >= 0.75:
                logger.debug(f"Transformer high confidence ({confidence:.2f}), skipping lexicon correction.")
            
            elif sentiment == 'negative' and lexicon_sentiment == 'neutral':
                margin = neg_score - max(pos_score, neu_score)
                if margin < 0.2 and confidence < 0.55:
                    sentiment = 'neutral'
                    polarity = 0.0
                    confidence = confidence * 0.7
                    logger.debug(f"Hybrid neutral correction: '{text[:40]}...'")
            
            elif sentiment == 'negative' and lexicon_sentiment == 'positive':
                if lexicon_result['confidence'] > 0.7:
                    sentiment = lexicon_sentiment
                    polarity = lexicon_polarity * 0.7
                    confidence = (confidence + lexicon_result['confidence']) / 2
                    logger.debug(f"Hybrid positive correction: '{text[:40]}...'")
                else:
                    sentiment = 'neutral'
                    polarity = 0.0
                    confidence = confidence * 0.6
            
            elif sentiment == 'neutral' and lexicon_sentiment == 'positive':
                if lexicon_result['confidence'] > 0.6:
                    sentiment = 'positive'
                    polarity = lexicon_polarity * 0.8
                    confidence = (confidence + lexicon_result['confidence']) / 2
                    logger.debug(f"Hybrid positive boost: '{text[:40]}...'")
            
            if star_rating is not None:
                rating_hint = 'neutral'
                if star_rating <= 2.5:
                    rating_hint = 'negative'
                elif star_rating >= 3.5:
                    rating_hint = 'positive'
                
                if (rating_hint == 'positive' and sentiment == 'negative') or \
                   (rating_hint == 'negative' and sentiment == 'positive'):
                    confidence *= 0.7
                    if confidence < 0.6:
                        sentiment = 'neutral'
                        polarity = 0.0
            
            subjectivity = confidence
            
            return {
                "polarity": float(polarity),
                "sentiment": sentiment,
                "subjectivity": float(subjectivity),
                "confidence": float(confidence),
                "raw_results": results
            }
            
        except Exception as e:
            logger.error(f"Error in transformer analysis: {e}")
            return {
                "polarity": 0.0,
                "sentiment": "neutral",
                "subjectivity": 0.0,
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _analyze_with_lexicon(self, text: str) -> Dict[str, Any]:
        if not text or not isinstance(text, str) or not text.strip():
            return {
                "polarity": 0.0,
                "sentiment": "neutral",
                "subjectivity": 0.0,
                "confidence": 0.0
            }
        
        try:
            words = text.lower().split()
            
            if not words:
                return {
                    "polarity": 0.0,
                    "sentiment": "neutral",
                    "subjectivity": 0.0,
                    "confidence": 0.0
                }
            
            positive_score = 0.0
            negative_score = 0.0
            sentiment_word_count = 0
            
            for i, word in enumerate(words):
                multiplier = 1.0
                if i > 0 and words[i-1] in self.intensifiers:
                    multiplier = self.intensifiers[words[i-1]]
                
                is_negated = False
                if i > 0 and words[i-1] in self.negations:
                    is_negated = True
                if i > 1 and words[i-2] in self.negations:
                    is_negated = True
                
                if word in self.positive_words:
                    sentiment_word_count += 1
                    score = 1.0 * multiplier
                    if is_negated:
                        negative_score += score
                    else:
                        positive_score += score
                        
                elif word in self.negative_words:
                    sentiment_word_count += 1
                    score = 1.0 * multiplier
                    if is_negated:
                        positive_score += score
                    else:
                        negative_score += score
            
            if positive_score + negative_score > 0:
                polarity = (positive_score - negative_score) / (positive_score + negative_score)
            else:
                polarity = 0.0
            
            subjectivity = min(sentiment_word_count / len(words), 1.0)
            
            if polarity > 0.15:
                sentiment = "positive"
            elif polarity < -0.15:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            
            base_confidence = min(abs(polarity), 1.0)
            word_density_factor = min(sentiment_word_count / 10.0, 1.0)
            
            confidence = base_confidence * 0.7 + word_density_factor * 0.3
            confidence = min(confidence, 1.0)
            
            return {
                "polarity": float(polarity),
                "sentiment": sentiment,
                "subjectivity": float(subjectivity),
                "confidence": float(confidence)
            }
            
        except Exception as e:
            return {
                "polarity": 0.0,
                "sentiment": "neutral",
                "subjectivity": 0.0,
                "confidence": 0.0,
                "error": str(e)
            }
    
    def analyze_sentiment(self, text: str, star_rating: Optional[float] = None) -> Dict[str, Any]:
        if self.mode == "transformer" and self._transformer_available:
            return self._analyze_with_transformer(text, star_rating)
        else:
            return self._analyze_with_lexicon(text)
    
    def analyze_with_rating_hint(
        self, 
        text: str, 
        star_rating: float
    ) -> Dict[str, Any]:
        result = self.analyze_sentiment(text, star_rating)
        
        result['star_rating'] = star_rating
        result['rating_hint'] = 'neutral'
        
        if star_rating <= 2.5:
            result['rating_hint'] = 'negative'
        elif star_rating >= 3.5:
            result['rating_hint'] = 'positive'
        
        return result
    
    def set_mode(self, mode: str):
        if mode not in ["lexicon", "transformer"]:
            raise ValueError("Mode must be 'lexicon' or 'transformer'")
        
        if mode == "transformer" and not self._transformer_pipeline:
            try:
                self._init_transformer()
                self._transformer_available = True
            except Exception as e:
                logger.warning(
                    f"Could not initialize transformer mode: {e}. "
                    "Staying in lexicon mode."
                )
                return
        
        self.mode = mode
        logger.info(f"Switched to {mode} mode")
    
    def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        return [self.analyze_sentiment(text) for text in texts]
    
    def get_sentiment_summary(self, sentiments: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not sentiments:
            return {
                "count": 0,
                "avg_polarity": 0.0,
                "avg_subjectivity": 0.0,
                "positive_count": 0,
                "neutral_count": 0,
                "negative_count": 0,
                "positive_percentage": 0.0,
                "neutral_percentage": 0.0,
                "negative_percentage": 0.0
            }
        
        count = len(sentiments)
        avg_polarity = sum(s["polarity"] for s in sentiments) / count
        avg_subjectivity = sum(s["subjectivity"] for s in sentiments) / count
        
        positive_count = sum(1 for s in sentiments if s["sentiment"] == "positive")
        neutral_count = sum(1 for s in sentiments if s["sentiment"] == "neutral")
        negative_count = sum(1 for s in sentiments if s["sentiment"] == "negative")
        
        return {
            "count": count,
            "avg_polarity": float(avg_polarity),
            "avg_subjectivity": float(avg_subjectivity),
            "positive_count": positive_count,
            "neutral_count": neutral_count,
            "negative_count": negative_count,
            "positive_percentage": float(positive_count / count * 100),
            "neutral_percentage": float(neutral_count / count * 100),
            "negative_percentage": float(negative_count / count * 100)
        }
    
    def categorize_by_sentiment(
        self, 
        items: List[Dict[str, Any]], 
        sentiment_key: str = "sentiment_analysis"
    ) -> Dict[str, List[Dict[str, Any]]]:
        categorized = {
            "positive": [],
            "neutral": [],
            "negative": []
        }
        
        for item in items:
            sentiment = item.get(sentiment_key, {}).get("sentiment", "neutral")
            categorized[sentiment].append(item)
        
        return categorized
