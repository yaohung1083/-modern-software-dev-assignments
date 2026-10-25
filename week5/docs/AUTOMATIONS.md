# Codex 自學版 automations

兩個流程皆由本機 Python 執行，不使用 Warp、排程服務或雲端 automation。重複執行不修改程式碼或正式資料庫；每次新增一份帶時間的 JSON 紀錄至 `docs/runs/`，失敗回傳非零狀態，不會 commit 或 push。

## 安裝（從 week5 執行）

```bash
python3 -m venv .venv
.venv/bin/python -m pip install fastapi sqlalchemy pydantic python-dotenv pytest httpx ruff playwright
.venv/bin/python -m playwright install chromium
```

React 從固定版本的 `esm.sh` CDN 載入，需要網路。若使用自行安裝的 Chromium，可以設定 `WEEK5_CHROMIUM_EXECUTABLE` 為其執行檔絕對路徑；一般安裝 Playwright 瀏覽器後不需設定。本次驗證環境位於暫存目錄；重現時請使用上述 `.venv` 安裝步驟。

## A：品質驗收

```bash
.venv/bin/python scripts/run_automation.py quality
```

依序執行所有後端測試、Ruff、僅 week5 的 `git diff --check`、Chromium React 整合測試；任一步失敗即停止並寫紀錄。瀏覽器 runner 直接提供前端檔案，不需啟動 API 或開啟埠；測試頁 mock API，不操作真實資料庫。後端另由暫存資料庫 pytest 測試，這不是完整真實 API 的瀏覽器端到端測試。

## B：索引效能比較

```bash
.venv/bin/python scripts/run_automation.py performance --rows 50000 --repeats 20
```

先跑索引的 3 項回歸測試，再用暫存 SQLite 建立資料，比較四種查詢的索引前後結果、EXPLAIN 與暖快取中位數。輸入 rows/repeats 必須大於零；測試驗證查詢計畫與結果，不用容易受機器負載影響的時間門檻。

## 實際紀錄

- [品質驗收：29 tests、12 browser assertions](runs/20261023T182702572117-quality.json)
- [效能比較：3 tests、50,000 rows、20 repeats](runs/20261023T182703743599-performance.json)
- [文件收尾後再次品質驗收：29 tests、12 browser assertions](runs/20261023T182928309089-quality.json)

報告包含開始／結束時間（Asia/Taipei）、Python／平台、每個子命令、退出碼與 stdout/stderr。效能數字只適用當次資料與負載，且不含 COUNT、HTTP 或索引建立成本。兩份初次收尾紀錄的執行時間重疊，因此也會有資源競爭；不能把加速倍率當成保證。

## 公開紀錄的路徑匿名化

`docs/runs/` 的既有紀錄僅將本機專案與驗證環境路徑改為 `<PROJECT_ROOT>/`、`<VALIDATION_ENV>/`。時間、測試結果、警告、退出碼與效能數字均保留；各 JSON 的 `path_redaction` 欄位明確標示此處理。
