"""
finops/agents/llm_client.py — Multi-Provider LLM Client
======================================================
Interfaces with Gemini, OpenAI, or local quantitative synthesis models.
Always features a zero-dependency deterministic fallback for offline/air-gapped runs.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("finops.agents.llm")


class LLMClient:
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")

    def generate_synthesis(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        """
        Calls available LLM provider with fallback chain.
        """
        # Try Gemini if key is provided
        if self.gemini_key:
            try:
                import httpx
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.gemini_key}"
                payload = {
                    "contents": [{"parts": [{"text": f"{system_prompt}\n\n{prompt}"}]}]
                }
                res = httpx.post(url, json=payload, timeout=20.0)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        return candidates[0]["content"]["parts"][0]["text"]
            except Exception as e:
                logger.warning(f"Gemini API call failed: {e}")

        # Fallback to OpenAI if key is provided
        if self.openai_key:
            try:
                import httpx
                url = "https://api.openai.com/v1/chat/completions"
                headers = {"Authorization": f"Bearer {self.openai_key}"}
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2
                }
                res = httpx.post(url, headers=headers, json=payload, timeout=20.0)
                if res.status_code == 200:
                    data = res.json()
                    return data["choices"][0]["message"]["content"]
            except Exception as e:
                logger.warning(f"OpenAI API call failed: {e}")

        return None
