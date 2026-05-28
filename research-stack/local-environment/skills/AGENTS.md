# AGENTS

本目录是研究型 Codex 工作环境的源规则层。  
项目级 `AGENTS.md` 必须继承这里的约束，并且只能继续收紧，不能扩权。

## 全局研究约束

- 正式学术引用必须基于可审计证据核验，且同时具备：作者、年份、标题、期刊或正式来源、真实性核验证据。
- DOI 是强核验证据；正式论文写作和参考文献链中，如果证据材料里出现 DOI，必须核验。DOI 不是唯一硬门槛：用户提供的论文来源、拥有完整论文 PDF 原文文件的条目、或能在 Google Scholar、OpenAlex、CNKI 等公开学术检索系统中核验到的条目，可以豁免“必须有 DOI”的要求。
- DOI 豁免不等于免核验。无 DOI 条目必须记录可审计证据：用户提供来源、完整 PDF 原文证据，或公开学术检索记录；仍需具备作者、年份、标题、期刊或正式来源、核验依据。无 DOI 且无上述证据的条目，不得进入正式参考文献链；不得伪造 DOI。
- 中文为默认协作语言。
- 涉及分析解释的文本，优先采用 `PEEL` 闭环，不使用空洞套话。
- `research-autopilot` 是唯一总入口；项目型任务进入多 agent 规划后，仍不得绕过正式核验链、社媒证据链和复现链。
- 本地环境治理以工程控制论为首要框架：任何环境演化都必须显式说明目标、被控变量、反馈信号、控制器、执行器、稳定性验证和回滚方式。
- `skills/catalog/control_kernel.json` 是控制论底层逻辑的机器可读入口；`AGENTS.md` 只保存最高约束，不承载细粒度控制合同。
- 项目型多 agent 编排必须在项目目录里使用真实落盘的 `AGENTS.md` 和 `.codex/agents/*.json`。缺失时先用 `envctl ensure-project-contract` 或 `plan-team` 的自动初始化补齐；不得用对话上下文、临时 JSON 或 `audit/` 目录伪造项目 contract。
- 经验沉淀必须遵守 `skills/catalog/memory_admission_policy.json`：底层逻辑进 control kernel，可复用流程进 skill，长解释和复盘进 Obsidian，临时噪声丢弃。
- 外部 GitHub、plugin、MCP 或 skill 候选不得整包接管本地环境，必须先经过 `skill-vetter`、`external_systems_research.json` 和 `external_adoption_reviews.json`。

## 继承规则

- 项目级 `AGENTS.md` 可以：
  - 继续增加 `forbid_skills_mcp`
  - 继续增加 `forbid_write_roots`
  - 进一步收紧 `max_execution_mode`
  - 继续增加 `require_review_for`
  - 继续补充 `project_truth_sources`
- 项目级 `AGENTS.md` 不可以：
  - 放宽这里已经定义的限制
  - 让 reviewer 直接写主产物
  - 绕过 `citation-verifier -> zotero-sync`
  - 绕过 `writing-reference-capture`
  - 绕过 `social-platform-reader / social-platform-mcp`
  - 绕过 `reproducibility-package`

```yaml
agent_constraints:
  forbid_skills_mcp: []
  forbid_write_roots:
  max_execution_mode: null
  require_review_for:
    - paper_draft
    - revision_package
    - submission_package
    - figures_tables
    - reproducibility_bundle
    - literature_synthesis
    - case_dataset
    - project_map
    - app_opportunity_brief
    - user_needs_hierarchy
    - target_specifications
    - concept_selection_matrix
    - concept_test_report
    - prototype_test_plan
    - development_economics_note
    - app_prd
    - visual_design_spec
    - app_screen_mockups
    - app_icon_assets
    - app_architecture
    - ui_implementation
    - design_system_rules
    - desktop_build
    - release_package
  project_truth_sources:
    - research-map.md
    - findings-memory.md
    - material-passport.yaml
    - evidence-ledger.yaml
```
