"""AI 分析层：强制经 OpenRouter API 调用 Ox Alpha 模型，完成：

1. 逐条语义清洗与分类（bug/feature/question/doc/other + 痛感分级 + 情绪标注）
2. 两阶段语义聚类：分批归纳主题 → 全局合并去重
3. 开发者情绪分布与市场趋势研判

性能设计：分类阶段使用线程池并发请求多个批次（I/O 密集场景），
传输层内置 429/5xx 指数退避；失败批次自动兜底，不中断整体管线。
API Key 从环境变量 OPENROUTER_API_KEY 读取，或由调用方显式传入。
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import re
import threading
import time
from typing import Callable

import requests

# 本项目强制通过 OpenRouter 调用 Ox Alpha
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "stealth/ox-alpha"
DEFAULT_API_KEY_ENV = "OPENROUTER_API_KEY"

VALID_CATEGORY = {"bug", "feature", "question", "doc", "other"}
VALID_EMOTION = {"positive", "neutral", "negative", "angry"}

CLASSIFY_PROMPT = """你是资深开源社区分析师。下面是若干条 GitHub Issue 的原始文本。
对每一条输出分类结果，严格返回 JSON 数组，不要任何多余文字：
[{"id": <序号>, "category": "bug|feature|question|doc|other", "pain_level": 1-5,
  "emotion": "positive|neutral|negative|angry", "summary": "<不超过40字的中文概括>"}]
判定规则：
- bug: 报错/崩溃/行为异常; feature: 请求新功能或增强; question: 使用咨询;
  doc: 文档问题; other: 其他。
- pain_level: 问题对用户的阻碍程度，崩溃/数据丢失=5，轻微不便=1。
- emotion: 依据文本语气判断社区情绪。"""

CLUSTER_PROMPT = """你是市场分析师。以下是一批 GitHub Issue 的分类摘要。
请归纳为若干"主题簇"，合并同义项，严格返回 JSON：
{"themes": [{"name": "<主题名，<=12字>", "category": "bug|feature|question|doc|other",
  "frequency": <该主题覆盖的issue数>, "severity": "高|中|低",
  "representatives": ["<代表性原话/标题，最多3条>"],
  "insight": "<一句话中文洞察>"}]}
要求：主题数量 5~12 个；frequency 之和接近总条数；feature 类主题单独成簇以便拆分报告板块。"""

TREND_PROMPT = """你是技术市场分析师。基于以下统计与主题归纳，撰写开发者情绪与市场趋势研判。
严格返回 JSON：
{"overall_sentiment": "正面|中性|偏负面|负面",
 "sentiment_reason": "<一句话依据>",
 "hot_topics": ["<热度上升的话题>"],
 "risks": ["<社区风险信号>"],
 "opportunities": ["<产品机会点，可指导路线图>"],
 "trend_summary": "<150字以内趋势总结>"}
只依据给定材料，不要编造数据。"""


def _load_dotenv(path: str | None = None) -> None:
    """极简 .env 加载器：把 KEY=VALUE 注入环境变量（已存在的变量不覆盖）。"""
    env_file = path or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    try:
        with open(env_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                k, v = k.strip(), v.strip().strip("'\"")
                if k and v and k not in os.environ:
                    os.environ[k] = v
    except OSError:
        pass


_load_dotenv()


def _extract_json(text: str):
    """从模型回复中稳健抽取 JSON（容忍 ``` 围栏与前后闲话）。"""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.+?)```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for start_ch, end_ch in (("[", "]"), ("{", "}")):
        s, e = text.find(start_ch), text.rfind(end_ch)
        if s != -1 and e > s:
            try:
                return json.loads(text[s : e + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError(f"模型未返回合法 JSON: {text[:200]}")


def _chunk(seq: list, size: int):
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


class PainIntelEngine:
    """面向痛点情报的分析管线（OpenRouter · Ox Alpha，并发批处理）。"""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
        temperature: float = 0.2,
        timeout: int = 240,
        max_workers: int = 4,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key or os.environ.get(DEFAULT_API_KEY_ENV, "")
        self.temperature = temperature
        self.timeout = timeout
        # 并发上限保护：过高会触发平台限流（429），反而更慢
        self.max_workers = max(1, min(max_workers, 8))
        self.last_failures: list[str] = []  # 最近一次分类中降级失败的批次信息
        if not self.api_key:
            raise ValueError(
                f"缺少 OpenRouter API Key：请设置环境变量 {DEFAULT_API_KEY_ENV} "
                f"或在界面中填入（获取地址：https://openrouter.ai/keys）"
            )

    # ---------- 底层传输 ----------
    def _headers(self) -> dict:
        """OpenRouter 鉴权头 + 站点归因头（归因头可选但推荐）。"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://localhost/gh-pain-intel",
            "X-Title": "gh-pain-intel",
        }

    def chat(self, system: str, user: str) -> str:
        """对话补全，内置 429/5xx 与网络抖动的指数退避重试（线程安全）。"""
        delay = 2.0
        last_exc: Exception | None = None
        for attempt in range(4):
            try:
                resp = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(),
                    json={
                        "model": self.model,
                        "temperature": self.temperature,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ],
                    },
                    timeout=self.timeout,
                )
                if resp.status_code == 429 or resp.status_code >= 500:
                    wait = resp.headers.get("Retry-After")
                    time.sleep(min(float(wait) if wait else delay, 30.0))
                    delay *= 2
                    last_exc = RuntimeError(f"HTTP {resp.status_code}")
                    continue
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]
            except (requests.ConnectionError, requests.Timeout) as exc:
                last_exc = exc
                if attempt == 3:
                    raise
                time.sleep(delay)
                delay *= 2
        raise RuntimeError(f"OpenRouter 请求连续失败: {last_exc}")

    def chat_json(self, system: str, user: str, retries: int = 2):
        last_exc: Exception | None = None
        for _ in range(retries + 1):
            try:
                return _extract_json(self.chat(system, user))
            except Exception as exc:  # 解析失败 → 重试
                last_exc = exc
                time.sleep(1)
        raise RuntimeError(f"JSON 解析连续失败: {last_exc}")

    def health_check(self) -> bool:
        """连通性 + Key 有效性快速校验（/auth/key 异常时退回 /models 探测）。"""
        try:
            resp = requests.get(f"{self.base_url}/auth/key", headers=self._headers(), timeout=10)
            if resp.status_code == 200:
                return True
            if resp.status_code == 401:
                return False
            models = requests.get(f"{self.base_url}/models", headers=self._headers(), timeout=10)
            return models.status_code == 200
        except requests.RequestException:
            return False

    # ---------- 分类（并发批处理核心） ----------
    @staticmethod
    def _default_record(iss) -> dict:
        """单批彻底失败时的兜底记录，保证结果与输入等长。"""
        return {"issue": iss, "category": "other", "pain_level": 3,
                "emotion": "neutral", "summary": "（分类失败，已兜底）"}

    @staticmethod
    def _parse_classification(batch: list, data) -> list[dict]:
        """把模型返回的 JSON 解析为与 batch 等长的标准化记录列表。"""
        items = data if isinstance(data, list) else (
            data.get("results", []) if isinstance(data, dict) else []
        )
        by_id: dict[int, dict] = {}
        for it in items:
            try:
                by_id[int(it.get("id"))] = it
            except (TypeError, ValueError, AttributeError):
                continue
        out: list[dict] = []
        for i, iss in enumerate(batch):
            raw = by_id.get(i, {})
            cat = str(raw.get("category", "other")).lower()
            emo = str(raw.get("emotion", "neutral")).lower()
            try:
                pain = max(1, min(5, int(raw.get("pain_level", 3))))
            except (TypeError, ValueError):
                pain = 3
            out.append(
                {
                    "issue": iss,
                    "category": cat if cat in VALID_CATEGORY else "other",
                    "pain_level": pain,
                    "emotion": emo if emo in VALID_EMOTION else "neutral",
                    "summary": str(raw.get("summary", ""))[:80],
                }
            )
        return out

    def classify_issues(
        self,
        issues: list,
        batch_size: int = 20,
        max_workers: int | None = None,
        progress_cb: Callable[[int, int], None] | None = None,
    ) -> list[dict]:
        """并发分批分类：多个批次同时请求模型，输出与输入等长且顺序一致。

        失败的批次自动用中性默认值兜底（详情记入 self.last_failures），不中断整体。
        """
        self.last_failures = []
        if not issues:
            return []
        batches = list(_chunk(issues, batch_size))
        workers = max(1, min(max_workers or self.max_workers, self.max_workers))
        total = len(batches)

        def work(idx: int, batch: list) -> tuple[int, list[dict]]:
            payload = "\n\n".join(
                f"### id={i}\n{iss.flat_text[:1600]}" for i, iss in enumerate(batch)
            )
            return idx, self._parse_classification(batch, self.chat_json(CLASSIFY_PROMPT, payload))

        results: dict[int, list[dict]] = {}
        failed: set[int] = set()
        lock = threading.Lock()
        done = [0]

        with ThreadPoolExecutor(max_workers=min(workers, len(batches))) as pool:
            fut_map = {pool.submit(work, i, b): i for i, b in enumerate(batches)}
            for fut in as_completed(fut_map):
                idx = fut_map[fut]
                try:
                    _, recs = fut.result()
                    results[idx] = recs
                except Exception as exc:  # 单批失败不影响其他批次
                    failed.add(idx)
                    self.last_failures.append(f"批次{idx}: {str(exc)[:150]}")
                finally:
                    with lock:
                        done[0] += 1
                        if progress_cb:
                            progress_cb(done[0], total)

        ordered: list[dict] = []
        for idx, batch in enumerate(batches):
            if idx in failed:
                ordered.extend(self._default_record(iss) for iss in batch)
            else:
                ordered.extend(results[idx])
        return ordered

    # ---------- 聚类与趋势 ----------
    def cluster_themes(self, classified: list[dict]) -> list[dict]:
        """第二阶段：把全部分类摘要归纳为全局主题簇。"""
        lines = [
            f"- [{c['category']}|痛感{c['pain_level']}|{c['emotion']}] {c['summary']}"
            for c in classified
        ]
        data = self.chat_json(CLUSTER_PROMPT, "\n".join(lines))
        themes = data.get("themes", []) if isinstance(data, dict) else []
        cleaned: list[dict] = []
        for t in themes:
            try:
                freq = max(1, int(t.get("frequency", 1)))
            except (TypeError, ValueError):
                freq = 1
            cleaned.append(
                {
                    "name": str(t.get("name", "未命名"))[:24],
                    "category": t.get("category", "other"),
                    "frequency": freq,
                    "severity": t.get("severity", "中"),
                    "representatives": [str(x)[:120] for x in (t.get("representatives") or [])][:3],
                    "insight": str(t.get("insight", ""))[:160],
                }
            )
        return cleaned

    def analyze_trends(self, classified: list[dict], themes: list[dict]) -> dict:
        """第三阶段：情绪聚合 + 趋势研判（输入为统计摘要，控制上下文体积）。"""
        total = len(classified) or 1
        emo_dist: dict[str, int] = {}
        for c in classified:
            emo_dist[c["emotion"]] = emo_dist.get(c["emotion"], 0) + 1
        stat_lines = [f"总Issue: {len(classified)}"] + [
            f"{k}: {v} ({v / total:.0%})" for k, v in emo_dist.items()
        ]
        theme_lines = [
            f"- {t['name']}[{t['category']}|{t['severity']}] x{t['frequency']}: {t['insight']}"
            for t in themes
        ]
        data = self.chat_json(
            TREND_PROMPT, "统计数据:\n" + "\n".join(stat_lines) + "\n\n主题归纳:\n" + "\n".join(theme_lines)
        )
        if not isinstance(data, dict):
            data = {}
        data.setdefault("emotion_distribution", emo_dist)
        return data

    # ---------- 完整管线 ----------
    def run_pipeline(
        self,
        issues: list,
        batch_size: int = 20,
        max_workers: int | None = None,
        progress_cb: Callable[[str, float], None] | None = None,
    ) -> dict:
        """完整管线：并发分类 → 聚类 → 趋势。progress_cb(stage, ratio)。"""

        def notify(stage: str, cur: int, tot: int) -> None:
            if progress_cb:
                progress_cb(stage, cur / max(tot, 1))

        notify("classify", 0, 1)
        classified = self.classify_issues(
            issues, batch_size=batch_size, max_workers=max_workers,
            progress_cb=lambda c, t: notify("classify", c, t),
        )
        notify("cluster", 0, 1)
        themes = self.cluster_themes(classified)
        notify("trends", 0, 1)
        trends = self.analyze_trends(classified, themes)
        return {"classified": classified, "themes": themes, "trends": trends}
