import asyncio
import json
import logging
import os
import re
import tempfile
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

CHEAT_ON_CONTENT_DIR = "/Users/jiacong.wu/AI/AIWeMedia/cheat-on-content"

V2_RUBRIC_SYSTEM_PROMPT = """\
你是一位资深短视频内容分析师，精通内容爆款预测。你需要按照下方 **v2 rubric** 对稿件进行盲评打分。

## 评分维度（7 维，0-5 分）

| 维度 | 权重 | 0 分描述 | 3 分描述 | 5 分描述 |
|------|------|----------|----------|----------|
| **ER** Emotional Resonance | ×1.5 | 纯信息传递，无情绪触动 | 引发一般性共鸣，观众能感受到情绪 | 精准刺中自我认知，产生"这说的就是我"的感觉 |
| **SR** Social Resonance | ×1.5 | 仅个人叙事，无社交传播力 | 描述了一个被广泛认同的现象 | 精准命名了一个结构性社会模式 |
| **HP** Hook Potential | ×1.5 | 泛泛而谈的开头 | 给出了具体承诺/悬念 | 让人无法停止处理信息的强烈钩子 |
| **QL** Quotable Lines | ×1.0 | 全文叙事体，无记忆点 | 有令人印象深刻的结尾金句 | 有多条可独立传播的金句 |
| **NA** Narrativity | ×1.0 | 列表/清单式内容 | 有松散叙事弧线 | 紧凑的三幕式叙事结构 |
| **AB** Audience Breadth | ×1.0 | 极窄受众，仅特定圈层 | 中等受众面 | 具有普遍性，人人可共鸣 |
| **SAT** Satire Depth | ×1.0 | 真诚表达，无讽刺 | 一层反讽 | 多层嵌套/自反性讽刺 |

## 复合得分公式

composite = (ER×1.5 + SR×1.5 + HP×1.5 + QL×1.0 + NA×1.0 + AB×1.0 + SAT×1.0) / 8.5 × 2.0

满分 10.0 分。

## 冷启动分桶定义

| 桶名 | composite 区间 | 描述 |
|------|---------------|------|
| 底部 | 0.0 - 2.0 | 数据极差，几乎无曝光 |
| 基础盘 | 2.0 - 4.0 | 正常表现，获得基础流量池推送 |
| 命中 | 4.0 - 6.0 | 表现良好，进入中等流量池 |
| 小爆 | 6.0 - 8.0 | 爆款潜力，有望突破常规流量池 |
| 大爆 | 8.0 - 10.0 | 极强爆款潜力，可能引发大规模传播 |

## 输出要求

你 **必须** 严格按照下方 JSON schema 输出，不要输出任何额外文字。JSON 用 ```json 代码块包裹。

```json
{
  "title": "视频标题",
  "summary": "200-300字内容摘要",
  "dimensions": {
    "ER": { "score": 0, "confidence": "high|medium|low", "reason": "≤30字理由" },
    "SR": { "score": 0, "confidence": "high|medium|low", "reason": "≤30字理由" },
    "HP": { "score": 0, "confidence": "high|medium|low", "reason": "≤30字理由" },
    "QL": { "score": 0, "confidence": "high|medium|low", "reason": "≤30字理由" },
    "NA": { "score": 0, "confidence": "high|medium|low", "reason": "≤30字理由" },
    "AB": { "score": 0, "confidence": "high|medium|low", "reason": "≤30字理由" },
    "SAT": { "score": 0, "confidence": "high|medium|low", "reason": "≤30字理由" }
  },
  "composite": 0.0,
  "bucket": {
    "headline": "底部|基础盘|命中|小爆|大爆",
    "probability_distribution": { "底部": 0.0, "基础盘": 0.0, "命中": 0.0, "小爆": 0.0, "大爆": 0.0 },
    "centroid": "一句话描述该桶的典型表现"
  },
  "anchors": [
    { "description": "锚点内容描述", "composite": 0.0, "outcome": "实际表现" }
  ],
  "counterfactuals": {
    "底部": "要达到底部桶需要怎样改动",
    "基础盘": "要达到基础盘需要怎样改动",
    "命中": "要达到命中需要怎样改动",
    "小爆": "要达到小爆需要怎样改动",
    "大爆": "要达到大爆需要怎样改动"
  },
  "calibration_hypothesis": "你对这次预测的校准假设说明"
}
```"""


def _cheat_on_content_ready() -> bool:
    """Check if cheat-on-content is initialized and claude CLI is available."""
    state_file = os.path.join(CHEAT_ON_CONTENT_DIR, ".cheat-state.json")
    rubric_file = os.path.join(CHEAT_ON_CONTENT_DIR, "rubric_notes.md")
    if not (os.path.isfile(state_file) and os.path.isfile(rubric_file)):
        return False
    # Check claude CLI availability
    try:
        result = os.popen("which claude").read().strip()
        return bool(result)
    except Exception:
        return False


class ContentAnalyzer:
    def __init__(self, api_key: str, base_url: str, model: str):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    # ── Public API ──────────────────────────────────────────────────────

    async def generate_score_report(
        self,
        video_title: str,
        transcript: str,
        video_path: str = "",
    ) -> str:
        """Summary mode: try cheat-on-content CLI first, fall back to API."""
        if _cheat_on_content_ready():
            try:
                return await self._score_via_cli(transcript)
            except Exception as e:
                logger.warning("cheat-score CLI failed, falling back to API: %s", e)
        # Fallback: API-based scoring with v2 rubric prompt
        return await self._score_via_api(video_title, transcript)

    async def generate_full_prediction(
        self, video_title: str, transcript: str
    ) -> str:
        """Full mode: call Claude API with v2 rubric, return markdown report."""
        system = V2_RUBRIC_SYSTEM_PROMPT
        user_prompt = (
            f"请对以下视频稿件进行 v2 rubric 盲评。\n\n"
            f"视频标题: {video_title}\n\n"
            f"稿件内容:\n{transcript}"
        )
        raw = await self._call_api(user_prompt, system=system, max_tokens=8192)
        parsed = self._try_parse_json(raw)
        if parsed is not None:
            return self._prediction_json_to_markdown(parsed)
        # If parsing completely failed, return raw text
        return raw

    # ── Legacy methods (kept as fallback) ───────────────────────────────

    async def generate_summary(
        self,
        video_title: str,
        transcript: str = "",
        extra_info: str = "",
    ) -> str:
        prompt = self._build_summary_prompt(video_title, transcript, extra_info)
        return await self._call_api(prompt)

    async def generate_full_analysis(
        self,
        video_title: str,
        transcript: str = "",
        extra_info: str = "",
    ) -> str:
        prompt = self._build_full_prompt(video_title, transcript, extra_info)
        return await self._call_api(prompt)

    # ── Internal: cheat-score CLI ───────────────────────────────────────

    async def _score_via_cli(self, transcript: str) -> str:
        """Write transcript to temp .md, invoke `claude -p /cheat-score ...`."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", dir=CHEAT_ON_CONTENT_DIR, delete=False
        ) as tmp:
            tmp.write(transcript)
            tmp_path = tmp.name

        try:
            cmd = [
                "claude",
                "-p",
                f"/cheat-score {tmp_path} -- OUTPUT_DETAIL: full",
                "--output-format",
                "text",
                "--max-turns",
                "10",
                "--allowedTools",
                "Read,Glob,Grep,Task",
            ]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=CHEAT_ON_CONTENT_DIR,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=180
            )
            if proc.returncode != 0:
                err_msg = stderr.decode(errors="replace").strip()
                raise RuntimeError(
                    f"claude CLI exited {proc.returncode}: {err_msg}"
                )
            return stdout.decode(errors="replace").strip()
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    # ── Internal: API-based scoring ─────────────────────────────────────

    async def _score_via_api(self, video_title: str, transcript: str) -> str:
        """Fallback: use v2 rubric system prompt via API for summary scoring."""
        system = V2_RUBRIC_SYSTEM_PROMPT
        user_prompt = (
            f"请对以下视频稿件进行 v2 rubric 盲评，输出完整 JSON。\n\n"
            f"视频标题: {video_title}\n\n"
            f"稿件内容:\n{transcript}"
        )
        raw = await self._call_api(user_prompt, system=system, max_tokens=8192)
        parsed = self._try_parse_json(raw)
        if parsed is not None:
            return self._prediction_json_to_markdown(parsed)
        return raw

    # ── Internal: HTTP API call ─────────────────────────────────────────

    async def _call_api(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> str:
        messages: List[Dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=180) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": max_tokens,
                    "messages": messages,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    # ── Internal: JSON parsing helpers ──────────────────────────────────

    @staticmethod
    def _try_parse_json(text: str) -> Optional[Dict[str, Any]]:
        """Try to parse JSON from raw text or markdown code blocks."""
        # 1) Try direct JSON parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # 2) Try extracting from ```json ... ``` code block
        match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        # 3) Try extracting from ``` ... ``` (no language tag)
        match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        return None

    # ── Internal: Markdown report builder ───────────────────────────────

    @staticmethod
    def _prediction_json_to_markdown(data: Dict[str, Any]) -> str:
        """Convert prediction JSON to a nicely formatted markdown report."""
        lines: List[str] = []

        # Title
        title = data.get("title", "未知标题")
        lines.append(f"# 内容分析报告: {title}\n")

        # Summary
        summary = data.get("summary", "")
        if summary:
            lines.append("## 内容摘要\n")
            lines.append(f"{summary}\n")

        # Dimensions table
        dimensions = data.get("dimensions", {})
        if dimensions:
            lines.append("## 七维评分\n")
            lines.append(
                "| 维度 | 分数 | 置信度 | 理由 |"
            )
            lines.append(
                "|------|------|--------|------|"
            )
            dim_labels = {
                "ER": "情感共鸣 (ER)",
                "SR": "社会共鸣 (SR)",
                "HP": "钩子潜力 (HP)",
                "QL": "金句力 (QL)",
                "NA": "叙事性 (NA)",
                "AB": "受众广度 (AB)",
                "SAT": "讽刺深度 (SAT)",
            }
            confidence_emoji = {"high": "🟢", "medium": "🟡", "low": "🔴"}
            for key in ["ER", "SR", "HP", "QL", "NA", "AB", "SAT"]:
                dim = dimensions.get(key, {})
                score = dim.get("score", "-")
                conf = dim.get("confidence", "-")
                emoji = confidence_emoji.get(conf, "")
                reason = dim.get("reason", "-")
                label = dim_labels.get(key, key)
                lines.append(
                    f"| {label} | {score} | {emoji} {conf} | {reason} |"
                )
            lines.append("")

        # Composite score
        composite = data.get("composite", 0)
        lines.append("## 综合得分\n")
        lines.append(
            f"**{composite:.1f}** / 10.0\n"
        )
        lines.append(
            "*公式: (ER×1.5 + SR×1.5 + HP×1.5 + QL + NA + AB + SAT) / 8.5 × 2.0*\n"
        )

        # Bucket prediction
        bucket = data.get("bucket", {})
        if bucket:
            headline = bucket.get("headline", "-")
            prob_dist = bucket.get("probability_distribution", {})
            centroid = bucket.get("centroid", "")
            lines.append("## 爆款预测\n")
            lines.append(f"**预测分桶: {headline}**\n")
            if centroid:
                lines.append(f"> {centroid}\n")
            if prob_dist:
                lines.append("概率分布:\n")
                for bucket_name in ["底部", "基础盘", "命中", "小爆", "大爆"]:
                    prob = prob_dist.get(bucket_name, 0)
                    bar_len = int(prob * 40)
                    bar = "█" * bar_len + "░" * (40 - bar_len)
                    lines.append(
                        f"  {bucket_name}  `{bar}` {prob:.0%}"
                    )
                lines.append("")

        # Anchor comparison
        anchors = data.get("anchors", [])
        if anchors:
            lines.append("## 锚点对比\n")
            lines.append("| 锚点描述 | composite | 实际表现 |")
            lines.append("|----------|-----------|----------|")
            for a in anchors:
                desc = a.get("description", "-")
                ac = a.get("composite", "-")
                outcome = a.get("outcome", "-")
                if isinstance(ac, (int, float)):
                    ac = f"{ac:.1f}"
                lines.append(f"| {desc} | {ac} | {outcome} |")
            lines.append("")

        # Counterfactuals
        cfs = data.get("counterfactuals", {})
        if cfs:
            lines.append("## 反事实分析\n")
            for bucket_name in ["底部", "基础盘", "命中", "小爆", "大爆"]:
                cf_text = cfs.get(bucket_name, "")
                if cf_text:
                    lines.append(f"- **{bucket_name}**: {cf_text}")
            lines.append("")

        # Calibration hypothesis
        cal = data.get("calibration_hypothesis", "")
        if cal:
            lines.append("## 校准假设\n")
            lines.append(f"{cal}\n")

        return "\n".join(lines)

    # ── Legacy prompt builders ──────────────────────────────────────────

    @staticmethod
    def _build_summary_prompt(title: str, transcript: str, extra_info: str) -> str:
        parts = [
            f"请为以下视频生成一份中文内容分析报告（Markdown格式）。\n\n视频标题: {title}"
        ]
        if transcript:
            parts.append(f"\n\n视频字幕/转录:\n{transcript}")
        if extra_info:
            parts.append(f"\n\n额外信息:\n{extra_info}")
        parts.append(
            "\n\n请生成以下内容:\n"
            "1. **内容摘要** (200-300字)\n"
            "2. **核心观点** (3-5个要点)\n"
            "3. **内容结构分析**\n"
            "4. **值得学习的亮点**\n\n"
            "输出纯 Markdown 格式。"
        )
        return "".join(parts)

    @staticmethod
    def _build_full_prompt(title: str, transcript: str, extra_info: str) -> str:
        parts = [
            f"请为以下视频生成一份完整的中文内容分析报告（Markdown格式），包含 Rubric 打分和爆款预测。\n\n视频标题: {title}"
        ]
        if transcript:
            parts.append(f"\n\n视频字幕/转录:\n{transcript}")
        if extra_info:
            parts.append(f"\n\n额外信息:\n{extra_info}")
        parts.append(
            "\n\n请生成以下内容:\n"
            "1. **内容摘要** (200-300字)\n"
            "2. **核心观点** (3-5个要点)\n"
            "3. **Rubric 打分** (每项1-10分):\n"
            "   - 选题吸引力\n"
            "   - 内容深度\n"
            "   - 表达清晰度\n"
            "   - 情绪共鸣\n"
            "   - 信息密度\n"
            "   - 独特角度\n"
            "   - 行动召唤力\n"
            "4. **综合得分** (加权平均)\n"
            "5. **爆款预测**:\n"
            "   - 预计播放量区间\n"
            "   - 预计互动率\n"
            "   - 目标受众画像\n"
            "6. **改进建议** (2-3条)\n"
            "7. **值得学习的亮点**\n\n"
            "输出纯 Markdown 格式。"
        )
        return "".join(parts)
