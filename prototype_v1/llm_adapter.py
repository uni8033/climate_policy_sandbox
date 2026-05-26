"""可选的云端大模型适配层。

默认情况下使用本地模板叙事器，确保原型在没有 API 的环境中也能运行。
如果设置了 OPENAI_API_KEY，则可以切换到 OpenAI-compatible 接口。
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import List


@dataclass
class NarrationRequest:
    role_name: str
    role_description: str
    status_label: str
    positive_points: List[str]
    concern_points: List[str]
    asks: List[str]
    policy_text: str
    round_index: int


class TemplateNarrator:
    """稳定、可复现的本地模板叙事器。"""

    def describe(self) -> str:
        return "template-local"

    def render_statement(self, request: NarrationRequest) -> str:
        opening_map = {
            "支持": "我们总体支持这项政策，原因是",
            "有保留地支持": "我们可以在保留意见的前提下支持这项政策，前提是",
            "有保留地反对": "我们对这项政策持保留态度，主要担忧是",
            "强烈反对": "我们目前强烈反对这项政策，核心问题在于",
        }
        opening = opening_map.get(request.status_label, "我们的态度是")
        positive = "；".join(request.positive_points[:2]) if request.positive_points else "目前缺少足够的积极条件"
        concerns = "；".join(request.concern_points[:2]) if request.concern_points else "当前没有明显无法接受的问题"
        asks = "；".join(request.asks[:2]) if request.asks else "本轮暂无额外条件"
        return (
            f"第 {request.round_index} 轮中，{request.role_name}表示：{opening}{concerns}。"
            f"从我们立场看，当前方案中较积极的部分包括：{positive}。"
            f"若要推动下一步谈判，我们最希望增加的条件是：{asks}。"
        )


class OpenAICompatibleNarrator:
    """面向 OpenAI-compatible 接口的轻量封装。"""

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        self.api_path = os.getenv("OPENAI_API_PATH", "chat/completions")
        self.timeout = int(os.getenv("OPENAI_TIMEOUT", "90"))
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")

    def describe(self) -> str:
        return f"openai-compatible:{self.model}"

    def render_statement(self, request: NarrationRequest) -> str:
        endpoint = self.base_url.rstrip("/") + "/" + self.api_path.lstrip("/")
        system_prompt = (
            "你是气候政策多利益相关方博弈中的角色代理。"
            "请基于给定立场和条件，输出简洁、真实、清晰的中文表态。"
            "不要编造额外事实，不要脱离角色立场。"
        )
        user_prompt = (
            f"政策文本：{request.policy_text}\n"
            f"轮次：第 {request.round_index} 轮\n"
            f"角色：{request.role_name}\n"
            f"角色背景：{request.role_description}\n"
            f"当前态度：{request.status_label}\n"
            f"支持点：{request.positive_points}\n"
            f"担忧点：{request.concern_points}\n"
            f"希望增加的条件：{request.asks}\n"
            "请用 2 到 3 句话输出该角色本轮发言。"
        )
        payload = self._build_payload(system_prompt, user_prompt)
        request_obj = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json, text/plain, */*",
                "User-Agent": os.getenv("OPENAI_USER_AGENT", "climate-policy-sandbox/1.0"),
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request_obj, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"LLM request failed: HTTP {error.code} {body}") from error
        except urllib.error.URLError as error:
            raise RuntimeError(f"LLM request failed: {error}") from error
        return self._extract_text(body)

    def _build_payload(self, system_prompt: str, user_prompt: str) -> dict:
        if self.api_path.rstrip("/").endswith("responses"):
            return {
                "model": self.model,
                "input": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.5,
            }
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.5,
        }

    def _extract_text(self, body: dict) -> str:
        if "choices" in body and body["choices"]:
            return body["choices"][0]["message"]["content"].strip()
        if body.get("output_text"):
            return body["output_text"].strip()
        for output_item in body.get("output", []):
            for content_item in output_item.get("content", []):
                text = content_item.get("text")
                if text:
                    return text.strip()
        raise RuntimeError(f"LLM response format not recognized: {json.dumps(body, ensure_ascii=False)[:800]}")


def build_narrator():
    if os.getenv("OPENAI_API_KEY"):
        try:
            return OpenAICompatibleNarrator()
        except Exception:
            return TemplateNarrator()
    return TemplateNarrator()
