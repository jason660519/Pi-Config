# hivestack Skills 使用指南（面向全體工程師）

本文件針對「Agent 角色對應的技能（commands / roles）」給出統一的存放規範、使用方式與維護機制，並以你提供的清單為主（`/office-hours`、`/plan-*-review`、`/review`、`/qa`、`/cso`、`/ship`、`/land-and-deploy`、`/investigate`、`/document-release`）。

## 1) 統一存放位置（符合現有倉庫規範）

本倉庫目前已採用「folder-per-skill」結構，且在技能文件中已明確以 `preferred-backends: [claude]` 為主要後端。因此，後續轉換為 Claude skill 時，建議以現行結構作為唯一真實來源（single source of truth），避免重複維護。

### 1.1 來源目錄（Source of Truth）

- **Commands（斜線命令）**：`hivestack/commands/<skill-slug>/SKILL.md`
- **Roles（人格/職能）**：`hivestack/roles/<role-slug>/SKILL.md`
- **Tools（可執行工具/依賴）**：`hivestack/tools/<tool-slug>/...`（含程式碼、依賴檔、可執行檔）
- **Docs（整體規範/架構）**：`hivestack/docs/`

對應現行 layout 定義可參考：[README.md](file:///Users/jasonmacbbookpro/Project/Agent%20Swam%20Harness/hivestack/README.md#L59-L68)

### 1.2 轉換為 Claude skill 的可擴展存放規劃

為了同時滿足「版本迭代、權限管理、依賴管理」需求，建議採用以下規則（不要求立即改動目錄；先作為團隊規範落地）：

- **版本迭代（SemVer）**
  - `SKILL.md` 內的 `version:` 使用語意化版本（例如 `1.2.0`）。
  - 同一技能的歷史版本以 Git 版本控制為主；若未來需要長期同時維護多個 major 版本，才引入子目錄：
    - `hivestack/commands/<skill>/versions/v1/SKILL.md`
    - `hivestack/commands/<skill>/versions/v2/SKILL.md`
- **權限管理（Ownership / Review Gate）**
  - 以「目錄邊界」作為權限與審核邊界：每個 squad 擁有對應子樹（例如 Security squad 擁有 `hivestack/roles/cso/`、`hivestack/commands/privacy-audit/`）。
  - 落地工具建議（擇一或併用）：CODEOWNERS / 分支保護規則 / 必要審核人數（此倉庫目前未提供 CODEOWNERS，先以流程規範為準）。
- **依賴管理（Dependencies）**
  - **技能本體（commands/roles）保持 Markdown-only**：只描述何時用、怎麼用、產出什麼，不直接引入 runtime 依賴。
  - **任何需要依賴或可執行能力的部分，一律下沉到 tools**（例如 `swarm-browse`、`swarm-bridge`），並在 command 的 `tools_invoked:` 明示。

### 1.3 SKILL.md 統一格式（強制）

每個 skill 都必須有 `SKILL.md`，並包含：

- YAML front matter（`name/kind/version/description/allowed-tools/triggers/preferred-backends/...`）
- `## When to invoke`（適用場景）
- `## Inputs`、`## Outputs`（輸入輸出規範）
- `## Preamble`（統一載入方式；讓 Claude/工具鏈在一致上下文中工作）

範例可參考：[office-hours/SKILL.md](file:///Users/jasonmacbbookpro/Project/Agent%20Swam%20Harness/hivestack/commands/office-hours/SKILL.md)

## 2) 使用指南（何時用、怎麼叫、吃什麼、吐什麼）

### 2.1 通用調用方式

- **斜線命令（commands）**：在 Claude Code 中直接輸入 `/skill-name ...`
- **角色（roles）**：通常由 commands 透過 `roles_invoked` 載入；若需要單獨使用，可在對話中明確要求「以 `<role>` 身份按其 SKILL.md 規範執行」，並附上 role 的檔案路徑

### 2.2 清單技能（以你提供的 Agent 角色為主）

以下整理「適用場景 / 觸發條件 / 輸入輸出 / 調用方式」，並附上來源檔案連結。

#### /office-hours（命令）

- 適用場景：產品想法/新方向評估，寫 PRD、寫 code 之前先做「六問」質詢
- 觸發條件：`office hours`、`should I build X`、`help me think through` 等
- 輸入：一句話 idea 或段落描述；可附競品/參考連結
- 輸出：一份 idea artifact（寫入 `~/.hivestack/projects/<slug>/ideas/...`）+ 一句 verdict
- 調用：`/office-hours`
- 來源：[office-hours/SKILL.md](file:///Users/jasonmacbbookpro/Project/Agent%20Swam%20Harness/hivestack/commands/office-hours/SKILL.md)

#### /plan-eng-review（命令）

- 適用場景：PRD/方案有架構或跨服務影響，需要產出 ADR、風險清單
- 觸發條件：`architecture review`、`plan eng review`、`is the architecture sound`
- 輸入：PRD/plan 路徑或貼上內容；可附 scale/SLO
- 輸出：ADR artifact（`~/.hivestack/projects/<slug>/decisions/...`）+ vote block + verdict
- 調用：`/plan-eng-review`
- 來源：[plan-eng-review/SKILL.md](file:///Users/jasonmacbbookpro/Project/Agent%20Swam%20Harness/hivestack/commands/plan-eng-review/SKILL.md)

#### /plan-design-review（命令）

- 適用場景：UI 方案/Mock/Figma/已建畫面需要設計與可用性（a11y）雙人 council sign-off
- 觸發條件：`design review this plan`、`is the design ready`
- 輸入：PRD（含 UI scope）或 mock URL/路徑
- 輸出：兩份 vote block + 綜合 verdict
- 調用：`/plan-design-review`
- 來源：[plan-design-review/SKILL.md](file:///Users/jasonmacbbookpro/Project/Agent%20Swam%20Harness/hivestack/commands/plan-design-review/SKILL.md)

#### /review（命令）

- 適用場景：實作完成後、出貨前的差異檢視（正確性、重用、簡化），避免「CI 能過但生產會炸」
- 觸發條件：`review this diff`、`any bugs in`
- 輸入：預設針對當前 diff；必要時可提供 base ref 或變更範圍描述（依該 SKILL.md）
- 輸出：具體問題清單 + 修正建議（通常含可直接套用的 patch 思路）
- 調用：`/review`
- 來源：[review/SKILL.md](file:///Users/jasonmacbbookpro/Project/Agent%20Swam%20Harness/hivestack/commands/review/SKILL.md)

#### /qa（命令）

- 適用場景：`/review` 後、`/ship` 前；以真實 Chromium 逐頁面走 golden path 與 edge cases
- 觸發條件：`qa this`、`smoke test this url`、`verify the deploy`
- 輸入：`<url>`；可選 `--feature <slug>`
- 輸出：QA report artifact + 截圖目錄（若 `swarm-browse` 可用）+ vote block
- 調用：`/qa <url>`
- 來源：[qa/SKILL.md](file:///Users/jasonmacbbookpro/Project/Agent%20Swam%20Harness/hivestack/commands/qa/SKILL.md)

#### /ship（命令）

- 適用場景：出貨 gate；彙總多方 sign-off 後才允許落地（通常依 charter 規則）
- 觸發條件：`ship this`、`ready to deploy`（依該 SKILL.md）
- 輸入：通常針對當前分支/變更；可選參數依 SKILL.md
- 輸出：是否允許出貨、阻擋項（must_fix）與建議（should_consider）
- 調用：`/ship`
- 來源：[ship/SKILL.md](file:///Users/jasonmacbbookpro/Project/Agent%20Swam%20Harness/hivestack/commands/ship/SKILL.md)

#### /land-and-deploy（命令）

- 適用場景：同步主分支 → 跑測試 → 開 PR → 部署（偏 DevOps/Release 流程）
- 觸發條件：`land and deploy`、`merge and deploy`（依該 SKILL.md）
- 輸入：目標分支/環境等（依 SKILL.md）
- 輸出：PR/部署結果、必要的命令與狀態摘要
- 調用：`/land-and-deploy`
- 來源：[land-and-deploy/SKILL.md](file:///Users/jasonmacbbookpro/Project/Agent%20Swam%20Harness/hivestack/commands/land-and-deploy/SKILL.md)

#### /cso（角色）

- 適用場景：安全審計（OWASP Top 10 + STRIDE）、secret 偵測、依賴風險、auth boundary
- 觸發條件：`security review`、`is this safe to ship` 等
- 輸入：當前 diff + repo context；必要時提供 base ref
- 輸出：可重現的 finding 清單（含 `how_to_repro`）+ vote block
- 調用方式（建議）：
  - 出貨前：由 `/ship` 流程要求 `cso` sign-off
  - 需單獨執行：在對話中要求「依 [cso/SKILL.md](file:///Users/jasonmacbbookpro/Project/Agent%20Swam%20Harness/hivestack/roles/cso/SKILL.md) 執行安全審計，輸出 vote block」
- 來源：[cso/SKILL.md](file:///Users/jasonmacbbookpro/Project/Agent%20Swam%20Harness/hivestack/roles/cso/SKILL.md)

#### /investigate（目前建議映射到 oncall-sre 角色）

目前倉庫內尚未有 `hivestack/commands/investigate/`，但 `oncall-sre` 角色已包含「investigate / postmortem」完整流程，可先視為 `/investigate` 的行為定義。

- 適用場景：線上事故/告警排查、root cause 分析、產出時間線與 action items
- 觸發條件：`investigate`、`prod is down`、`postmortem`
- 輸入：症狀、時間點、服務/環境、可取得的 logs/metrics/traces
- 輸出：Triage 5 lines、假設梯、時間線、初步 root cause、後續 action items（依 role 規範）
- 調用方式（建議）：以 `oncall-sre` 角色執行（見來源）
- 來源：[oncall-sre/SKILL.md](file:///Users/jasonmacbbookpro/Project/Agent%20Swam%20Harness/hivestack/roles/oncall-sre/SKILL.md)

#### /document-release（目前建議映射到 tech-writer 角色）

目前倉庫內尚未有 `hivestack/commands/document-release/`，但 `tech-writer` 角色已涵蓋 release notes / changelog / docs 分類方法，可先視為 `/document-release` 的行為定義。

- 適用場景：版本發佈說明、變更摘要、文件同步（把 docs 當 code）
- 觸發條件：`release notes`、`changelog`、`document this`
- 輸入：版本號、變更範圍（PR/commit/diff）、目標受眾
- 輸出：release-note 草稿或 docs 更新稿（依 role 模板）
- 調用方式（建議）：以 `tech-writer` 角色執行（見來源）
- 來源：[tech-writer/SKILL.md](file:///Users/jasonmacbbookpro/Project/Agent%20Swam%20Harness/hivestack/roles/tech-writer/SKILL.md)

#### /plan-ceo-review（命令；v0.7 已落地）

- 適用場景：`/spec` 後、`/plan-eng-review` 前；CEO + CFO 雙人 council 對「商業價值 + 燃燒率」做 sanity check
- 觸發條件：`ceo review this plan`、`is this worth funding`、`business review`
- 輸入：PRD 或 `/office-hours` idea 檔路徑
- 輸出：CEO + CFO 兩份 vote block；artifact 在 `decisions/ceo-review-<feature>-<ts>.md`
- 調用：`/plan-ceo-review`
- 來源：[plan-ceo-review/SKILL.md](../commands/plan-ceo-review/SKILL.md)

#### 其他 v0.7 已落地 commands（同事原文未涵蓋）

| Command | 角色 | 一句話 |
|---|---|---|
| `/spec <feature>` | pm | 把 `/office-hours` 通過的 idea 寫成 PRD（含 success metric + acceptance criteria） |
| `/retro` | learning-officer | 掃過去 N 天 artifacts → 抽 pattern → 寫回 swarm-brain |
| `/learn [<query>]` | (read-only) | 從 brain 撈相關 lesson 印出來；preamble 自動跑 same-skill filter |
| `/cost-report` | cfo | 從 swarm-guard 的 cost-ledger rollup（by session/day/skill） |
| `/pair "<prompt>"` | (router) | 同題雙投到兩個 backend，diff 後人選 |
| `/privacy-audit` | privacy-officer | PII / retention / log redaction / LLM prompt PII |
| `/compliance-check` | compliance-officer | license / SOC2 / vendor TOS scan |
| `/benchmark <target>` | perf-eng | SLO 為前提；無 SLO 拒絕跑 |
| `/canary <pct>` | devops + oncall-sre | 流量切到 `{1,5,10,25,50}` % 之一（hardcoded） |
| `/freeze` / `/unfreeze` | release-manager | 寫 / 解 repo-local `FREEZE` 鎖；`/ship` 會讀 |

#### 仍未落地（清單外的歷史名稱）

- `/design-consultation`：建議先用 `roles/designer`（諮詢）或 `/plan-design-review`（sign-off）
- `/qa-only`：v0.7 的 `/qa` 在 swarm-browse 為 stub 時會自動 fall back 到 matrix-only 模式，等於 alias
- `/investigate`：仍以 `roles/oncall-sre` 規範為主（line 130–139）
- `/document-release`：仍以 `roles/tech-writer` 規範為主（line 141–150）

## 3) 團隊同步說明（可直接當會議議程）

- 目標：全員知道「技能放哪裡、怎麼用、怎麼改不會壞」
- 建議議程（45–60 分）
  - Layout 與原則：commands / roles / tools 的責任邊界
  - Demo（3 條常見路徑）：
    - `/office-hours` → `/spec` → `/plan-eng-review`
    - `/review` → `/qa` → `/ship`
    - 安全/事故：`cso` 與 `oncall-sre`
  - 新增/調整 skill 的 PR 規範（見下一節維護機制）
  - Q&A + 收集痛點
- 回饋收集（建議）
  - 以 issue/PR 收集（標籤：`skills`），每條回饋固定欄位：場景、預期、實際、建議修改的 skill 檔案路徑

## 4) 後續維護機制（轉換為 Claude skill 過程的持續可用性）

- 變更流程（PR Checklist）
  - 任何改動 `hivestack/commands/**/SKILL.md` 或 `hivestack/roles/**/SKILL.md`：
    - 必須同步更新：適用場景（When to invoke）、Inputs/Outputs、triggers（如適用）
    - 若行為/輸出有實質改動：提升 `version:`
  - 任何新增「可執行能力/依賴」：
    - 必須新增到 `hivestack/tools/<tool>/`，由 command 透過 `tools_invoked` 或流程引用
- 相容性策略
  - 對外可見的命令名稱（`/xxx`）視為 API：避免隨意改名；若必須改名，保留舊名 alias（或在文檔標記 deprecate）至少一個 minor 版本週期
- 週期性盤點
  - 每月一次：抽樣 5 個常用 commands，檢查其 triggers/Inputs/Outputs 是否與真實用法一致
  - 每季一次：盤點 tools 依賴更新與安全掃描（由 Security/DevOps squad 主導）
