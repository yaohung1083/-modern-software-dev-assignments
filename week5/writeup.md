# Week 5 — Codex 自學版 Write-up

## 基本資料與範圍

- Name: Yang Yao-Hong（楊曜鴻）
- SUNet ID: N/A (Independent learner)
- Total time spent: Not tracked (self-study)。未記錄實際總投入時間，不以 Codex 執行時間代替。
- 引用／協助：本專案 [assignment.md](assignment.md)、[TASKS.md](docs/TASKS.md)；OpenAI Codex 與兩個 Subagents 協助實作、測試、文件整理。實際紀錄見 [MULTI_AGENT_LOG.md](docs/MULTI_AGENT_LOG.md) 與 [AUTOMATIONS.md](docs/AUTOMATIONS.md)。

本次依使用者指定採 Codex 自學流程，保留兩個任務、兩個可重複 automation、實際多代理與執行證據的練習目標。沒有使用或宣稱使用 Warp Drive、Warp MCP、Warp saved prompts 或 Warp 多分頁；因此不宣稱完成原課程的 Warp 專屬要求。

## 完成的任務

| 任務 | 難度 | 實作與證據 |
| --- | --- | --- |
| Task 2：Notes search with pagination and sorting | medium | SQLAlchemy 組合標題／內容不分大小寫搜尋、排序及 SQL 分頁；回傳 items、total、page、page_size。React 提供搜尋框、筆數、排序與前後頁。`backend/tests/test_notes.py` 包含空搜尋、找不到、萬用字元、非法參數、排序與分頁邊界測試。 |
| Task 9：Query performance and indexes | easy–medium | 建立 `(title, id)` 與 `(created_at DESC, id DESC)` 索引，啟動時可重複初始化。以 5,000 筆資料檢查 EXPLAIN、前後結果一致與啟動接線；50,000 筆資料實測比較。 |

搜尋實作路徑為 `/notes/search/`；不帶結尾斜線的課題路徑由 FastAPI 重新導向至此路徑。Task 2 採 React browser modules，未實作 Task 1 的 Vite 遷移。React 固定為 18.3.1 並由 CDN 載入，使用時需要網路。

## Automation A：Codex 品質驗收

### 設計、輸入輸出與步驟

入口為 `python scripts/run_automation.py quality`，從任何工作目錄執行皆使用 week5 作為根目錄。輸入是目前程式與測試；輸出是退出碼及 `docs/runs/` 的帶時間 JSON 紀錄。步驟依序為：所有後端 pytest、Ruff、week5 差異空白檢查、Playwright Chromium 執行 React 測試頁。失敗停止後續步驟並留下輸出。

### Before vs. after

原本需手動輸入後端測試、lint，另開瀏覽器操作搜尋、排序與分頁，且輸出散在終端機。現在以一條命令依序驗證並保留命令、時間、退出碼與完整輸出。瀏覽器執行器已由暫存目錄整理到專案，不依賴這次對話。

### 自主程度、權限與監督

使用者授權 Codex 在 week5 實作及測試，禁止 commit/push。流程本身不自動修復程式、不操作正式資料庫；pytest 使用暫存資料庫、前端測試使用 mock API。主 Agent 審閱變更並執行驗收。下載依賴與啟動 Chromium 需要環境允許的網路／程序權限；本次透過受審查的升權工具執行，未修改權限設定。

### 實際使用與效果

收尾實際執行結果：29 項後端測試、12 個瀏覽器斷言、Ruff 與差異檢查全部通過。見 [原始 quality 紀錄](docs/runs/20261023T182702572117-quality.json)。前端涵蓋搜尋、空結果、分頁邊界、排序重設頁數及原有新增／完成操作。這解決整合後遺漏檢查與沒有保留輸出的問題。

文件收尾後再執行一次，結果相同，證實流程可重複執行，見 [最終 quality 紀錄](docs/runs/20261023T182928309089-quality.json)。

## Automation B：Codex 索引效能比較

### 設計、輸入輸出與步驟

入口為 `python scripts/run_automation.py performance --rows 50000 --repeats 20`。輸入為資料筆數與重複次數，皆須大於零。先執行索引的 3 項 pytest，再建立暫存 SQLite 資料庫；量測索引前後的四種分頁查詢、EXPLAIN 計畫，並確認前後結果一致。輸出同樣保存為 JSON；暫存資料庫結束後刪除，不修改 `data/app.db`。

### Before vs. after

原本要手動準備資料、建索引、複製 SQL、查看查詢計畫及整理時間，容易拿不同資料比較。現在同一份固定生成資料先量測再建索引，保存原始計畫與中位數，方便重跑與審閱。時間只作比較，測試不設易受負載影響的速度門檻。

### 自主程度、權限與監督

Codex 可新增索引 helper、測試與 benchmark；Agent B 不可修改既有未提交檔案，啟動接線由主 Agent 負責。主 Agent 審閱 SQL、查詢結果與計畫，獨立重跑。流程沒有部署、提交或推送功能。

### 實際使用與效果

見 [原始 performance 紀錄](docs/runs/20261023T182703743599-performance.json)：3 項索引測試通過，50,000 筆、20 次重複、page=11、page_size=10 的暖快取中位數如下。

| 查詢 | 索引前 ms | 索引後 ms |
| --- | ---: | ---: |
| 標題排序 | 5.5437 | 0.0517 |
| 標題排序＋篩選 | 24.1789 | 0.3280 |
| 時間排序 | 8.3922 | 0.0497 |
| 時間排序＋篩選 | 59.6185 | 0.3060 |

結果一致，查詢計畫取消暫存排序並使用對應索引。這解決只憑感覺判定索引有效的問題。量測與 quality 流程有時間重疊，受機器負載影響；數字不代表固定加速倍率。比較僅含 SELECT，不含 COUNT、HTTP、索引建立或寫入成本；任意子字串搜尋仍需掃描，深分頁也不保證同樣收益。

## 真實 Codex 多代理協作

實作階段由主 Agent 建立兩個真正的 Subagents，先後啟動且執行期間重疊，並非單一 Agent 模擬角色：

- Agent A `/root/task2_frontend`：只編輯 `frontend/`，完成 Task 2 React UI 與瀏覽器測試頁。
- Agent B `/root/task9_indexes`：只新增索引模組、索引測試及 benchmark 三個指定檔案。
- 主 Agent `/root`：事先備存既有差異、確認檔案所有權，接線索引、審閱整合、獨立驗收並整理文件。

B 回報 helper 介面後主 Agent 完成啟動接線；A 同時製作前端。分工讓前端與資料庫工作互不等待。共享目錄可能造成覆寫，以檔案隔離與訊息協調降低風險；沒有使用 worktree，也沒有觀察到檔案衝突。既有 7 個未提交檔案中，6 個差異保持不變，main.py 保留原遷移變更後只增添索引接線。沒有量測單代理基準，因此不捏造節省時數。

Agent A 初報 13 個斷言，主 Agent 實際執行結果是 12 個，紀錄以實測修正。收尾的 quality/performance 是可重複子程序流程，不將它們冒稱為新的多代理 session。完整過程見 [協作紀錄](docs/MULTI_AGENT_LOG.md)。

## 驗收限制與完成狀態

兩個指定任務、兩個可重複流程、真實執行證據、Codex 多代理紀錄與本 writeup 均已完成。保留既有 Pydantic／FastAPI／Starlette 棄用警告，本次不擴大範圍重構。原自動化瀏覽器測試使用 mock API，後端 API 由 pytest 獨立驗證。後續另於暫存副本啟動真正 FastAPI 與全新 SQLite，以 Chromium 驗證 React、搜尋、排序、分頁及重新整理後資料保留；沒有 mock API。使用者也已親自完成真實瀏覽器驗收並回報全部通過。

依自學版範圍已完成；姓名已依使用者提供填寫，總時間誠實記為未追蹤。未進行 Warp 操作。提交前依使用者授權整理公開紀錄並建立 Git commit；不執行 push。原課程的 collaborators、Gradescope 與 Warp 證據不列為此次自學版要求。
