# 参考文献全文获取流程

适用场景：从论文、报告或项目文献池出发，尽量取得每条正式文献的 PDF 原文，并输出可审计的“已取得”和“仍缺失”清单。

## 1. 解析参考文献

从稿件中定位参考文献段落，逐条编号。优先抽取 DOI；无 DOI 条目保留题名、原始引用和 PDF 全文证据，不伪造 DOI。

推荐字段：

```text
index
raw_reference
input_doi
input_title_guess
doi_verified
verification_sources
verified_title
verified_authors
verified_year
verified_journal
verified_doi
doi_url
verification_basis
pdf_fulltext_evidence
doi_waiver_evidence
openalex_is_oa
status
downloaded_file
download_source
failure_reason
candidate_pdf_urls
local_text_evidence
```

中文期刊、图书和章节通常没有 DOI 或 DOI 不稳定。它们可以记录为用户提供来源、中文数据库材料、公开学术检索记录或 PDF 全文证据；不得伪装成 DOI 完整条目。

## 2. 引用证据与元数据核验

DOI 有则按以下顺序核验：

1. DOI resolver / 出版社页面
2. Crossref
3. OpenAlex
4. Semantic Scholar
5. 正式期刊或数据库页面

若 DOI 与题名冲突，以 DOI resolver / 出版社页面为优先；冲突无法解释时标记为待复核。没有 DOI 时不直接阻断，改用 DOI 豁免证据核验：用户提供来源、完整论文 PDF 原文、或 Google Scholar / OpenAlex / CNKI 等公开学术检索记录；仍须核验作者、年份、题名和来源。

## 3. 批量合法开放全文尝试

全文下载先走批量路线。对 DOI 条目依次尝试：

1. Crossref `link` 中的 PDF。
2. OpenAlex `best_oa_location` / `locations` 中的 `pdf_url` 和落地页。
3. Unpaywall `best_oa_location`。
4. Semantic Scholar `openAccessPdf`。
5. 出版社常见 PDF 端点和机构知识库。

每个候选 URL 都先下载到 `tmp/` 并校验。失败记录要区分：HTTP 403、非 PDF、连接失败、题名不匹配、需要机构访问。

OpenAlex 在这里的角色是批量发现、开放获取状态判断和候选 URL 收集。英文或国际文献在这一轮没有直接取得可校验 PDF 时，不要停在“OpenAlex 未发现全文”；系统应把未通过校验的条目写成缺失队列，并自动进入 Google Scholar 单篇检索。

### 3.1 常见遗漏原因与补救

上一轮容易遗漏的主要原因通常不是“网上没有 PDF”，而是获取路径过早停止：

1. 只用 OpenAlex/Unpaywall/Crossref/Semantic Scholar 批量接口，未进入 Scholar 逐篇右侧 PDF 点击。
2. 只用脚本 HTTP 请求下载 Scholar 右侧链接。Academia、ResearchGate、SSRN、机构库和出版社页面经常对脚本返回 `HTTP 403`、HTML 登录页或非 PDF，但在用户已登录的可见 Chrome 中可以打开 PDF 阅读器或生成最终签名 PDF URL。
3. 只搜索题名，没有用 DOI 精确检索。有些 Scholar 结果在 DOI 查询下出现右侧 PDF，题名查询反而没有。
4. 下载目录中出现 `download.pdf`、`ssrn-*.pdf`、短文件名或浏览器扩展重命名文件，未被回收到项目 PDF 目录。
5. 自动前三页 DOI/题名校验过严，导致 NBER/SSRN/大学仓储工作论文版本、扫描件、PDF 字符乱码文件被误判为 rejected。
6. Scholar 右侧 PDF 也会指向回应文章、综述、相近题名或无关论文；只看链接文字会造成误收，必须打开首页核验题名和作者。

补救顺序：先 DOI 精确检索并点击右侧 PDF；打开候选后记录最终 URL 或点击浏览器下载按钮；扫描下载目录并标准化命名；自动校验失败但首页疑似正确的 PDF 进入双独立审核；错链保留 rejected 证据并写明拒收理由。

## 4. Google Scholar 逐篇点击补抓

这是批量开放源尝试后的自动后续步骤，不是可选人工补充。只有已通过批量 PDF 校验的条目可以跳过；其余条目必须进入逐篇点击队列。不要高频批量抓取 Scholar。按单篇执行：

1. 打开 `https://scholar.google.com/schhp?hl=zh-CN&as_sdt=0,5`。
2. 用精确题名搜索：`"<verified_title>"`。
3. 优先识别搜索结果右侧的 `[PDF] domain` 链接；如果用户明确要求“像浏览器里右上角 PDF 那样点一下”，必须在可见浏览器里逐篇点击该链接，再下载候选 PDF。
4. 如果首页没有可通过校验的 PDF，打开“所有版本”，逐页检查右侧 PDF。
5. 如果仍失败，按更精确的定向查询重试：`"<title>" "<doi>"`、`"<title>" "<first_author_surname>"`、`"<title>" "<journal>"`、`"<title>" pdf`。
6. 跳过 Sci-Hub、LibGen、Z-Library、Chrome Web Store、广告页、明显非论文页和与目标题名不符的近似文献。
7. 保存后仍做题名、DOI 和元数据校验；Google Scholar 只提供候选 PDF 线索，不能替代正式文献核验。

如果 Google Scholar 出现可见的“我不是机器人”复选框，可以点击一次。图片选择、滑块、短信、账号验证等挑战由用户手动处理；不要尝试绕过。

Windows 下 `agent-browser.cmd` 可能错误处理 URL 中的 `%22/%2C` 编码；可直接调用 `agent-browser-win32-x64.exe`，或确保参数未被 shell 展开。

### 4.0 用户 Chrome 优先规则

当脚本请求失败但用户能在自己的已登录 Chrome 中看到右侧 PDF 时，不要继续把该条记为“不可获取”。Google Scholar、Academia、ResearchGate、SSRN、机构库 PDF viewer、Google Scholar Reader、浏览器 PDF 下载按钮和下载目录回收，默认优先使用用户 Chrome；只有用户 Chrome 不可用、未授权或无法连接时，才退回隔离可控浏览器、无头浏览器或脚本请求。

1. 使用用户已登录 Chrome 打开 Scholar 查询页；若插件、账号、easyScholar、Google Scholar Reader 或下载记录只存在于用户浏览器，不能用隔离浏览器替代最终判断。
2. 先用 DOI 精确检索；若 DOI 无结果，再用精确题名和 `title + author/journal`。
3. 点击右侧 `[PDF] domain`。如果页面进入 Google Scholar Reader、Chrome PDF viewer、机构库 PDF viewer 或 Academia 页面，等待 PDF 文本/首页渲染。
4. 若地址栏已是最终 PDF URL，可用该 URL 再走下载函数；若脚本仍失败，点击浏览器 PDF 工具栏“下载”，再从系统下载目录回收。
5. 对 Academia 页面，优先点击页面内 `Download PDF`，再选免费单篇下载；如出现“send a note”弹窗，下载文件通常已经落地，先检查下载目录，不需要发送消息。
6. 对 ResearchGate、SAGE、Cloudflare、人机挑战、登录墙或机构访问页面，不绕过。记录为 `verification_required`、`access_blocked` 或 `publisher_access_blocked`，再寻找其他合法公开来源。
7. 下载后必须重新命名为 `<reference_id>_<safe_title>.pdf`，并写入候选来源、最终 URL、下载时间和校验状态。

### 4.1 推荐的逐篇点击执行模型

使用可见 Chrome/CDP 或其他可审计浏览器会话，避免无头脚本制造大量不可解释失败。每篇文献至少记录：

```text
reference_id
verified_title
doi
scholar_query_url
query_variant
right_pdf_links_found
clicked_pdf_url
download_status
file_path
validation_status
note
```

推荐分层执行：

1. `initial_scholar_click`：对缺全文清单逐篇搜索 `"<verified_title>"`，点击首页右侧 `[PDF] domain`。每批控制在 10-15 篇，批间检查状态和验证码。
2. `failed_item_retry`：只重试失败项，不覆盖原始成功记录。依次尝试 `title + DOI`、精确标题、`title + pdf`。
3. `all_versions_pass`：进入每篇的“所有版本/All versions”页，抽取每个版本页右侧 `[PDF] domain`。
4. `targeted_pass`：对仍缺失的短题名或高误匹配文献，用 `title + DOI`、`title + first author`、`title + journal` 定向搜索。
5. `orphan_download_match`：浏览器可能下载 `ssrn-*.pdf`、`download.pdf` 等未按参考文献编号命名的文件。扫描下载目录和 rejected 目录，用 DOI 或强标题 token 覆盖匹配目标文献，匹配后复制为标准文件名。
6. `rejected_deep_validation`：对于已被移入 rejected、但文件名或来源提示可能对应目标文献的 PDF，扫描前 20-30 页；若 DOI 或强标题匹配出现，可恢复为“人工/深度确认”候选。
7. `browser_download_recovery`：检查 `Downloads/` 和浏览器默认下载目录最近文件，匹配 Scholar 点击时间、文件名、PDF 页数、题名/作者/DOI。浏览器下载成功但脚本下载失败时，以浏览器下载文件为候选，复制进项目目录后再校验。
8. `manual_identity_audit`：对仍处于 `acquired_needs_manual_validation` 的 PDF，渲染首页或读取前两页，核验题名、作者、工作论文编号、期刊版本关系。错文献必须移入 `rejected_mismatch/`。
9. `dual_agent_identity_audit`：对自动校验失败但疑似正确的开放版本，交给两个独立审核者分别判断 `accept/reject/uncertain`。只有两个都 `accept` 才提升为已取得；任一 `reject` 或结论冲突则不计入已取得。

### 4.2 状态表和合并规则

每轮 Scholar 操作都要写独立表，避免失败重试污染原始记录。推荐文件名：

```text
google_scholar_pdf_click_status.csv
google_scholar_pdf_click_attempts.csv
google_scholar_pdf_retry_status.csv
google_scholar_pdf_retry_attempts.csv
google_scholar_all_versions_status.csv
google_scholar_all_versions_attempts.csv
google_scholar_targeted_remaining_status.csv
google_scholar_targeted_remaining_attempts.csv
orphan_downloaded_pdf_match_status.csv
browser_download_recovery_status.csv
rejected_expected_pdf_deep_validation.csv
manual_pdf_identity_audit.csv
dual_agent_manual_acceptance.csv
fulltext_final_status.csv
```

合并时按 `reference_id` 保留最强状态：

1. `acquired_strict_doi_or_title_validated`
2. `acquired_dual_agent_identity_accepted_open_version`
3. `acquired_open_working_paper_version_visual_confirmed`
4. `acquired_needs_manual_identity_review`
5. `missing_candidate_rejected_by_dual_agent_identity_audit`
6. `missing_publisher_or_database_access_blocked_no_valid_pdf`
7. `missing_after_all_legal_routes`

不要因为浏览器下载了 PDF 就标记为已取得。只有通过 DOI、强标题匹配、作者/题名首页图像确认、双独立审核或用户提供原件确认后，才可进入已取得或可读版本清单。工作论文版本可以作为阅读全文，但正式引用仍用已核验的期刊 DOI，并在证据表记录版本说明。

错链应保留明确拒收状态。典型拒收理由包括：回应文章替代原文、综述替代经典原文、相近题名、作者不符、年份/期刊不符、只在参考文献中出现目标题名、PDF 页面是验证码/登录/HTML。

### 4.3 PDF 身份校验标准

自动通过的最低规则：

- 文件头为 `%PDF`，页数可读。
- 前 1-3 页检出 DOI；或
- 题名有效 token 不少于 4 个，覆盖率达到约 0.65 以上。

二次深度校验可扫描前 20-30 页，但通过后要标记为 `deep_validated` 或 `needs_manual_identity_review`，不要混同于前三页严格通过。短题名文献，如 `Law and Finance`、`Legal Origins`、`Courts`、`Text as Data`，容易误抓同名或近似文献，必须提高阈值并结合作者、期刊、年份或 DOI 复核。

人工/视觉确认适用情形：

- NBER、SSRN、World Bank、大学仓储提供的是工作论文版本，首页题名和作者与正式论文一致。
- PDF 文本抽取乱码，但首页图像清楚显示题名、作者、工作论文编号或稳定来源。
- 期刊版本不可公开获取，但开放工作论文版本与正式论文存在明确版本关系。

双独立审核适用情形：

- 自动校验失败原因是短题名、扫描件、PDF 字符编码乱码或 DOI 不在首页。
- 首页或仓储元数据显示题名、作者、年份、来源与目标一致。
- NBER、SSRN、CEPR、大学仓储、作者主页或机构库提供同题同作者版本，但不是出版社 PDF。

双审输出字段：

```text
reference_id
reviewer_id
decision: accept | reject | uncertain
reason
evidence_title
evidence_authors
evidence_source_or_version
evidence_doi_or_stable_url
```

验收规则：两个独立审核均为 `accept` 才标记 `acquired_dual_agent_identity_accepted_open_version`。一个 `reject` 即拒收；出现 `uncertain` 或结论冲突，保留为 `acquired_needs_manual_identity_review` 或 `missing_uncertain_identity`，不进入最终已取得数。

拒收情形：

- 首页题名、作者、年份或 DOI 指向另一篇文献。
- 只因题名中有一个通用短语而命中。
- PDF 是书章、综述、教材、插件页、验证码页、广告页或下载失败 HTML。
- Scholar 右侧链接来自 ResearchGate/Academia/SSRN 但返回 403、HTML 或需要登录，且没有可校验 PDF。
- Scholar 右侧链接打开后是目标文献的 response/comment/review，而非目标原文。

### 4.4 人机验证和访问边界

Scholar 出现人机验证时：

- 保存截图，记录 `verification_required_stopped`。
- 停止自动流程，等待用户在可见浏览器中处理。
- 不编写绕过验证码、滑块、短信、账号验证或访问控制的逻辑。
- 用户处理完成后，从失败清单或未处理清单继续，而不是从头重跑全部文献。

出版社、JSTOR、OUP、Wiley、SAGE、Elsevier 等返回 `HTTP 403`、登录页或机构访问页时，记录为缺失或需机构访问。不得改用 Sci-Hub、LibGen、Z-Library 等绕过访问控制来源。

### 4.5 最终报告写法

最终报告至少包含：

- 正式候选文献总数。
- 严格 DOI/标题校验通过数。
- 双独立审核通过的开放版本数。
- 公开工作论文版本视觉确认数。
- 仍缺全文数。
- 已完成的获取路径列表。
- 仍缺全文清单，列出 `reference_id`、题名、期刊、DOI。
- 被拒收或错配 PDF 的目录。
- 每个缺失项的最终原因：错链双审拒收、出版社/数据库访问受阻、验证码/Cloudflare 阻断、未发现合法公开 PDF。

示例状态表达：

```text
Strict DOI/title-validated PDFs: 45
Dual-agent accepted open versions: 8
Open working-paper versions visually confirmed: 2
Still missing after all legal/open routes: 23
Usable full texts for structured reading with version notes where needed: 47
```

这种表达区分“正式期刊 PDF”“公开工作论文版本”“缺失”，比笼统说“已下载 47 篇”更可审计。

## 5. CNKI 授权下载

CNKI 是受控授权下载链，不是正式引用核验链。

### 5.0 CNKI 用户 Chrome 优先规则

CNKI 下载依赖用户的授权登录态、机构权限、下载插件/CAJ 阅读器关联和验证码处理。涉及这些环节时，默认优先使用用户已登录 Chrome；专用可控 Chrome/CDP 或 `envctl` 是批量执行器，不替代用户浏览器登录态。

1. 先在用户已登录 Chrome 中确认 CNKI 可访问、账号/机构权限有效、下载按钮可见。
2. 检索、详情页核验、下载按钮点击、CAJ/PDF 文件落地和验证码恢复，优先在用户 Chrome 中完成或由工具接管该会话完成。
3. 只有用户 Chrome 不可用、用户未登录、用户明确要求隔离环境，或需要稳定批量下载时，才启动专用可控 Chrome/CDP。
4. 不保存、导出或复用用户 cookies；不绕过登录、机构权限、滑块、短信、图片验证码或安全验证。
5. 浏览器下载成功但脚本状态失败时，扫描用户下载目录和项目收件箱，按题名、作者、来源、DOI/刊期或 CNKI 元数据侧车文件回收并重命名。

### 5.1 CNKI 执行顺序

1. 默认先用用户 Chrome 或 `envctl cnki-zotero find/fetch` 做候选发现。
2. 用用户已登录 Chrome、可控 Chrome/CDP 或用户已安装的批量下载脚本执行授权下载。
3. 下载目录必须是项目输出区，优先 `<project_root>/outputs/inbox/cnki-downloads`；若 CNKI/浏览器落到系统下载目录，必须回收并生成 manifest。
4. 如果任务限定作者单位，候选必须带有作者单位证据；作者检索排序、全文混合检索不能替代作者单位核验。
5. 批量下载遇到滑块或安全验证时，停止自动流程，写入 `captcha_checkpoint`，不要继续硬跑后续论文。
6. 用户在可见的已登录 CNKI 浏览器窗口手动完成验证后，用上一份报告继续 `browser-download`；系统读取 `captcha_checkpoint.resume_candidates`，从被打断的论文继续。
7. 下载后运行 `envctl cnki-zotero ingest-plan` 生成 Zotero 导入计划。

示例恢复命令：

```powershell
python -m skills.scripts.envctl cnki-zotero browser-download --input "<上一份 cnki-zotero 报告.json>" --project-root "C:\path\to\project" --direct-cdp --cdp 9333 --output auto
```

## 6. 用户提供 PDF 纳入

用户给出本地 PDF 时：

1. 读取 PDF 元数据和前 1-3 页文本。
2. 与目标条目的题名、作者、期刊、年份、DOI 或稳定 URL 比对。
3. 匹配后复制到 `pdfs/`，文件名用参考文献编号和安全题名。
4. 更新状态表：`status=downloaded`，`download_source=user_provided_file | <source_path>`。
5. 重新生成已取得、缺失清单和 PDF 校验报告。

## 7. 中文原件归档

用户提供中文原件文件夹时：

1. 复制到项目输出区内的中文原件目录。
2. 生成 manifest：源路径、项目路径、大小、SHA256、复制时间。
3. 用题名、作者、文件名和抽取文本做匹配。
4. 严禁只凭泛化关键词错配；低置信匹配必须人工复核。

## 8. PDF 校验标准

最低校验：

- 文件存在，大小合理。
- 文件头含 `%PDF`。
- `pypdf` 能读取页数。
- 前 1-3 页文本或 PDF 元数据与题名 token 有足够重合。
- DOI 或稳定 URL 命中可以作为强证据。没有 DOI 时，用户提供来源、完整 PDF 原文、或 Google Scholar / OpenAlex / CNKI 等公开学术检索记录可以作为 DOI 豁免证据；有 DOI 的条目仍必须核验 DOI。

建议输出 `pdf_validation.csv`：

```text
index,title,doi,verification_basis,doi_waiver_basis,file,exists,pages,title_overlap,author_or_source_match,year_or_source_match,doi_hit,ok,note
```

## 9. 输出

每轮结束必须输出：

1. 总览：总条目、已取得、英文 PDF、中文原件、仍缺失。
2. 已取得全文清单：题名、DOI 或 DOI 豁免状态、文件路径。
3. 仍缺失清单：必须有题名、DOI 或 DOI 豁免证据状态、简明原因。
4. PDF 校验报告。
5. 若有拒收文件，保留在 `rejected_mismatch/`，不要计入已取得。
