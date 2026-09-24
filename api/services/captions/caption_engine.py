"""
Caption Engine — Phase 5
Word-level timing, subtitle formats, styling, emoji integration
"""
from __future__ import annotations

import json
import logging
import math
import re
import statistics
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Tuple
from uuid import uuid4
from datetime import datetime, timezone

import cv2
import numpy as np

from api.app.config import settings

logger = logging.getLogger(__name__)


class CaptionFormat(str, Enum):
    SRT = "srt"
    VTT = "vtt"
    JSON = "json"
    ASS = "ass"


class CaptionAlignment(str, Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    AUTO = "auto"


class CaptionAnimation(str, Enum):
    FADE = "fade"
    SLIDE = "slide"
    ZOOM = "zoom"
    POP = "pop"
    TYPEWRITER = "typewriter"
    NONE = "none"


class CaptionEmojiStyle(str, Enum):
    OFF = "off"
    RECOMMENDED = "recommended"
    AGGRESSIVE = "aggressive"


@dataclass
class CaptionWord:
    """A single word with timing"""
    text: str
    start: float  # seconds
    end: float  # seconds
    confidence: float
    alternatives: List[str] = field(default_factory=list)


@dataclass
class CaptionLine:
    """A line of captions (multiple words)"""
    text: str
    start: float
    end: float
    words: List[CaptionWord] = field(default_factory=list)
    emoji_replacement: Optional[dict] = None
    style_override: Optional[dict] = None


@dataclass
class CaptionSegment:
    """A segment of synchronized captions"""
    id: str = field(default_factory=lambda: str(uuid4()))
    lines: List[CaptionLine] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0
    language: str = "en"
    style: Optional[dict] = None


@dataclass
class CaptionStyle:
    """Caption styling configuration"""
    font_family: str = "Inter"
    font_size: int = 24
    font_color: str = "#FFFFFF"
    background_color: str = "#000000"
    background_opacity: float = 0.7
    outline: bool = True
    outline_color: str = "#000000"
    outline_width: int = 2
    shadow: bool = False
    shadow_color: str = "#000000"
    shadow_blur: int = 4
    position: str = "bottom"
    max_words_per_line: int = 5
    max_lines: int = 2
    animation_type: str = "fade"
    animation_duration: float = 0.3
    letter_spacing: float = 0.0
    word_wrap: bool = True
    custom_css: Optional[str] = None


class CaptionEngine:
    """Main caption generation engine"""

    def __init__(self):
        self.whisper_model = None
        self._load_whisper()

    def _load_whisper(self):
        """Load Faster-Whisper model for transcription"""
        try:
            from faster_whisper import WhisperModel
            model_size = getattr(settings, 'WHISPER_MODEL_SIZE', 'medium')
            self.whisper_model = WhisperModel(
                model_size,
                device="cpu",
                compute_type="int8",
                cpu_threads=4,
            )
            logger.info(f"Faster-Whisper {model_size} model loaded")
        except ImportError:
            logger.warning("Faster-Whisper not available. Using fallback transcription.")
            self.whisper_model = None

    def generate_captions(
        self,
        transcript: List[dict],
        video_duration: float,
        language: str = "en",
        style: Optional[CaptionStyle] = None,
        emoji_style: CaptionEmojiStyle = CaptionEmojiStyle.RECOMMENDED,
    ) -> List[CaptionSegment]:
        """
        Generate captions from transcript data
        
        Process:
        1. Parse transcript into word-level segments
        2. Group words into caption lines (max words per line)
        3. Apply timing adjustments (minimum display time)
        4. Detect and replace emojis
        5. Apply styling rules
        6. Generate segments with proper timing
        """
        if style is None:
            style = CaptionStyle()

        # Parse transcript
        words = self._parse_transcript(transcript)

        # Generate word-level timing
        timed_words = self._assign_timing(words, video_duration)

        # Group into lines
        lines = self._group_into_lines(timed_words, style.max_words_per_line)

        # Process each line
        segments = self._create_segments(lines, language, style, emoji_style)

        return segments

    def _parse_transcript(self, transcript: List[dict]) -> List[CaptionWord]:
        """Parse transcript data into CaptionWord objects"""
        words = []

        for segment in transcript:
            text = segment.get("text", "")
            start = segment.get("start", 0.0)
            end = segment.get("end", 0.0)
            confidence = segment.get("confidence", 0.9)

            # Split text into words
            tokens = re.findall(r'\S+|\s+', text)
            word_start = start

            for token in tokens:
                if token.isspace():
                    word_start += len(token) * 0.1  # Approximate space duration
                    continue

                word_end = word_start + self._estimate_word_duration(token, confidence)
                words.append(CaptionWord(
                    text=token,
                    start=word_start,
                    end=word_end,
                    confidence=confidence,
                ))
                word_start = word_end

        return words

    def _estimate_word_duration(self, word: str, confidence: float) -> float:
        """Estimate word duration based on length and confidence"""
        base_duration = len(word) * 0.05 + 0.08  # Average character duration
        return base_duration * (1.0 + (1.0 - confidence) * 0.5)

    def _assign_timing(
        self,
        words: List[CaptionWord],
        video_duration: float
    ) -> List[CaptionWord]:
        """Adjust word timing to fit within video duration"""
        if not words:
            return []

        total_duration = words[-1].end - words[0].start
        if total_duration <= 0:
            return words

        # Scale timing to fit video duration
        scale = video_duration / total_duration
        scale = min(scale, 1.2)  # Don't stretch more than 20%

        adjusted_words = []
        for word in words:
            adjusted_words.append(CaptionWord(
                text=word.text,
                start=word.start * scale,
                end=word.end * scale,
                confidence=word.confidence,
            ))

        return adjusted_words

    def _group_into_lines(
        self,
        words: List[CaptionWord],
        max_words_per_line: int
    ) -> List[CaptionLine]:
        """Group words into caption lines"""
        lines = []
        current_words = []
        current_start = 0.0
        current_end = 0.0

        for word in words:
            current_words.append(word)
            current_end = max(current_end, word.end)

            if len(current_words) >= max_words_per_line:
                lines.append(CaptionLine(
                    text=" ".join(w.text for w in current_words),
                    start=current_start,
                    end=current_end,
                    words=list(current_words),
                ))
                current_words = []
                current_start = word.end

        if current_words:
            lines.append(CaptionLine(
                text=" ".join(w.text for w in current_words),
                start=current_start,
                end=current_end,
                words=list(current_words),
            ))

        return lines

    def _create_segments(
        self,
        lines: List[CaptionLine],
        language: str,
        style: CaptionStyle,
        emoji_style: CaptionEmojiStyle,
    ) -> List[CaptionSegment]:
        """Create caption segments from lines"""
        segments = []
        current_segment = CaptionSegment(
            language=language,
            style=self._style_to_dict(style),
        )

        for line in lines:
            # Check if line fits in current segment
            if not current_segment.lines:
                current_segment.start_time = line.start
            else:
                last_line = current_segment.lines[-1]
                gap = line.start - last_line.end
                if gap > 1.5 or len(current_segment.lines) >= 3:
                    # Finalize current segment
                    current_segment.end_time = last_line.end
                    current_segment.duration = current_segment.end_time - current_segment.start_time
                    segments.append(current_segment)
                    current_segment = CaptionSegment(language=language, style=self._style_to_dict(style))
                    current_segment.start_time = line.start

            # Process emoji replacement
            processed_line = self._process_emoji(line, emoji_style)
            current_segment.lines.append(processed_line)
            current_segment.end_time = max(current_segment.end_time, line.end)

        # Add final segment
        if current_segment.lines:
            current_segment.end_time = max(current_segment.end_time, current_segment.lines[-1].end)
            current_segment.duration = current_segment.end_time - current_segment.start_time
            segments.append(current_segment)

        return segments

    def _process_emoji(self, line: CaptionLine, emoji_style: CaptionEmojiStyle) -> CaptionLine:
        """Process emojis in caption line"""
        if emoji_style == CaptionEmojiStyle.OFF:
            return line

        # Emoji replacement based on context
        emoji_map = self._get_emoji_replacements(line.text)
        if emoji_map:
            return CaptionLine(
                text=line.text,
                start=line.start,
                end=line.end,
                words=line.words,
                emoji_replacement=emoji_map,
            )
        return line

    def _get_emoji_replacements(self, text: str) -> Optional[dict]:
        """Get emoji replacements for caption text"""
        emoji_patterns = {
            r'\b(laugh|lmao|lol|hahaha)\b': '😂',
            r'\b(sad|cry|😢)\b': '😢',
            r'\b(happy|excited|wow)\b': '😃',
            r'\b(love|❤️)\b': '❤️',
            r'\b(angry|mad|furious)\b': '😠',
            r'\b(surprise|wow|holy)\b': '😱',
            r'\b(think|hmm|interesting)\b': '🤔',
            r'\b(fire|lit|hot)\b': '🔥',
        }

        replacements = {}
        for pattern, emoji in emoji_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                replacements[pattern] = emoji

        return replacements if replacements else None

    @staticmethod
    def _style_to_dict(style: CaptionStyle) -> dict:
        """Convert CaptionStyle to dict"""
        return {
            "font_family": style.font_family,
            "font_size": style.font_size,
            "font_color": style.font_color,
            "background_color": style.background_color,
            "background_opacity": style.background_opacity,
            "outline": style.outline,
            "outline_color": style.outline_color,
            "outline_width": style.outline_width,
            "shadow": style.shadow,
            "shadow_color": style.shadow_color,
            "shadow_blur": style.shadow_blur,
            "position": style.position,
            "max_words_per_line": style.max_words_per_line,
            "max_lines": style.max_lines,
            "animation_type": style.animation_type,
            "animation_duration": style.animation_duration,
            "letter_spacing": style.letter_spacing,
            "word_wrap": style.word_wrap,
        }


class SubtitleGenerator:
    """Generate subtitle files in various formats"""

    @staticmethod
    def to_srt(segments: List[CaptionSegment]) -> str:
        """Generate SRT subtitle file"""
        lines = []
        for i, segment in enumerate(segments, 1):
            lines.append(str(i))
            lines.append(f"{SubtitleGenerator._format_time(segment.start_time)} --> {SubtitleGenerator._format_time(segment.end_time)}")

            for line in segment.lines:
                lines.append(line.text)

            lines.append("")  # Empty line separator

        return "\n".join(lines)

    @staticmethod
    def to_vtt(segments: List[CaptionSegment]) -> str:
        """Generate WebVTT subtitle file"""
        lines = ["WEBVTT", ""]

        for segment in segments:
            lines.append(f"{SubtitleGenerator._format_time_vtt(segment.start_time)} --> {SubtitleGenerator._format_time_vtt(segment.end_time)}")

            for line in segment.lines:
                lines.append(line.text)

            lines.append("")  # Empty line separator

        return "\n".join(lines)

    @staticmethod
    def to_json(segments: List[CaptionSegment]) -> str:
        """Generate JSON subtitle format"""
        output = []
        for segment in segments:
            output.append({
                "id": segment.id,
                "start": segment.start_time,
                "end": segment.end_time,
                "duration": segment.duration,
                "language": segment.language,
                "lines": [
                    {
                        "text": line.text,
                        "start": line.start,
                        "end": line.end,
                        "words": [w.text for w in line.words],
                    }
                    for line in segment.lines
                ],
                "style": segment.style,
            })
        return json.dumps(output, indent=2)

    @staticmethod
    def to_ass(segments: List[CaptionSegment], style: Optional[CaptionStyle] = None) -> str:
        """Generate ASS (Advanced SubStation Alpha) subtitle file"""
        if style is None:
            style = CaptionStyle()

        lines = [
            "[Script Info]",
            f"ScriptType: v4.00+",
            f"Name: ClipForge",
            "",
            "[V4+ Styles]",
            f"Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            f"Style: Default,{style.font_family},{style.font_size},&H{SubtitleGenerator._color_to_hex(style.font_color)},"
            f"&H000000FF,&H{SubtitleGenerator._color_to_hex(style.outline_color)},&H{SubtitleGenerator._color_to_hex(style.background_color)},"
            f"{'-1' if style.outline else '0'},{'-1' if style.shadow else '0'},0,0,100,100,1,2,{style.outline_width},1,"
            f"{SubtitleGenerator._alignment_value(style.position)},30,30,30,1",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        ]

        for segment in segments:
            for line in segment.lines:
                start = SubtitleGenerator._format_time_ass(line.start)
                end = SubtitleGenerator._format_time_ass(line.end)
                text = SubtitleGenerator._escape_ass(line.text)
                lines.append(f"0,{start},{end},Default,,0,0,0,,{text}")

        return "\n".join(lines)

    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format time as SRT timestamp"""
        total_ms = int(seconds * 1000)
        hours = total_ms // 3600000
        minutes = (total_ms % 3600000) // 60000
        secs = (total_ms % 60000) // 1000
        ms = total_ms % 1000
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"

    @staticmethod
    def _format_time_vtt(seconds: float) -> str:
        """Format time as VTT timestamp"""
        total_ms = int(seconds * 1000)
        hours = total_ms // 3600000
        minutes = (total_ms % 3600000) // 60000
        secs = (total_ms % 60000) // 1000
        ms = total_ms % 1000
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{ms:03d}"

    @staticmethod
    def _format_time_ass(seconds: float) -> str:
        """Format time as ASS timestamp"""
        total_ms = int(seconds * 100)
        hours = total_ms // 360000
        minutes = (total_ms % 360000) // 6000
        secs = (total_ms % 6000) // 100
        return f"{hours:01d}:{minutes:02d}:{secs:02d}"

    @staticmethod
    def _color_to_hex(color: str) -> str:
        """Convert hex color to ASS format"""
        color = color.lstrip("#")
        if len(color) == 6:
            r, g, b = color[0:2], color[2:4], color[4:6]
            return f"{int(b, 16):02X}{int(g, 16):02X}{int(r, 16):02X}"
        return "FFFFFF"

    @staticmethod
    def _alignment_value(position: str) -> int:
        """Get ASS alignment value"""
        alignment_map = {
            "top": 9, "center": 2, "bottom": 1,
            "top-left": 7, "top-center": 8, "top-right": 9,
            "middle-left": 4, "middle-center": 5, "middle-right": 6,
            "bottom-left": 1, "bottom-center": 2, "bottom-right": 3,
        }
        return alignment_map.get(position, 2)

    @staticmethod
    def _escape_ass(text: str) -> str:
        """Escape text for ASS format"""
        text = text.replace("\\", "\\\\")
        text = text.replace("{", "\\{")
        text = text.replace("}", "\\}")
        text = text.replace("\n", "\\N")
        return text


class CaptionRenderer:
    """Render captions onto video frames"""

    def __init__(self):
        self.frame_cache = {}

    def render_caption(
        self,
        frame: np.ndarray,
        caption_line: CaptionLine,
        style: CaptionStyle,
        frame_number: int = 0,
    ) -> np.ndarray:
        """Render a caption line onto a frame"""
        # This would use OpenCV to render text on the frame
        # In production, this uses proper font rendering

        frame_height, frame_width = frame.shape[:2]
        font_scale = style.font_size / 100.0
        thickness = max(1, int(font_scale * 2))

        # Calculate text position
        text_size = cv2.getTextSize(
            caption_line.text, cv2.FONT_HERSHEY_SIMPLEX,
            font_scale, thickness
        )[0]

        if style.position == "bottom":
            y_pos = frame_height - 100
        elif style.position == "top":
            y_pos = 50
        else:
            y_pos = frame_height // 2

        x_pos = (frame_width - text_size[0]) // 2

        # Draw background
        if style.background_color:
            bg_x = max(0, x_pos - 10)
            bg_y = max(0, y_pos - text_size[1] - 10)
            bg_w = text_size[0] + 20
            bg_h = text_size[1] + 20
            cv2.rectangle(frame, (bg_x, bg_y), (bg_x + bg_w, bg_y + bg_h),
                         self._hex_to_bgr(style.background_color), -1)

        # Draw outline
        if style.outline:
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                cv2.putText(frame, caption_line.text, (x_pos + dx, y_pos + dy),
                           cv2.FONT_HERSHEY_SIMPLEX, font_scale,
                           self._hex_to_bgr(style.outline_color),
                           thickness + 2)

        # Draw text
        cv2.putText(frame, caption_line.text, (x_pos, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, font_scale,
                   self._hex_to_bgr(style.font_color), thickness)

        return frame

    @staticmethod
    def _hex_to_bgr(hex_color: str) -> tuple:
        """Convert hex color to BGR tuple"""
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 6:
            return (int(hex_color[4:6], 16), int(hex_color[2:4], 16), int(hex_color[0:2], 16))
        return (0, 0, 0)

    def render_caption_overlay(
        self,
        frame: np.ndarray,
        segment: CaptionSegment,
        current_time: float,
        style: CaptionStyle,
    ) -> np.ndarray:
        """Render all active captions for a frame"""
        for line in segment.lines:
            if line.start <= current_time <= line.end:
                frame = self.render_caption(frame, line, style)
        return frame


class CaptionAnalyzer:
    """Analyze caption quality and readability"""

    @staticmethod
    def analyze_readability(segments: List[CaptionSegment]) -> dict:
        """Analyze caption readability metrics"""
        total_words = 0
        total_lines = 0
        readability_scores = []
        timing_issues = []

        for segment in segments:
            segment_words = 0
            for line in segment.lines:
                segment_words += len(line.text.split())
                total_lines += 1

                # Check timing issues
                line_duration = line.end - line.start
                if line_duration < 1.0:
                    timing_issues.append({
                        "segment_id": segment.id,
                        "text": line.text[:30],
                        "issue": "too_short",
                        "duration": line_duration,
                    })
                if line_duration > 7.0:
                    timing_issues.append({
                        "segment_id": segment.id,
                        "text": line.text[:30],
                        "issue": "too_long",
                        "duration": line_duration,
                    })

                # Check words per line
                words_in_line = len(line.text.split())
                if words_in_line > 8:
                    timing_issues.append({
                        "segment_id": segment.id,
                        "text": line.text[:30],
                        "issue": "too_many_words",
                        "word_count": words_in_line,
                    })

            total_words += segment_words
            readability_scores.append(segment_words / max(len(segment.lines), 1))

        avg_words_per_line = total_words / max(total_lines, 1)
        avg_readability = statistics.mean(readability_scores) if readability_scores else 0

        return {
            "total_segments": len(segments),
            "total_words": total_words,
            "total_lines": total_lines,
            "avg_words_per_line": round(avg_words_per_line, 2),
            "avg_readability_score": round(avg_readability, 2),
            "timing_issues": timing_issues,
            "readability_grade": CaptionAnalyzer._calculate_grade(avg_readability),
        }

    @staticmethod
    def _calculate_grade(score: float) -> str:
        """Calculate readability grade"""
        if score >= 8.0:
            return "A+"
        elif score >= 7.0:
            return "A"
        elif score >= 6.0:
            return "B"
        elif score >= 5.0:
            return "C"
        elif score >= 4.0:
            return "D"
        else:
            return "F"

    @staticmethod
    def detect_overlap(segments: List[CaptionSegment]) -> List[dict]:
        """Detect timing overlaps between caption segments"""
        overlaps = []
        for i, seg1 in enumerate(segments):
            for seg2 in segments[i + 1:]:
                if seg1.start_time < seg2.end_time and seg2.start_time < seg1.end_time:
                    overlaps.append({
                        "segment_1": seg1.id,
                        "segment_2": seg2.id,
                        "overlap_start": max(seg1.start_time, seg2.start_time),
                        "overlap_end": min(seg1.end_time, seg2.end_time),
                        "overlap_duration": min(seg1.end_time, seg2.end_time) - max(seg1.start_time, seg2.start_time),
                    })
        return overlaps