"""
AI Clip Engine — Phase 3
Handles: candidate detection, semantic analysis, scoring, deduplication, clip selection
"""
from __future__ import annotations

import json
import logging
import os
import re
import statistics
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict
from uuid import uuid4
from datetime import datetime, timezone

import httpx

from api.app.config import settings

logger = logging.getLogger(__name__)


class ClipStrategy(str, Enum):
    """Detection strategies for finding clip candidates"""
    SENTENCE_BOUNDARY = "A"
    TOPIC_CHANGE = "B"
    Q_A_SEQUENCE = "C"
    STRONG_OPENING = "D"
    EMOTIONAL_PEAK = "E"
    SURPRISING_CLAIM = "F"
    COMPLETE_THOUGHT = "G"
    KEYWORD_TRIGGER = "H"


class ScoreCategory(str, Enum):
    """Scoring dimensions"""
    HOOK_STRENGTH = "hook_score"
    INFORMATION_DENSITY = "information_density"
    EMOTIONAL_INTENSITY = "emotional_intensity"
    NOVELTY = "novelty"
    NARRATIVE_COMPLETE = "narrative_completeness"
    CURIOSITY = "curiosity"
    QUOTABILITY = "quotability"
    AUDIENCE_RELEVANCE = "audience_relevance"
    DEAD_AIR = "dead_air"
    CONTEXT_DEPENDENCY = "excessive_context_dependency"
    DUPLICATE_CONTENT = "duplicate_content"


@dataclass
class Segment:
    """A transcript segment"""
    start_time: float
    end_time: float
    text: str
    speaker: Optional[str] = None
    words: list[str] = field(default_factory=list)
    emotion: Optional[str] = None
    keywords: list[str] = field(default_factory=list)


@dataclass
class ClipCandidate:
    """A detected clip candidate with full scoring"""
    id: str = field(default_factory=lambda: str(uuid4()))
    video_id: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    score: float = 0.0
    hook_text: str = ""
    category: str = "general"
    confidence: float = 0.0
    strategy: ClipStrategy = ClipStrategy.SENTENCE_BOUNDARY
    metadata: dict = field(default_factory=dict)
    is_duplicate: bool = False
    selected: bool = False
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "video_id": self.video_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "score": self.score,
            "hook_text": self.hook_text,
            "category": self.category,
            "confidence": self.confidence,
            "strategy": self.strategy.value,
            "metadata": self.metadata,
            "is_duplicate": self.is_duplicate,
            "selected": self.selected,
            "reason": self.reason,
        }


@dataclass
class ScoringWeights:
    """Configurable scoring weights"""
    hook_score: float = 1.2
    information_density: float = 1.0
    emotional_intensity: float = 0.9
    novelty: float = 0.8
    narrative_completeness: float = 0.7
    curiosity: float = 0.8
    quotability: float = 1.0
    audience_relevance: float = 0.9
    dead_air_penalty: float = -0.5
    context_dependency_penalty: float = -0.3
    duplicate_penalty: float = -0.6

    def get_total_weight(self) -> float:
        positive = sum(v for k, v in self.__dict__.items() if v > 0)
        negative = sum(v for k, v in self.__dict__.items() if v < 0)
        return positive + abs(negative)


@dataclass
class AnalysisResult:
    """Result of AI video analysis"""
    video_id: str
    total_duration: float
    candidates: List[ClipCandidate]
    segments: List[Segment]
    topics: list[str]
    language: str
    processing_time_seconds: float
    metadata: dict


class TranscriptProcessor:
    """Processes and segments transcripts for analysis"""

    @staticmethod
    def segment_by_sentences(transcript: dict) -> List[Segment]:
        """Segment transcript by sentence boundaries"""
        segments = []
        words = transcript.get("words", [])
        full_text = transcript.get("full_text", "")

        if not words:
            # Fallback to text segments
            for seg in transcript.get("segments", []):
                segments.append(Segment(
                    start_time=seg["start"],
                    end_time=seg["end"],
                    text=seg["text"],
                ))
            return segments

        current_words = []
        current_start = words[0]["start"]
        sentence_end_pattern = re.compile(r'[.!?]+["\']?\s*$')

        for i, word_data in enumerate(words):
            word = word_data["word"]
            current_words.append(word)

            if sentence_end_pattern.search(" ".join(current_words[-5:])) or i == len(words) - 1:
                text = " ".join(current_words)
                segments.append(Segment(
                    start_time=current_start,
                    end_time=word_data["end"],
                    text=text.strip(),
                    words=current_words.copy(),
                ))
                current_words = []
                if i < len(words) - 1:
                    current_start = words[i + 1]["start"]

        return segments

    @staticmethod
    def detect_topic_changes(segments: List[Segment], similarity_threshold: float = 0.7) -> List[int]:
        """Detect topic changes using simple keyword analysis"""
        # In production, use embeddings for better detection
        topic_changes = []
        prev_keywords = set()

        for i, seg in enumerate(segments):
            current_keywords = set(re.findall(r'\b\w{4,}\b', seg.text.lower()))
            if i > 0:
                common = current_keywords & prev_keywords
                if len(common) / max(len(current_keywords), 1) < similarity_threshold and common:
                    topic_changes.append(i)
            prev_keywords = current_keywords

        return topic_changes

    @staticmethod
    def detect_qa_sequences(segments: List[Segment]) -> List[tuple]:
        """Detect question → answer sequences"""
        qa_pairs = []
        for i, seg in enumerate(segments):
            text = seg.text.strip().lower()
            if any(q in text for q in ["what is", "how does", "why", "can you", "tell me", "do you", "when"]) or text.endswith("?"):
                if i + 1 < len(segments):
                    qa_pairs.append((i, i + 1))
        return qa_pairs

    @staticmethod
    def detect_complete_thoughts(segments: List[Segment]) -> List[int]:
        """Detect segments ending on complete thoughts (terminal punctuation)"""
        complete = []
        end_pattern = re.compile(r'[.!?]["\']?\s*$')
        for i, seg in enumerate(segments):
            if end_pattern.search(seg.text):
                complete.append(i)
        return complete

    @staticmethod
    def detect_keywords(segments: List[Segment], keywords: list[str] = None) -> Dict[int, list[str]]:
        """Detect keyword-triggered segments"""
        if keywords is None:
            keywords = ["surprising", "important", "critical", "breakthrough", "discovery", "reveal", "shocking"]

        triggered = {}
        for i, seg in enumerate(segments):
            found = [kw for kw in keywords if kw.lower() in seg.text.lower()]
            if found:
                triggered[i] = found
        return triggered


class SemanticAnalyzer:
    """Analyzes transcript semantics for clip detection"""

    @staticmethod
    async def analyze_segments(segments: List[Segment]) -> List[dict]:
        """Analyze segments for semantic content"""
        results = []
        for seg in segments:
            analysis = {
                "segment": seg,
                "word_count": len(seg.words) if seg.words else len(seg.text.split()),
                "sentiment_score": 0.0,
                "has_emotion": False,
                "has_hook": False,
                "is_informative": False,
                "is_quotable": False,
                "contains_number": bool(re.search(r'\b\d+\b', seg.text)),
                "contains_exclamation": "!" in seg.text,
                "contains_question": "?" in seg.text,
                "keywords": [],
            }

            # Simple keyword detection
            hook_words = ["but", "however", "actually", "surprisingly", "critical", "important", "breakthrough", "shocking", "revealed", "discovered"]
            analysis["has_hook"] = any(w in seg.text.lower() for w in hook_words)

            emotion_words = {
                "excited": ["amazing", "incredible", "wow", "unbelievable", "wow", "wow"],
                "sad": ["sad", "tragic", "heartbreaking", "devastating"],
                "angry": ["outrageous", "unacceptable", "disgraceful", "wrong"],
                "humorous": ["hilarious", "funny", "laugh", "joke", "comedian"],
                "surprised": ["shocking", "surprising", "never expected", "unexpected"],
            }
            for emotion, words in emotion_words.items():
                if any(w in seg.text.lower() for w in words):
                    analysis["has_emotion"] = True
                    analysis["emotion"] = emotion
                    break

            results.append(analysis)
        return results


class ScoringEngine:
    """Structured scoring engine for clip candidates"""

    def __init__(self, weights: ScoringWeights | None = None):
        self.weights = weights or ScoringWeights()

    def calculate_score(self, segment: Segment, analysis: dict, context: dict) -> float:
        """Calculate viral score for a segment using weighted formula"""
        score = 0.0

        # Positive factors
        score += self.weights.hook_score * self._score_hook(segment, analysis)
        score += self.weights.information_density * self._score_information_density(segment, analysis)
        score += self.weights.emotional_intensity * self._score_emotional_intensity(segment, analysis)
        score += self.weights.novelty * self._score_novelty(segment, analysis)
        score += self.weights.narrative_completeness * self._score_narrative(segment, context)
        score += self.weights.curiosity * self._score_curiosity(segment, analysis)
        score += self.weights.quotability * self._score_quotability(segment, analysis)
        score += self.weights.audience_relevance * self._score_relevance(segment)

        # Negative penalties
        score += self.weights.dead_air_penalty * self._score_dead_air(segment)
        score += self.weights.context_dependency_penalty * self._score_context_dependency(segment, context)

        # Normalize to 0-100
        normalized = self._normalize_score(score)

        return round(normalized, 1)

    def _score_hook(self, segment: Segment, analysis: dict) -> float:
        """Score hook strength"""
        hook_score = 0.0
        if analysis["has_hook"]:
            hook_score += 20
        if analysis["has_emotion"]:
            hook_score += 15
        if analysis["contains_exclamation"]:
            hook_score += 10
        if segment.start_time < 30:  # Early in video
            hook_score += 5
        return min(hook_score / 30.0, 1.0)

    def _score_information_density(self, segment: Segment, analysis: dict) -> float:
        """Score information density"""
        word_count = analysis["word_count"]
        has_number = analysis["contains_number"]
        # Ideal: 10-30 words, has numbers
        if word_count < 5:
            return 0.2
        if word_count > 50:
            return 0.4
        density = 1.0 if 10 <= word_count <= 30 else 0.7
        return density * (1.2 if has_number else 1.0)

    def _score_emotional_intensity(self, segment: Segment, analysis: dict) -> float:
        """Score emotional intensity"""
        if analysis["has_emotion"]:
            return 1.0
        if analysis["contains_exclamation"]:
            return 0.7
        if analysis["contains_question"]:
            return 0.5
        return 0.2

    def _score_novelty(self, segment: Segment, analysis: dict) -> float:
        """Score novelty"""
        novelty_words = ["new", "first", "never", "unexpected", "discovery", "breakthrough", "unique", "unprecedented"]
        if any(w in segment.text.lower() for w in novelty_words):
            return 1.0
        if analysis["contains_number"]:
            return 0.7
        return 0.3

    def _score_narrative(self, segment: Segment, context: dict) -> float:
        """Score narrative completeness"""
        # Check if segment has a complete arc: setup → conflict → resolution
        text = segment.text.lower()
        has_setup = any(w in text for w in ["first", "started", "initially", "when"])
        has_conflict = any(w in text for w in ["but", "however", "problem", "issue", "challenge"])
        has_resolution = any(w in text for w in ["finally", "solution", "resolved", "then", "result"])
        if has_setup and has_conflict and has_resolution:
            return 1.0
        if has_setup and has_conflict:
            return 0.7
        return 0.4

    def _score_curiosity(self, segment: Segment, analysis: dict) -> float:
        """Score curiosity"""
        curiosity_words = ["why", "how", "what if", "imagine", "secret", "hidden", "behind", "truth"]
        if any(w in segment.text.lower() for w in curiosity_words):
            return 1.0
        if analysis["contains_question"]:
            return 0.8
        return 0.3

    def _score_quotability(self, segment: Segment, analysis: dict) -> float:
        """Score quotability"""
        if analysis["has_emotion"] and analysis["contains_exclamation"]:
            return 1.0
        if analysis["word_count"] < 20:  # Short, punchy
            return 0.8
        return 0.4

    def _score_relevance(self, segment: Segment) -> float:
        """Score audience relevance"""
        # Broader appeal = higher relevance
        if len(segment.text.split()) > 5:
            return 0.8
        return 0.5

    def _score_dead_air(self, segment: Segment) -> float:
        """Score dead air penalty"""
        # Check for long pauses, filler words
        filler_words = ["um", "uh", "you know", "like", "so", "basically", "kind of"]
        has_filler = any(fw in segment.text.lower() for fw in filler_words)
        return 0.8 if has_filler else 0.1

    def _score_context_dependency(self, segment: Segment, context: dict) -> float:
        """Score excessive context dependency penalty"""
        # If segment requires heavy context, penalize
        if len(segment.text.split()) < 8 and segment.start_time > 60:
            return 0.5
        return 0.1

    def _normalize_score(self, score: float) -> float:
        """Normalize score to 0-100 range"""
        total_weight = self.weights.get_total_weight()
        if total_weight == 0:
            return 0.0
        normalized = (score / total_weight) * 100
        return max(0, min(100, round(normalized, 1)))

    def score_candidate(self, candidate: ClipCandidate, segments: List[Segment], context: dict) -> ClipCandidate:
        """Full scoring of a clip candidate"""
        for seg in segments:
            if seg.start_time <= candidate.start_time and seg.end_time >= candidate.end_time:
                analysis = SemanticAnalyzer.analyze_segments([seg])[0]
                candidate.score = self.calculate_score(seg, analysis, context)
                break
        return candidate


class DeduplicationEngine:
    """Removes duplicate/overlapping clip candidates"""

    @staticmethod
    def deduplicate(candidates: List[ClipCandidate], overlap_threshold: float = 0.5) -> List[ClipCandidate]:
        """Remove overlapping candidates, keeping higher-scored ones"""
        # Sort by score descending
        sorted_candidates = sorted(candidates, key=lambda c: c.score, reverse=True)
        kept = []
        seen = set()

        for candidate in sorted_candidates:
            # Check if this candidate overlaps with already kept ones
            is_duplicate = False
            for kept_candidate in kept:
                overlap = DeduplicationEngine._calculate_overlap(candidate, kept_candidate)
                if overlap >= overlap_threshold:
                    candidate.is_duplicate = True
                    is_duplicate = True
                    break

            if not is_duplicate:
                kept.append(candidate)

        logger.info(f"Deduplication: {len(candidates)} → {len(kept)} candidates")
        return kept

    @staticmethod
    def _calculate_overlap(a: ClipCandidate, b: ClipCandidate) -> float:
        """Calculate temporal overlap between two candidates"""
        overlap_start = max(a.start_time, b.start_time)
        overlap_end = min(a.end_time, b.end_time)
        overlap = max(0, overlap_end - overlap_start)

        shorter_duration = min(a.end_time - a.start_time, b.end_time - b.start_time)
        if shorter_duration == 0:
            return 0.0

        return overlap / shorter_duration

    @staticmethod
    def deduplicate_by_content(candidates: List[ClipCandidate], similarity_threshold: float = 0.8) -> List[ClipCandidate]:
        """Remove candidates with similar content"""
        # Simple keyword-based similarity check
        # In production, use embeddings
        kept = []
        for candidate in candidates:
            is_duplicate = False
            for kept_candidate in kept:
                if DeduplicationEngine._content_similarity(candidate, kept_candidate) > similarity_threshold:
                    candidate.is_duplicate = True
                    is_duplicate = True
                    break
            if not is_duplicate:
                kept.append(candidate)
        return kept

    @staticmethod
    def _content_similarity(a: ClipCandidate, b: ClipCandidate) -> float:
        """Check content similarity"""
        if a.hook_text and b.hook_text:
            words_a = set(a.hook_text.lower().split())
            words_b = set(b.hook_text.lower().split())
            if words_a and words_b:
                return len(words_a & words_b) / len(words_a | words_b)
        return 0.0


class ClipSelectionEngine:
    """Multi-strategy clip selection"""

    def __init__(self):
        self.strategies = {
            ClipStrategy.SENTENCE_BOUNDARY: self._strategy_sentence_boundary,
            ClipStrategy.TOPIC_CHANGE: self._strategy_topic_change,
            ClipStrategy.Q_A_SEQUENCE: self._strategy_qa_sequence,
            ClipStrategy.STRONG_OPENING: self._strategy_strong_opening,
            ClipStrategy.EMOTIONAL_PEAK: self._strategy_emotional_peak,
            ClipStrategy.SURPRISING_CLAIM: self._strategy_surprising_claim,
            ClipStrategy.COMPLETE_THOUGHT: self._strategy_complete_thought,
            ClipStrategy.KEYWORD_TRIGGER: self._strategy_keyword_trigger,
        }

    async def detect_candidates(
        self,
        segments: List[Segment],
        transcript: dict,
        min_score: float = 60.0,
        max_candidates: int = 20,
    ) -> List[ClipCandidate]:
        """Detect clip candidates using all strategies"""
        all_candidates: List[ClipCandidate] = []

        for strategy, func in self.strategies.items():
            try:
                candidates = await func(segments, transcript)
                for c in candidates:
                    c.strategy = strategy
                all_candidates.extend(candidates)
            except Exception as e:
                logger.warning(f"Strategy {strategy.value} failed: {e}")

        # Score all candidates
        scoring_engine = ScoringEngine()
        context = {"segments": segments, "transcript": transcript}
        for candidate in all_candidates:
            scoring_engine.score_candidate(candidate, segments, context)

        # Sort by score
        all_candidates.sort(key=lambda c: c.score, reverse=True)

        # Deduplicate
        dedup_engine = DeduplicationEngine()
        all_candidates = dedup_engine.deduplicate(all_candidates)
        all_candidates = dedup_engine.deduplicate_by_content(all_candidates)

        # Filter by minimum score
        all_candidates = [c for c in all_candidates if c.score >= min_score]

        # Limit to max candidates
        all_candidates = all_candidates[:max_candidates]

        logger.info(f"Detected {len(all_candidates)} candidates from {len(all_candidates)} total")
        return all_candidates

    async def _strategy_sentence_boundary(self, segments: List[Segment], transcript: dict) -> List[ClipCandidate]:
        """Strategy A: Clip at sentence boundaries"""
        candidates = []
        for seg in segments:
            if seg.end_time - seg.start_time >= 10 and seg.end_time - seg.start_time <= 60:
                candidates.append(ClipCandidate(
                    video_id="",
                    start_time=seg.start_time,
                    end_time=seg.end_time,
                    hook_text=seg.text[:80],
                    strategy=ClipStrategy.SENTENCE_BOUNDARY,
                ))
        return candidates

    async def _strategy_topic_change(self, segments: List[Segment], transcript: dict) -> List[ClipCandidate]:
        """Strategy B: Clip at topic changes"""
        topic_changes = TranscriptProcessor.detect_topic_changes(segments)
        candidates = []
        for idx in topic_changes:
            if idx < len(segments):
                seg = segments[idx]
                candidates.append(ClipCandidate(
                    video_id="",
                    start_time=seg.start_time,
                    end_time=seg.end_time,
                    hook_text=f"Topic change: {seg.text[:60]}",
                    category="topic_change",
                    strategy=ClipStrategy.TOPIC_CHANGE,
                ))
        return candidates

    async def _strategy_qa_sequence(self, segments: List[Segment], transcript: dict) -> List[ClipCandidate]:
        """Strategy C: Question → Answer sequences"""
        qa_pairs = TranscriptProcessor.detect_qa_sequences(segments)
        candidates = []
        for q_idx, a_idx in qa_pairs:
            if a_idx < len(segments):
                seg = segments[a_idx]
                candidates.append(ClipCandidate(
                    video_id="",
                    start_time=segments[q_idx].start_time,
                    end_time=seg.end_time,
                    hook_text=f"Q&A: {seg.text[:60]}",
                    category="qa",
                    strategy=ClipStrategy.Q_A_SEQUENCE,
                ))
        return candidates

    async def _strategy_strong_opening(self, segments: List[Segment], transcript: dict) -> List[ClipCandidate]:
        """Strategy D: Strong opening statements"""
        candidates = []
        for i, seg in enumerate(segments[:5]):  # First 5 segments
            if len(seg.text.split()) > 8:
                candidates.append(ClipCandidate(
                    video_id="",
                    start_time=seg.start_time,
                    end_time=seg.end_time,
                    hook_text=f"Opening: {seg.text[:60]}",
                    category="opening",
                    strategy=ClipStrategy.STRONG_OPENING,
                ))
        return candidates

    async def _strategy_emotional_peak(self, segments: List[Segment], transcript: dict) -> List[ClipCandidate]:
        """Strategy E: Emotional peaks"""
        analysis_results = await SemanticAnalyzer.analyze_segments(segments)
        candidates = []
        for i, result in enumerate(analysis_results):
            if result["has_emotion"] or result["contains_exclamation"]:
                seg = segments[i]
                candidates.append(ClipCandidate(
                    video_id="",
                    start_time=seg.start_time,
                    end_time=seg.end_time,
                    hook_text=f"Emotional moment: {seg.text[:60]}",
                    category="emotional",
                    strategy=ClipStrategy.EMOTIONAL_PEAK,
                ))
        return candidates

    async def _strategy_surprising_claim(self, segments: List[Segment], transcript: dict) -> List[ClipCandidate]:
        """Strategy F: Surprising claims"""
        surprising_words = ["shocking", "surprising", "never", "unexpected", "no one", "nobody", "secret", "hidden"]
        candidates = []
        for seg in segments:
            if any(w in seg.text.lower() for w in surprising_words):
                candidates.append(ClipCandidate(
                    video_id="",
                    start_time=seg.start_time,
                    end_time=seg.end_time,
                    hook_text=f"Surprising: {seg.text[:60]}",
                    category="surprising",
                    strategy=ClipStrategy.SURPRISING_CLAIM,
                ))
        return candidates

    async def _strategy_complete_thought(self, segments: List[Segment], transcript: dict) -> List[ClipCandidate]:
        """Strategy G: Complete thoughts"""
        complete_indices = TranscriptProcessor.detect_complete_thoughts(segments)
        candidates = []
        for idx in complete_indices:
            seg = segments[idx]
            if 10 <= seg.end_time - seg.start_time <= 60:
                candidates.append(ClipCandidate(
                    video_id="",
                    start_time=seg.start_time,
                    end_time=seg.end_time,
                    hook_text=f"Complete thought: {seg.text[:60]}",
                    category="complete_thought",
                    strategy=ClipStrategy.COMPLETE_THOUGHT,
                ))
        return candidates

    async def _strategy_keyword_trigger(self, segments: List[Segment], transcript: dict) -> List[ClipCandidate]:
        """Strategy H: Keyword-triggered segments"""
        triggered = TranscriptProcessor.detect_keywords(segments)
        candidates = []
        for idx, keywords in triggered.items():
            seg = segments[idx]
            candidates.append(ClipCandidate(
                video_id="",
                start_time=seg.start_time,
                end_time=seg.end_time,
                hook_text=f"Keywords {keywords}: {seg.text[:60]}",
                category="keyword",
                strategy=ClipStrategy.KEYWORD_TRIGGER,
            ))
        return candidates


class GeminiIntegration:
    """Integration with Google Gemini API for advanced analysis"""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.client = None

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def analyze_video(self, transcript_text: str, duration: float) -> dict:
        """Analyze video using Gemini API"""
        if not self.is_available():
            raise ValueError("Gemini API key not configured")

        prompt = self._build_analysis_prompt(transcript_text, duration)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }],
                    "generationConfig": {
                        "temperature": 0.7,
                        "max_output_tokens": 2048,
                    }
                },
                timeout=30,
            )

            if response.status_code != 200:
                raise ValueError(f"Gemini API error: {response.status_code}")

            data = response.json()
            return self._parse_response(data)

    def _build_analysis_prompt(self, transcript: str, duration: float) -> str:
        """Build the Gemini prompt for viral moment detection"""
        return f"""Analyze this video transcript and identify the most viral moments.

Video duration: {duration} seconds

Transcript:
{transcript[:10000]}

For each candidate clip, provide:
1. Timestamps (start_time, end_time)
2. A compelling hook title
3. Category (insight, emotional, humorous, educational, etc.)
4. Viral score (0-100)
5. Confidence level (0-1)
6. Why it would be viral
7. Detection strategy (A-H)

Scoring criteria:
- HOOK_STRENGTH: Does it grab attention immediately?
- EMOTIONAL_PAYOFF: Does it evoke an emotional response?
- QUOTABILITY: Is it memorable and shareable?
- SELF_CONTAINED: Does it make sense without context?
- DENSITY: Is it information-rich?

Return JSON format:
{{
  "candidates": [
    {{
      "start_time": 120.4,
      "end_time": 153.8,
      "hook_text": "...",
      "category": "...",
      "score": 87,
      "confidence": 0.91,
      "strategy": "A",
      "reason": "..."
    }}
  ],
  "topics": ["..."],
  "summary": "..."
}}"""

    def _parse_response(self, data: dict) -> dict:
        """Parse Gemini API response"""
        try:
            candidates = []
            text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            # Parse JSON from text
            json_start = text.find("{")
            if json_start >= 0:
                parsed = json.loads(text[json_start:])
                return parsed
        except Exception as e:
            logger.warning(f"Failed to parse Gemini response: {e}")
        return {"candidates": [], "topics": [], "summary": ""}


class AIAnalysisService:
    """Main service for AI-powered video analysis"""

    def __init__(self):
        self.clip_selection = ClipSelectionEngine()
        self.scoring = ScoringEngine()
        self.gemini = GeminiIntegration()

    async def analyze(self, video_id: str, transcript: dict, segments: List[Segment]) -> AnalysisResult:
        """Run complete AI analysis on video"""
        start_time = datetime.now()

        # Step 1: Process transcript
        if not segments:
            segments = TranscriptProcessor.segment_by_sentences(transcript)

        # Step 2: Detect candidates
        candidates = await self.clip_selection.detect_candidates(
            segments, transcript,
            min_score=float(os.environ.get("CLIPPYME_MIN_VIRAL_SCORE", "60")),
            max_candidates=int(os.environ.get("CLIPPYME_MAX_CLIPS", "20")),
        )

        # Step 3: Try Gemini analysis if available
        if self.gemini.is_available():
            try:
                gemini_results = await self.gemini.analyze_video(
                    transcript.get("full_text", ""),
                    transcript.get("duration", 0)
                )
                # Merge Gemini candidates with local candidates
                for gc in gemini_results.get("candidates", []):
                    candidate = ClipCandidate(
                        video_id=video_id,
                        start_time=gc["start_time"],
                        end_time=gc["end_time"],
                        score=gc["score"],
                        hook_text=gc["hook_text"],
                        category=gc["category"],
                        confidence=gc["confidence"],
                        strategy=ClipStrategy(gc["strategy"]),
                        reason=gc.get("reason", ""),
                    )
                    # Check for duplicates before adding
                    if not any(abs(c.start_time - candidate.start_time) < 5 for c in candidates):
                        candidates.append(candidate)
            except Exception as e:
                logger.warning(f"Gemini analysis failed, using local detection only: {e}")

        # Step 4: Sort and finalize
        candidates.sort(key=lambda c: c.score, reverse=True)
        candidates = candidates[:20]

        # Step 5: Detect topics
        topics = self._extract_topics(segments)

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        return AnalysisResult(
            video_id=video_id,
            total_duration=transcript.get("duration", 0),
            candidates=candidates,
            segments=segments,
            topics=topics,
            language=transcript.get("language", "en"),
            processing_time_seconds=processing_time,
            metadata={
                "total_candidates": len(candidates),
                "processing_time": processing_time,
                "gemini_used": self.gemini.is_available(),
            },
        )

    def _extract_topics(self, segments: List[Segment]) -> list[str]:
        """Extract topics from segments"""
        topic_changes = TranscriptProcessor.detect_topic_changes(segments)
        topics = []
        if topic_changes:
            for idx in topic_changes[:5]:  # Max 5 topics
                if idx < len(segments):
                    topics.append(segments[idx].text[:50])
        return topics if topics else ["general"]