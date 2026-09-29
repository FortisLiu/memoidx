# AI agent memory systems：本機隱私評估

研究日期：2026-09-24。這是依 GitHub stars 作初篩、再以「記憶資料庫、索引與檢索可留在本機」作條件的 10 個候選；stars 只是受歡迎程度的代理值，數字會變動，不代表品質或安全性。Letta 特別說明：舊的 letta 專案累積了約 24.9k stars，但活躍實作已轉到 letta-code（約 3.4k）；本文按 Letta 系統／專案沿革列入，若只按目前活躍 repo stars 排名，ReMe（約 3.5k）會是接近的替代候選。

本次已將十個淺層 clone 放在本資料夾；不安裝套件、不跑它們、不連線到任何記憶服務。每個專案的說明是基於 clone 當下 README、文件、設定與主要程式路徑做的靜態研究。stars 取 2026-09-24 前後的 GitHub 頁面約值。

## 名單與本機化重點

| 順序 | 系統 | Stars 約值 | 儲存／本機化重點 | CJK 初判 |
|---|---|---:|---|---|
| 1 | [Mem0](https://github.com/mem0ai/mem0) | 65.9k | 自架向量庫及 metadata DB；關閉遙測、替換遠端 embedding | 依 embedding 模型 |
| 2 | [Graphiti](https://github.com/getzep/graphiti) | 31.1k | 本機 Neo4j／FalkorDB + 本機模型 | 依模型與 graph full-text 設定 |
| 3 | [Cognee](https://github.com/topoteretes/cognee) | 31.0k | SQLite、LanceDB、local model／GLiNER | 依模型；未確認專用 CJK tokenizer |
| 4 | [Supermemory](https://github.com/supermemoryai/supermemory) | 30.9k | Local binary、資料放本機；MCP 必須指向 localhost | 預設 embedding 偏英文 |
| 5 | [Hindsight](https://github.com/vectorize-io/hindsight) | 27.1k | 本機 PostgreSQL + pgvector；可用 Ollama 等本機模型 | 依 multilingual embedding／LLM |
| 6 | [Letta Code](https://github.com/letta-ai/letta-code) | 24.9k¹ | local backend、Git 管理的本機 MemFS | 文字可存 CJK；無專用分詞保證 |
| 7 | [Memori](https://github.com/MemoriLabs/Memori) | 16.9k | BYODB 用本機 SQLite 等；不要選 Cloud 整合 | 預設 all-MiniLM-L6-v2 偏英文 |
| 8 | [MemU](https://github.com/NevaMind-AI/memU) | 14.4k | Local mode + 本機 SQLite；embedding provider 要改成本機 | 依 embedding；未見專用 CJK tokenizer |
| 9 | [EverOS](https://github.com/EverMind-AI/EverOS) | 13.2k | Markdown 為主檔，SQLite + LanceDB 本機索引 | 明確依賴 jieba，中文支援較有把握 |
| 10 | [MemOS Local Plugin](https://github.com/MemTensor/MemOS) | 11.6k | 選 Local Plugin；本機 SQLite，不選 Cloud Plugin | 中文內容可用；檢索品質仍依模型與 FTS |

¹ Letta 的舊 repo stars 是系統沿革參考，不能和 letta-code 現行 repo stars 直接比較。

### 隱私邊界先看這裡

- 「本機儲存」不等於「整個 agent 對話不出網路」。若把記憶片段注入 Claude、Codex 或其他雲端 LLM 的 prompt，該文字會傳到該模型供應商。若只允許把記憶送去模型做整理，其他推理也要避免自動注入含記憶的雲端 prompt；改用本機 LLM，或先確認你接受這個傳輸。
- 遠端 embedding 服務也會收到待嵌入文字或查詢；查詢記憶時應用本機 embedding。SQLite、向量索引與 MCP/API server 請綁 localhost／本機磁碟，不要填雲端 DB、託管向量庫或官方 hosted MCP URL。
- 「本機模式」仍可能在首次啟動下載模型、套件或更新，也可能有遙測。先下載並檢查權重，再以網路防火牆允許清單封鎖非必要外連。已知需要明確關閉的遙測：Mem0 設 MEM0_TELEMETRY=false；Graphiti 設 GRAPHITI_TELEMETRY_ENABLED=false。
- 以下所說「LLM 可選／可遠端」代表可以指定使用者核准的 Claude、Codex 或其他 LLM API；需在設定中確認資料只送往所選模型 endpoint。要做到嚴格離線，可選本機 Ollama、llama.cpp、vLLM 等相容 endpoint。

---

## 1. Mem0

原始碼：[open-source/mem0](./mem0/README.md) · [官方 repo](https://github.com/mem0ai/mem0) · [Cursor plugin](./mem0/integrations/cursor-plugin/hooks/hooks.json)

1. **一句話定位：** 將對話切成可獨立管理、以向量檢索的長期記憶，並用 SDK 或 Cursor plugin 接到 agent。
2. **怎麼存：** ADD-only 流程由 LLM 從新訊息抽出候選記憶，向量與 metadata 寫入自選 vector store；OSS 預設常見組合是 Qdrant 與 SQLite metadata。改用本機 embedding 與本機 Qdrant／SQLite。
3. **怎麼取：** 以 query embedding 做語意相似度搜尋，附 user／agent／run 等範圍過濾；設定可加入 rerank／關聯訊息。
4. **記憶衝突：** 目前 README 的 ADD-only 路徑不做 UPDATE/DELETE；遇到「住台北」和「搬到台中」可同時留下，需人工刪改或在上層整理，不能假設自動判新覆舊。
5. **有自動化嗎：** SDK 由應用呼叫 add/search；Cursor plugin 有本機 hook、自動回想、工具紀錄與結束／壓縮前 flush。
6. **有哪些 hook（高維步驟）：** Cursor 的 sessionStart＝辨識 session 並初始化；beforeSubmitPrompt＝prompt 進模型前找相關記憶；postToolUse／postToolUseFailure＝保存工具結果或錯誤；afterAgentResponse／stop＝保存 assistant 完成內容；preCompact／sessionEnd＝整理並 flush 累積資料。這組生命週期整合是 Cursor plugin 的能力，不是每種 host 的 Mem0 SDK 都自帶。
7. **強項與限制：** API 簡單、store adapter 多、agent 生態完整；ADD-only 易累積重複或矛盾資料，效果高度依賴抽取模型、embedding 與召回參數。
8. **哪些步驟有 LLM：** 新訊息抽記憶需要 LLM；向量生成若用 OpenAI 預設會外傳，改成本機模型；純向量檢索通常不需生成式 LLM。
9. **CJK：** 儲存 UTF-8 沒問題；沒有看到通用 CJK 分詞保證。選本機多語 embedding，中文 query 和記憶以實際資料驗收。
10. **Dependency：** Python 3.10+；pydantic、openai client、qdrant-client、SQLAlchemy、PostHog 等；vector-stores、Ollama、sentence-transformers 等是選配。
11. **其他評估：** 遙測預設啟用，設 MEM0_TELEMETRY=false；不同整合可能有不同儲存與傳輸路徑，Cursor plugin 是 Python/SQLite 的獨立實作，需分開審查。

## 2. Graphiti

原始碼：[open-source/graphiti](./graphiti/README.md) · [官方 repo](https://github.com/getzep/graphiti) · [Graphiti 文件](https://help.getzep.com/graphiti/graphiti/overview)

1. **一句話定位：** 把對話與事件建成帶有效時間的知識圖譜，適合查「何時、誰、什麼改變」。
2. **怎麼存：** add_episode 將文字或訊息解析成 entity、edge 與時間欄位寫入圖資料庫；使用本機 Neo4j 或 FalkorDB，向量也留在本機。
3. **怎麼取：** 混合圖遍歷、向量語意與關鍵字／全文搜尋；依 entity、時間與關係範圍過濾。
4. **記憶衝突：** 新關係會判斷是否與現存 edge 矛盾，將舊 edge 設成失效時間、保留歷史，再寫新有效關係；這是 temporal supersession，不是刪除舊事實。
5. **有自動化嗎：** 本身是 library/API/MCP 記憶後端；應用在對話寫入或任務前查詢。通用 agent lifecycle hook 要由 host adapter 接。
6. **有哪些 hook（高維步驟）：** 沒有一套跨 host 的原生生命週期 hook。應用需接「對話／事件完成→add_episode」與「規劃／作答前→search」，各自指向本機服務。
7. **強項與限制：** 時間線、關係和事實沿革表達力強；要維護 graph DB、embedding 與 LLM 抽取，部署與 schema 選擇比純檔案系統複雜。
8. **哪些步驟有 LLM：** episode 抽實體／關係、去重與矛盾判斷需要 LLM；search 的排序可走本機向量與圖資料庫，避免把 query 送遠端 embedding。
9. **CJK：** 未見專用中文 tokenizer 保證；選本機多語 embedding、確認 Neo4j/FalkorDB 的全文索引分詞，再用繁簡中文測試實體名與混合中英 query。
10. **Dependency：** Python 3.10+、Pydantic、Neo4j Python driver、OpenAI-compatible client、NumPy、Tenacity、PostHog；FalkorDB、sentence-transformers、其他 provider 為選配。
11. **其他評估：** Graphiti 遙測需設 GRAPHITI_TELEMETRY_ENABLED=false；local DB 不代表模型在本機，必須同時設定本機 LLM 與本機 embedding。

## 3. Cognee

原始碼：[open-source/cognee](./cognee/README.md) · [官方 repo](https://github.com/topoteretes/cognee) · [local Ollama 說明](https://docs.cognee.ai/guides/local-ollama)

1. **一句話定位：** 把文件與 agent 經驗轉成可分層查詢的知識圖譜和語意索引。
2. **怎麼存：** 記憶可分 session cache 與永久 dataset；持久層使用 SQLite、LanceDB 和本機圖資料庫選項（如 NetworkX／LadybugDB），輸入檔也可留在本機。
3. **怎麼取：** recall 可依 query 自動選圖、向量、全文等策略，session memory 優先，再回落永久圖譜。
4. **記憶衝突：** 可選 CONTRADICTION_DETECTION 產生 contradicts 關係；它標示矛盾但不保證替使用者選出正確值，需由查詢邏輯或 LLM／人工決策。
5. **有自動化嗎：** remember/recall API；@agent_memory decorator 在包裝函式前取回相關脈絡、完成後記 agent trace，後續 improve 可將 session 經驗提升到長期記憶。
6. **有哪些 hook（高維步驟）：** @agent_memory＝函式執行前 recall → 將脈絡交給 agent → 函式完成後記錄 trace；self-improvement＝收到明確或隱含回饋 → 改善資料集。通用 host event hook 由整合層提供。
7. **強項與限制：** ingestion-to-graph pipeline、搜尋策略與 session/long-term 結構完整；依賴多、安裝選項與 backend 容易選錯，整套關聯圖建置比單純 Markdown 系統重。
8. **哪些步驟有 LLM：** 本機 GLiNER 可做部分實體擷取並支援無雲端 key 的路徑；cognify/improve、摘要、回饋判讀或答案生成視 pipeline 而定。FastEmbed 可本機產 embedding；AUTO_FEEDBACK 預設路徑可能多出 LLM 呼叫，需停用或指定本機 endpoint。
9. **CJK：** 有語言偵測，但未確認此即代表中文分詞／召回保證；須配置多語 embedding、選合適抽取器並以中文基準資料實測。
10. **Dependency：** Python 3.10–3.14；OpenAI-compatible client、SQLite/SQLAlchemy、LanceDB、FastEmbed/ONNX Runtime、NetworkX、LadybugDB、FastAPI 等；GLiNER 是選配。
11. **其他評估：** 避開雲端 integration；資料庫與 LLM/embedding provider 要分開設定成本機。其多種 search strategy 是可調空間，也增加運維及比較基準的工作。
## 4. Supermemory

原始碼：[open-source/supermemory](./supermemory/README.md) · [官方 repo](https://github.com/supermemoryai/supermemory) · [self-host 文件](https://supermemory.ai/docs/self-hosting/overview)

1. **一句話定位：** 一個帶自動個人檔案、更新與遺忘策略的統一 memory API，並提供本機單機版。
2. **怎麼存：** Local binary 將資料放在使用者本機目錄，內嵌 graph engine 與本機 embedding；無須另建 vector DB。
3. **怎麼取：** 透過本機 API 查文件、個人 profile、hybrid search 與相關片段；agent 可以 MCP/tool 呼叫。
4. **記憶衝突：** 官方宣稱會辨識 temporal updates、解決矛盾與遺忘過期內容；這是模型策略，實際覆寫規則、證據保留與可逆性應以樣本測試，不等同 deterministic 規則。
5. **有自動化嗎：** local server + memory API/MCP 可由 agent 寫入及搜尋；SDK/agent integration 可自動建立 profile。接線時將 baseURL 指到 localhost。
6. **有哪些 hook（高維步驟）：** 核心 local API 沒有適用所有 host 的通用 hook。高階流程是 agent memory 工具送入內容→本機服務抽取／索引；回答前 MCP/API query→取回相關片段。不要把預設 hosted MCP endpoint 當成本機服務。
7. **強項與限制：** 上手快、資料與 embedding 可完全放本機、可接 Ollama；它是較完整 TypeScript monorepo，部署組件多，且預設英文 embedding 不適合直接假設中文效果。
8. **哪些步驟有 LLM：** 抽取記憶、profile、更新／矛盾判斷與遺忘可能用 LLM；用本機 Ollama 可把這些也留在機器。embedding 預設本機，但可切換遠端，需確認設定。
9. **CJK：** README 預設 Xenova/bge-base-en-v1.5；它是英文向模型。改用本機 multilingual embedding，並以中日韓混排 query 測試。
10. **Dependency：** Node.js 20+、Bun workspace；TypeScript、Hono、Drizzle、embedded local engine、Transformers/AI SDK 等。它是 monorepo，完整服務依賴明顯多於單一 SDK。
11. **其他評估：** Local mode 和 hosted platform 介面相似，最容易把 MCP 或 connector 接錯。隱私部署只接 localhost、不同步雲端文件，也檢查首次啟動模型下載。

## 5. Hindsight

原始碼：[open-source/hindsight](./hindsight/README.md) · [官方 repo](https://github.com/vectorize-io/hindsight) · [coding-agent 整合](./hindsight/hindsight-integrations/coding-agents/README.md) · [模型設定](https://hindsight.vectorize.io/developer/models)

1. **一句話定位：** 以 retain/recall/reflect 三種操作，把經驗、證據、belief 和時間關係變成可反思的長期記憶。
2. **怎麼存：** 本機 Hindsight API + PostgreSQL/pgvector；retain 從文字抽事實、時間、entity 和關係，保留來源內容與證據。
3. **怎麼取：** recall 混合語意、BM25、圖與 temporal retrieval；reflect 再讓模型以記憶作推理回答。
4. **記憶衝突：** 以 belief、證據與引用來源整理，非單純覆寫；新事實可調整／細化舊 belief，並保留根據。不同來源互相矛盾時仍要評估反思答案是否正確。
5. **有自動化嗎：** 多種 coding agents 整合會自動回想與保留 session；也提供 MCP 工具。Claude Code/Codex hook 是較完整的方式。
6. **有哪些 hook（高維步驟）：** SessionStart＝啟動／確認本機 daemon；UserPromptSubmit＝依新問題 recall 並注入相關上下文；Stop＝收集本回合 transcript 並送 retain；SessionEnd＝關閉或清理本次 daemon 資源。各 host 的可用事件略有差異。
7. **強項與限制：** evidence/provenance、時間與 reflect 能力突出；需跑 API、PostgreSQL/pgvector 與多模型流程，寫入可能較慢且 LLM/DB 維運負擔較高。
8. **哪些步驟有 LLM：** retain 抽取與整理需要 LLM；recall 可混合搜尋；reflect 需要 LLM。文件支援 Ollama、LM Studio、llama.cpp 等本機 provider。
9. **CJK：** 可選多語模型，但預設 recall 品質會由 embedding、BM25 tokenizer 和抽取 LLM 共同決定；Chinese BM25 不應未測就視為可靠。
10. **Dependency：** Python 3.11+、FastAPI、PostgreSQL + pgvector；Docker 常用；本機 LLM provider 選 Ollama／LM Studio／llama.cpp。
11. **其他評估：** API 預設值、DB bind、身份驗證和 agent prompt 注入都要檢查；本機 Hindsight 不會阻止 Claude/Codex 主 agent 將取回文字送往其遠端模型。

## 6. Letta Code

原始碼：[open-source/letta](./letta/README.md)（此目錄 clone 自活躍的 letta-code）· [現行 repo](https://github.com/letta-ai/letta-code) · [Letta 文件](https://docs.letta.com/letta-code/memory)

1. **一句話定位：** 以有身份、可改寫上下文與技能的 stateful agent 為核心，讓 agent 自己維護長期記憶。
2. **怎麼存：** persona/human 等 memory blocks，加上 agent state、skills 與 MemFS；MemFS 用 Git 在本機追蹤上下文和記憶版本。
3. **怎麼取：** agent 直接讀寫 memory blocks、檔案、技能與歷史；/palace 可檢視記憶，搜尋歷史訊息供回顧。
4. **記憶衝突：** agent 可依新情況改寫 memory block，Git 有助於檢視／還原變更；未見可保證的語義矛盾仲裁器。repo 中的 memory conflict repair 處理並行 Git worktree／patch 衝突，不能當成「使用者兩個事實誰正確」的判斷。
5. **有自動化嗎：** /sleeptime 讓 agent 在閒置時進行 dreaming；可加自訂 lifecycle hooks、crons 和 schedules。
6. **有哪些 hook（高維步驟）：** hooks 可在 agent 執行的關鍵階段跑自訂 script；高階使用方式是「開始前讀取／補齊 agent memory → agent 執行並寫回 → session 後整理或由 schedule 夢想整理」。這是可配置擴充點，無固定的一組內建 memory hooks。
7. **強項與限制：** agent 能主動調整 persona、流程與技能，Git 歷史透明；它是 agent runtime/harness，不只是可插入任一系統的記憶 DB，若只要本機索引需自行整合。
8. **哪些步驟有 LLM：** 代理器的記憶改寫、dreaming、技能生成由 agent LLM 決策；文字檔讀寫／Git diff 本身不必用 LLM。模型端點可本機或遠端。
9. **CJK：** 記憶是 UTF-8 文字，語言模型可整理中文；未見專用 CJK tokenizer／embedding recall 的保證。
10. **Dependency：** Node.js 22.19+、Bun 1.3.2+；TypeScript/Bun app server、SDK 與 Git。local backend 不代表模型一定本機。
11. **其他評估：** Cloud 是預設後端，明確切成 letta backend local；不要啟用把 MemFS push 到 GitHub 的 repository sync，除非該 remote 被明確核准。

## 7. Memori

原始碼：[open-source/memori](./memori/README.md) · [官方 repo](https://github.com/MemoriLabs/Memori) · [BYODB 文件](https://memorilabs.ai/docs/memori-byodb/) · [Advanced Augmentation](https://memorilabs.ai/docs/memori-byodb/concepts/advanced-augmentation/)

1. **一句話定位：** 包裝既有 LLM client，背景把對話與 agent trace 抽成帶歸屬的 facts、attributes、events 和 graph triples。
2. **怎麼存：** BYODB 可接本機 SQLite 或本機 PostgreSQL 等；Rust FastEmbed 產 embedding，FAISS/資料庫進行向量與結構化儲存。不要用 Cloud storage。
3. **怎麼取：** wrapped LLM call 前做本機語意相似度搜尋，依 attribution 找到 top-N facts，再注入 system context；也有 recall API。
4. **記憶衝突：** 重複 triple 會去重並增加提及次數／更新時間；未看到 BYODB 明確的矛盾事實仲裁，互斥的新舊值可能共存。
5. **有自動化嗎：** Python/TypeScript SDK 包裝模型 client，自動捕捉呼叫並在背景做 augmentation；下一次模型呼叫時自動召回。
6. **有哪些 hook（高維步驟）：** BYODB SDK 的核心 seam 是「攔截 LLM client 呼叫→保存對話→非同步 augmentation」與「下次呼叫前 recall→把記憶加進 prompt」。Claude Code 範例與 OpenClaw/Hermes 某些 plugin 使用 Memori Cloud，不能直接拿來當本機 BYODB hook。
7. **強項與限制：** DB 可沿用既有 infrastructure；非同步降低主回應延遲，資料模型和 attribution 清楚。預設 Cloud 快速開始與 BYODB 使用方式不同，容易接錯；預設 embedding 英文取向。
8. **哪些步驟有 LLM：** augmentation 用 LLM 抽 facts、preferences、semantic triples；embedding 預設本機 Rust FastEmbed；recall 以本機相似度檢索。若 LLM 用雲端，抽取內容會傳到該 API。
9. **CJK：** 預設 all-MiniLM-L6-v2 偏英文。要替換成支援中日韓的本機模型；沒有專用 CJK 分詞保證。
10. **Dependency：** Python 3.10+；Memori native Rust extension（setuptools-rust）、FastEmbed/ONNX、FAISS、NumPy、HTTP client；SQLAlchemy 為選配，資料庫 driver 依 BYODB。
11. **其他評估：** BYODB 文件主張資料留在自有 DB，但 repo 同時有 Cloud API 與直連 Cloud 的 host plugin。採用前應限定 BYODB SDK 和本機 DB，並以出站網路檢查驗證該版本執行路徑。
## 8. MemU

原始碼：[open-source/memu](./memu/README.md) · [官方 repo](https://github.com/NevaMind-AI/memU) · [developer integration](./memu/docs/developer.md)

1. **一句話定位：** 從各 agent 本機歷史抽出可讀的 memory、resource 與 skills，再跨 host 重用。
2. **怎麼存：** Local mode 預設 SQLite，並由 agent 寫出／維護 Markdown memory、skill 檔；可選本機 PostgreSQL/pgvector。Cloud mode 是另一條產品路徑。
3. **怎麼取：** progressive retrieve 依 query 取回相關 memory/resource/skill；adapter 會要求 agent 作答前先執行 retrieve。
4. **記憶衝突：** self-evolve job 由 agent 閱讀既有資料，再自行決定不改、patch 或建立新 skill；沒有可保證的自動 fact-conflict 規則，應 review Markdown diff。
5. **有自動化嗎：** 註冊 scheduled bridge 讀取完成的 session log、整理成工作項目，再讓 host agent 提煉與 commit；在 instruction file 加入 pre-answer retrieve 指令。
6. **有哪些 hook（高維步驟）：** scheduled memorize＝找新增 session → prepare job → agent 對照既有 memory/skills → 寫 Markdown → commit 並建立索引；standing retrieval instruction＝每次回答前 query → 把回傳記憶納入工作上下文。這比較像 scheduler + agent instruction，不是所有 host 都有同一原生 event hook。
7. **強項與限制：** 跨 Claude/Codex/Cursor/OpenClaw 等 host，Markdown 易讀且可 review；支援範圍隨 host/OS 不同，排程和指令注入需要安裝器正確辨識 session 檔。
8. **哪些步驟有 LLM：** MemoryService 負責儲存、embedding、檢索，不自行作 chat/LLM calls；真正的整理與技能撰寫由 host agent 做。embedding 預設 provider 是 OpenAI，須改成本機 endpoint，否則檢索文字會送出。
9. **CJK：** 未見通用中文分詞方案；中文需要多語本機 embedding。若依 BM25 關鍵字召回，需以繁體中文長詞與中英混合詞測試。
10. **Dependency：** Python 3.11+、NumPy、OpenAI-compatible client、SQLModel、Alembic、HTTPX；SQLite 預設，pgvector/Postgres 是選配。
11. **其他評估：** 需設定 MEMU_MEMORY_MODE=Local、MEMU_DB 指本機、MEMU_BASE_URL 指本機 embedding service；README 的 hosted 安裝訊息和 self-host 安裝訊息不要混用。

## 9. EverOS

原始碼：[open-source/everos](./everos/README.md) · [官方 repo](https://github.com/EverMind-AI/EverOS) · [How memory works](./everos/docs/how-memory-works.md)

1. **一句話定位：** 以本機 Markdown 為記憶真相來源，將 agent 對話、資料與技能變成易檢查的長期知識庫。
2. **怎麼存：** 人可讀 Markdown 為 source of truth；SQLite 存 metadata/audit，LanceDB 存向量與 BM25 索引；filesystem watcher 做 cascade 同步。
3. **怎麼取：** 本機關鍵字／BM25，配置後可混合 embedding、rerank、skill/profile 搜尋；API/CLI/MCP 可接 agent。
4. **記憶衝突：** 檔案版本、時間與證據可保留歷程；未確認保證自動選出真值的通用 conflict resolver，讓 LLM 改寫前應保留舊值或來源。
5. **有自動化嗎：** 對話先 add/buffer，再於 flush／boundary 整理成持久記憶；檔案 watcher 建索引；Offline Memory Evolution scheduler 在背景跑策略。
6. **有哪些 hook（高維步驟）：** flush＝提交緩衝內容→依策略抽取並寫 Markdown；cascade watcher＝偵測檔案變更→更新本機 SQLite/LanceDB；OME schedule＝週期性執行 profile/fact/skill 等演進工作。接 agent 時透過本機 API/CLI/MCP；沒有單一通用 Claude/Codex lifecycle hook。
7. **強項與限制：** 原始 Markdown 可讀、可 Git review，source/index 分離易重建；Python 版本需求新、LanceDB/SQLite 索引維護較複雜，模型策略仍需設定。
8. **哪些步驟有 LLM：** 最小 add/flush/Markdown/BM25 流程可不依賴雲端 LLM；記憶抽取、reflection、skill extraction 依配置叫 LLM，embedding/rerank 也可選本機 endpoint。
9. **CJK：** 明確依賴 jieba 做中文 BM25/tokenization，是此候選中對中文關鍵字檢索最有直接證據的一個；語意檢索仍需多語本機 embedding。
10. **Dependency：** Python 3.12+、LanceDB、SQLite/SQLModel、FastAPI、watchdog/watchfiles、APScheduler、jieba、OpenAI-compatible SDK；可選觀測或其他 storage。
11. **其他評估：** Markdown 原稿與衍生索引分開，利於稽核與復原；確認 LanceDB、embedding/rerank endpoint 均本機，勿啟用遠端 Milvus/Zilliz。

## 10. MemOS Local Plugin

原始碼：[open-source/memos/apps/memos-local-plugin](./memos/apps/memos-local-plugin/README.md) · [官方 repo](https://github.com/MemTensor/MemOS) · [Local plugin 文件](./memos/apps/memos-local-plugin/docs)

1. **一句話定位：** 以反思與回饋讓 agent 從行動軌跡提煉可重用政策、世界模型與 skills 的本機記憶 plugin。
2. **怎麼存：** Local Plugin 的 runtime home 用 SQLite 儲存 L1 trace、L2 policy、L3 world model、episode、feedback，skill 另以本機檔案保存；不要選 MemOS Cloud Plugin。
3. **怎麼取：** 三層 retrieval 先 skill，再 trace/episode，再 world model；以相關性將結果注入 agent 當前上下文。
4. **記憶衝突：** 可透過 feedback 對 memory 作 correct/supplement/replace；自動演化會綜合 trace 與回饋，但不等於每對矛盾事實都自動且正確地裁定。
5. **有自動化嗎：** OpenClaw、Hermes、DeepSeek Harness adapter 可自動 recall、記錄 turn/tool trace，並在背景做 feedback、reflection、policy/skill 演進。
6. **有哪些 hook（高維步驟）：** OpenClaw message_received＝擷取乾淨的 user input；before_prompt_build＝查 SQLite memory 並注入 prompt；agent_end＝保存本回合 trace 並排入後續反思。DeepSeek Harness 在每個非空 user turn 的 agent/pre-step 做有界 recall，capture/reflection 背景執行。各 adapter event 名稱不同。
7. **強項與限制：** 層次清楚，技能可逐步結晶，支援多個 agent host 且 Local Plugin 明確把資料放本機；目前主要是特定 host plugin，需維護 Node/native SQLite/模型相容性。
8. **哪些步驟有 LLM：** trace 評估、反思、策略／關係／技能摘要會使用 host 已設定或明確指定的 LLM；本機 embedding/向量檢索可由 Transformers 本機模型完成。若 host 的 LLM 是雲端，注入 memory 的 prompt 也會外送。
9. **CJK：** 可存中文；檢索品質依本機 embedding/model 與 SQLite FTS5 行為，沒有確認通用的 CJK 字詞斷詞保證；需要測繁體同義詞、姓名與中英混合。
10. **Dependency：** Node.js 20+、TypeScript、better-sqlite3、Hugging Face Transformers；可能帶 ONNX/native binaries，並依賴所接 agent host 的 plugin SDK。
11. **其他評估：** Local/Cloud 是不同 plugin；Viewer 預設 loopback，但應確認 bindHost；檢查設定、日誌與 audit log 位置以及升級時 SQLite schema migration 備份。

---

## 給 MemoIdx 選型的建議

- **先做中文、重視可檢查性：** 優先試 EverOS（Markdown + jieba），再和 MemOS Local Plugin 或 MemU 比較；用本機多語 embedding，確認中文向量搜尋。
- **想處理事實時間變更／衝突：** Graphiti 的 valid-time edges 和 Hindsight 的 evidence/belief 比較值得作原型；它們解決的是不同問題，前者重圖譜沿革，後者重證據與反思。
- **最快接現有 agent：** Mem0 Cursor plugin、Hindsight coding-agent hooks、MemOS adapters；先確認 hook 捕捉了哪些 transcript/tool output，避免不必要的敏感資料持久化。
- **最低外流風險驗收：** 以本機 SQLite/Neo4j/pgvector/LanceDB、localhost LLM 與 embedding 起跑；記錄進程出站連線，在禁網狀態驗證寫入、召回、整理仍正常。再逐個開放明確核准的 LLM API endpoint。
- **重要測試集：** 事實更新（地址、偏好、專案決策）、相互矛盾且有時間戳的記憶、繁體／簡體／日文／韓文、中英混排、專有名詞、刪除與過期、跨專案隔離、來源引用、模型或 DB 不可用時降級、備份／還原和索引重建。