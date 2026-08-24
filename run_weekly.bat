@echo off
REM ============================================================
REM  gh-pain-intel 周报定时抓取脚本
REM  由 Windows 任务计划程序调用；也可双击手动运行
REM  报告输出: %PROJECT_DIR%\reports\pain_intel_report_YYYYMMDD_HHMM.md
REM ============================================================

REM ---------- 配置区（按需修改） ----------
set "PROJECT_DIR=C:\Users\wangqixiu\gh-pain-intel"
set "REPOS=ollama/ollama,langchain-ai/langchain"
set "DAYS=7"
set "MAX_PER_REPO=120"
set "BATCH_SIZE=10"
set "MAX_WORKERS=4"

REM ---------- 执行区（一般无需改动） ----------
cd /d "%PROJECT_DIR%"

echo [%date% %time%] gh-pain-intel 周报任务开始 >> run.log
"%PROJECT_DIR%\.venv\Scripts\python.exe" cli.py ^
  --repos "%REPOS%" ^
  --days %DAYS% ^
  --max-per-repo %MAX_PER_REPO% ^
  --batch-size %BATCH_SIZE% ^
  --max-workers %MAX_WORKERS% ^
  --out-dir "%PROJECT_DIR%\reports" >> run.log 2>&1

if %errorlevel% neq 0 (
  echo [%date% %time%] 任务失败，退出码 %errorlevel% >> run.log
) else (
  echo [%date% %time%] 任务成功完成 >> run.log
)
