# Skill / Rules 撰寫規則指南

> 整理自各平台官方文件，涵蓋 Claude Code、AGY (Antigravity)、OpenAI Codex、OpenCode 四個 AI Coding Agent 平台的 skill / rules 撰寫規範。

---

## 目錄

1. [Claude Code — `CLAUDE.md` & Skills](#1-claude-code--claudemd--skills)
2. [AGY (Antigravity) — `SKILL.md` & Rules](#2-agy-antigravity--skillmd--rules)
3. [OpenAI Codex — `AGENTS.md`](#3-openai-codex--agentsmd)
4. [OpenCode — `SKILL.md` & Rules](#4-opencode--skillmd--rules)
5. [跨平台比較表](#5-跨平台比較表)

---

## 1. Claude Code — `CLAUDE.md` & Skills

**官方文件**：https://docs.anthropic.com/en/docs/claude-code/memory

### 核心概念

Claude Code 的持久記憶機制有兩個互補系統：

| 機制 | 誰撰寫 | 用途 |
|---|---|---|
| `CLAUDE.md` | 開發者 | 持久指令與規則 |
| Auto Memory | Claude 自動寫入 | 跨 session 的學習與偏好 |

兩者都在每次對話開始時載入。Claude 將其視為「context」而非強制配置，**指令愈具體、愈簡潔，遵從率愈高**。

---

### 1.1 `CLAUDE.md` 撰寫規則

#### 放置位置（依 scope 由廣到窄）

| Scope | 路徑 | 說明 |
|---|---|---|
| **Managed Policy**（組織全局） | macOS: `/Library/Application Support/ClaudeCode/CLAUDE.md`<br>Linux: `/etc/claude-code/CLAUDE.md`<br>Windows: `C:\Program Files\ClaudeCode\CLAUDE.md` | IT/DevOps 管理，不可被個人設定覆蓋 |
| **User**（個人全局） | `~/.claude/CLAUDE.md` | 跨所有專案的個人偏好 |
| **Project**（專案共享） | `./CLAUDE.md` 或 `./.claude/CLAUDE.md` | 透過版控與團隊共享 |
| **Local**（個人專案） | `./CLAUDE.local.md` | 個人專用，加入 `.gitignore` |

Claude Code 載入當前目錄及其所有**上層目錄**的 `CLAUDE.md`，子目錄的 `CLAUDE.md` 則在 Claude 讀取該目錄中的檔案時才按需載入。

#### 何時該新增內容

在以下情況時新增至 `CLAUDE.md`：
- Claude 重複犯同一個錯誤
- Code review 發現 Claude 本應知道的 codebase 規範
- 你在 chat 中重複輸入相同的糾正或說明
- 新隊員也需要相同 context 才能順利工作

**不應放入**的內容：多步驟流程（改用 Skills）、只針對 codebase 某一部分的指令（改用 Path-scoped rules）。

#### 有效撰寫原則

1. **Size（大小）**：每個 `CLAUDE.md` 目標 **< 200 行**。超過會降低遵從率。Claude Code 跳過大於 4 MiB 的檔案。
2. **Structure（結構）**：使用 Markdown headers 和 bullets 分組相關指令。避免大段落文字。
3. **Specificity（具體性）**：
   - ✅ `"Use 2-space indentation"`
   - ❌ `"Format code properly"`
   - ✅ `"Run 'npm test' before committing"`
   - ❌ `"Test your changes"`
4. **Consistency（一致性）**：避免不同 `CLAUDE.md` 之間的矛盾指令。定期審查。

#### 檔案 Import 語法

```markdown
<!-- 在 CLAUDE.md 中 -->
See @README for project overview and @package.json for available npm commands.

# Additional Instructions
- git workflow @docs/git-instructions.md
```

- 支援相對路徑與絕對路徑
- 遞迴 import 最多 4 層
- 用 backtick 包住路徑可防止 import（如 `` `@README` ``）

---

### 1.2 Path-Scoped Rules（`.claude/rules/` 目錄）

對於任務專用或路徑限定的規則，使用 `.claude/rules/` 而非放在主 `CLAUDE.md`。

#### 目錄結構

```text
your-project/
├── .claude/
│   ├── CLAUDE.md              # 主專案指令
│   └── rules/
│       ├── code-style.md      # 程式碼風格
│       ├── testing.md         # 測試規範
│       └── security.md        # 安全要求
```

#### Path-Specific Rules 格式

使用 YAML frontmatter 限定規則只在 Claude 處理特定檔案時載入：

```markdown
---
paths:
  - "src/api/**/*.ts"
  - "src/**/*.{ts,tsx}"
---

# API Development Rules

- All API endpoints must include input validation
- Use the standard error response format
```

| 模式 | 匹配 |
|---|---|
| `**/*.ts` | 任何目錄下的 TypeScript 檔案 |
| `src/**/*` | `src/` 下的所有檔案 |
| `*.md` | 根目錄的 Markdown 檔案 |
| `src/components/*.tsx` | 特定目錄的 React components |

#### 與其他平台的相容

Claude Code 讀取 `CLAUDE.md` 而非 `AGENTS.md`。若 repo 中已有 `AGENTS.md`，建議：

```markdown
<!-- CLAUDE.md -->
@AGENTS.md

## Claude Code 專用指令
Use plan mode for changes under `src/billing/`.
```

---

## 2. AGY (Antigravity) — `SKILL.md` & Rules

**官方文件**：內建 `agy-customizations` skill（`~/.gemini/antigravity-cli/builtin/skills/agy-customizations/`）

### 核心概念

Antigravity 使用 **Progressive Disclosure（漸進揭露）** 機制：

- **Skills**：預設不載入 context，只注入名稱與 description。**僅在 model 或 user 明確啟用時**才載入全文。
- **Rules**：`always_on` 的規則無條件載入；`trigger: model_decision` 的規則只注入名稱+描述。

所有 customization 以 **resolved file path** 為基礎去重，不會重複注入。

---

### 2.1 Skill 撰寫規則

#### 目錄結構

```text
.agents/skills/<skill-name>/
├── SKILL.md      # 必要：含 YAML frontmatter 的主指令檔
├── scripts/      # 選用：Helper 腳本
├── examples/     # 選用：參考實作
├── resources/    # 選用：素材或模板
└── references/   # 選用：詳細文件（按需讀取，省 token）
```

#### `SKILL.md` 格式

```markdown
---
name: my-specialized-skill
description: >-
  Describe when the agent should use this skill. Use third-person.
  Example: "Use this skill when the user asks to run integration tests for the XYZ service."
---

# My Specialized Skill

Provide clear, step-by-step instructions for the agent here.

## Steps

1. Run the preparation script:
   [prepare.sh](./scripts/prepare.sh)
2. Execute the test command:
   `npm test`
3. Analyze the results in the log file.
```

#### Frontmatter 欄位

| 欄位 | 必要 | 說明 |
|---|---|---|
| `name` | ✅ | 全小寫、hyphen 分隔的唯一識別名稱 |
| `description` | ✅ | **最關鍵欄位**。Agent 依此決定是否啟用 skill。應清楚說明「做什麼」和「何時使用」 |

#### 最佳實踐

1. **漸進揭露**：主 `SKILL.md` 保持簡潔，大量文件放在 `references/`，按需連結。
2. **Executable Helpers**：複雜指令封裝在 `scripts/` 中，以相對路徑連結。
3. **Validation Steps**：包含如何驗證步驟成功的指令（如：檢查 log、執行 dry-run）。
4. **No Duplication**：不要重複說明 agent 本已知道的一般規範，聚焦在工作流程的獨特部分。

---

### 2.2 Rules（`GEMINI.md` / `AGENTS.md`）

#### 位置與優先順序（高到低）

1. **Workspace Project**：從 CWD 向上遍歷到 repo root 的階層式發現
2. **Declared Configurations**：`skills.json` 或 `plugins.json` 中明確列出的
3. **Global Discovery**：`~/.gemini/config/`
4. **Built-in Customizations**：應用程式內建
5. **Global Declared Configurations**：全域 JSON 配置中明確列出的

#### 發現位置

| 類型 | 路徑 |
|---|---|
| Workspace（專案共享） | `.agents/`（或 `.agent/`, `_agents/`, `_agent/`）根目錄 |
| Directory Rules | `GEMINI.md`, `AGENTS.md`, `.agents/rules/*.md` |
| Global（機器本地） | `~/.gemini/config/` |

#### 格式規則

- 以 Markdown 撰寫
- 獨立的 `GEMINI.md` / `AGENTS.md` **不支援** frontmatter，永遠對所在目錄生效
- 自動去重：即使透過多個路徑發現，每個規則只套用一次

---

## 3. OpenAI Codex — `AGENTS.md`

**官方文件**：https://github.com/openai/codex

### 核心概念

Codex CLI 是 OpenAI 的輕量終端機 coding agent。它採用 `AGENTS.md` 作為指令文件（此名稱已成為跨平台事實標準）。

### 3.1 `AGENTS.md` 撰寫格式

```markdown
# Project Instructions

## Build Commands
- Build: `npm run build`
- Test: `npm test`
- Lint: `npm run lint`

## Code Style
- Use TypeScript for all new files
- Follow ESLint configuration
- Use 2-space indentation

## Architecture
- API handlers in `src/api/handlers/`
- Models in `src/models/`
- Utilities in `src/utils/`

## Workflow Rules
- Always run tests before committing
- Never push directly to main branch
- Create feature branches with format: `feature/<description>`
```

### 3.2 撰寫規則

1. **簡潔直接**：以清單格式呈現，避免冗長說明
2. **Build & Test 命令**：明確列出所有常用指令
3. **架構說明**：描述關鍵目錄結構和職責劃分
4. **工作流規範**：定義分支策略、commit 格式等團隊協作規則
5. **禁止事項**：明確列出 agent 不應執行的操作

### 3.3 `AGENTS.md` 的跨平台意義

`AGENTS.md` 已成為多個平台共同支援的配置格式：

| 平台 | 支援方式 |
|---|---|
| Claude Code | 透過 `@AGENTS.md` import 或 symlink |
| OpenCode | 直接讀取 |
| AGY | 支援作為 rules 文件 |
| Codex | 主要配置文件 |

> ⚠️ **注意**：Codex Web（cloud-based agent）與 Codex CLI（本地終端）是不同產品，各自的配置方式略有差異。

---

## 4. OpenCode — `SKILL.md` & Rules

**官方文件**：https://opencode.ai/docs/skills/ & https://opencode.ai/docs/rules/

### 核心概念

OpenCode 透過內建的 `skill` tool 按需載入 skills。Agent 可見所有可用 skill 的名稱與描述，並在需要時載入完整內容。

---

### 4.1 Skill 放置位置

```text
# 專案配置（推薦）
.opencode/skills/<name>/SKILL.md

# 全局配置
~/.config/opencode/skills/<name>/SKILL.md

# Claude 相容路徑
.claude/skills/<name>/SKILL.md
~/.claude/skills/<name>/SKILL.md

# Agent 相容路徑
.agents/skills/<name>/SKILL.md
~/.agents/skills/<name>/SKILL.md
```

**Discovery 機制**：從當前工作目錄向上遍歷到 git worktree，載入沿途所有匹配的 `skills/*/SKILL.md`。

---

### 4.2 `SKILL.md` 格式

每個 `SKILL.md` **必須**以 YAML frontmatter 開頭：

```markdown
---
name: my-skill-name
description: "Clear description of what this skill does and when to use it."
license: MIT                     # 選用
compatibility: opencode>=1.0.0   # 選用
metadata:                        # 選用，字串到字串的 map
  author: "Your Name"
  version: "1.0.0"
---

# Skill Title

Instructions for the agent go here...
```

---

### 4.3 Frontmatter 欄位規則

| 欄位 | 必要 | 說明 |
|---|---|---|
| `name` | ✅ | 1–64 字元，小寫字母+數字，hyphen 分隔 |
| `description` | ✅ | Agent 用於決定是否使用此 skill |
| `license` | ❌ | SPDX license 識別符 |
| `compatibility` | ❌ | 版本限制字串 |
| `metadata` | ❌ | 字串到字串的 map，任意 key-value |

**未知欄位會被忽略**（不會報錯）

---

### 4.4 `name` 命名規則

```text
^[a-z0-9]+(-[a-z0-9]+)*$
```

- **長度**：1–64 字元
- **字元**：小寫字母 + 數字，hyphen 作為分隔符
- **禁止**：以 `-` 開頭或結尾；不可連續 `--`
- **目錄名一致性**：`name` 必須與包含 `SKILL.md` 的**目錄名稱相同**

#### 命名範例

| ✅ 合法 | ❌ 非法 |
|---|---|
| `my-skill` | `-my-skill`（開頭 hyphen）|
| `deploy-to-aws` | `my--skill`（連續 hyphen）|
| `run-tests` | `MySkill`（大寫字母）|
| `skill1` | `my skill`（空格）|

---

### 4.5 Description 撰寫建議

Description 是 agent 決定是否啟動 skill 的核心依據：

- 明確說明「什麼時候」該使用此 skill
- 使用第三人稱
- 包含具體的觸發情境關鍵字

```yaml
# ✅ 好的 description
description: "Use this skill when deploying the application to AWS ECS. 
  Covers building Docker images, pushing to ECR, and updating ECS services."

# ❌ 差的 description
description: "Deployment stuff"
```

---

### 4.6 Rules（`RULES.md` / `AGENTS.md`）

OpenCode 的 rules 系統採用純 Markdown，配置路徑：

```text
# 專案規則
.opencode/rules.md
AGENTS.md              # 相容其他 agent 平台

# 全局規則
~/.config/opencode/rules.md
```

Rules 在每次對話都會載入。應包含：
- 編碼風格規範
- 測試要求
- 架構決策
- 工作流程限制

---

## 5. 跨平台比較表

### 5.1 Skill 撰寫對比

| 項目 | Claude Code | AGY | Codex | OpenCode |
|---|---|---|---|---|
| **主指令格式** | `CLAUDE.md` | `SKILL.md` | `AGENTS.md` | `SKILL.md` |
| **YAML Frontmatter** | 選用（path rules 用） | ✅ 必要 | ❌ 不使用 | ✅ 必要 |
| **Name 欄位** | N/A | 小寫 hyphen | N/A | 小寫 hyphen，1–64 字元 |
| **Description 欄位** | N/A | ✅ 必要，決定啟用時機 | N/A | ✅ 必要，決定啟用時機 |
| **按需載入** | ✅（Skills via rules dir）| ✅（漸進揭露）| ❌（每次全部載入）| ✅（skill tool）|
| **目錄結構** | `.claude/rules/` | `.agents/skills/<name>/` | 無固定結構 | `.opencode/skills/<name>/` |
| **全局配置** | `~/.claude/CLAUDE.md` | `~/.gemini/config/` | `~/.codex/` | `~/.config/opencode/skills/` |

### 5.2 Rules / Instructions 對比

| 項目 | Claude Code | AGY | Codex | OpenCode |
|---|---|---|---|---|
| **主配置檔** | `CLAUDE.md` / `CLAUDE.local.md` | `GEMINI.md` / `AGENTS.md` | `AGENTS.md` | `AGENTS.md` / `rules.md` |
| **載入時機** | 每次 session 開始 | 每次對話 | 每次任務 | 每次對話 |
| **階層發現** | ✅ 向上至 repo root | ✅ 向上至 repo root | 依實作 | ✅ 向上至 git worktree |
| **Path Scoping** | ✅ YAML frontmatter paths | ❌ | ❌ | ❌ |
| **Import 語法** | `@path/to/file` | ❌ | ❌ | ❌ |
| **去重機制** | ✅ | ✅ | 依實作 | 依實作 |
| **大小建議** | < 200 行 / 4 MiB 上限 | 盡量簡潔 | 盡量簡潔 | 盡量簡潔 |

### 5.3 共通最佳實踐

無論使用哪個平台，以下原則普遍適用：

1. **具體勝於模糊**：寫可驗證的指令，而非抽象建議
2. **簡潔勝於冗長**：過長的指令文件降低遵從率
3. **避免重複**：不要說明 agent 本已知道的事
4. **結構化**：使用 headers、bullets、表格組織內容
5. **版控管理**：將共享規則加入版控，個人規則加入 `.gitignore`
6. **AGENTS.md 作為共通格式**：以 `AGENTS.md` 為核心，各平台透過 import/symlink 讀取，避免重複維護

---

## 附錄：常見模板

### AGY / OpenCode 通用 SKILL.md 模板

```markdown
---
name: skill-name
description: >-
  Use this skill when [具體觸發情境].
  This skill covers [主要功能說明].
---

# Skill Title

Brief overview of what this skill does.

## Prerequisites

- Requirement 1
- Requirement 2

## Steps

1. **Step 1**: Description
   ```bash
   command-to-run
   ```

2. **Step 2**: Description

3. **Verify**: How to confirm success
   ```bash
   verification-command
   ```

## Notes

- Important caveat 1
- Important caveat 2
```

### Claude Code `CLAUDE.md` 模板

```markdown
<!-- maintainer notes: last updated YYYY-MM -->

## Build & Test
- Build: `npm run build`
- Test: `npm test`
- Lint: `npm run lint`

## Code Style
- Use 2-space indentation
- TypeScript for all new files
- ESLint + Prettier configured in repo root

## Architecture
- API handlers: `src/api/handlers/`
- Models: `src/models/`
- Tests: `tests/` (mirrors src/ structure)

## Workflow
- Run `npm test` before every commit
- Branch naming: `feature/<description>` or `fix/<issue-number>`
- PR title format: `[type] brief description`
```

### 跨平台通用 `AGENTS.md` 模板

```markdown
# Project Guidelines

## Commands
- Build: `<build command>`
- Test: `<test command>`
- Lint: `<lint command>`

## Code Style
- Language: <language>
- Indentation: <spaces>
- Key conventions: ...

## Directory Structure
- `src/`: Source code
- `tests/`: Test files
- `docs/`: Documentation

## Git Workflow
- Branch format: `<type>/<description>`
- Never commit directly to main
- Run tests before every commit

## Important Rules
- <rule 1>
- <rule 2>
```

---

*文件來源*：
- Claude Code Docs: https://docs.anthropic.com/en/docs/claude-code/memory
- AGY Customizations: built-in `agy-customizations` skill
- OpenAI Codex: https://github.com/openai/codex
- OpenCode: https://opencode.ai/docs/skills/ & https://opencode.ai/docs/rules/
