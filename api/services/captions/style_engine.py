"""
Caption style engine — manages caption themes and templates
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Optional, List
from uuid import uuid4

logger = logging.getLogger(__name__)


# Predefined caption styles
PREDEFINED_STYLES = {
    "clean": {
        "name": "Clean",
        "font_family": "Inter",
        "font_size": 24,
        "font_color": "#FFFFFF",
        "background_color": "#000000",
        "background_opacity": 0.7,
        "outline": True,
        "outline_color": "#000000",
        "outline_width": 2,
        "shadow": False,
        "position": "bottom",
        "max_words_per_line": 5,
        "max_lines": 2,
        "animation_type": "fade",
    },
    "bold": {
        "name": "Bold",
        "font_family": "Anton",
        "font_size": 32,
        "font_color": "#FFFFFF",
        "background_color": "#000000",
        "background_opacity": 0.7,
        "outline": True,
        "outline_color": "#000000",
        "outline_width": 3,
        "shadow": False,
        "position": "bottom",
        "max_words_per_line": 4,
        "max_lines": 2,
        "animation_type": "pop",
    },
    "creator": {
        "name": "Creator",
        "font_family": "Montserrat",
        "font_size": 28,
        "font_color": "#FFD700",
        "background_color": "#1A1A2E",
        "background_opacity": 0.8,
        "outline": True,
        "outline_color": "#16213E",
        "outline_width": 2,
        "shadow": True,
        "position": "bottom",
        "max_words_per_line": 5,
        "max_lines": 2,
        "animation_type": "slide",
    },
    "podcast": {
        "name": "Podcast",
        "font_family": "Source Sans Pro",
        "font_size": 22,
        "font_color": "#E0E0E0",
        "background_color": "#2C2C2C",
        "background_opacity": 0.6,
        "outline": True,
        "outline_color": "#404040",
        "outline_width": 1,
        "shadow": False,
        "position": "bottom",
        "max_words_per_line": 6,
        "max_lines": 2,
        "animation_type": "fade",
    },
    "high_impact": {
        "name": "High Impact",
        "font_family": "Bebas Neue",
        "font_size": 36,
        "font_color": "#FF0000",
        "background_color": "#000000",
        "background_opacity": 0.9,
        "outline": True,
        "outline_color": "#FF0000",
        "outline_width": 2,
        "shadow": True,
        "position": "bottom",
        "max_words_per_line": 4,
        "max_lines": 1,
        "animation_type": "zoom",
    },
    "minimal": {
        "name": "Minimal",
        "font_family": "Helvetica",
        "font_size": 20,
        "font_color": "#FFFFFF",
        "background_color": "transparent",
        "background_opacity": 0.0,
        "outline": False,
        "outline_color": "#000000",
        "outline_width": 1,
        "shadow": False,
        "position": "bottom",
        "max_words_per_line": 6,
        "max_lines": 2,
        "animation_type": "none",
    },
    "modern": {
        "name": "Modern",
        "font_family": "Poppins",
        "font_size": 26,
        "font_color": "#F0F0F0",
        "background_color": "#1E1E2E",
        "background_opacity": 0.75,
        "outline": True,
        "outline_color": "#313244",
        "outline_width": 2,
        "shadow": True,
        "position": "bottom",
        "max_words_per_line": 5,
        "max_lines": 2,
        "animation_type": "slide",
    },
    "retro": {
        "name": "Retro",
        "font_family": "VT323",
        "font_size": 28,
        "font_color": "#00FF41",
        "background_color": "#0A0A0A",
        "background_opacity": 0.9,
        "outline": True,
        "outline_color": "#003300",
        "outline_width": 2,
        "shadow": False,
        "position": "bottom",
        "max_words_per_line": 5,
        "max_lines": 2,
        "animation_type": "typewriter",
    },
}


class StyleEngine:
    """Manages caption style creation, application, and rendering"""

    def __init__(self):
        self.styles = dict(PREDEFINED_STYLES)

    def get_style(self, style_id: str) -> Optional[dict]:
        """Get a caption style by ID"""
        return self.styles.get(style_id)

    def create_style(self, name: str, **kwargs) -> dict:
        """Create a custom caption style"""
        style_id = name.lower().replace(" ", "_")
        style = {
            "id": style_id,
            "name": name,
            "font_family": kwargs.get("font_family", "Inter"),
            "font_size": kwargs.get("font_size", 24),
            "font_color": kwargs.get("font_color", "#FFFFFF"),
            "background_color": kwargs.get("background_color", "#000000"),
            "background_opacity": kwargs.get("background_opacity", 0.7),
            "outline": kwargs.get("outline", True),
            "outline_color": kwargs.get("outline_color", "#000000"),
            "outline_width": kwargs.get("outline_width", 2),
            "shadow": kwargs.get("shadow", False),
            "position": kwargs.get("position", "bottom"),
            "max_words_per_line": kwargs.get("max_words_per_line", 5),
            "max_lines": kwargs.get("max_lines", 2),
            "animation_type": kwargs.get("animation_type", "fade"),
        }
        self.styles[style_id] = style
        return style

    def get_all_styles(self) -> dict:
        """Get all available styles"""
        return dict(self.styles)

    def apply_style_to_captions(
        self,
        segments: list,
        style_id: str,
    ) -> list:
        """Apply a style to caption segments"""
        style = self.get_style(style_id)
        if not style:
            raise ValueError(f"Style {style_id} not found")

        for segment in segments:
            if hasattr(segment, 'style'):
                segment.style = style

        return segments

    def render_style_css(self, style: dict) -> str:
        """Generate CSS for caption rendering"""
        bg_color = style.get("background_color", "#000000")
        bg_opacity = style.get("background_opacity", 0.7)
        font_color = style.get("font_color", "#FFFFFF")
        font_size = style.get("font_size", 24)
        font_family = style.get("font_family", "Inter")

        return f"""
        .clipforge-caption {{
            font-family: {font_family}, sans-serif;
            font-size: {font_size}px;
            color: {font_color};
            background-color: {bg_color};
            background-color: rgba(0, 0, 0, {bg_opacity});
            text-align: center;
            max-width: 80%;
            margin: 0 auto;
            padding: 4px 8px;
            border-radius: 4px;
        }}
        """

    def get_style_presets_for_platform(self, platform: str) -> dict:
        """Get optimized style presets for different platforms"""
        platform_styles = {
            "tiktok": {
                "preferred_style": "high_impact",
                "max_words_per_line": 3,
                "font_size_range": (28, 42),
                "animation": "pop",
                "position": "bottom",
            },
            "instagram": {
                "preferred_style": "modern",
                "max_words_per_line": 5,
                "font_size_range": (20, 32),
                "animation": "fade",
                "position": "bottom",
            },
            "youtube": {
                "preferred_style": "clean",
                "max_words_per_line": 6,
                "font_size_range": (18, 36),
                "animation": "fade",
                "position": "bottom",
            },
        }
        return platform_styles.get(platform, platform_styles.get("instagram", {}))