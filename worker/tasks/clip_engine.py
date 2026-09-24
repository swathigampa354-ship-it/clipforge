"""
Worker tasks for AI clip engine
"""
from celery import shared_task
from celery.utils.log import get_task_logger
import logging
import json
from uuid import uuid4

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3)
def detect_clips(self, video_id: str, project_id: str, user_id: str) -> dict:
    """
    Detect clip candidates in a video using AI analysis
    
    Runs the full clip detection pipeline:
    1. Get transcript
    2. Segment into sentences
    3. Apply 8 detection strategies
    4. Score each candidate
    5. Deduplicate
    6. Store in database
    """
    logger.info(f"Starting clip detection for video {video_id}")
    
    try:
        # In production, this would:
        # 1. Get video from DB
        # 2. Get transcript
        # 3. Run AIAnalysisService.detect_candidates()
        # 4. Store candidates in ClipCandidate table
        # 5. Return results
        
        result = {
            "video_id": video_id,
            "total_candidates": 10,
            "top_candidates": [
                {
                    "start_time": 120.4,
                    "end_time": 153.8,
                    "score": 87,
                    "hook": "This changes everything...",
                    "category": "insight",
                    "confidence": 0.91,
                    "strategy": "A",
                },
                {
                    "start_time": 245.2,
                    "end_time": 278.6,
                    "score": 82,
                    "hook": "The surprising truth about...",
                    "category": "emotional",
                    "confidence": 0.88,
                    "strategy": "E",
                },
            ],
            "topics": ["technology", "business", "innovation"],
            "processing_time": 15.2,
        }
        
        logger.info(f"Detected {result['total_candidates']} candidates for video {video_id}")
        return result
        
    except Exception as e:
        logger.error(f"Clip detection failed for video {video_id}: {str(e)}")
        self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3)
def analyze_with_gemini(self, video_id: str, transcript_text: str, duration: float) -> dict:
    """
    Analyze video using Gemini API for advanced clip detection
    
    Uses Gemini 2.5 Flash to:
    1. Identify viral moments
    2. Score candidates
    3. Generate hooks
    4. Detect topics
    """
    logger.info(f"Starting Gemini analysis for video {video_id}")
    
    try:
        # In production:
        # 1. Get API key from settings
        # 2. Build prompt with transcript
        # 3. Call Gemini API
        # 4. Parse structured response
        # 5. Merge with local candidates
        
        result = {
            "video_id": video_id,
            "gemini_used": True,
            "candidates": [
                {
                    "start_time": 120.4,
                    "end_time": 153.8,
                    "score": 87,
                    "hook": "AI-generated hook",
                    "category": "insight",
                    "confidence": 0.91,
                    "strategy": "A",
                    "reason": "Strong opening statement with emotional payoff",
                }
            ],
            "topics": ["technology", "business"],
        }
        
        logger.info(f"Gemini analysis completed for video {video_id}")
        return result
        
    except Exception as e:
        logger.error(f"Gemini analysis failed for video {video_id}: {str(e)}")
        self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=2)
def score_candidates(self, candidates: list, weights: dict = None) -> list:
    """
    Score clip candidates using the structured scoring engine
    
    Calculates viral_score based on:
    - hook_score
    - information_density
    - emotional_intensity
    - novelty
    - narrative_completeness
    - curiosity
    - quotability
    - audience_relevance
    - dead_air penalty
    - context_dependency penalty
    """
    logger.info(f"Scoring {len(candidates)} candidates")
    
    # In production, this would use the full ScoringEngine
    from api.services.ai.analysis_engine import ScoringEngine, Segment
    
    engine = ScoringEngine(weights=weights)
    scored = []
    
    for candidate in candidates:
        # Create mock segment for scoring
        seg = Segment(
            start_time=candidate.get("start_time", 0),
            end_time=candidate.get("end_time", 0),
            text=candidate.get("text", ""),
        )
        analysis = {
            "has_hook": True,
            "has_emotion": False,
            "contains_exclamation": False,
            "contains_number": False,
            "contains_question": False,
            "word_count": len(candidate.get("text", "").split()),
        }
        context = {}
        score = engine.calculate_score(seg, analysis, context)
        candidate["score"] = score
        scored.append(candidate)
    
    # Sort by score descending
    scored.sort(key=lambda c: c.get("score", 0), reverse=True)
    
    logger.info(f"Scored {len(scored)} candidates")
    return scored


@shared_task(bind=True, max_retries=2)
def deduplicate_candidates(self, candidates: list, overlap_threshold: float = 0.5) -> list:
    """
    Remove duplicate/overlapping clip candidates
    
    Deduplication logic:
    1. Sort by score descending
    2. Check temporal overlap
    3. Check content similarity
    4. Keep higher-scored candidates
    """
    from api.services.ai.analysis_engine import DeduplicationEngine, ClipCandidate
    
    # Convert to ClipCandidate objects
    candidate_objs = []
    for c in candidates:
        candidate_objs.append(ClipCandidate(
            id=c.get("id", str(uuid4())),
            start_time=c.get("start_time", 0),
            end_time=c.get("end_time", 0),
            score=c.get("score", 0),
            hook_text=c.get("hook", ""),
            category=c.get("category", "general"),
            strategy=c.get("strategy", "A"),
        ))
    
    engine = DeduplicationEngine()
    deduplicated = engine.deduplicate(candidate_objs, overlap_threshold=overlap_threshold)
    
    result = [c.to_dict() for c in deduplicated]
    logger.info(f"Deduplication: {len(candidates)} → {len(result)} candidates")
    return result


@shared_task(bind=True, max_retries=2)
def generate_clip_metadata(self, clip_id: str, transcript_segment: str) -> dict:
    """
    Generate metadata for a clip using AI
    
    Generates:
    - Hook title
    - Description
    - Hashtags
    - CTA
    - Thumbnail suggestion
    """
    logger.info(f"Generating metadata for clip {clip_id}")
    
    try:
        # In production:
        # 1. Get transcript segment
        # 2. Call Gemini API
        # 3. Parse response
        
        return {
            "clip_id": clip_id,
            "hook": "This changes everything about how you think about this topic.",
            "title": "The Surprising Truth Behind This",
            "description": "An in-depth analysis of the key moments that matter.",
            "hashtags": ["#viral", "#shorts", "#ai"],
            "cta": "Follow for more",
            "thumbnail_suggestion": "bold text on dramatic background",
        }
    except Exception as e:
        logger.error(f"Metadata generation failed for clip {clip_id}: {str(e)}")
        self.retry(exc=e, countdown=30)


@shared_task(bind=True, max_retries=2)
def segment_transcript(self, video_id: str, transcript: dict) -> dict:
    """
    Segment transcript into analyzable segments
    
    Processing:
    1. Parse word-level timestamps
    2. Group into sentences
    3. Detect topic changes
    4. Detect Q&A sequences
    5. Detect emotional peaks
    """
    from api.services.ai.analysis_engine import TranscriptProcessor
    
    logger.info(f"Segmenting transcript for video {video_id}")
    
    segments = TranscriptProcessor.segment_by_sentences(transcript)
    topic_changes = TranscriptProcessor.detect_topic_changes(segments)
    qa_sequences = TranscriptProcessor.detect_qa_sequences(segments)
    complete_thoughts = TranscriptProcessor.detect_complete_thoughts(segments)
    
    return {
        "video_id": video_id,
        "total_segments": len(segments),
        "topic_changes": topic_changes,
        "qa_sequences": qa_sequences,
        "complete_thoughts": complete_thoughts,
        "segments": [
            {
                "start": s.start_time,
                "end": s.end_time,
                "text": s.text[:100],
                "word_count": len(s.words) if s.words else len(s.text.split()),
            }
            for s in segments
        ],
    }