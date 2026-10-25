# Week 5 協作紀錄（2026-10-23）

本次使用 Codex 真正的兩個 Subagents，兩者在任何一方完成前均已啟動，平行處理獨立任務。依使用者指定，本次採 Codex 自學版，不要求 Warp 專屬功能。此紀錄不是 Warp 不同分頁操作證明，也不宣稱符合原課程的 Warp 專屬要求。

## 分工與隔離

| 角色 | 任務 | 檔案所有權 |
| --- | --- | --- |
| `/root/task2_frontend`（Agent A） | Task 2（medium）：React 搜尋、結果數、排序、分頁，保留原有操作 | 僅 `frontend/` |
| `/root/task9_indexes`（Agent B） | Task 9（easy–medium）：索引、回歸測試、效能比較 | 僅新增 `backend/app/indexes.py`、`backend/tests/test_indexes.py`、`scripts/benchmark_indexes.py` |
| `/root`（主 Agent） | 協調、啟動接線、獨立驗收、文件 | `backend/app/main.py` 的增量接線與文件 |

開始前已有 7 個後端／測試檔案未提交。主 Agent 將原始差異備存至 暫存目錄中的 `week5-before-multiagent.patch`；兩個 Subagents 均不得修改這些檔案。主 Agent 只在原有 main.py 修改之上增加索引匯入與初始化。沒有 commit 或 push。

## 協作過程與結果

1. 主 Agent 先宣布檔案隔離方案，再連續啟動 A、B，讓前端與索引工作同時進行。
2. B 提供 `ensure_query_indexes(engine)` 介面；主 Agent 在資料表建立及舊資料遷移後接線，避免修改 B 的檔案。
3. A 確認 Task 2 需要 React，但不要求 Task 1 的 Vite 遷移，因此採固定版本 React 18.3.1 ES modules，沿用靜態服務，避免增加完整建置工具。
4. 主 Agent 在 `/tmp` 建立 Python 測試環境，供 B 測試；A 同時製作獨立瀏覽器測試頁。
5. B 完成兩個排序索引、5,000 筆資料回歸測試與 50,000 筆 benchmark；A 完成 React 功能與 mock API 瀏覽器驗收頁。
6. 主 Agent 審閱整合、格式化新增 benchmark，獨立重跑測試與效能比較，檢查原始未提交內容保留。

平行的收益是前端與資料庫測試互不等待。主要風險是共享目錄及啟動介面不一致，以明確檔案所有權與訊息確認介面處理。此次沒有使用隔離 worktree，也沒有發生檔案衝突。

## 使用與限制

- 啟動方式維持 README 的 `make run`；前端需要連線至 `esm.sh` 載入 React，不需 npm 建置。
- 前端測試入口：啟動應用後開啟 `/static/tests.html`。使用 mock API，不會修改實際資料庫。
- 後端測試：`PYTHONPATH=. python -m pytest -q backend/tests -p no:cacheprovider`。
- 效能比較：`PYTHONPATH=. python scripts/benchmark_indexes.py --rows 50000 --repeats 20`；僅操作暫存資料庫。

## 主 Agent 效能重跑

50,000 筆、20 次重複、暖快取中位數，page=11、page_size=10：

| 查詢 | 索引前 ms | 索引後 ms |
| --- | ---: | ---: |
| 標題排序 | 4.4615 | 0.0444 |
| 標題排序＋MATCH 篩選 | 23.5526 | 0.2800 |
| 建立時間排序 | 5.1437 | 0.0426 |
| 建立時間排序＋MATCH 篩選 | 32.7974 | 0.2669 |

前後查詢結果完全一致。EXPLAIN 從全表掃描＋暫存排序改為使用相應索引，取消暫存排序。這只比較分頁 SELECT，不含 COUNT、HTTP、前端與索引建立成本；任意子字串搜尋仍需掃描，不能推論所有搜尋或深分頁均有相同加速。

後端 29 項測試及 Ruff 檢查通過。既有 Pydantic Config 與 FastAPI startup 寫法有棄用警告，本次未擴大範圍重構。

主 Agent 使用 Playwright 與 Chromium 實際執行 `frontend/tests.html`，12 個斷言全數通過（Agent A 起初回報 13 個，依實際輸出修正）。涵蓋搜尋、空結果、排序、上一頁／下一頁與邊界，以及新增筆記、新增／完成 Action Items。以瀏覽器 route 提供本機檔案、mock API 驗證 React UI；後端由獨立 pytest 驗證，未宣稱完整真實 API 端到端驗證。

## 自學版收尾

主 Agent 將原先位於 `/tmp` 的瀏覽器執行器整理為 `scripts/check_frontend.py`，新增 `scripts/run_automation.py`，提供 quality 與 performance 兩個可重複流程，並實際執行。操作方式與原始輸出見 [AUTOMATIONS.md](AUTOMATIONS.md) 及 `docs/runs/`；writeup 已依此更新。收尾沒有再啟動 Subagents，也未將兩個子程序誤稱為多代理；真正的多代理是上面記錄的 A、B 實作階段。

授權範圍：代理可讀寫 week5、在暫存目錄安裝驗證工具並執行測試；不得 commit、push 或覆蓋既有未提交修改。主 Agent 審閱檔案邊界、對照原差異、整合並獨立驗證。依賴下載及 Chromium 執行曾因沙箱限制使用受審查的升權工具執行，並非無限制系統權限。

## 正式提交前驗收

後續在暫存副本與全新 SQLite 啟動真實 FastAPI，透過 API 建立 12 筆筆記與 1 筆 Action Item；Chromium 直接連線首頁，確認搜尋、排序、分頁及重新整理後資料保留，不使用 mock API。使用者親自完成瀏覽器驗收並回報全部通過。原專案與原資料庫經雜湊比對保持不變。公開前僅匿名化既有執行紀錄中的本機路徑，保留測試結果、警告與效能證據。
