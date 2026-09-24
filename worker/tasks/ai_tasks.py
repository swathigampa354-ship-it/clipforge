"""
AI tasks for clip analysis and metadata generation
"""
from __future__ import annotations

import logging

from celery import shared_task
from celery.utils.log import get_task_logger

from api.app.config import settings

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3)
def analyze_video_content(self, video_id: str, transcript_text: str, transcript_segments: list = None) -> dict:
    """Analyze video content using local analysis engine (not Gemini API)"""
    logger.info(f"Analyzing video content for video {video_id}")
    
    try:
        from api.services.ai.analysis_engine import AIAnalysisService, Segment
        
        engine = AIAnalysisService()
        
        # Parse segments if provided
        segments = []
        if transcript_segments:
            for seg in transcript_segments:
                segments.append(Segment(
                    start_time=seg.get("start", 0),
                    end_time=seg.get("end", 0),
                    text=seg.get("text", ""),
                ))
        
        result = await engine.analyze(
            video_id=video_id,
            transcript=transcript_text,
            segments=segments,
        )
        
        return {
            "video_id": video_id,
            "candidates": [c.to_dict() for c in result.candidates],
            "topics": result.topics,
            "total_candidates": len(result.candidates),
            "processing_time": result.processing_time_seconds,
        }
    except Exception as e:
        logger.error(f"Content analysis failed for video {video_id}: {str(e)}")
        # Return empty candidates on error
        return {
            "video_id": video_id,
            "candidates": [],
            "topics": [],
            "total_candidates": 0,
            "error": str(e),
        }


@shared_task(bind=True, max_retries=3)
def generate_hook(self, clip_id: str, transcript_segment: str) -> dict:
    """Generate a hook for a clip using Ollama"""
    logger.info(f"Generating hook for clip {clip_id}")
    
    try:
        from api.services.ai.ollama_service import OllamaService
        
        service = OllamaService()
        prompt = f"""Generate a compelling 1-line hook from this transcript segment:

{transcript_segment}

Return ONLY the hook text, no other commentary."""
        hook = await service.generate(prompt)
        
        return {
            "clip_id": clip_id,
            "hook": hook.strip(),
            "confidence": 0.85,
        }
    except Exception as e:
        logger.error(f"Hook generation failed for clip {clip_id}: {str(e)}")
        return {
            "clip_id": clip_id,
            "hook": "Untitled Hook",
            "confidence": 0.0,
            "error": str(e),
        }


@shared_task(bind=True, max_retries=2)
def generate_title(self, clip_id: str, transcript_text: str) -> dict:
    """Generate title for a clip using Ollama"""
    logger.info(f"Generating title for clip {clip_id}")
    
    try:
        from api.services.ai.ollama_service import OllamaService
        
        service = OllamaService()
        prompt = f"""Generate a compelling video title (max 60 characters) from this transcript:

{transcript_text[:2000]}

Return ONLY the title, no other text."""
        title = await service.generate(prompt)
        
        return {
            "clip_id": clip_id,
            "title": title.strip(),
            "alternatives": [title.strip()],
        }
    except Exception as e:
        logger.error(f"Title generation failed for clip {clip_id}: {str(e)}")
        return {
            "clip_id": clip_id,
            "title": "Untitled Video",
            "alternatives": ["Untitled Video"],
            "error": str(e),
        }


@shared_task(bind=True, max_retries=2)
def generate_hashtags(self, clip_id: str, transcript_text: str) -> dict:
    """Generate hashtags for a clip using Ollama"""
    logger.info(f"Generating hashtags for clip {clip_id}")
    
    try:
        from api.services.ai.ollama_service import OllamaService
        
        service = OllamaService()
        prompt = f"""Extract 8 relevant hashtags from this transcript:

{transcript_text[:2000]}

Return ONLY a comma-separated list of hashtags like #tech #ai #coding, no other text."""
        hashtags_text = await service.generate(prompt)
        hashtags = [h.strip() for h in hashtags_text.split(",") if h.strip().startswith("#")]
        
        return {
            "clip_id": clip_id,
            "hashtags": hashtags[:10],
        }
    except Exception as e:
        logger.error(f"Hashtag generation failed for clip {clip_id}: {str(e)}")
        return {
            "clip_id": clip_id,
            "hashtags": [],
            "error": str(e),
        }


@shared_task(bind=True, max_retries=2)
def detect_complete_thoughts(self, transcript_text: str) -> list:
    """Detect complete thought boundaries in transcript"""
    logger.info("Detecting complete thoughts")
    
    try:
        from api.services.ai.transcript_service import TranscriptService
        from api.services.ai.analysis_engine import TranscriptProcessor
        
        processor = TranscriptProcessor()
        segments = processor.segment_by_sentences(transcript_text)
        
        thoughts = []
        for seg in segments:
            thoughts.append({
                "start": seg.start_time,
                "end": seg.end_time,
                "text": seg.text[:200],
            })
        
        return thoughts
    except Exception as e:
        logger.error(f"Complete thought detection failed: {str(e)}")
        return []


@shared_task(bind=True, max_retries=2)
def score_clips(self, candidates: list) -> list:
    """Score and rank clip candidates using ScoringEngine"""
    logger.info(f"Scoring {len(candidates)} candidates")
    
    try:
        from api.services.ai.analysis_engine import ScoringEngine
        
        engine = ScoringEngine()
        scored = []
        for candidate in candidates:
            score = engine.score(
                hook_score=candidate.get("hook_score", 50),
                information_density=candidate.get("information_density", 50),
                emotional_intensity=candidate.get("emotional_intensity", 50),
                novelty=candidate.get("novelty", 50),
                curiosity=candidate.get("curiosity", 50),
                narrative_completeness=candidate.get("narrative_completeness", 50),
                quotability=candidate.get("quotability", 50),
                audience_relevance=candidate.get("audience_relevance", 50),
                dead_air=candidate.get("dead_air", 50),
                context_dependency=candidate.get("context_dependency", 50),
                duplicate_content=candidate.get("duplicate_content", 50),
            )
            candidate["score"] = score
            scored.append(candidate)
        
        return sorted(scored, key=lambda c: c.get("score", 0), reverse=True)
    except Exception as e:
        logger.error(f"Clip scoring failed: {str(e)}")
        return sorted(candidates, key=lambda c: c.get("score", 0), reverse=True)


@shared_task(bind=True, max_retries=3)
def generate_metadata(self, clip_id: str, transcript_text: str) -> dict:
    """Generate titles, hooks, descriptions, hashtags for a clip using Ollama"""
    logger.info(f"Generating metadata for clip {clip_id}")
    
    try:
        from api.services.ai.ollama_service import OllamaService
        
        service = OllamaService()
        metadata = await service.generate_metadata(transcript_text)
        
        return {"clip_id": clip_id, "metadata": metadata}
    except Exception as e:
        logger.error(f"Metadata generation failed for clip {clip_id}: {str(e)}")
        return {
            "clip_id": clip_id,
            "metadata": {
                "title": "Untitled Video",
                "description": "A video generated by ClipForge",
                "hashtags": [],
                "keywords": [],
                "summary": "",
                "thumbnail_prompt": "",
            },
            "error": str(e),
        }