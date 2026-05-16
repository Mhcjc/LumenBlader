from anthropic import AsyncAnthropic


class ContentAnalyzer:
    def __init__(self, api_key: str, base_url: str, model: str):
        self.model = model
        self.client = AsyncAnthropic(
            api_key=api_key,
            base_url=base_url,
        )

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

    async def _call_api(self, prompt: str) -> str:
        message = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    @staticmethod
    def _build_summary_prompt(title: str, transcript: str, extra_info: str) -> str:
        parts = [f"请为以下视频生成一份中文内容分析报告（Markdown格式）。\n\n视频标题: {title}"]
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
        parts = [f"请为以下视频生成一份完整的中文内容分析报告（Markdown格式），包含 Rubric 打分和爆款预测。\n\n视频标题: {title}"]
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
