# gh-pain-intel · 开源社区痛点情报看板

监控指定 GitHub 仓库最近 N 天的 Issue，调用大模型完成语义分类、主题聚类与情绪趋势
研判，一键导出结构化 Markdown 市场研究报告。默认经 OpenRouter 调用 Ox Alpha，
**可在界面一键切换 OpenAI / Gemini / Claude / DeepSeek / Kimi / 智谱 / 通义千问 /
Grok 等主流模型**（任意 OpenAI 兼容端点，见[多模型切换](#-多模型切换)）。

> ⚠️ 合规边界：本项目对公开数据**只读**分析、产出**内部研究报告**，不向任何第三方
> 平台自动发帖；引用的社区文本版权归原作者所有。

## 快速开始

```bash
pip install -r requirements.txt

# Web 看板
streamlit run app.py

# 命令行批处理
python cli.py --repos ollama/ollama,vllm-project/vllm --days 7 --out report.md

# 命令行切换其他模型（如 Gemini）
python cli.py --provider gemini --repos ollama/ollama --days 7 --out report.md
```

## 环境变量

| 变量 | 说明 |
|---|---|
| `GITHUB_TOKEN` | GitHub PAT，配额从 60 次/小时 提升至 5000 次/小时（[创建教程见下](#-如何创建-github_token)） |
| `OPENROUTER_API_KEY` | 默认服务商 OpenRouter 的 Key（https://openrouter.ai/keys） |
| `OPENROUTER_MODEL` / `OPENROUTER_BASE_URL` | OpenRouter 的模型 / 端点覆盖（历史兼容） |
| `LLM_API_KEY` | 通用 Key 兜底，优先级高于 `OPENROUTER_API_KEY`（自定义端点常用） |
| `LLM_PROVIDER` | CLI 的默认服务商（如 `gemini`、`deepseek`），不影响界面手动切换 |
| 各服务商专属 Key | `OPENAI_API_KEY`、`GEMINI_API_KEY`、`ANTHROPIC_API_KEY`、`DEEPSEEK_API_KEY`、`MOONSHOT_API_KEY`、`ZHIPU_API_KEY`、`DASHSCOPE_API_KEY`、`XAI_API_KEY`、`SILICONFLOW_API_KEY`、`GROQ_API_KEY` —— 在界面选中对应服务商后自动带入 |

本地运行推荐把 Key 写入项目根目录 `.env`（已被 gitignore 排除），引擎启动时自动加载。

## 🧠 多模型切换

「模型设置」可在主流大模型之间一键切换：全走 **OpenAI Chat Completions 兼容协议**，
切换服务商时自动带出官方端点与默认模型，Key 的获取地址见输入框帮助文字。

| 服务商 | 端点 | Key 环境变量 |
|---|---|---|
| OpenRouter（默认 · Ox Alpha） | `https://openrouter.ai/api/v1` | `OPENROUTER_API_KEY` |
| OpenAI | `https://api.openai.com/v1` | `OPENAI_API_KEY` |
| Google Gemini | `…/v1beta/openai`（官方兼容端点） | `GEMINI_API_KEY` |
| Anthropic Claude | `https://api.anthropic.com/v1`（官方兼容层） | `ANTHROPIC_API_KEY` |
| DeepSeek | `https://api.deepseek.com/v1` | `DEEPSEEK_API_KEY` |
| Moonshot（Kimi） | `https://api.moonshot.cn/v1` | `MOONSHOT_API_KEY` |
| 智谱 GLM | `https://open.bigmodel.cn/api/paas/v4` | `ZHIPU_API_KEY` |
| 通义千问（百炼） | `…/compatible-mode/v1` | `DASHSCOPE_API_KEY` |
| xAI（Grok） | `https://api.x.ai/v1` | `XAI_API_KEY` |
| 硅基流动 SiliconFlow | `https://api.siliconflow.cn/v1` | `SILICONFLOW_API_KEY` |
| Groq | `https://api.groq.com/openai/v1` | `GROQ_API_KEY` |
| Ollama（本地 · 免费） | `http://localhost:11434/v1` | 无需 Key |
| 自定义 | 任意 OpenAI 兼容端点 | `LLM_API_KEY`（选填） |

> - 模型名更新很快：下拉列表只是常用预置，选「✏️ 其他（手动输入）」即可填写任意模型名。
> - 云端 Secrets 按需配置即可（用到哪个服务商就配哪个）：
>   ```toml
>   GEMINI_API_KEY = "AIza…"
>   DEEPSEEK_API_KEY = "sk-…"
>   ```

## 🔑 如何创建 GITHUB_TOKEN

> 不配置也能用，但匿名配额仅 **60 次/小时** 且按 IP 共享（云端部署极易耗尽）；
> 配置后提升至 **5000 次/小时**。整个过程约 1 分钟。

1. 登录 GitHub → 打开 **https://github.com/settings/tokens**
2. 点击 **「Generate new token」→「Generate new token (classic)」**
3. 填写两项即可：
   - **Note**：随便起名，如 `gh-pain-intel`
   - **Expiration**：有效期，建议 `90 days` 或 `No expiration`
4. ⬇️ **权限 scopes 一项都不用勾选**——本工具只读公开数据
5. 点击页面底部绿色按钮 **「Generate token」**
6. **立即复制**页面显示的 Token（`ghp_` 开头，只显示这一次！）
7. 写入配置（二选一）：
   - 本地：项目根目录 `.env` 文件中加一行
     ```ini
     GITHUB_TOKEN=***
     ```
   - 云端：应用右下角 **Manage app → Settings → Secrets** 中添加
     ```toml
     GITHUB_TOKEN = "ghp_你的token"
     ```

> ✅ 安全说明：该 Token 只能读取你账号可见的公开数据，无法写入或修改任何仓库；
> 泄露了也只需回到同一页面点 Delete 重新生成一个。

## ☁️ 在线访问

云端版已部署于 Streamlit Community Cloud：
**https://gh-pain-intel-8egvafff3urokytzxa63x2.streamlit.app/**

> 云端凭据通过 Streamlit Secrets 服务端注入，访客无需（也无法）看到；
> 请勿将包含敏感数据的 App 链接公开传播。

## 架构

```
src/scraper.py    抓取层：REST API + 限流退避(Retry-After) + PR过滤 + 热度排序 + 评论上下文
src/trending.py   热榜层：解析 GitHub 官方 Trending 页的“stars today”，输出每日 Star 增幅 Top10（UTC 日缓存，不耗 API 配额）
src/llm_providers.py 服务商注册表：主流大模型兼容端点/模型/Key 预设（新增服务商在此登记即接入）
src/ai_engine.py  分析层：OpenAI 兼容协议调用所选端点 → 逐条分类 → 两阶段语义聚类 → 趋势研判（强制JSON+重试）
src/report.py     报告层：三大板块 Markdown 装配（数字全部本地实算，可复核）
app.py            Streamlit 看板（指标卡 / 三板块Tab / 一键下载报告）
cli.py            无头批处理入口
tests/            离线单元测试：python -m unittest discover -s tests -v
```

## 🔥 每日 Star 增幅榜

主页顶部的「🔥 今日 STAR 增幅 TOP 10」卡片栅格（默认展开）展示 GitHub 官方 Trending
统计的**最近一天新增星标数**（`stars today`），并按增幅数值降序排列——不是总星数排行，
榜单每天都会换血，适合发现正在爆发的新仓库。点击卡片上的 ➕ 可一键把仓库加入分析目标。

- 数据源：https://github.com/trending?since=daily （页面抓取，不消耗 GitHub API 配额，无需 Token）
- 刷新节奏：按 UTC 日期缓存，每天首次打开应用时抓取一次
- 已知边界：数据来自 GitHub 官方页面 HTML，若页面结构调整，榜单会显示“暂时不可用”而不影响其他功能

