"""大模型服务商注册表：OpenAI Chat Completions 兼容端点预设。

本项目分析层的传输协议只有一种 —— OpenAI Chat Completions
（POST {base_url}/chat/completions）。主流服务商要么原生兼容该协议
（OpenAI / DeepSeek / Moonshot / 智谱 / Groq …），要么提供官方兼容端点
（Gemini、Anthropic、阿里云百炼），因此接入新服务商只需在此登记：
base_url + 常用模型名 + Key 的环境变量名与获取地址，看板与 CLI 自动获得切换能力。

字段说明：
- base_url: OpenAI 兼容端点（不带末尾斜杠），分析层会在其后拼 /chat/completions
- models:   界面下拉预置的常用模型名；空列表表示只能手动输入
- key_env:  Key 的环境变量 / Streamlit Secrets 名；None 表示无需鉴权（如本地 Ollama）
- note:     该服务商的特殊说明，会显示在界面上
"""
from __future__ import annotations

PROVIDERS: dict[str, dict] = {
    "openrouter": {
        "label": "OpenRouter（默认 · Ox Alpha）",
        "short": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "models": [
            "stealth/ox-alpha",
            "openai/gpt-4o-mini",
            "anthropic/claude-sonnet-4.5",
            "google/gemini-2.5-flash",
            "deepseek/deepseek-chat-v3.1",
        ],
        "key_env": "OPENROUTER_API_KEY",
        "key_url": "https://openrouter.ai/keys",
        "key_hint": "sk-or-v1-…",
    },
    "openai": {
        "label": "OpenAI（GPT 系列）",
        "short": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4o-mini", "gpt-4o", "gpt-4.1", "gpt-4.1-mini", "o4-mini"],
        "key_env": "OPENAI_API_KEY",
        "key_url": "https://platform.openai.com/api-keys",
        "key_hint": "sk-…",
    },
    "gemini": {
        "label": "Google Gemini（官方兼容端点）",
        "short": "Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "models": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"],
        "key_env": "GEMINI_API_KEY",
        "key_url": "https://aistudio.google.com/apikey",
        "key_hint": "AIza…",
    },
    "anthropic": {
        "label": "Anthropic Claude（官方兼容层）",
        "short": "Claude",
        "base_url": "https://api.anthropic.com/v1",
        "models": ["claude-sonnet-4.5", "claude-opus-4.1", "claude-3-5-haiku-latest"],
        "key_env": "ANTHROPIC_API_KEY",
        "key_url": "https://console.anthropic.com/settings/keys",
        "key_hint": "sk-ant-…",
        "note": "经 Anthropic 官方 OpenAI 兼容层调用，属实验性支持",
    },
    "deepseek": {
        "label": "DeepSeek（深度求索）",
        "short": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "key_env": "DEEPSEEK_API_KEY",
        "key_url": "https://platform.deepseek.com/api_keys",
        "key_hint": "sk-…",
    },
    "moonshot": {
        "label": "Moonshot AI（Kimi）",
        "short": "Kimi",
        "base_url": "https://api.moonshot.cn/v1",
        "models": ["kimi-k2-0905-preview", "moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
        "key_env": "MOONSHOT_API_KEY",
        "key_url": "https://platform.moonshot.cn/console/api-keys",
        "key_hint": "sk-…",
    },
    "zhipu": {
        "label": "智谱 AI（GLM 系列）",
        "short": "智谱 GLM",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "models": ["glm-4.6", "glm-4.5", "glm-4.5-air", "glm-4-flash"],
        "key_env": "ZHIPU_API_KEY",
        "key_url": "https://open.bigmodel.cn/usercenter/apikeys",
        "key_hint": "…",
    },
    "dashscope": {
        "label": "阿里云百炼（通义千问 Qwen）",
        "short": "通义千问",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "models": ["qwen-max", "qwen-plus", "qwen-turbo", "qwen3-235b-a22b"],
        "key_env": "DASHSCOPE_API_KEY",
        "key_url": "https://bailian.console.aliyun.com/?apiKey=1",
        "key_hint": "sk-…",
    },
    "xai": {
        "label": "xAI（Grok 系列）",
        "short": "Grok",
        "base_url": "https://api.x.ai/v1",
        "models": ["grok-4", "grok-3", "grok-3-mini"],
        "key_env": "XAI_API_KEY",
        "key_url": "https://console.x.ai",
        "key_hint": "xai-…",
    },
    "siliconflow": {
        "label": "硅基流动 SiliconFlow（聚合平台）",
        "short": "硅基流动",
        "base_url": "https://api.siliconflow.cn/v1",
        "models": ["deepseek-ai/DeepSeek-V3.1", "Qwen/Qwen3-32B", "moonshotai/Kimi-K2-Instruct"],
        "key_env": "SILICONFLOW_API_KEY",
        "key_url": "https://cloud.siliconflow.cn/account/ak",
        "key_hint": "sk-…",
    },
    "groq": {
        "label": "Groq（高速推理）",
        "short": "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "models": ["llama-3.3-70b-versatile", "openai/gpt-oss-120b"],
        "key_env": "GROQ_API_KEY",
        "key_url": "https://console.groq.com/keys",
        "key_hint": "gsk_…",
    },
    "ollama": {
        "label": "Ollama（本地模型 · 免费）",
        "short": "Ollama",
        "base_url": "http://localhost:11434/v1",
        "models": ["qwen3:8b", "llama3.1:8b", "deepseek-r1:8b"],
        "key_env": None,
        "key_url": "https://ollama.com",
        "key_hint": "",
        "note": "本地运行无需 API Key；云端部署时请改为公网可达的端点地址",
    },
    "custom": {
        "label": "自定义（任意 OpenAI 兼容端点）",
        "short": "自定义",
        "base_url": "",
        "models": [],
        "key_env": "LLM_API_KEY",
        "key_url": "",
        "key_hint": "",
        "note": "填入兼容 OpenAI Chat Completions 协议的 base_url 与模型名即可接入；端点需要鉴权时才填 Key",
    },
}

DEFAULT_PROVIDER = "openrouter"
