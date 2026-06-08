# Hivewire 專業詞彙表（Single Source of Truth）

本文件為 Hivewire 專案的術語定義與解釋，提供繁體中文、簡體中文與英文的一致對照，作為跨國工程師協作的唯一參照來源（Single Source of Truth）。

---

## 使用規則（Normative）

1. 本文件中的英文術語為主鍵（Primary key）；中文以英文術語對照為準。
2. 程式碼與 API 欄位命名保持原樣（例如 `runId`、`parentRunId`、`from_seq`、`HIVEWIRE_MODEL_SMART`），不進行翻譯。
3. 若術語在不同上下文有不同語義，必須拆分成不同條目（例如 Session vs Run）。
4. 新增/修改術語時，必須同時補齊三語定義並標注常見混淆點（Pitfalls）。

---

## 詞彙表（Glossary）

### 協議與事件（Protocol & Events）

| 英文術語 | 繁體中文 | 简体中文 | 定義與解釋 |
|---|---|---|---|
| AG-UI | AG-UI（代理—使用者互動協議） | AG-UI（代理—用户交互协议） | 一套開放、輕量、事件驅動的 Agent ↔ UI 協議標準，用於將 agent 後端的狀態、事件、工具調用與訊息串流，以統一事件格式傳給前端應用。 |
| Agent–User Interaction Protocol | 代理—使用者互動協議 | 代理—用户交互协议 | AG-UI 的全名所描述的協議層定位：專注於 UI 與 agent 的互動事件流，而非模型供應商 API。 |
| Event | 事件 | 事件 | 協議中最小的通訊單位；以 `type` 區分語義，並可攜帶識別資訊（如 `runId`）與內容（如文字增量、工具結果）。 |
| Event stream | 事件串流 | 事件流 | 後端以流式方式連續推送事件給客戶端；Hivewire 使用 SSE 來承載事件串流。 |
| SSE (Server-Sent Events) | 伺服器推送事件 | 服务器推送事件 | 基於 HTTP 的單向流式推送機制；瀏覽器端通常以 `EventSource` 接收。Hivewire 用 SSE 發送 AG-UI 事件。 |
| Protocol Gateway | 協議閘道 | 协议网关 | 對外暴露 HTTP/SSE 端點的服務；UI/Editor 只與 Gateway 交互，不直接連到 runtime。 |
| Wire-compatible | 線路相容 / 協議相容 | 线路兼容 / 协议兼容 | 指輸出事件格式與語義足以被對應協議的客戶端直接消費，不需額外適配層。 |
| Custom event | 自定義事件 | 自定义事件 | 不在標準事件集合內、但允許擴展的事件；在 Hivewire 中常用於例如 `extension_reloaded` 的廣播通知。 |
| Snapshot | 快照 | 快照 | 用於一次性同步完整狀態的事件/資料（例如 `STATE_SNAPSHOT`、`MESSAGES_SNAPSHOT`），通常搭配 delta 增量事件使用。 |
| Delta | 增量 | 增量 | 用於同步狀態變化的增量片段（差量更新），與 Snapshot 互補。 |

### 會話、分支與可回放（Sessions, Branching, Replay）

| 英文術語 | 繁體中文 | 简体中文 | 定義與解釋 |
|---|---|---|---|
| Session | 會話 | 会话 | 使用者與 agent 的一次持續互動上下文；在 Hivewire 中，session 對應一條事件日誌（JSONL），可被續傳、重播與分叉。 |
| Thread / threadId | 執行緒/對話線（threadId） | 线程/对话线（threadId） | AG-UI 常用識別一段對話的欄位；在 Hivewire 中常可視為 session 的對應識別。 |
| Run / runId | 一次執行（runId） | 一次执行（runId） | agent 對某個輸入（steer/follow-up）的一次處理流程；同一 session 中可有多個 run。 |
| parentRunId | 父執行 ID | 父执行 ID | 表示 run 的血緣關係：子 run 指向其 parent run，支援 swarm 子代理分軌與分支追溯。 |
| Fork | 分叉 | 分叉 | 從既有事件序列的某個節點（seq）建立一個新的 session 分支；原分支不變，新分支從該點繼續演進。 |
| Time travel | 時光旅行（回溯/分叉） | 时光旅行（回溯/分叉） | 泛指從某一歷史步驟回到當時狀態並沿另一條路徑繼續的能力；通常由 replay + fork 支撐。 |
| Replay | 重播 | 重播 | 將歷史事件按序重新輸出給客戶端，以便 UI 重建狀態或用於審計與除錯。 |
| Resume | 續傳 | 续传 | 客戶端斷線後，從特定 `from_seq` 重新訂閱事件流並接續後續事件。 |
| Append-only log | 只追加日誌 | 只追加日志 | 事件存儲模型：新事件只能追加，既有事件不修改；利於審計、回放、分支與可觀測性。 |
| JSONL | JSON Lines | JSON Lines | 一種按行存放 JSON 物件的格式；Hivewire 用它作為 session 事件落盤格式。 |
| seq | 序號（seq） | 序号（seq） | 事件在單一 session 內的單調遞增序列號，用於重播與續傳定位。 |
| ts / timestamp | 時間戳（ts） | 时间戳（ts） | 事件時間資訊；在 Hivewire 中常用 `ts`（浮點秒）作為落盤時間。 |

### 輸入模式（Steer & Follow-up）

| 英文術語 | 繁體中文 | 简体中文 | 定義與解釋 |
|---|---|---|---|
| Steer | 介入/導向（Steer） | 介入/导向（Steer） | 立即改變 agent 當前工作方向的輸入模式；常用於中斷正在進行的計畫並重新導向。 |
| Follow-up | 後續追加（Follow-up） | 后续追加（Follow-up） | 不打斷當前 run 的輸入模式；通常進入隊列，等待當前 run 結束後再處理。 |
| Interrupt | 中斷 | 中断 | 人在迴路（Human-in-the-loop）的介入能力；在 Hivewire 中通常與 steer 相關。 |

### Swarm 與並行（Swarm & Concurrency）

| 英文術語 | 繁體中文 | 简体中文 | 定義與解釋 |
|---|---|---|---|
| Swarm | 群體協作 / 多代理並行（Swarm） | 群体协作 / 多代理并行（Swarm） | parent run 將任務拆分為多個子任務，並行啟動多個 sub-agent；事件以 `runId`/`parentRunId` 關聯，UI 可分軌展示。 |
| Sub-agent | 子代理 | 子代理 | 在 swarm 中被派生出的獨立 agent run，通常負責單一子任務。 |
| Concurrency | 並行（非必然平行） | 并行（非必然并行） | 多個任務在時間上重疊執行；在 Python 中常以 `asyncio` 實現。 |

### 模型、路由與成本（Models, Routing, Cost）

| 英文術語 | 繁體中文 | 简体中文 | 定義與解釋 |
|---|---|---|---|
| Provider | 模型供應商 | 模型供应商 | 提供模型 API 的平台（例如 Anthropic/OpenAI/Gemini）或本地推理後端。 |
| LiteLLM | LiteLLM（模型閘道/代理） | LiteLLM（模型网关/代理） | 用於統一多供應商與本地後端的調用介面；可作為 Python 依賴或獨立 proxy（Docker）運行。 |
| API base | API 基址 | API 基址 | 代理/供應商的 API 入口（例如 `HIVEWIRE_API_BASE` 指向 LiteLLM proxy）。 |
| Tier | 層級（smart/cheap） | 层级（smart/cheap） | 用能力/成本抽象模型選擇；上層工作流傳 tier 而非模型名，便於成本路由。 |
| smart | 高能力層（smart） | 高能力层（smart） | 預期用於高品質/高成本模型的 tier。 |
| cheap | 低成本層（cheap） | 低成本层（cheap） | 預期用於便宜或本地模型的 tier，常用於 swarm fan-out 子任務。 |
| Mock model | 模擬模型 | 模拟模型 | 無外部模型配置時的 fallback，返回可預期輸出以驗證事件流與 UI。 |

### 擴充、工具與安全（Extensions, Tools, Security）

| 英文術語 | 繁體中文 | 简体中文 | 定義與解釋 |
|---|---|---|---|
| Extension | 擴充 | 扩展 | 可插拔的功能包（目錄+`manifest.json`）；可新增工具、提示詞、主題或 MCP 接入。 |
| manifest.json | 擴充清單檔 | 扩展清单文件 | 描述擴充種類（kind）、入口（entry/command）、能力宣告（capabilities）等的元資料。 |
| kind | 類型（kind） | 类型（kind） | 擴充的貢獻類型：常見有 `tool`、`mcp`、`prompt`、`theme`。 |
| Tool | 工具 | 工具 | agent 可調用的函數能力；在 Hivewire 中通常由 extension 提供並以事件方式呈現 tool call 生命週期。 |
| Tool call | 工具調用 | 工具调用 | agent 對工具的一次呼叫過程，通常包含開始、參數、結果等事件。 |
| MCP (Model Context Protocol) | MCP（模型上下文協議） | MCP（模型上下文协议） | Agent ↔ Tools/Data 的開放標準，讓 agent 以標準化方式連接外部系統工具與資料源。 |
| Capability | 能力（權限） | 能力（权限） | extension 需要的權限宣告（如網路、檔案讀寫），由 allow-list 策略控制。 |
| Allow-list | 白名單 | 白名单 | 允許集合；超出白名單的 capability 會被拒絕載入或執行。 |
| Sandbox | 沙箱 | 沙箱 | 隔離執行環境，用於降低不可信擴充的風險；Hivewire 提供 subprocess 或 Docker 兩種模式。 |
| Subprocess sandbox | 子程序沙箱 | 子进程沙箱 | 在本機以子程序執行擴充；隔離程度較低但啟動快速。 |
| Docker sandbox | Docker 沙箱 | Docker 沙箱 | 在容器中執行擴充；可搭配唯讀檔案系統、網路隔離與資源限制提升安全性。 |
| Hot reload | 熱重載 | 热重载 | 檔案變更後自動重新載入擴充，並以事件通知 UI（常見為 `extension_reloaded`）。 |

### UI 與資訊架構（UI & Information Architecture）

| 英文術語 | 繁體中文 | 简体中文 | 定義與解釋 |
|---|---|---|---|
| UI host | UI 宿主 | UI 宿主 | 負責渲染與互動的前端應用（Web UI）；透過協議事件流驅動狀態更新。 |
| Sidebar | 側欄 | 侧栏 | IDE-like 佈局的左側導覽區；Hivewire 通常用於 sessions tree。 |
| Session tree | 會話樹 | 会话树 | 以 parent/from_seq 呈現 fork 分支關係的樹狀結構導覽。 |
| Inspector | 檢視器/詳情面板 | 检视器/详情面板 | IDE-like 佈局的右側細節區（可選/規劃），呈現 run/tool/model 等細節。 |
| Composer | 輸入區 | 输入区 | 用於輸入 steer/follow-up 的消息編輯區（通常在底部）。 |
| Toast | 提示浮層 | 提示浮层 | 短暫通知（例如擴充重載、fork 成功）的 UI 元件。 |

### 編輯器整合（Editor Integration）

| 英文術語 | 繁體中文 | 简体中文 | 定義與解釋 |
|---|---|---|---|
| ACP (Agent Client Protocol) | ACP（代理客戶端協議） | ACP（代理客户端协议） | 讓編輯器（Zed/JetBrains/Neovim 等）以標準方式與 agent runtime 互動的協議；常以 JSON-RPC over stdio 形式出現。 |
| JSON-RPC | JSON-RPC | JSON-RPC | 一種以 JSON 表達的 RPC 協議格式；常用於 stdio 或 WebSocket 傳輸層。 |

### 記憶與狀態（Memory & State）

| 英文術語 | 繁體中文 | 简体中文 | 定義與解釋 |
|---|---|---|---|
| Memory | 記憶（跨會話） | 记忆（跨会话） | 為提升長期協作體驗，在不同 session 間保存與召回資訊的機制。 |
| Recall | 召回 | 召回 | 從 memory 中挑選與當前任務相關的片段，注入到模型/agent 的上下文中。 |
| Honcho | Honcho（外部記憶後端） | Honcho（外部记忆后端） | 一種可選的記憶後端；未配置或不可用時可回退至 local memory。 |

---

## 常見混淆點（Pitfalls）

1. Session vs Run：Session 是長期上下文（可 fork/tree），Run 是一次輸入處理（有起止事件）。
2. Replay vs Resume：Replay 是重放歷史；Resume 是從某個 seq 接續訂閱。
3. Swarm vs Fork：Swarm 是並行子代理協作；Fork 是從歷史節點分支出新 session。
4. MCP vs Tool：MCP 是接工具/資料的標準協議；Tool 是 agent 實際可調用的能力單元（可能由 MCP 提供）。
5. Sandbox vs Capability：Sandbox 是執行隔離；Capability 是策略授權，兩者互補但不等價。

