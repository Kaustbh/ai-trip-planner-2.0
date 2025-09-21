"""
Summarize Tool

Tool for text summarization and content processing.
"""

from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime

from ..base_tool import BaseTool, ToolConfig, ToolType, ToolCapability, ToolResult


class SummarizeTool(BaseTool):
    """
    Tool for text summarization and content processing.
    
    Capabilities:
    - Text summarization
    - Content extraction
    - Key phrase extraction
    - Sentiment analysis
    - Language detection
    """
    
    def __init__(self, config: Optional[ToolConfig] = None):
        if config is None:
            config = ToolConfig(
                name="Summarize Tool",
                tool_type=ToolType.FUNCTION,
                description="Text summarization and content processing tool",
                capabilities=[ToolCapability.TRANSFORM, ToolCapability.READ],
                timeout=30,
                rate_limit=50
            )
        super().__init__(config)
        
        # Summarization settings
        self.max_input_length = 10000
        self.default_summary_length = 3  # sentences
        self.supported_languages = ["en", "es", "fr", "de", "it", "pt"]
    
    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Execute summarization with given parameters."""
        text = parameters.get("text", "")
        operation = parameters.get("operation", "summarize")
        length = parameters.get("length", self.default_summary_length)
        language = parameters.get("language", "en")
        
        if not text:
            return ToolResult(
                success=False,
                error="Text input is required"
            )
        
        if len(text) > self.max_input_length:
            return ToolResult(
                success=False,
                error=f"Text too long. Maximum length is {self.max_input_length} characters"
            )
        
        try:
            if operation == "summarize":
                result = await self._summarize_text(text, length, language)
            elif operation == "extract_keywords":
                result = await self._extract_keywords(text, language)
            elif operation == "sentiment_analysis":
                result = await self._analyze_sentiment(text, language)
            elif operation == "detect_language":
                result = await self._detect_language(text)
            elif operation == "extract_entities":
                result = await self._extract_entities(text, language)
            else:
                return ToolResult(
                    success=False,
                    error=f"Unsupported operation: {operation}"
                )
            
            return ToolResult(
                success=True,
                data=result,
                metadata={
                    "operation": operation,
                    "input_length": len(text),
                    "language": language
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Summarization failed: {str(e)}"
            )
    
    async def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate summarization parameters."""
        if "text" not in parameters:
            return False
        
        text = parameters.get("text", "")
        if not isinstance(text, str) or len(text) == 0:
            return False
        
        operation = parameters.get("operation", "summarize")
        valid_operations = ["summarize", "extract_keywords", "sentiment_analysis", "detect_language", "extract_entities"]
        if operation not in valid_operations:
            return False
        
        return True
    
    async def _summarize_text(self, text: str, length: int, language: str) -> Dict[str, Any]:
        """Summarize text to specified number of sentences."""
        # Mock summarization - in reality would use NLP libraries or AI models
        await asyncio.sleep(0.5)
        
        # Simple extractive summarization simulation
        sentences = text.split('.')
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= length:
            summary = text
        else:
            # Select first, middle, and last sentences
            selected_indices = []
            if length >= 1:
                selected_indices.append(0)  # First sentence
            if length >= 2 and len(sentences) > 2:
                selected_indices.append(len(sentences) // 2)  # Middle sentence
            if length >= 3 and len(sentences) > 3:
                selected_indices.append(-1)  # Last sentence
            
            # Add more sentences if needed
            while len(selected_indices) < length and len(selected_indices) < len(sentences):
                for i in range(len(sentences)):
                    if i not in selected_indices:
                        selected_indices.append(i)
                        break
            
            selected_sentences = [sentences[i] for i in sorted(selected_indices)]
            summary = '. '.join(selected_sentences) + '.'
        
        return {
            "summary": summary,
            "original_length": len(sentences),
            "summary_length": len(summary.split('.')),
            "compression_ratio": len(summary) / len(text) if text else 0
        }
    
    async def _extract_keywords(self, text: str, language: str) -> Dict[str, Any]:
        """Extract keywords from text."""
        await asyncio.sleep(0.3)
        
        # Mock keyword extraction
        words = text.lower().split()
        
        # Simple frequency-based keyword extraction
        word_freq = {}
        for word in words:
            # Remove punctuation and short words
            clean_word = ''.join(c for c in word if c.isalnum())
            if len(clean_word) > 3:
                word_freq[clean_word] = word_freq.get(clean_word, 0) + 1
        
        # Sort by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        # Get top keywords
        keywords = [word for word, freq in sorted_words[:10]]
        
        return {
            "keywords": keywords,
            "keyword_count": len(keywords),
            "total_words": len(words),
            "unique_words": len(word_freq)
        }
    
    async def _analyze_sentiment(self, text: str, language: str) -> Dict[str, Any]:
        """Analyze sentiment of text."""
        await asyncio.sleep(0.4)
        
        # Mock sentiment analysis
        positive_words = ["good", "great", "excellent", "amazing", "wonderful", "fantastic", "love", "like", "happy", "pleased"]
        negative_words = ["bad", "terrible", "awful", "horrible", "hate", "dislike", "angry", "sad", "disappointed", "frustrated"]
        
        words = text.lower().split()
        
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        if positive_count > negative_count:
            sentiment = "positive"
            score = 0.7
        elif negative_count > positive_count:
            sentiment = "negative"
            score = -0.7
        else:
            sentiment = "neutral"
            score = 0.0
        
        return {
            "sentiment": sentiment,
            "score": score,
            "positive_words": positive_count,
            "negative_words": negative_count,
            "confidence": abs(score)
        }
    
    async def _detect_language(self, text: str) -> Dict[str, Any]:
        """Detect language of text."""
        await asyncio.sleep(0.2)
        
        # Mock language detection
        # In reality would use language detection libraries
        
        # Simple heuristic-based detection
        common_words = {
            "en": ["the", "and", "is", "in", "to", "of", "a", "that", "it", "with"],
            "es": ["el", "la", "de", "que", "y", "a", "en", "un", "es", "se"],
            "fr": ["le", "de", "et", "à", "un", "il", "être", "et", "en", "avoir"],
            "de": ["der", "die", "und", "in", "den", "von", "zu", "das", "mit", "sich"]
        }
        
        words = text.lower().split()
        language_scores = {}
        
        for lang, words_list in common_words.items():
            score = sum(1 for word in words if word in words_list)
            language_scores[lang] = score
        
        detected_language = max(language_scores.items(), key=lambda x: x[1])[0]
        confidence = language_scores[detected_language] / len(words) if words else 0
        
        return {
            "language": detected_language,
            "confidence": confidence,
            "scores": language_scores
        }
    
    async def _extract_entities(self, text: str, language: str) -> Dict[str, Any]:
        """Extract named entities from text."""
        await asyncio.sleep(0.6)
        
        # Mock entity extraction
        # In reality would use NER libraries like spaCy or NLTK
        
        entities = {
            "persons": [],
            "organizations": [],
            "locations": [],
            "dates": [],
            "other": []
        }
        
        # Simple pattern-based entity extraction
        words = text.split()
        
        for i, word in enumerate(words):
            # Check for capitalized words (potential entities)
            if word[0].isupper() and len(word) > 1:
                # Simple heuristics for entity types
                if word.lower() in ["mr", "mrs", "ms", "dr", "prof"]:
                    # Potential person
                    if i + 1 < len(words):
                        entities["persons"].append(f"{word} {words[i + 1]}")
                elif word.lower() in ["inc", "corp", "ltd", "llc", "company"]:
                    # Potential organization
                    if i > 0:
                        entities["organizations"].append(f"{words[i - 1]} {word}")
                elif word.lower() in ["street", "avenue", "road", "city", "state", "country"]:
                    # Potential location
                    if i > 0:
                        entities["locations"].append(f"{words[i - 1]} {word}")
                else:
                    entities["other"].append(word)
        
        # Remove duplicates
        for entity_type in entities:
            entities[entity_type] = list(set(entities[entity_type]))
        
        return {
            "entities": entities,
            "total_entities": sum(len(ents) for ents in entities.values()),
            "entity_types": list(entities.keys())
        }
    
    def set_max_input_length(self, length: int) -> None:
        """Set maximum input text length."""
        self.max_input_length = length
    
    def set_default_summary_length(self, length: int) -> None:
        """Set default summary length in sentences."""
        self.default_summary_length = length
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return self.supported_languages.copy()
