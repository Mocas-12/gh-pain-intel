# gh-pain-intel · 开源社区痛点情报看板

监控指定 GitHub 仓库最近 N 天的 Issue，**强制经 OpenRouter API 调用 Ox Alpha**
（默认 `stealth/ox-alpha`）完成语义分类、主题聚类与情绪趋势研判，一键导出结构化
Markdown 市场研究报告。

> ⚠️ 合规边界：本项目对公开数据**只读**分析、产出**内部研究报告**，不向任何第三方
> 平台自动发帖；引用的社区文本版权归原作者所有。

## 快速开始

```bash
pip install -r requirements.txt

# Web 看板
streamlit run app.py

# 命令行批处理
python cli.py --repos ollama/ollama,vllm-project/vllm --days 7 --out report.md
```

## 环境变量

| 变量 | 说明 |
|---|---|
| `GITHUB_TOKEN` | GitHub PAT，配额从 60 次/小时 提升至 5000 次/小时 |
| `OPENROUTER_API_KEY` | **必填**，OpenRouter API Key（https://openrouter.ai/keys） |
| `OPENROUTER_MODEL` | 模型覆盖，默认 `stealth/ox-alpha` |
| `OPENROUTER_BASE_URL` | 端点覆盖，默认 `https://openrouter.ai/api/v1` |

本地运行推荐把 Key 写入项目根目录 `.env`（已被 gitignore 排除），引擎启动时自动加载。

## ☁️ 在线访问

云端版已部署于 Streamlit Community Cloud：
**https://mocas-12-gh-pain-intel.streamlit.app**

> 云端凭据通过 Streamlit Secrets 服务端注入，访客无需（也无法）看到；
> 请勿将包含敏感数据的 App 链接公开传播。

## 架构

```
src/scraper.py    抓取层：REST API + 限流退避(Retry-After) + PR过滤 + 热度排序 + 评论上下文
src/ai_engine.py  分析层：逐条分类(类别/痛感/情绪) → 两阶段语义聚类 → 趋势研判（强制JSON+重试）
src/report.py     报告层：三大板块 Markdown 装配（数字全部本地实算，可复核）
app.py            Streamlit 看板（指标卡 / 三板块Tab / 一键下载报告）
cli.py            无头批处理入口
tests/            离线单元测试：python -m unittest discover -s tests -v
```
