# Hivewire 產品需求說明書（PRD）

| 欄位 | 內容 |
|---|---|
| 產品名稱 | Hivewire — Agent Swarm Harness |
| 產品定位 | 自託管、供應商無關（provider-agnostic）的 agent swarm harness；以可觀測、可續傳、可版本化的協議層（AG-UI 相容）連接 UI 與 runtime；以 append-only event log 為核心原語，提供 replay / fork / time-travel |
| 目標受眾 | 平台/基礎設施工程師、Agent 應用開發者、研究者/高階使用者、編輯器使用者（ACP 客戶端） |
| 文件版本 | 2.1 |
| 產品版本 | 0.0.1（research preview） |
| 最後更新 | 2026-06-08 |
| UI 對齊基準 | TRAE IDE 空間佈局與視覺規範（左側 Explorer / 主工作區 / 右側 Inspector / 底部 Panel） |
| 參考實作 | `hivewire/`（Python FastAPI gateway + agent runtime + event store）、`hivewire/ui/`（React/Vite UI host）、`hivestack/`（部署與角色腳本） |

---

## 0. 文件閱讀指引

- 第 1–4 章：定義「為什麼做、做給誰」，適合決策者與產品經理。
- 第 5–7 章：定義「做什麼」，是工程開發的功能契約。
- 第 8 章：定義「長什麼樣、怎麼擺」，是 UI/UX 設計與前端落地的視覺規範。所有 UI 排版標準均對齊 TRAE IDE。
- 第 9–12 章：非功能需求、里程碑、成功指標、風險。

---

## 1. 背景與問題

### 1.1 背景
現代 agent 應用正從「單一對話迴圈」演進到「多代理協作（swarm）+ 長時間運行 + 可審計/可回放」。傳統整合方式常把 UI、runtime、模型供應商綁定在一起，造成成本、可觀測性、可擴展性、協作效率的瓶頸。Hivewire 賭的是：未來的 agent 基礎設施會像現代資料庫一樣，**以 append-only event log 為核心原語**，從中免費獲得可觀測性、續傳、版本化與分叉。

### 1.2 核心痛點
| # | 痛點 | 現況 | 後果 |
|---|---|---|---|
| P1 | 供應商鎖定 | runtime 直接 import 某家 SDK | 換模型 / 比價 / 接本地模型都要改碼 |
| P2 | 不可觀測 | agent 內部狀態藏在記憶體裡 | 出錯難 debug、無法審計、無法回放 |
| P3 | 不可回溯 | 對話只能線性前進 | 想試「另一條路」就得從頭重來 |
| P4 | UI 與 runtime 綁死 | 換前端 = 重接協議 | Web / Editor / CLI 無法共享同一個 runtime |
| P5 | 擴充麻煩、不安全 | 改 tool 要重啟；第三方擴充無隔離 | 開發迴圈慢、執行不可信代碼有風險 |
| P6 | 成本失控 | 所有任務都用 frontier model | fan-out 並行子任務燒錢 |

---

## 2. 產品目標與非目標

### 2.1 產品目標（Goals）
- **G1 Provider-agnostic**：模型供應商可替換，切換為「配置變更」而非「程式碼變更」。
- **G2 協議層解耦**：UI / Editor / CLI 等客戶端只需對接協議閘道（Gateway），不直連 runtime。
- **G3 以事件為核心**：session = append-only event log，天然提供 observable / resumable / versioned。
- **G4 Fork / Replay**：任一步 fork 新分支；任意 seq 重播與續傳。
- **G5 Swarm**：一個 parent run 可並行 fan-out 多子代理，並在 UI 以 runId / parentRunId 分軌呈現。
- **G6 熱重載擴充**：擴充（tool / mcp / prompt / theme）修改後自動 reload，UI 無需手動刷新。
- **G7 可控成本**：以 tier（smart / cheap）抽象模型能力，支援成本路由策略。
- **G8 IDE/Editor 原生**：支援 ACP（Agent Client Protocol），讓編輯器可直接使用同一套 runtime。
- **G9 IDE-class UI**：前端排版與互動標準對齊 TRAE IDE，確保「可長時間沉浸使用」的資訊密度與一致性。

### 2.2 非目標（Non-Goals）
- **N1** 不提供 SaaS 托管與計費方案；本階段定位為可自託管的開源基礎設施。
- **N2** 不將沙箱目標定為完整 syscall 等級隔離；目前以 process + secret 隔離為主，Docker 沙箱作為可選硬化方案。
- **N3** 不綁定特定垂直場景（Coding agent / Customer support 等屬於上層產品，可建立在 Hivewire 之上）。
- **N4** 不取代模型供應商或 LiteLLM；Hivewire 是其上的協議與編排層。

---

## 3. 產品範圍與核心功能模塊

### 3.1 核心功能模塊（按責任邊界）

| # | 模塊 | 責任 | 對應實作 |
|---|---|---|---|
| M1 | 協議閘道 Protocol Gateway | 對外 HTTP API + SSE，輸出 AG-UI 相容事件流；控制 session、replay、fork、input（steer / follow-up） | `hivewire/src/hivewire/gateway.py` |
| M2 | 事件存儲 Event Store | session JSONL 事件日誌；seq / ts 打戳並持久化；支援 tree / lineage（fork parent / from_seq） | `hivewire/src/hivewire/store.py` |
| M3 | Agent Runtime | agent loop；steer / follow-up；swarm fan-out；runId / parentRunId 關聯 | `hivewire/src/hivewire/agent.py` |
| M4 | LLM 路由 Model Routing | tier→model 映射（smart / cheap），可選經 LiteLLM proxy；無模型時 mock | `hivewire/src/hivewire/llm.py` |
| M5 | 擴充系統 Extensions | kind：tool / mcp / prompt / theme；capability allow-list；熱重載 + 廣播 reload 事件 | `hivewire/src/hivewire/extensions.py` |
| M6 | 記憶 Memory | 跨 session 記憶：local JSONL / honcho / off | `hivewire/src/hivewire/memory.py` |
| M7 | UI Host | Web UI：會話樹、消息流、fork、theme picker、輸入框（steer / follow-up） | `hivewire/ui/src/` |
| M8 | Editor Adapter | ACP（JSON-RPC over stdio）橋接到 gateway / runtime | `hivewire/src/hivewire/acp.py` |
| M9 | 包管理 Packaging | ASS 擴充包：`install <git\|path>` / `list` | `hivewire/src/hivewire/packaging.py` |
| M10 | 部署 Stack | `hivestack/` 提供 setup、roles、commands、tools 等可組合部署腳本 | `hivestack/` |

### 3.2 範圍邊界

| 範圍 | 內容 |
|---|---|
| In scope | 協議層、事件存儲、agent 編排、擴充宿主、模型路由、Web UI、ACP adapter、ASS 包工具鏈 |
| Out of scope（本版） | 多租戶、SSO、雲端托管、垂直應用、計費 |

---

## 4. 用戶與使用場景

### 4.1 Persona

| Persona | 目標 | 典型行為 | Hivewire 如何幫 |
|---|---|---|---|
| 平台/基礎設施工程師 | 為團隊搭建可觀測、可擴充、可自託管的 agent 平台底座 | 關注協議、存儲、權限、沙箱、成本 | 協議層 + event store + LiteLLM gateway |
| Agent 應用開發者 | 在底座之上快速做工具與流程 | 編輯擴充、調試 tool、迭代 prompt | 擴充熱重載 + replay/fork + AG-UI |
| 研究者/高階使用者 | 多路徑實驗與對照評估 | 高頻 fork、比較不同 prompt / 模型 | fork、swarm、tier 路由 |
| 編輯器使用者 | 在 IDE 內完成任務 | 透過 ACP 使用同一 runtime | ACP adapter（Zed / JetBrains / Neovim） |
| 決策者 / 評估者 | 評估是否採用 | 比較鎖定風險、成本、合規 | 開源 + provider-agnostic + cost routing |

### 4.2 核心用戶場景（User Scenarios）

1. **離線快速驗證**：不配置 API key，使用 mock 模型觀察完整事件流與 UI 互動。
2. **成本路由**：主 agent 用 `smart`，swarm 子任務用 `cheap`，節省 token。
3. **Time-travel 除錯**：某一步偏離預期，從該 seq fork 分支並調整 prompt / 工具重跑。
4. **擴充開發**：改動 extension 後 UI 自動更新（toast + 內容立即生效）。
5. **IDE 內使用**：編輯器以 ACP 連接 gateway / runtime，實現一致體驗。
6. **多客戶端共享**：同一 session 可同時被 Web UI、Editor、CLI 訂閱，事件流一致。

---

## 5. 交互流程（Interaction Flows）

### 5.1 建立會話與串流
1. 使用者打開 UI → 自動 `POST /sessions` 建立 session。
2. UI 連線 SSE `GET /sessions/{id}/stream?from_seq=0`。
3. Gateway 先回放 history，再 tail live events。

### 5.2 Steer 與 Follow-up

| 動作 | 鍵盤 | 用途 | 行為 |
|---|---|---|---|
| Steer | Enter | 立即改變當前工作方向 | 若 runtime 正在跑，將 steer 注入（中斷剩餘計畫）；若無正在跑的 run，等同 follow-up 立即入列 |
| Follow-up | Alt+Enter | 排隊追加任務，不打斷當前 run | 入隊，待當前 run 完成後按序執行 |
| 換行 | Shift+Enter | 在輸入框內插入新行 | 不送出 |

### 5.3 Swarm（並行子代理）
1. 使用者輸入 `swarm: a | b | c`。
2. Runtime 建立 parent run → 並行啟動多個 sub-agent run（每個子任務一個 runId）。
3. 事件流中每個事件帶 runId；子代理事件帶 parentRunId，便於 UI 分軌展示（左側 3px 線條 + 縮排）。

### 5.4 Fork（Time-travel）
1. 使用者在任意消息 bubble 點 `⑂ fork`。
2. UI 發 `POST /sessions/{sid}/fork?from_seq=N`。
3. Gateway 建 forked session 並回傳新 sessionId。
4. UI 切換到新 session，並從 `from_seq=0` 重新串流。
5. 會話樹（Sessions Tree）更新：新 session 以 `parent / from_seq` 附著在原節點下。

### 5.5 Extension Hot Reload
1. 開發者修改 `extensions/*` 下檔案。
2. Host 偵測到變更 → reload extension。
3. Gateway 對所有 live session append `CUSTOM: hivewire.extension_reloaded`。
4. UI 顯示 toast，並刷新 extensions 列表 / 主題等配置。

---

## 6. 功能需求（Functional Requirements）

> 標記：**[Done]** 已驗證 ｜ **[Beta]** 可用待硬化 ｜ **[Planned]** roadmap

### 6.1 協議與會話
- **FR-1 [Done]** 建立 session：`POST /sessions` 回傳 sessionId。
- **FR-2 [Done]** 事件串流：SSE `GET /sessions/{id}/stream?from_seq=N`，先 replay 再 live。
- **FR-3 [Done]** 事件重播：`GET /sessions/{id}/events` 返回完整事件序列。
- **FR-4 [Done]** Session tree：`GET /sessions/tree` 返回 parent / from_seq 以構建樹。
- **FR-5 [Done]** Fork：`POST /sessions/{id}/fork?from_seq=N` 建立分支。
- **FR-6 [Done]** AG-UI v3 事件詞彙：`RUN_*`、`TEXT_MESSAGE_*`、`TOOL_CALL_*`、`STATE_*`、`MESSAGES_SNAPSHOT`、`CUSTOM`。

### 6.2 輸入與運行
- **FR-7 [Done]** Steer：`POST /sessions/{id}/input` mode=steer，立刻打斷 / 改變方向。
- **FR-8 [Done]** Follow-up：mode=follow_up，入隊等待。
- **FR-9 [Done]** Run 分軌：所有事件需攜帶 runId；子代理事件需攜帶 parentRunId。
- **FR-10 [Done]** Swarm：輸入 `swarm: a | b | c` 觸發 fan-out。

### 6.3 模型與路由
- **FR-11 [Done]** tier→model 映射：smart / cheap（可配置），支援 LiteLLM proxy。
- **FR-12 [Done]** Mock fallback：未配置模型時可離線跑。
- **FR-13 [Beta]** 經 LiteLLM proxy 做多供應商、成本追蹤、負載平衡。

### 6.4 擴充與安全
- **FR-14 [Done]** Extension kind：tool / mcp / prompt / theme。
- **FR-15 [Done]** Hot reload：變更即生效並廣播 reload 事件。
- **FR-16 [Done]** Capability allow-list：拒絕超權擴充。
- **FR-17 [Beta]** Sandbox：subprocess（預設）與 docker（可選）。
- **FR-18 [Done]** ASS 包：`hivewire install <git|path>` / `hivewire list`。

### 6.5 記憶
- **FR-19 [Done]** Memory 策略：local / honcho / off，召回注入 system message。

### 6.6 整合
- **FR-20 [Done]** ACP adapter：`hivewire acp`，JSON-RPC over stdio。
- **FR-21 [Done]** MCP：包裝任意 MCP server 成 Hivewire 工具。

### 6.7 UI 與互動
- **FR-22 [Done]** 三分區佈局（Sidebar / Main / 可擴展 Inspector），對齊 TRAE IDE。
- **FR-23 [Done]** Sessions Tree：顯示 fork 層級、active 節點高亮、節點 hover 高亮。
- **FR-24 [Done]** Composer：Enter / Alt+Enter / Shift+Enter 三種鍵盤行為。
- **FR-25 [Done]** Toast 通知：extension reload、fork 成功等。
- **FR-26 [Done]** Theme picker：theme extension 可即時套用。
- **FR-27 [Planned]** Inspector 面板：工具呼叫詳情、run 狀態、事件搜尋 / 過濾。
- **FR-28 [Planned]** Bottom Panel：連線狀態、錯誤、性能 / 成本統計。

---

## 7. 協議端點（API Contract）

| Method | Path | 用途 |
|---|---|---|
| POST | `/sessions` | 建立 session |
| GET | `/sessions/tree` | 取得 session 樹狀結構（含 fork lineage） |
| GET | `/sessions/{id}/stream?from_seq=N` | SSE 串流；先 replay 再 live |
| GET | `/sessions/{id}/events` | 重播完整事件 JSON |
| POST | `/sessions/{id}/input` | `{text, mode: "steer"｜"follow_up"}` |
| POST | `/sessions/{id}/fork?from_seq=N` | 從第 N 步分叉 |
| GET | `/extensions` | 列出已載入擴充（含 themes） |

事件均符合 AG-UI v3 規範，並由 Hivewire 在 `CUSTOM` 通道擴展自有訊號（如 `hivewire.extension_reloaded`）。

---

## 8. UI/UX 規範（與 TRAE IDE 對齊）

> 本章是 UI 設計與前端落地的視覺契約。所有色彩、字級、間距、組件樣式均需以本章為單一事實來源（single source of truth）。

### 8.1 空間佈局（Layout Structure）

對齊 TRAE IDE 的四區域模型：

```
┌────────────────────────────────────────────────────────────┐
│  Header (44–52px)  ─ brand · session id · actions · theme  │
├─────────┬──────────────────────────────┬───────────────────┤
│ Sidebar │           Main               │   Inspector       │
│ (L1)    │           (L2)               │   (L3, 可選)       │
│         │  ┌────────────────────────┐  │                   │
│ Sessions│  │   Conversation Log     │  │  Run details      │
│ Tree    │  │   (bubbles + tools)    │  │  Tool I/O         │
│         │  │                        │  │  Model tier       │
│         │  └────────────────────────┘  │  Event filter     │
│         │  ┌────────────────────────┐  │                   │
│         │  │   Composer (footer)    │  │                   │
│         │  └────────────────────────┘  │                   │
├─────────┴──────────────────────────────┴───────────────────┤
│  Bottom Panel (可選) — 連線狀態 · 成本 · 錯誤 · Terminal     │
└────────────────────────────────────────────────────────────┘
```

| 區域 | 尺寸建議 | 用途 | 對齊 TRAE IDE |
|---|---|---|---|
| **Header** | 高 44–52px | 品牌、session 短 ID、New、Theme picker、sidebar toggle | TRAE 頂部工具列高度與配置一致 |
| **L1 Sidebar** | 寬 200–240px（預設 210px），可收合 | Sessions Tree、未來：Extensions / Settings | 與 TRAE Explorer 寬度範圍一致 |
| **L2 Main** | 自適應，內容最大寬 720px | 對話/事件流 + Composer | 與 TRAE 編輯區「中央焦點」一致 |
| **L3 Inspector**（可選） | 寬 280–360px | Run 狀態、工具細節、事件過濾 | 對應 TRAE 右側 Agent / Outline 區 |
| **Bottom Panel**（可選） | 高 160–240px，可收合 | 連線、錯誤、成本、Terminal | 對應 TRAE 底部 Console / Terminal |
| **Composer** | 自適應高，最大 160px | Textarea + Send | 對應 TRAE 底部輸入區行為 |

### 8.2 色彩體系（Color System）

採深色 IDE 風格為基準；所有顏色必須來自語義 token，不允許硬編碼，theme extension 可覆蓋。

| Token | 用途 | 預設值 |
|---|---|---|
| `--bg` | 應用底色 | `#0f0f12` |
| `--panel` | 一般面板 / bubble 背景 | `#1a1a20` |
| `--sidebar` | 側欄背景（可略深於 panel） | `#15151b` |
| `--border` | 分隔線 / 邊框 | `rgba(138,138,153,0.20)` |
| `--text` | 主要文字 | `#eaeaf0` |
| `--muted` | 次要文字（時間、meta、placeholder） | `#8a8a99` |
| `--accent` | 主操作色（按鈕、focus、active 節點） | `#3b6ef5` |
| `--accent-on` | accent 上層文字 | `#ffffff` |
| `--success` | 成功狀態 / Toast 背景 | `#2a6f3a` |
| `--warning` | 警告 / tool bubble 邊框 | `#b58900` |
| `--danger` | 危險 / 錯誤 | `#d14b4b` |
| `--tool-bg` | tool 消息底色 | `#2a2a1f` |
| `--tool-fg` | tool 消息字色 | `#d8d8a0` |

色彩對比度規範：正文文字 / 背景 ≥ 4.5:1（WCAG AA）；`muted` 僅用於輔助資訊不承載關鍵內容。

### 8.3 字級規範（Typography）

對齊 TRAE IDE 的「高資訊密度、清晰可讀、ID 用等寬」原則。

| 層級 | 字級 | line-height | 字體 | 用途 |
|---|---|---|---|---|
| Display | 20px | 1.4 | system | 空狀態大標 |
| Title | 16px | 1.4 | system | 區塊標題 |
| Brand | 15px | 1.4 | system | Header 品牌 |
| Body | 14px | 1.5 | system-ui, sans-serif | 消息正文、輸入框 |
| Control | 13px | 1.4 | system | 按鈕、Chip |
| Meta | 12px | 1.4 | `ui-monospace, monospace` | 時間戳、runId、session ID、tree 節點 |
| Caption | 11px | 1.4 | system | 標籤、bubble 上方 role 行 |

說明：所有 ID / seq / runId / sessionId / 時間戳一律使用等寬字體（與 TRAE IDE 一致），確保視覺對齊。

### 8.4 間距與栅格（Spacing & Grid）

採 **4 / 8 基準制**：

| Token | 值 | 用途 |
|---|---|---|
| `--space-1` | 4px | 最小視覺單位（icon 與文字內距） |
| `--space-2` | 8px | 緊湊間距（chip 內距、控件 gap） |
| `--space-3` | 12px | 標準間距（bubble 內距、卡片內邊） |
| `--space-4` | 16px | 面板內距 |
| `--space-5` | 24px | 區塊分隔 |

控件高度：
- 小型按鈕 / icon button：**28px**
- 標準按鈕 / Send / 輸入框最小高：**44px**（觸控友好，並與 TRAE 主操作按鈕一致）

圓角規範：
- 按鈕 / Chip：**6–8px**
- Bubble：**12px**
- Toast：**8px**

### 8.5 組件樣式（Components）

#### 8.5.1 Header
- 結構：`[sidebar toggle] [brand "Hivewire"] [session 短 ID, muted] [flex spacer] [+ New] [Theme select]`
- 高度 48px；底部 1px border。
- New 按鈕：accent 背景 / 白字 / 13px / 600 weight / 圓角 6px。

#### 8.5.2 Sidebar Tree（會話樹）
- 節點：單行省略、hover 微高亮、active 背景 = accent 色 / 白字。
- 深度縮進步進 **14px**，根節點以 `●` 表示，分叉以 `⑂` 表示。
- 節點右側 muted 顯示 `@from_seq`。
- 字級 12px 等寬。

#### 8.5.3 Bubble（消息氣泡）

| 角色 | 對齊 | 背景 | 文字 | 特殊 |
|---|---|---|---|---|
| `user` | 右對齊 | accent | 白 | 最大寬 80% 或 720px |
| `assistant` | 左對齊 | panel | text | 最大寬 80% 或 720px |
| `tool` | 左對齊 | tool-bg（深黃卡其） | tool-fg | 內容以 `▸ name(...)` / `→ result` 格式呈現 |
| `sub-agent` | 左對齊 + 28px 縮排 | 同 role | 同 role | 左側 3px warning 色線條 + 最大寬 70% 或 640px |

bubble 上方 role 行：左 `role · runId`（muted, 11px），右 `⑂ fork` 按鈕（hover 出現）。

#### 8.5.4 Composer（輸入框）
- Textarea：min-h 24px，max-h 160px，自適應高，圓角 10px。
- Placeholder：`"Message Hivewire…  (Enter = steer · Alt+Enter = follow-up · Shift+Enter = newline)"`。
- Send 按鈕：高 44px、accent 背景、disabled 時降低不透明度。
- 鍵盤：
  - `Enter` → steer
  - `Alt+Enter` → follow-up
  - `Shift+Enter` → 換行

#### 8.5.5 Toast
- 位置：right: 16px / top: 56px（Header 下方）。
- 背景：success 色；padding 6/12；圓角 8px；陰影 `0 4px 16px #0008`。
- 自動消失：3 秒。
- 用途：extension reload、fork 成功、連線狀態變化。

#### 8.5.6 Chip / Example
- 空狀態下展示範例 prompt 的點擊區塊。
- 背景 panel、邊框 border、圓角 8px、padding 8/12、字級 13px、左對齊。

#### 8.5.7 Theme Select
- 原生 `<select>`，背景 panel、字色 text、邊框 border、圓角 6px、字級 12px。

### 8.6 互動與鍵盤（Keyboard Map）

| 快捷鍵 | 行為 | 對齊 TRAE IDE |
|---|---|---|
| `Enter` | 送出（steer） | 與聊天 / 命令面板提交直覺一致 |
| `Shift+Enter` | 換行 | 標準 textarea 慣例 |
| `Alt+Enter` | follow-up | 「不打斷當前動作的追加」 |
| `Esc`（建議） | 關閉浮層 / Inspector | IDE 通用退出 |
| `Cmd/Ctrl+K`（建議） | 聚焦輸入框 | IDE 通用命令焦點 |
| `Cmd/Ctrl+B`（建議） | 切換 Sidebar | 對齊 TRAE / VS Code |

### 8.7 狀態與回饋（States & Feedback）

| 狀態 | 視覺呈現 |
|---|---|
| Idle | Composer 可輸入、Send disabled 直至有文本 |
| Connecting | Header 顯示 `connecting…`（muted） |
| Streaming | 對應 bubble text 增長；Run lane 持續更新 |
| Tool calling | tool bubble 顯示 `▸ name(...)`，完成後追加 `→ result` |
| Extension reloaded | Toast `🔁 extension reloaded: <name>` |
| Fork created | Toast `⑂ forked from seq N`，並切換 session |
| Error / Disconnect | 底部 Panel 顯示紅色橫條（規劃） |

### 8.8 可用性與可訪問性（A11y）

- **對比度**：正文與背景對比 ≥ 4.5:1；muted 僅用於輔助。
- **焦點態**：所有可互動元素需要可見 focus ring（建議：半透明 accent 2px outline）。
- **鍵盤可達**：所有 click 操作必須可由鍵盤觸發（Tab / Enter / Space）。
- **滾動策略**：新消息自動滾到底；使用者手動向上閱讀時不強制拉回（後續增強：「回到底部」按鈕）。
- **語義 HTML**：使用 `<header> <aside> <main> <footer>`，便於螢幕閱讀器導航。

---

## 9. 非功能需求（NFR）

| 類別 | 需求 |
|---|---|
| **性能** | SSE 事件延遲 < 100ms（本地）；swarm 並行以 `asyncio.gather` 為基礎，可線性擴展子代理數量 |
| **可靠性** | 斷線可從 `from_seq` 精準恢復；重啟後可從磁碟 rehydrate session；replay 成功率 → 100% |
| **可觀測性** | 所有關鍵行為以事件落盤；可重播與審計；事件帶 seq / ts / runId |
| **安全** | Capability 白名單為策略邊界；Docker 沙箱為執行隔離；不可信擴充建議整 host 跑容器 |
| **可移植性** | 離線可跑（無需 API key）；Python ≥ 3.11；`uv sync` 起動；前後端分離；支援 editor / IDE 客戶端 |
| **可維護性** | 四層解耦（UI host / gateway / runtime / model gateway）；擴充與核心分離 |
| **相容性** | AG-UI v3 wire-compatible；ACP 相容；瀏覽器支援現代 Chromium / Safari / Firefox |
| **可訪問性** | WCAG AA 對比度；鍵盤全可達；focus ring 可見 |

---

## 10. 里程碑（Milestones）

### 10.1 現況（已具備 / Done）
- AG-UI 相容事件流、replay、fork、session tree
- steer / follow-up
- Swarm fan-out + parentRunId 分軌
- Extensions（tool / mcp / prompt / theme）+ hot reload + capability allow-list
- LiteLLM 路由 + tier 抽象 + mock fallback
- Memory（local / honcho / off）
- ACP adapter
- 對齊 TRAE IDE 的三分區 UI 基礎

### 10.2 Now（0–1 月）— 硬化核心
- R1 沙箱硬化：seccomp / AppArmor 範本與文件
- R2 事件 store 持久化選項：SQLite / 物件儲存後端 + retention policy
- R3 協議版本遷移策略
- R4 觀測強化：OpenTelemetry metrics / tracing 匯出
- R5 UI Inspector 面板（FR-27）：工具呼叫詳情、事件搜尋 / 過濾

### 10.3 Next（1–3 月）— 規模與協作
- R6 Swarm 進階：子代理間訊息傳遞、聚合策略（map-reduce）、失敗重試
- R7 權限與多租戶：session 級存取控制、API 認證
- R8 擴充市集 / registry：可發現、可評分、版本鎖定的 ASS 包目錄
- R9 UI Bottom Panel（FR-28）：連線、成本、錯誤、Terminal 整合

### 10.4 Later（3–6 月+）— 生態與企業
- R10 持久化 agent / 排程
- R11 評估框架：跨模型 / 分支 eval 與回放比較
- R12 更多 client SDK（官方 JS / Python）
- R13 企業部署藍圖：Helm chart、SSO、稽核日誌

---

## 11. 成功指標（KPI）

| 維度 | 指標 | 北極星方向 |
|---|---|---|
| **採用 Adoption** | GitHub stars、安裝數、活躍自託管部署 | 月增長 |
| **黏著 Engagement** | 平均 session / 週、fork 使用率、swarm 使用率 | 上升 |
| **生態 Ecosystem** | 第三方擴充（ASS 包）數量、MCP 整合數 | 上升 |
| **成本效益 Cost** | cheap-tier 任務佔比、相對全 frontier 的 token 節省 | 節省 ↑ |
| **可靠性 Reliability** | replay 成功率、e2e 測試通過率、console error 數 | error → 0 |
| **DX** | 從 clone 到首條事件流的時間（離線） | 最小化 |
| **UI 一致性** | 違反 8.2–8.5 token 的硬編碼樣式數 | 0 |

---

## 12. 風險與緩解

| 風險 | 影響 | 緩解 |
|---|---|---|
| 沙箱非完整隔離 | 不可信擴充可能逃逸 | 整 host 跑容器（seccomp / AppArmor / 唯讀 FS）；capability 預設拒絕 |
| AG-UI 規格演進 | wire 相容性破裂 | 釘住 v3、追蹤上游、`protocol_version` 遷移策略（R3） |
| LiteLLM 依賴 | 上游 API / 行為變動 | runtime 對其為可選；mock fallback；版本釘選 |
| JSONL store 擴展性 | 大量 / 長期 session 效能 | 可插拔後端（R2）、保留政策 |
| Early-stage 0.0.1 | API 仍可能變動 | 明示 research preview、語義化版本、變更日誌 |
| UI 樣式分散 | 與 TRAE IDE 對齊飄移 | 強制以 8.2–8.5 token 為單一事實來源 + lint 規則 |
| 單人 / 小團隊維護 | bus factor | 開源社群化、文件完善、擴充市集 |

---

## 13. 開放問題

1. 事件 store 的長期保留與隱私（PII）政策？是否需要事件層級加密？
2. 多租戶與認證要做到哪個層級（單機開源 vs. 企業托管）？
3. Swarm 子代理間是否需要共享狀態 / 黑板（blackboard）模型？
4. ASS 擴充市集的信任模型：簽章、審核、能力宣告稽核？
5. 是否提供官方托管版本，或維持純自託管開源？
6. UI Inspector 與 Bottom Panel 啟用後，預設是否展開？是否記憶使用者偏好？

---

## 14. 附錄

### 14.1 快速開始（離線、免 API key）

```bash
# 1. runtime + gateway
cd hivewire
uv sync
uv run hivewire           # http://127.0.0.1:8787

# 2. UI（另一個終端）
cd ui
npm install
npm run dev               # http://127.0.0.1:5173
```

互動：**Enter = steer**（中斷當前工作）、**Alt+Enter = follow-up**（排隊）。未設 `HIVEWIRE_MODEL` 時使用 mock 模型，可離線看完整事件流。

### 14.2 真實模型 + 成本路由

```bash
# 單一本地模型
HIVEWIRE_MODEL=ollama/qwen2.5:0.5b uv run hivewire

# 分 tier
HIVEWIRE_MODEL_SMART=anthropic/claude-opus-4-8 \
HIVEWIRE_MODEL_CHEAP=ollama/qwen2.5:0.5b uv run hivewire

# 或經 LiteLLM proxy
docker compose up -d litellm
HIVEWIRE_MODEL_SMART=smart HIVEWIRE_MODEL_CHEAP=cheap \
HIVEWIRE_API_BASE=http://127.0.0.1:4000 uv run hivewire
```

### 14.3 關鍵環境變數

| 變數 | 作用 |
|---|---|
| `HIVEWIRE_MODEL` | 兩 tier 的 fallback 模型 |
| `HIVEWIRE_MODEL_SMART` / `HIVEWIRE_MODEL_CHEAP` | 分 tier 模型 |
| `HIVEWIRE_API_BASE` | LiteLLM proxy 位址 |
| `HIVEWIRE_SANDBOX` | `subprocess`（預設） / `docker` |
| `HIVEWIRE_ALLOWED_CAPS` | 逗號分隔的允許能力（如 `net,fs:read`） |
| `HIVEWIRE_MEMORY` | `local`（預設） / `honcho` / `off` |
| `HIVEWIRE_SANDBOX_IMAGE` | Docker 沙箱映像（預設 `python:3.11-slim`） |

### 14.4 名詞對照

| 詞 | 解釋 |
|---|---|
| **AG-UI** | Agent ↔ UI 的事件協議；Hivewire wire-compatible v3 |
| **ACP** | Agent Client Protocol（Zed / JetBrains / Neovim） |
| **ASS 包** | 含 `manifest.json` 的擴充目錄，可從 git / 本地安裝 |
| **Tier** | 任務成本等級（`smart` / `cheap`） |
| **Fork / Replay** | 從事件日誌任一點分叉新分支 / 重播 |
| **Swarm** | 一個 parent run 並行 fan-out 多個子代理 |
| **TRAE IDE** | 本專案 UI 對齊的視覺與空間佈局基準 IDE |

---

*本 PRD 以現有程式碼與專案文件（`hivewire/PRD.md`、`hivewire/README.md`、`hivewire/ui/src/App.tsx`）為事實基礎撰寫；UI/UX 規範對齊 TRAE IDE 截圖所示之空間佈局、密度、深色配色。*
