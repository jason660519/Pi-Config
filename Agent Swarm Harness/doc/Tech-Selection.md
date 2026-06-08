# Hivewire 技術選型方案

本文件整理 Hivewire 的技術棧現狀與未來建議，並針對「**協議層解耦、可觀測 / 可續傳 / 可版本化、可擴充與沙箱、與 TRAE IDE 一致的 UI 排版與空間邏輯**」的產品目標，給出選型依據、兼容性、可維護性、可擴展性結論。

| 欄位 | 內容 |
|---|---|
| 文件版本 | 2.1 |
| 對齊文件 | `doc/PRD.md` v2.1、`doc/Architecture.md` v2.1 |
| 對齊實作 | `hivewire/pyproject.toml`、`hivewire/ui/package.json` |
| 最後更新 | 2026-06-08 |

---

## 1. 選型原則（Selection Principles）

| # | 原則 | 含義 |
|---|---|---|
| **SP-1** | 協議優先 | UI / Editor / CLI 透過穩定協議層接入，避免對 runtime 的直接依賴 |
| **SP-2** | 可觀測 / 可回放 | 所有核心狀態變化以事件落盤並可重播 |
| **SP-3** | 快速迭代 | 本地開發與熱更新效率優先（含擴充） |
| **SP-4** | 供應商無關 | 模型供應商切換成本極低，且支援本地模型 |
| **SP-5** | 安全邊界清晰 | 擴充能力（capability）為策略邊界；沙箱為執行隔離邊界 |
| **SP-6** | UI 與 TRAE IDE 對齊 | 技術棧必須能穩定實現「左 Explorer + 主 Workspace + 右 Inspector + 底 Panel」+ 深色系密集排版 |
| **SP-7** | 離線可跑 | 無 API key、無外部依賴即可端到端跑通 |
| **SP-8** | 偏好已驗證的小棧 | 不為「未來可能性」引入未驗證大依賴 |

---

## 2. 現狀技術棧（As-Is）

### 2.1 後端（Python）— `hivewire/pyproject.toml`

| 類別 | 選擇 | 版本要求 | 角色 |
|---|---|---|---|
| 語言執行環境 | Python | ≥ 3.11 | 充分利用 `asyncio` / `TaskGroup` |
| Web 框架 | **FastAPI** | latest | 協議閘道（HTTP + SSE） |
| ASGI server | **uvicorn[standard]** | latest | 高性能 ASGI 執行 |
| 串流 | **sse-starlette** | latest | 標準 SSE 實作 |
| 資料模型 | **pydantic v2** | latest | AG-UI 事件 schema 驗證 |
| 文件監控 | **watchdog** | latest | extensions 熱重載 |
| HTTP 客戶端 | **httpx** | latest | LiteLLM proxy / provider 呼叫 |
| LLM 介面 | **litellm** | 可選 | provider 抽象；無配置時 mock |
| 依賴管理 / 運行 | **uv** | latest | `uv sync` / `uv run` |
| 沙箱（可選） | **Docker** | — | per-extension 容器隔離 |

### 2.2 前端（Web UI Host）— `hivewire/ui/package.json`

| 類別 | 選擇 | 版本 | 角色 |
|---|---|---|---|
| UI 框架 | **React** | ^18.3.1 | 組件化 + Hooks |
| 語言 | **TypeScript** | ^5.6.3 | 事件型別、狀態約束 |
| 構建工具 | **Vite** | ^6.0.3 | 開發 server + production build |
| 插件 | **@vitejs/plugin-react** | ^4.3.4 | React 支援 |
| E2E 測試 | **Playwright** | ^1.60.0 | UI 端到端驗證 |
| 樣式方案 | **Inline style objects**（由 theme token 推導） | — | 零依賴、最小耦合 |
| 套件管理 | **npm** | — | 與全域偏好一致（不用 yarn / pnpm） |

### 2.3 部署 / 運維 — `hivestack/`

| 類別 | 選擇 | 角色 |
|---|---|---|
| 腳本 | Shell（zsh / bash） | `setup`、`bin/*`、`commands/*` |
| 角色定義 | YAML / Markdown | `roles/*` |
| 容器編排 | Docker / docker-compose | LiteLLM、可選擴充沙箱 |

---

## 3. 技術選型依據（Why These Choices）

### 3.1 FastAPI + sse-starlette + uvicorn（協議閘道）

**選型理由**
- **適合協議型服務**：以 HTTP + SSE 對外暴露簡潔、可擴展的協議端點，符合 AG-UI 規範。
- **長連線串流**：SSE 對應 AG-UI 的事件串流需求；瀏覽器原生 `EventSource` 支援良好。
- **生態成熟**：pydantic v2 schema 驗證 + httpx 客戶端 + 標準依賴注入，便於擴充認證 / 限流 / 觀測。
- **與 Python 並發模型契合**：`asyncio` 原生支援 swarm fan-out。

**兼容性**
- 現代瀏覽器全面支援 SSE；反向代理（nginx / Caddy）需注意關閉 buffering 與調整超時。
- 若未來需要雙向低延遲 / 二進制傳輸，可加 WebSocket 端點（不替換 SSE）。

**可維護性**
- pydantic v2 對事件 schema 提供型別與序列化保證，AG-UI 升版可由 schema 驅動。

**可擴展性**
- FastAPI middleware 可橫向擴展認證、限流、tracing；uvicorn 可橫向多 worker / 容器化。

**風險與緩解**
- 風險：SSE 在某些代理環境下會被緩衝。
- 緩解：文件中明示 reverse proxy 配置；提供 `?from_seq=` 容錯重連。

### 3.2 JSONL Append-only Store（事件存儲）

**選型理由**
- **極簡 / 可移植 / 可審計**：純文本 append-only，天然可 diff、可備份、易排查。
- **與產品原語一致**：順序事件 + seq 提供重播 / 續傳 / 分叉基礎，**等於核心架構原語**。
- **離線友好**：不用部署 DB 也能端到端跑通。

**兼容性**
- POSIX 檔案系統即可運作；雲端持久卷（PV）相容。

**可維護性**
- 落盤檔案可被任意工具（`cat`、`jq`、`tail -f`）審查與除錯。

**可擴展性**
- 早期 / 中小規模直接使用；若 session 數量大量增長，引入**可插拔後端**（SQLite / 對象存儲 / log service）+ retention policy（roadmap R2）。
- 抽象介面建議：`EventStore.append() / read(from_seq) / fork(sid, seq) / tree()`。

**風險與緩解**
- 風險：大 session 的隨機讀取效能不佳。
- 緩解：以順序讀為主（replay / live tail）；後續加索引或切換到 SQLite。

### 3.3 LiteLLM（模型路由）

**選型理由**
- **Provider-agnostic**：屏蔽 Anthropic / OpenAI / Gemini / Ollama / llama.cpp / vLLM 差異，統一 OpenAI-format。
- **承接 tier / 成本策略**：可在 proxy 層做路由、統計、負載均衡。
- **本地模型支援路徑清晰**。

**兼容性**
- 既可作為 Python 依賴內嵌呼叫，也可作為 docker compose 啟動的 proxy。
- 保留 **mock fallback**：無配置時離線可跑（已實作）。

**可維護性**
- 模型升版 / 切換為配置變更，零代碼改動。

**可擴展性**
- 後續可接入企業 LLM gateway / 私有 proxy；OTEL 觀測（roadmap R4）。

**風險與緩解**
- 風險：上游 API / 行為變動。
- 緩解：runtime 對 LiteLLM 為**可選依賴**；版本釘選；mock fallback。

### 3.4 React + TypeScript + Vite（UI Host）

**選型理由**
- **迭代效率高**：Vite HMR 對「Hivewire 自身的擴充熱重載 + UI 即時 reflect」是天然配對。
- **IDE-like 佈局可控**：React 組件化可穩定實現 sidebar / main / inspector / panel 四分區（對齊 TRAE IDE）。
- **TypeScript 對協議契約友善**：AG-UI 事件 type、`AGEvent` discriminated union 可由 schema 推導。

**兼容性**
- 現代瀏覽器全面支援；ESM build；無 IE 包袱。

**與 TRAE IDE UI 對齊能力（關鍵）**
- React 提供「**容器組件 + flex/grid layout primitives**」，可直接映射 TRAE 四區域。
- TypeScript 約束 UI 狀態，避免 ID / seq / runId 混排錯位（搭配等寬字體規範）。
- 樣式系統（無論 inline / CSS Var / CSS Modules）均能承載 PRD §8 的 token 規範。

**可維護性**
- TS + 組件樹清晰；目前 `App.tsx` 即承載全部主視圖，後續可平滑拆分（Header / Sidebar / Log / Composer / Inspector）。

**可擴展性**
- 後續可加入：
  - 狀態管理（見 §5.3）
  - Headless 組件庫（Dialog / Popover / Menu）— 用於 Inspector / Settings
  - 國際化 / 主題系統升級

**風險與緩解**
- 風險：inline style 規模化後可讀性下降。
- 緩解：分階段引入 CSS Variables → CSS Modules（見 §5.1）。

### 3.5 watchdog + Capability allow-list + Sandbox（擴充系統）

**選型理由**
- **watchdog** 提供跨平台文件監控，是熱重載基礎。
- **Capability allow-list** 與 **Sandbox** 分開：策略 vs. 執行隔離，降低耦合。
- **subprocess + Docker 雙模式**：開發階段輕量、生產階段可硬化。

**安全評估**
- 目前非完整 syscall 沙箱；不可信擴充建議整 host 容器化（seccomp / AppArmor，roadmap R1）。
- Capability 預設**空集合**（默認拒絕），符合 secure-by-default。

### 3.6 ACP / MCP（整合協議）

**選型理由**
- **ACP**：覆蓋 Editor 客戶端（Zed / JetBrains / Neovim），複用同一 runtime。
- **MCP**：包裝任意 MCP server 成 Hivewire 工具，接入既有生態。

**兼容性**
- 都是 JSON-RPC / SSE 標準；對 stdio / HTTP 雙協議友好。

### 3.7 uv（Python 依賴管理）

**選型理由**
- 與全域偏好一致（**不用 pip / poetry / conda**）。
- 速度快、lock 機制可靠、與 PEP 517 / 621 相容。

### 3.8 npm（Node 依賴管理）

**選型理由**
- 與全域偏好一致（**不用 yarn / pnpm**）。
- Vite + React 生態與 npm 完全相容；`package-lock.json` 已存在。

---

## 4. 技術選型如何支撐「TRAE IDE 一致 UI 排版」（重點驗證）

### 4.1 關鍵能力映射

| TRAE IDE 規範要求 | 對應技術支撐 | 驗證 |
|---|---|---|
| **四分區佈局**（左 Explorer / 主 Workspace / 右 Inspector / 底 Panel） | React 組件化 + CSS flex / grid（`display: flex` + `flex-direction`） | ✅ 已實作 Header + Sidebar + Main（Inspector / Panel 為 planned） |
| **深色 IDE 配色 / 語義 token** | CSS Custom Properties（CSS Variables）+ Theme extension 注入 | ✅ 已有 `DEFAULT_THEME` + theme picker |
| **高資訊密度 / 等寬 ID** | `font-family: ui-monospace, monospace` for meta；Body 14px / Meta 12px | ✅ `App.tsx` 中 `node`、`muted`、`run` 已用等寬 |
| **左側 Tree 縮進與層級** | React 遞迴渲染 + `paddingLeft: depth * 14` | ✅ `renderNodes()` 已實作 |
| **鍵盤一致性**（Enter / Shift+Enter / Alt+Enter / Esc / Cmd+K） | React `onKeyDown` + 全域 keymap | ✅ Composer 已實作三鍵；Esc / Cmd+K 規劃中 |
| **可插拔主題** | theme extension → token 覆蓋 → React state → 即時生效 | ✅ `themes[activeTheme]` 已落地 |
| **Toast / Focus ring / 對比度** | inline style + `outline` + WCAG AA token | ✅ Toast 已實作；focus ring 規劃中 |
| **bubble 寬度限制 / role 分軌** | CSS `max-width: min(720px, 80%)` + `border-left: 3px` for sub-agent | ✅ 已實作 |
| **Composer 自適應高度** | `<textarea>` + `min-h: 24px; max-h: 160px` | ✅ 已實作 |

### 4.2 結論
**現有技術棧（React + TypeScript + Vite + inline-style-with-tokens）已足以實現 TRAE IDE 一致的排版規範**；無需立即引入新依賴。建議按 §5.1 路線分階段強化樣式系統。

---

## 5. 面向需求的 To-Be 選型建議（Evolution）

以下建議以「**不破壞當前最小可用**」為前提，按需求增長逐步引入。

### 5.1 樣式與設計系統（落地 TRAE IDE 對齊）

**目標**：可穩定實現 PRD §8 規範，並支援 theme extension 覆蓋。

| 方案 | 內容 | 優點 | 風險 | 推薦時機 |
|---|---|---|---|---|
| **A. 保留 inline + 集中 CSS Variables** | 將 `DEFAULT_THEME` 升級為 CSS Variables，在 `:root` 注入 | 最少依賴；快速統一規範 | 大規模樣式可讀性 | **近期推薦** |
| **B. CSS Modules + Variables** | 樣式與組件邊界清晰 | 長期維護友好 | 需重構部分 inline | 進入 Inspector / Settings 階段 |
| **C. 型別化 CSS-in-TS**（vanilla-extract 類） | token 與樣式型別約束 | 適合大規模 design system | 引入新工具鏈 | 設計系統正式化後 |

**落地標準（必須）**
- 所有顏色源於語義 token（`--bg / --panel / --sidebar / --text / --muted / --accent / --success / --warning / --danger`）。
- 所有間距源於 spacing scale（**4 / 8 / 12 / 16 / 24**）。
- 所有字級源於 type scale（**11 / 12 / 13 / 14 / 15 / 16 / 20**），ID / 序號使用等寬。
- 圓角源於 radius scale（**6 / 8 / 10 / 12**）。

### 5.2 UI 組件庫（可選）

**目標**：提高可訪問性、鍵盤導航、一致交互（對齊 IDE 習慣），降低自造輪子成本。

**建議方向**
- 優先採用 **Headless 組件**（只提供交互，不強制樣式）：
  - 候選：Radix UI / Headless UI / Ariakit
- 引入領域：Menu / Popover / Dialog / Tooltip / Focus management。

**風險與緩解**
- 風險：組件庫可能帶入全局 CSS 或 DOM 結構約束。
- 緩解：選 **Headless**；不引入完整視覺系統（避免破壞 TRAE IDE 對齊）。

**推薦時機**：實作 Inspector / Settings / Extensions 視圖時引入。

### 5.3 狀態管理（State Management）

**現狀**：`useState` + `useEffect` + `useRef` 足以支撐單頁 + 中小規模狀態。

**何時引入更強方案（信號）**
- 需要跨多視圖共享狀態：session、filters、Inspector selection、cost metrics。
- 需要可回放 / 可追蹤的 UI 狀態（與 event log 對齊）。

| 方案 | 描述 | 適用 |
|---|---|---|
| **A. Hooks + Custom Hooks** | 維持現狀，抽 `useSession()`、`useEventStream()` | 近期推薦 |
| **B. Zustand（輕量 store）** | 小巧、無 boilerplate、TS 友好 | Inspector + 多視圖共享時 |
| **C. 狀態機 / 事件驅動**（XState） | 嚴格模式、可視化、易測 | IDE 級複雜度時 |

**選型要求**
- 必須支援與事件流模型對接（按 seq 增量更新，避免全量重算）。
- 必須易於單元測試。

### 5.4 構建與品質（Build & Quality）

| 領域 | 現況 | 建議補齊 |
|---|---|---|
| 前端 lint / format | 未強制 | Prettier + ESLint（保守規則） |
| 後端 lint / format | 未強制 | Ruff + black（或單一 Ruff） |
| 型別檢查 | TS 已啟用 / mypy 未啟用 | 加 mypy strict-optional |
| E2E | Playwright | 加 fork / theme / extension reload 場景 |
| API 合約 | AG-UI 事件 schema | 嚴格版本化策略（`protocol_version` 升級時 migration） |
| 觀測性 | 無 | OTEL metrics / tracing（roadmap R4） |

### 5.5 存儲後端可插拔（Pluggable Store）

**抽象介面建議**
```python
class EventStore(Protocol):
    def append(self, sid: str, event: dict) -> int: ...
    def read(self, sid: str, from_seq: int = 0) -> Iterator[dict]: ...
    def fork(self, sid: str, from_seq: int) -> str: ...
    def tree(self) -> list[Node]: ...
```

**實作選項**
| 後端 | 優點 | 缺點 | 適用 |
|---|---|---|---|
| **JSONL**（現狀） | 極簡、可移植、易審計 | 大量 session 隨機讀效能 | 開發、中小規模 |
| **SQLite** | 索引、查詢、單檔 | 寫入吞吐有上限 | 中小規模、單機 |
| **S3-compatible 物件儲存** | 無限擴展、便宜 | 不適合高頻寫 / 隨機讀 | 歸檔層 |
| **PostgreSQL** | 索引、ACID、多用戶 | 部署成本 | 多租戶 / 企業 |

**Retention Policy 建議**
- 預設保留全部；提供 TTL / size cap / archive 策略（roadmap R2）。

### 5.6 沙箱硬化（Sandbox Hardening）

| 階段 | 內容 | 對應 |
|---|---|---|
| 現狀 | subprocess + secret 隔離；可選 Docker 容器 | FR-17 |
| 強化 | Docker 沙箱範本：seccomp profile + AppArmor + 無網路 + 唯讀 FS + CPU/RAM limits | R1 |
| 進階 | gVisor / Firecracker（如需更強隔離） | Later |

---

## 6. 兼容性 / 可維護性 / 可擴展性結論

### 6.1 兼容性（Compatibility）

| 維度 | 結論 |
|---|---|
| **瀏覽器** | Chrome / Safari / Firefox / Edge（現代版本）全面支援 SSE + ESM |
| **作業系統** | macOS / Linux / Windows（uv + Python ≥ 3.11） |
| **模型供應商** | LiteLLM 覆蓋主流商業與本地（Anthropic / OpenAI / Gemini / Ollama / llama.cpp / vLLM） |
| **客戶端協議** | AG-UI v3（Web UI）+ ACP（Editor）+ MCP（Tool） |
| **部署形態** | 本機 / Docker / k8s 均可（hivestack 提供 setup） |

### 6.2 可維護性（Maintainability）

| 維度 | 結論 |
|---|---|
| **層級解耦** | 四層架構（UI / Gateway / Runtime / Model Gateway）+ 擴充與核心分離 |
| **依賴最小化** | 前端 0 重型依賴；後端核心依賴可數 |
| **協議契約** | pydantic v2 + AG-UI schema + `protocol_version` |
| **可審計** | JSONL 事件可被任意工具讀取與 diff |
| **可測試** | Playwright（UI）+ smoke / verify scripts（backend） |
| **文件對齊** | PRD / Architecture / Tech-Selection 三件套 + 對齊 TRAE IDE 視覺 |

### 6.3 可擴展性（Scalability / Extensibility）

| 維度 | 結論 |
|---|---|
| **水平擴展** | Gateway 可多 worker / 多實例；Store 需可插拔後端（roadmap R2）以解除單檔瓶頸 |
| **功能擴展** | Extensions（tool / mcp / prompt / theme）為一級公民；ASS 包提供分發機制 |
| **生態擴展** | ACP / MCP 為標準協議，可接入既有 IDE 與工具生態 |
| **UI 擴展** | 四區域佈局已預留 Inspector / Bottom Panel；組件樹可平滑拆分 |
| **觀測性擴展** | OTEL 入口已留（roadmap R4） |

### 6.4 風險與緩解總覽

| 風險 | 等級 | 緩解 |
|---|---|---|
| JSONL 隨大量 session 變慢 | 中 | 抽象介面 + SQLite / 物件儲存可插拔（R2） |
| Inline style 規模化難維護 | 中 | 分階段升級到 CSS Variables → CSS Modules（§5.1） |
| LiteLLM 上游變動 | 中 | 版本釘選 + mock fallback + 抽象呼叫層 |
| 沙箱非完整隔離 | 高（若跑不可信擴充） | Capability 默認拒絕 + 整 host 容器化（R1） |
| AG-UI 規格演進 | 中 | `protocol_version` + migration 策略（R3） |
| UI 偏離 TRAE IDE 對齊 | 中 | Token 為單一事實 + 架構檢核點（C1–C8） |

---

## 7. 決策摘要（Decision Summary）

| 決策 | 選擇 | 替代方案 | 為什麼選這個 |
|---|---|---|---|
| 後端語言 | Python 3.11+ | Node / Go / Rust | 與 LiteLLM、watchdog、agent 生態最契合；asyncio 適合 swarm |
| Web 框架 | FastAPI | Flask / Starlette | 內建 pydantic、SSE 友善、生態成熟 |
| 事件存儲 | JSONL（append-only） | SQLite / Redis | 對齊「事件為核心原語」；極簡可審計；後續可換 |
| 模型路由 | LiteLLM | 自行抽象 / 直連 | 已有完整 provider 覆蓋；可作 lib / proxy 雙模 |
| 前端框架 | React | Vue / Svelte / Solid | 與 IDE-like 組件化思維契合；TS 生態完整 |
| 構建工具 | Vite | webpack / Next.js | 開發 HMR 快；無 SSR 需求；ESM |
| 樣式方案 | Inline + token（短期） / CSS Variables（中期） | Tailwind / styled-components | 對 TRAE IDE 對齊更可控；零外部視覺系統 |
| 狀態管理 | React Hooks | Redux / Zustand / XState | 當前規模充足；未來按信號引入 |
| 套件管理 | uv（Py）+ npm（Node） | poetry / pnpm | 與全域偏好一致；速度快、lock 可靠 |
| Sandbox | subprocess + Docker（可選） | gVisor / Firecracker | 對開發無摩擦；生產可硬化 |
| Editor 協議 | ACP | 自定義 | 標準化、覆蓋多 IDE |
| Tool 協議 | MCP | 自定義 | 標準化、生態大 |

---

## 8. 落地檢查清單（Adoption Checklist）

開發 / 評審 / PR review 時可逐項核對：

- [ ] 任何新依賴是否符合 §1 選型原則？
- [ ] 任何 UI 樣式是否來自 §5.1 的 token？（無硬編碼色 / 像素）
- [ ] 任何新 API 是否走 `/api/*`，且符合 AG-UI v3 / Hivewire CUSTOM 慣例？
- [ ] 任何 extension 是否宣告 capability 並通過 allow-list？
- [ ] 任何模型呼叫是否走 tier 抽象（`smart` / `cheap`），而非具體模型名？
- [ ] 任何破壞 PRD §8（UI 規範）的 PR 是否同步更新文件？
- [ ] 是否在離線環境（無 API key）可端到端跑通？
- [ ] 是否能由 `from_seq` 重連 SSE 並繼續工作？

---

*本技術選型文件以 `hivewire/pyproject.toml`、`hivewire/ui/package.json`、實際代碼為事實基礎；UI 對齊驗證以 PRD §8 與 TRAE IDE 截圖為基準。*
