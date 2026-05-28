# 本地研究环境搭建逻辑与过程

更新时间：2026-05-10

本文解释这套本地研究环境是怎么搭起来的，为什么这样分层，以及工程控制论、上下文工程、提示工程、工具接口、多角色协作、Zotero 和 Obsidian 等内容怎样被吸收进来。

如果只想知道日常怎么用，看 `README.md`。如果想理解“为什么要这样设计”，读这份。

## 先看总体思路

这套环境经历过一个重要转变：从“有很多研究技能”转向“有一套可治理的研究系统”。

早期的重点是把常见研究工作做成技能，例如文献综述、引文核验、文本分析、社媒证据读取、写作导出。后来发现，仅有技能还不够，因为系统还必须回答几个问题：

- 任务一开始应该由谁判断路线？
- 哪些材料可以成为正式证据？
- 哪些产物必须被审查？
- 项目结束后，经验如何进入长期规则？
- 外部工具和新插件能不能直接吸收？
- 出错后如何回退？

因此，本地环境逐步形成现在的结构：总入口负责判断，项目编排器负责组织任务，规则清单和结构约束负责定义边界，校验器负责检查，复盘机制负责演化。

## 这套系统要解决什么问题

本地环境的目标不是追求工具数量，而是追求三个结果：

1. 研究可信。正式引用、材料证据、数据来源和写作输出都要能核验。
2. 环境稳定。技能、插件、工具接口、配置文件和项目骨架不能互相漂移。
3. 经验可沉淀。项目中的有效做法可以进入长期规则，但必须经过复盘和校验。

用工程控制论的语言说，这套环境要有清楚的被控对象、目标函数、反馈信号、控制器、执行器和稳定性指标。用普通专业语言说，就是：知道自己管什么、为了什么而优化、怎么发现偏差、谁来纠偏、怎么确认没有改坏。

## 术语先统一

命令、文件名和产品名保留原文，是为了和真实系统名称一致；这里先给出中文含义。

| 术语 | 中文解释 |
| --- | --- |
| Codex | 本地 AI 助手，是交互和执行入口。 |
| HELM | 本地环境管理界面，负责展示状态、读取快照和调用环境控制命令。 |
| VELA | 可分发工作流和交接层，承接安全、稳定、可公开复用的规则。 |
| Zotero | 文献管理工具，保存经过核验的正式参考文献。 |
| Obsidian | 笔记和知识库工具，保存阅读笔记、方法卡、长解释和项目复盘。 |
| Git | 版本记录工具，用来保存改动、比较差异和回退问题。 |
| Python | 本环境主要使用的脚本语言。 |
| skill / 技能 | 一套可复用的工作方法。 |
| plugin / 插件 | 给 Codex 增加能力的包。 |
| MCP / 工具接口 | Codex 调用外部工具的标准接口。 |
| route / 任务路线 | 对任务类型的分类。 |
| profile / 工具配置 | 某条路线应该启用哪些工具接口。 |
| schema / 结构约束 | 规定文件字段和格式的规则。 |
| catalog / 规则清单 | 保存路线、技能、质量门、工具关系的清单。 |
| validator / 校验器 | 自动检查规则和文件是否一致的脚本。 |
| gate / 质量门 | 继续推进前必须通过的检查点。 |
| handoff / 交接材料 | 给下一轮线程、VELA 或 HELM 读取的结构化说明。 |
| snapshot / 快照 | 给管理界面或应用读取的一份稳定副本。 |
| source of truth / 源规则层 | 最终以哪一套文件为准。当前就是本仓库。 |
| DOI | 论文或正式出版物的永久编号，用来核验参考文献真实性。 |
| OCR | 把扫描图片中的文字识别成可搜索文本。 |
| dry-run / 预演 | 只报告将要发生什么，不实际改文件。 |
| commit / 提交 | 把已确认的改动写入 Git 历史。 |

## 阶段一：把研究工作拆成技能

最初的建设重点是把常用研究能力整理成可复用技能。

包括：

- 文献综述和单篇论文评审。
- 引用证据与元数据核验。DOI 有则核验，已有论文 PDF 全文稿件时仍须记录 PDF 证据；正式写作和参考文献链按规则核验 DOI 或记录人工确认例外。
- Zotero 文献入库。
- Obsidian 项目笔记同步。
- 定量分析、文本分析、网络分析、仿真。
- 社媒和网页证据读取。
- 写作导出、返修、投稿包、复现包。

这一阶段解决了“有什么工具可用”。但它还没有充分解决“什么时候用哪个工具”和“用了之后怎么判断质量”。

## 阶段二：建立总入口和项目编排

后来把所有研究任务统一交给 `research-autopilot`。它的作用不是做所有事情，而是先判断任务属于哪一类。

例如：

- 文献任务走文献路线。
- 社媒案例走证据读取路线。
- 数据分析走计算社科路线。
- 桌面应用开发走应用开发路线。
- 环境维护走环境治理路线。

当任务变成一个项目，`research-team-orchestrator` 会接管项目编排。它决定：

- 需要哪些角色。
- 哪些产物必须输出。
- 哪些产物必须被审查。
- 哪些质量门会阻断继续推进。

这个阶段的关键变化是：任务不再靠临时判断推进，而是先进入路线和项目结构。

## 阶段三：把规则写成机器可检查的文件

为了避免规则只停留在口头说明里，本地环境把核心规则放进了两类文件。

第一类是规则清单，放在 `skills/catalog`：

- 路线表。
- 技能清单。
- 质量门。
- 数据访问等级。
- 项目队形。
- 外部工具吸收记录。

第二类是结构约束，放在 `skills/schemas`：

- 项目交接文件必须有哪些字段。
- 项目队形文件必须如何书写。
- 校验器输出必须如何表达。
- HELM 快照必须包含和排除哪些内容。

这样做的意义是：规则不再只是文档，而是可以被脚本检查。规则写错、字段缺失、路径漂移，都能被校验器发现。

## 阶段四：把 HELM 和 VELA 放到正确位置

HELM 和 VELA 都有价值，但它们不能替代本地源规则层。

HELM 的定位是管理界面。它读取状态、展示报告、调用 `envctl`，但不直接承载研究逻辑。

VELA 的定位是工作流包装和交接层。它适合承接公开、安全、可分发的项目上下文和交接契约，但不能直接复制本地私有路径、浏览器状态、Zotero 或 Obsidian 私有内容。

当前跨仓吸收规则是：

```text
本地想法 -> 本地结构约束和测试 -> 稳定的公开子集 -> VELA 或 HELM
```

这条规则防止本地私有环境、公开工作流和管理界面互相混淆。

插件内部技能也按同一条边界处理。`research-autopilot` 插件里的技能采用“有意双暴露”：源文件只在本地仓维护，运行态同时同步到插件缓存和 `.codex\skills` 独立镜像。这样 Codex 新线程可以直接看到独立入口，插件入口也保持可用；治理时把独立镜像视为运行态副本，而不是第二套源规则。

## 阶段五：引入工程控制论

本轮重塑把钱学森《工程控制论》三份本地材料作为核心方法论源，把两篇公开平台文章作为现代 AI 编程语境下的实践解释。

这里的重点不是把书的内容写成一段提示词，而是把控制论思想转成环境规则。

### 控制论概念怎样落地

| 控制论概念 | 抽取出的工程方法 | 本地落点 |
| --- | --- | --- |
| 系统边界 | 先说明谁管什么，谁不能越权。 | 本地仓、VELA、HELM、Zotero、Obsidian、插件、工具接口分层。 |
| 目标函数 | 优化目标必须明确。 | 研究可信、环境稳定、可复盘演化。 |
| 前馈约束 | 执行前先给结构和限制。 | 路线、工具配置、项目骨架、质量门、交接格式。 |
| 反馈 | 偏差必须返回系统。 | 校验器、审查、每日审计、项目复盘、Zotero/Obsidian 同步。 |
| 能控性 | 只有能实际影响的对象才可控制。 | 不可写仓库、未暴露工具、无法访问页面都必须报告阻塞。 |
| 能观测性 | 状态必须能被看到。 | 项目状态、日志、证据台账、校验结果。 |
| 稳定性 | 能运行不等于稳定。 | 自动化可以受控处理低风险事项，但必须有日志、校验、Git 记录和回滚；用户级配置必须有备份和人工确认。 |
| 随机扰动 | 变化是常态，不是例外。 | 路径迁移、Codex 更新、网页变化、OCR 噪声进入漂移检查。 |
| 自适应 | 系统可以学习，但学习本身要受控。 | 项目复盘、治理提案、校验器、Git 提交。 |
| 大系统 | 多层系统靠接口协作。 | VELA 交接、HELM 快照、工具接口策略、项目队形。 |

机器可读控制核在：

```text
skills/catalog/control_kernel.json
skills/catalog/memory_admission_policy.json
skills/catalog/local_memory_system.json
skills/catalog/evolution_backlog.json
skills/catalog/cybernetic_source_rule_crosswalk.json
skills/catalog/engineering_cybernetics_source_evidence.json
```

这些文件不是给人休闲阅读的，而是让系统能检查“控制论方法有没有真正落地”。

## 两篇公开平台文章怎样被吸收

两篇文章的作用是把工程控制论放到 AI 编程和智能体协作的场景里解释。它们不是正式学术参考文献，也不替代三本书。

第一篇文章强调“环境设计比单次提示更重要”。本地吸收为：

- `AGENTS.md` 只放最高原则，不塞成巨型手册。
- 深层规则放进结构约束、规则清单、技能和校验器。
- 仓库里的状态、脚本、日志和审查记录比临时对话更可靠。
- 后台审计可以提出建议，但成熟前不能自动改源文件。

这里还有一条项目级规则：每个真实项目都必须有自己的 `AGENTS.md` 和 `.codex/agents/*.json`。本地环境仓里的同名规则是模板和校验源，不直接替代项目文件。原因很简单：多角色协作必须在项目目录里留下“谁负责执行、谁负责审查、产物写到哪里、质量门怎么记录”的真实痕迹。为避免新线程卡住，`plan-team` 和 `bootstrap` 会在旧项目缺少这些文件时自动调用 `ensure-project-contract` 补齐缺失契约；补齐失败才停止。

第二篇文章强调用控制论审查 AI 写出的软件。它指出几个典型风险：

- 返回“已修复”但实际上没有修复。
- 捕获异常却不记录日志，导致不可观测。
- 文档承诺的功能和代码状态不一致。
- 单个大文件承担过多职责，破坏系统边界。

本地吸收为：

- 校验器输出必须区分错误、警告、细节和真实写入状态。
- 用户级配置必须先预演、再写入、可备份、可回滚。
- 新能力默认拆成结构约束、规则清单、命令入口、校验器和测试。
- 大脚本继续拆分，旧入口只保留兼容。

第二篇文章提到的 19 条准则，本地只固化页面可见的分组和案例，不伪造未逐条核验的全文清单。这是证据边界，不是方法论缺口。

## 上下文工程、提示工程和执行环境工程

这三个词容易混在一起，本环境把它们分清。

| 名称 | 在本环境里的意思 |
| --- | --- |
| 上下文工程 | 让 Codex 知道项目当前状态、材料来源、证据和阶段。 |
| 提示工程 | 用清楚、可复用的表达告诉 Codex 目标、限制和失败模式。 |
| 执行环境工程 | 设计工具、文件、校验器、日志、回滚和质量门，让任务能可靠执行。 |

对应关系：

- 上下文工程落到 `research-map.md`、`findings-memory.md`、材料护照、证据台账和项目状态文件。
- 提示工程落到技能说明、路线卡和 `prompt_catalog_lite.json`。
- 执行环境工程落到 `envctl`、结构约束、校验器、测试、工具接口和回滚策略。

只有提示词是不够的。没有上下文，系统不知道自己处于什么状态；没有执行环境，系统无法稳定检查和回退。

## 多角色协作怎样进入系统

本地环境不把“同一段对话里换几个角度”叫作真正多角色协作。

真正的多角色协作至少要有：

- 明确角色。
- 独立任务包。
- 独立输出目录。
- 交接记录。
- 审查者。
- 质量门。

这些规则由以下文件共同管理：

```text
skills/catalog/research_team_playbooks.json
skills/catalog/subagent_registry.json
skills/schemas/research_team_playbook.schema.json
skills/schemas/subagent_registry.schema.json
```

这样做的目的不是增加复杂度，而是防止“看起来像多角色，实际无人审查”的假协作。

## Zotero 与 Obsidian 为什么都需要

Zotero 和 Obsidian 分工不同。

Zotero 是正式文献库。进入 Zotero 的正式参考文献必须经过可审计引用证据核验。DOI 是强证据，有则核验；如果已经有论文 PDF 全文稿件，包括用户上传、本地已有、授权下载或 Codex 下载，必须记录 PDF 文件来源、首页/元数据、题名、作者、年份、来源和页数可读性。确无 DOI 或 DOI 不适用时，必须记录人工确认例外；不能把 PDF 当作跳过 DOI 核验的借口。

Obsidian 是长期解释和知识沉淀层。它适合保存阅读笔记、方法卡、项目复盘和工作流解释。

本地记忆准入规则是：

- 底层系统逻辑进入控制核。
- 可重复流程进入技能。
- 长解释和复盘进入 Obsidian。
- 少量入口偏好进入 Codex 原生记忆。
- 旧路径、一次性失败、不可核验信息丢弃。

这能避免把所有信息都塞进一个地方，最后无法维护。

在这之上，`local_memory_system.json` 负责“候选记忆怎么形成、怎么评分、什么时候沉淀、什么时候过期”。它综合了三类外部记忆系统的优点：Brain 类系统的健康检查和状态摘要，向量记忆系统的质量过滤、热度、衰减和融合排序思想，OpenClaw 类系统的持久、私有、临时分层和自检报告。它不把这些外部系统装成本地运行时，也不启动向量数据库、后台服务或外部 hook。

轻量不等于低效果。这里的目标是减少冗余：同一经验要去重、合并、评分、过期或否决，不能每次运行都堆一份新记忆。只有用户明确确认、跨任务重复出现、能改变流程并通过校验的经验，才会形成进入 skill、控制核或 Obsidian 的提案。

`agentmemory` 只作为可选的运行时记忆辅助，不替代本地仓的规则源头。本地仓继续决定什么能成为规则、技能或自动化；`python -m skills.scripts.envctl memory reconcile --summary --probe-agentmemory` 只负责对账它是否健康、是否和本地自动化日志一致。这样既能利用更顺手的召回工具，又不会让外部记忆服务静默改写源规则层。

## 外部 GitHub 和插件怎样吸收

外部项目不能整包导入。它们只能作为受控输入。

标准流程是：

```text
发现候选 -> 技能审查 -> 外部系统研究记录 -> 吸收提案 -> 结构约束或校验器 -> 合并
```

每日自动化现在也走同一条控制链。项目收尾时产生的 `project_closure_retrospective.md`、`research_stack_change_proposal.md` 和 `PROJECT_CLOSED.md` 会被 `python -m skills.scripts.envctl evolution intake --write-report --append-backlog` 扫描成演化输入报告，并去重登记到 `evolution_backlog.json`。每日任务还会运行 `validate conflicts`、`validate environment-layers`、`route startup-summary` 和 `memory reconcile`，用来发现路线冲突、七层结构漂移、启动上下文过重和记忆状态不一致。这属于受控自动落地：自动登记候选、写日志、跑校验；不自动改技能、插件、MCP、运行时缓存或用户级配置。

定期环境更新线程再从 `evolution_backlog.json` 里挑低风险事项，在独立工作树和 `codex/` 分支上尝试收束。它必须完整校验通过才能提交；如果校验失败、风险不清或涉及用户级配置，只留下报告，不改源规则层。

路线选择本身也被纳入控制链。`conflict_matrix.json` 记录哪些路线、技能或工具容易互相误伤；`python -m skills.scripts.envctl route explain "..." --summary` 会解释候选路线和触发原因。如果指令含义模糊，例如“revision package”可能是审稿回复包，也可能被误解成复现包，系统应先问用户确认，而不是直接进入新链条。

当前已经吸收过的结构包括：

- `agentsmd/agents.md`：根规则继承模型。
- `academic-research-skills`：研究阶段、元数据、质量门、两阶段审稿、主张与证据对齐、材料护照、时间一致性和文献语料预筛。吸收为本地合同和校验思路，不安装它的 Claude 专用运行时。
- `Auto-claude-code-research-in-sleep`：吸收独立审查、运行痕迹、断点续跑、工具路径解析、运行副本漂移检查、超时和重试边界。它的自主夜间研究、供应商路由、飞书、GPU 和自动改稿运行时不进入默认链路。
- `codex-skills-workbench`：吸收 manifest 清单、源笔记保留、安装前校验、安装和导出方向分明、公开模板脱敏等技能维护方法；同时把关键词文献收割状态模型、R/ggplot 小型绘图适配器、PPT 图墙 manifest、中文学位论文 manifest/占位符/DOCX 模板写回思想并入现有 workflow。它不作为第二套技能源规则层，不能直接写 `<CODEX_HOME>\skills`，也不能覆盖受保护的知识蒸馏 skill；PubMed/Europe PMC、生态位、系统发育和学位论文专用流程都不进入社科默认链路。
- `guizang-ppt-skill`：原版安装到 `$CODEX_HOME/skills/guizang-ppt-skill`，由本地 `research-presentation-studio` 调度。它贡献两套主要视觉系统：电子杂志 × 电子墨水、瑞士国际主义；同时贡献单文件网页 PPT 模板、S01-S22 瑞士版式锁、截图适配、配图提示、浏览器预览和静态校验脚本。本地不改造它的视觉系统，也不把它升级为第二总路由；`.pptx` 仍由官方 Presentations 插件执行，网页高质量视觉直接委托原版 guizang skill 执行。
- `deepagents`：未来执行环境适配器接口。
- `subagent-driven-development`：审查纪律和集成审查。
- `superpowers`：工程规划、调试和验证方法。
- `awesome-codex-subagents`：角色元数据，不整包导入。
- `awesome-ai-research-writing`：深度吸收 prompt 里的可迁移约束，而不是复制 prompt 包。已经并入格式敏感中英转换、LaTeX/Word 输出容器区分、缩写/扩写的微调边界、去 AI 痕迹但不改主张、数据约束的结果分析、图题表题和图型推荐、整篇审稿的致命/可修复问题区分，以及换会议/改投别家的目标要求清单。OpenSkills 安装路径、当前模型排名、CS/LLM 会议默认结构和 arXiv 翻译运行时不进入默认链路。
- `humanities-thesis-skill`：只吸收人文社科论文写作中比本地更细的部分，包括写作前结构化提问、研究对象和问题意识确认、理论必须落到材料、细读与引文后分析、章节递进、术语一致性和脚注功能。它的检索脚本、平台说明、术语表和理论家速查表不作为本地运行时或正式参考来源；文献发现、全文获取、引用核验和 Zotero 入库仍走本地链路。
- `Awesome-Agent-Skills-for-Empirical-Research`：深度吸收量化实证研究和学术去模板化写作的规则，但不把外部技能整包装成新入口。它的 AER-style 识别优先、DID/IV/RDD/PSM/SCM/DML 等方法红线、完整实证分析链、稳健性矩阵、复现包纪律被转成 `empirical_quant_workflow.json`、`quant-analysis`、`causal_identification_checked` 和 `envctl validate empirical-quant-workflow`。它的 humanizer、deslop、stop-slop、avoid-ai-writing 和中文 de-AIGC 内容只吸收为“表层写作审计”：去掉空话、模板感和机械衔接，但不改变主张、证据、变量、结果、引用和局限，也不承诺绕过检测。
- `Yuan1z0825/nature-skills`：深度吸收图表契约、多面板证据层级、白底克制图形风格、章节职责、逻辑优先润色、审稿回复矩阵和数据可得性清单；新增 `manuscript_writing_workflow` 和 `manuscript-writing-studio`。英文期刊和计算社科/方法技术型文章可更积极借鉴它的写作结构，中文期刊、传统量化和质性研究以本地社科规则为主；不吸收 Nature/CNS、医学、理工或湿实验的默认审查标准。
- `journal-adapt-writing-skill`：吸收目标期刊适配润色的方法，把“目标期刊论文 -> 风格卡 -> 期刊画像 -> 临时写作规则 -> 逐节诊断和修订日志”纳入 `manuscript_writing_workflow` 和 `manuscript-writing-studio`。它不作为独立运行 skill 安装；目标期刊语料只学习结构、语气、贡献位置、讨论范围和段落推进，不允许改事实、结果、引用、公式、变量、图表或作者主张，也不替代 DOI、引用证据、审稿或投稿包检查。
- `DeepScientist`：项目结构和研究记忆文件。
- `VELA`：项目上下文、交接格式和项目队形契约。
- `darwin-skill`：评分、实测、只保留可验证改进和回滚的演化纪律。
- `bggg-skill-taotie`：从参考 skill 提取可迁移模式，而不是整包复制。
- `cookjohn/cnki-skills`：吸收“用户登录浏览器下载、CNKI 导出元数据、Zotero 本地接口写入”的工作模式，但不整包安装，不复制未审查脚本。
- `cfh-7598/cnki-codex-skills`：吸收“Codex 薄入口 + 共享 Python/Playwright 实现”的结构，把复杂浏览器动作封在 CLI 后面。
- `cookjohn/gs-skills`：吸收 `data-cid` 等稳定页面键和批量导出思路；拒绝任何非授权全文获取路径。
- `cookjohn/wos-skills`：本轮不进入默认链路，只保留为后续观察对象；当前不承诺 Web of Science 检索、导出或下载可用。
- `paper-search` 和 `find-skills` 类仓库：只作为技能发现和轻量 API 检索参考，不作为本地环境的主运行时。

吸收原则是只取结构、边界、检查方法和可验证模式，不引入新的主运行时。

这次对三个上游仓库的吸收比较了四种方案：

1. 直接安装外部工作台：拒绝作为默认方案。优点是省事，但会形成第二套技能源规则层，也可能覆盖运行时副本和受保护 skill。
2. 本地合同优先吸收：最终选择。把上游仓库中有价值的清单、源笔记、校验、断点续跑、证据审查和脱敏规则，改写成本地 `catalog + schema + validator + tests`。
3. 给所有技能建立源笔记镜像：暂时观察。这个方向适合未来公开模板化发布，但现在会让核心 skill 迁移成本过高。
4. 直接编辑运行时 skill 再反向导出：拒绝作为默认方案。它看起来即时生效，但会绕过本地源规则层，造成审计和回滚困难。

因此新增的规则核心是：

```text
skills/catalog/skill_workbench_policy.json
skills/schemas/skill_workbench_policy.v1.schema.json
python -m skills.scripts.envctl validate skill-workbench --summary
```

它把四类对象分清：本地 `research-autopilot` 源技能、Codex 运行副本、外部候选 skill、项目目录里的 `AGENTS.md` 和 `.codex/agents/*.json`。这样以后吸收第三方 skill 时，先审查和转译，再同步到运行态，不能反过来让外部安装脚本直接改本机 Codex 技能目录。

## CNKI 到 Zotero 的新边界

这套环境现在把中文数据库全文下载拆成三层：

1. 发现层：默认用 `envctl cnki-zotero find` 和可控 Chrome/CDP 找候选文献、详情页和元数据。它支持按作者、主题、关键词、篇名、作者单位、全文或 DOI 检索，也支持按被引、最新、相关度、下载量或综合排序。`cnki-mcp` 保留为观察项，只能在当前会话冒烟测试通过后临时作为候选传感器。
2. 下载层：Chrome 中用户已经登录的页面，或用户自己安装的批量下载脚本，负责把有权限访问的 PDF/CAJ 下载到项目收件箱。
3. 入库层：`envctl cnki-zotero` 先扫描收件箱并生成导入计划；确认后再用 Zotero MCP 把 PDF 或 DOI 记录写入 Zotero。

项目默认收件箱是：

```text
<项目根目录>/outputs/inbox/cnki-downloads
```

环境级收件箱 `skills/outputs/inbox/cnki-downloads` 只用于环境冒烟测试或无项目上下文的手工维护。项目下载必须落在项目自己的 `outputs/` 下，避免多个项目的全文材料混在一起。

这些目录不进入 git。系统只记录文件名、大小、哈希和拟执行动作，不把论文全文写进源仓库。

如果检索条件包含作者单位，候选选择必须先通过作者单位 gate。作者检索结果只能说明“作者名匹配”，全文检索只能说明“页面文本包含这些词”，二者都不能替代作者单位核验。可接受证据是高级检索的作者+单位组合、详情页作者单位、CNKI 导出元数据，或项目内经过人工确认的清单。

批量下载不再写死“作者 + 被引”。日常入口是 `fetch`：调用方提供检索词、检索字段、排序方式、下载数量和项目根目录。需要先看候选、不下载时，用 `find` 生成候选 JSON。`browser-batch-download` 和 `browser-discover` 继续作为调试入口保留。下载执行仍走同一个可控 Chrome 会话，并把文件放进项目 `outputs/inbox/cnki-downloads`。

这样设计的原因很直接：CNKI 下载依赖用户账号、机构权限、验证码和浏览器状态。环境可以把“下载后的文件如何进入 Zotero”做清楚，但不能替用户绕过访问控制。

## Google Scholar 的新边界

Google Scholar 被收束为候选发现层。默认入口是 `google-scholar-mcp`，备用入口是 `paper-search-mcp` 的 Google Scholar 搜索；二者只负责提出候选论文、引文线索和页面链接。

它不承担三件事：

1. 不直接生成正式参考文献。正式引用仍走 `citation-verifier -> zotero-sync -> writing-reference-capture`。
2. 不做全文批量下载。能否获得全文由 DOI、出版社页面、开放获取来源或用户已有材料另行核验；已有论文 PDF 全文稿件时，仍须记录 PDF 证据；正式写作和参考文献链有 DOI 必须核验，确无 DOI 或 DOI 不适用时须记录人工确认例外。
3. 不作为浏览器高频自动化对象。实测中直接浏览器打开 Scholar 搜索页会触发异常流量提示，因此默认不使用浏览器批量抓取 Scholar。

这让 Google Scholar 回到它最适合的位置：找线索、扩展引用、给文献综述提供候选池。质量门和正式入库仍由引用证据核验、Zotero 和写作引用链承担；DOI 有则核验，已有全文 PDF 时必须记录 PDF 证据；正式写作和参考文献链有 DOI 必须核验，确无 DOI 或 DOI 不适用时须记录人工确认例外。

## 2026-05-11 CNKI 与 Google Scholar 收束复盘

本轮只压实 CNKI 和 Google Scholar，两者在环境中的位置不同。

CNKI 是“发现 + 授权下载 + Zotero 入库计划”链路。现在默认面向用户暴露三个入口：`find` 只找候选，`fetch` 搜索并下载到项目收件箱，`ingest-plan` 扫描下载结果并生成 Zotero 导入计划。底层的 `browser-*` 和 `candidate-gate` 仍保留，但只作为调试和维护入口。实测结果是：专用可控 Chrome 运行在 9333 端口时，`fetch --query "工程控制论" --field subject --sort latest --limit 1 --cleanup` 能完成候选发现、PDF 下载和清理；`ingest-plan` 能在清理后给出空收件箱报告。下载文件始终落在项目 `outputs/inbox/cnki-downloads`，不会进入源仓库。

Google Scholar 是候选发现层。`google-scholar-mcp` 是主入口，`paper-search-mcp` 是备用入口；本轮实测二者都能返回 `engineering cybernetics` 的候选结果。浏览器直接打开 Google Scholar 搜索页会触发异常流量提示，因此不把 Scholar 浏览器页面作为高频自动化对象。

对整体环境的影响：

1. 没有新增主运行时。CNKI 继续复用本地 Python `envctl`、可控 Chrome 和已有 Zotero 链路。
2. 没有改变正式引用金标准的核心：CNKI 和 Google Scholar 都只提供候选，正式参考文献仍必须经过引用证据与元数据核验。变化是全文 PDF 被明确作为证据层记录；正式写作中有 DOI 仍必须核验，确无 DOI 或 DOI 不适用时才记录人工确认例外。
3. 没有改变项目隔离原则。项目下载进入项目自己的 `outputs/`，环境级输出只用于烟测或维护。
5. Web of Science 暂不纳入默认链路。当前只保留为后续观察对象，不承诺检索、导出或下载可用。

## 蒸馏学者咨询小组


这层设计有三个目的：

1. 让蒸馏学者能参与论文审稿、修改、润色和多学者讨论。
2. 让多个学者先独立审读，再交叉回应，最后交给正常写作链汇总。
3. 保留硬门槛：正式引用仍走引用证据与元数据核验，写作仍走写作质量门，最终采纳仍由作者决定。全文 PDF 可作为证据；正式写作和参考文献链有 DOI 必须核验，确无 DOI 或 DOI 不适用时须记录人工确认例外，但必须核验 PDF 证据。

咨询小组只写项目输出目录：

```text
```

它不直接覆盖论文正文，不写本地环境源文件，也不改用户级配置。多位学者之间的分歧会保留为分歧矩阵，不强行合并成一个看似一致的意见。这样做符合控制论里的反馈分层：学者角色提供高价值反馈信号，控制器仍然是项目质量门和作者决策。

## 为什么要收束说明文档

过去 `skills/docs` 下有很多历史说明、计划、复盘和日志。问题是：文档一多，就会出现路径漂移、说法冲突和读者不知道看哪一份。

现在收束成两份：

- `README.md` 管使用。
- `BUILD-LOGIC.md` 管搭建逻辑和演化过程。

控制论阅读证据、来源映射和交接记录不再散落成多份说明性 Markdown，而是进入机器可读文件和 VELA 交接材料。

这一点也被 `validate_research_stack` 检查：如果以后又出现 `skills/docs` 或 `skills/README.md`，校验会报错。

## 当前不做什么

为保持系统稳定，当前明确不做：

- 不把 VELA 变成本地环境总控。
- 不把 HELM 变成源规则层。
- 不把外部 GitHub 仓整包导入。
- 不把公开平台文章当作正式学术参考文献。
- 不把用户级配置静默写进提交。
- 不删除 `.venv`、`python/runtime`、`python/downloads`。
- 不用未暴露的浏览器或 Computer Use 能力替代已验证工具链。

## 维护时如何判断完成

一次环境变更只有同时满足以下条件，才算完成：

1. 改动边界清楚。
2. 规则文件和说明文件没有互相冲突。
3. 相关结构约束和规则清单仍然能通过校验。
4. 项目或工具路径没有漂移。
5. 高风险改动有回滚办法。
6. 提交前校验全部通过。

当前必须通过的校验链是：

```powershell
python -m unittest discover -s skills\tests
python -m skills.scripts.envctl validate contracts --summary
python -m skills.scripts.envctl validate stack --summary
python -m skills.scripts.envctl validate initializer-policy --summary
python -m skills.scripts.envctl validate helm-snapshot --summary
python -m skills.scripts.envctl validate drift --summary
python -m skills.scripts.envctl validate cybernetics --summary
python -m skills.scripts.envctl validate memory --summary
python -m skills.scripts.envctl validate conflicts --summary
python -m skills.scripts.envctl validate environment-layers --summary
python -m skills.scripts.envctl validate skill-workbench --summary
python -m skills.scripts.validate_subagent_registry
python -m skills.scripts.validate_agents_contract
python -m skills.scripts.validate_research_pipeline
python -m skills.scripts.validate_research_stack
```

这条校验链的意义很简单：本地环境不能只“看起来改好了”，必须能被自动检查证明没有破坏核心结构。

日常对话中默认使用摘要校验，避免完整 JSON 把响应流撑得过长。需要定位细节时，去掉 `--summary` 或把完整报告写入文件，再在对话里只汇报结论。

Codex App 的新线程启动稳定性由 `startup-safe` profile 兜底：默认不预启动 stdio MCP，任务需要时再切换到专用 profile。旧 MCP 子进程残留由 `skills/scripts/cleanup-stale-codex-mcp-processes.ps1` 清理。

对话中途的网络流断开不归 `startup-safe` 解决。先用 `skills/scripts/diagnose-codex-connectivity.ps1` 检查直连、DNS、本机代理和代理 HTTP 访问；若浏览器代理可用但 Codex 子进程没有继承代理，用 `skills/scripts/set-codex-user-proxy.ps1` 写入用户级代理环境变量并重启 Codex。
