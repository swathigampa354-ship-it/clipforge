"""
Ollama AI service integration
Provides: text generation, embeddings, summarization
"""
from __future__ import annotations

import json
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

import httpx

from api.app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class OllamaResponse:
    """Response from Ollama API"""
    model: str
    created_at: str
    response: str
    done: bool
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    prompt_eval_duration: Optional[int] = None
    eval_count: Optional[int] = None
    eval_duration: Optional[int] = None


class OllamaService:
    """Ollama API integration for AI tasks"""

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model = model or settings.OLLAMA_MODEL
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=120.0)

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        stream: bool = False,
        options: Optional[dict] = None,
    ) -> str:
        """
        Generate text using Ollama
        
        Args:
            prompt: The prompt to send to the model
            system: Optional system prompt
            stream: Whether to stream the response
            options: Additional generation options (temperature, etc.)
        
        Returns:
            Generated text response
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
        }
        if system:
            payload["system"] = system
        if options:
            payload["options"] = options

        try:
            response = await self.client.post(
                "/api/generate",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except httpx.HTTPError as e:
            logger.error(f"Ollama generate error: {str(e)}")
            raise

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        stream: bool = False,
        options: Optional[dict] = None,
    ) -> str:
        """
        Send a chat message to Ollama
        
        Args:
            messages: List of chat messages [{"role": "user", "content": "..."}]
            system: Optional system prompt
            stream: Whether to stream the response
            options: Additional generation options
        
        Returns:
            Chat response
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
        }
        if system:
            payload["system"] = system
        if options:
            payload["options"] = options

        try:
            response = await self.client.post(
                "/api/chat",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "")
        except httpx.HTTPError as e:
            logger.error(f"Ollama chat error: {str(e)}")
            raise

    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None,
    ) -> List[List[float]]:
        """
        Generate embeddings using Ollama
        
        Args:
            texts: List of texts to embed
            model: Optional embedding model override
        
        Returns:
            List of embedding vectors
        """
        embed_model = model or settings.OLLAMA_EMBEDDING_MODEL
        payload = {
            "model": embed_model,
            "input": texts,
        }

        try:
            response = await self.client.post(
                "/api/embed",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            embeddings = data.get("embeddings", [])
            return embeddings
        except httpx.HTTPError as e:
            logger.error(f"Ollama embed error: {str(e)}")
            raise

    async def summarize(
        self,
        text: str,
        max_length: int = 200,
    ) -> str:
        """
        Summarize text using Ollama
        
        Args:
            text: Text to summarize
            max_length: Maximum length of summary
        
        Returns:
            Summary text
        """
        prompt = f"""Summarize the following text in {max_length} words or less:

{text}

Summary:"""
        return await self.generate(prompt)

    async def extract_topics(
        self,
        text: str,
        max_topics: int = 5,
    ) -> List[str]:
        """
        Extract topics from text using Ollama
        
        Args:
            text: Text to analyze
            max_topics: Maximum number of topics to extract
        
        Returns:
            List of topics
        """
        prompt = f"""Extract the top {max_topics} topics from the following text.
Return ONLY a comma-separated list of topics, no other text.

{text}"""
        result = await self.generate(prompt)
        topics = [t.strip() for t in result.split(",") if t.strip()]
        return topics[:max_topics]

    async def generate_clip_analysis(
        self,
        transcript_segment: str,
        segment_start: float,
        segment_end: float,
    ) -> Dict[str, Any]:
        """
        Generate AI analysis for a transcript segment
        
        Args:
            transcript_segment: The transcript text
            segment_start: Start time in seconds
            segment_end: End time in seconds
        
        Returns:
            Analysis dict with score, hook, category, confidence
        """
        prompt = f"""Analyze this video transcript segment for clip potential.

Segment from {segment_start}s to {segment_end}s:
{transcript_segment}

Return JSON with:
- hook_score: 0-100 (how strong is the hook)
- information_density: 0-100 (how information-dense)
- emotional_intensity: 0-100 (emotional impact)
- novelty: 0-100 (how novel/unique)
- narrative_completeness: 0-100 (does it tell a complete story)
- curiosity: 0-100 (how curious/engaging)
- quotability: 0-100 (how quotable)
- audience_relevance: 0-100 (relevant to audience)
- dead_air: 0-100 (how much dead air/pauses)
- context_dependency: 0-100 (how much context needed)
- duplicate_content: 0-100 (how much duplicate content)
- hook_text: A one-line hook for this segment
- category: One of: education, entertainment, motivation, news, comedy, tutorial
- confidence: 0-100 (overall confidence)

Return ONLY valid JSON."""

        try:
            result = await self.generate(prompt)
            # Parse JSON from response
            json_str = result.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            analysis = json.loads(json_str)
            return analysis
        except (json.JSONDecodeError, httpx.HTTPError) as e:
            logger.error(f"Clip analysis error: {str(e)}")
            return {
                "hook_score": 50,
                "information_density": 50,
                "emotional_intensity": 50,
                "novelty": 50,
                "narrative_completeness": 50,
                "curiosity": 50,
                "quotability": 50,
                "audience_relevance": 50,
                "dead_air": 50,
                "context_dependency": 50,
                "duplicate_content": 50,
                "hook_text": "Untitled Clip",
                "category": "general",
                "confidence": 0,
            }

    async def generate_metadata(
        self,
        transcript: str,
    ) -> Dict[str, Any]:
        """
        Generate video metadata using Ollama
        
        Args:
            transcript: Full transcript
        
        Returns:
            Metadata dict with title, description, hashtags
        """
        prompt = f"""Generate metadata for a video based on this transcript.

Transcript:
{transcript[:5000]}

Return JSON with:
- title: An engaging title (max 60 chars)
- description: A short description (max 200 chars)
- hashtags: Array of 5-10 relevant hashtags
- keywords: Array of 5-10 keywords
- summary: A one-sentence summary
- thumbnail_prompt: Description for a thumbnail image

Return ONLY valid JSON."""

        try:
            result = await self.generate(prompt)
            json_str = result.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            metadata = json.loads(json_str)
            return metadata
        except (json.JSONDecodeError, httpx.HTTPError) as e:
            logger.error(f"Metadata generation error: {str(e)}")
            return {
                "title": "Untitled Video",
                "description": "A video generated by ClipForge",
                "hashtags": [],
                "keywords": [],
                "summary": "",
                "thumbnail_prompt": "",
            }

    async def health_check(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = await self.client.get("/api/tags")
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    async def list_models(self) -> List[str]:
        """List available Ollama models"""
        try:
            response = await self.client.get("/api/tags")
            data = response.json()
            return [m.get("name", "") for m in data.get("models", [])]
        except httpx.HTTPError:
            return []

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()