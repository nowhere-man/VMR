<!--
Sync Impact Report:
- Version change: [TEMPLATE] → 1.0.0
- Initial constitution creation for VQMR project
- Principles defined:
  * 总体原则 (5 principles): 清晰一致、规范驱动、透明可追溯、迭代式交付、审查优先
  * 设计与实现原则 (4 principles): 最小可用、最少依赖、禁止过度设计、可删除性
  * 测试优先原则 (Test-First)
  * 用户故事独立性
  * 语义化版本控制
- Sections added:
  * 一、总体原则 (Core Principles)
  * 二、设计与实现原则 (Design & Implementation Principles)
  * 三、语言与文档规范 (Language & Documentation Standards)
  * 四、代码规范 (Code Standards)
  * 五、测试与质量保证 (Testing & Quality Assurance)
  * 六、版本管理与变更控制 (Version Management & Change Control)
  * 七、工作流程 (Workflow)
  * 八、治理 (Governance)
- Templates requiring updates:
  ✅ plan-template.md - Constitution Check section aligns with principles
  ✅ spec-template.md - Requirement structure supports specification-first approach
  ✅ tasks-template.md - Task organization reflects test-first and user story principles
- Language: All documentation in Simplified Chinese as per project requirement
- Follow-up TODOs: None - all placeholders filled
-->

# VQMR Constitution

> 本文件为 VQMR（Video Quality Metrics Report）项目的开发与管理约定文件，旨在确保团队在整个生命周期内遵循统一的规范、质量标准与协作方式。
> 除源代码外，所有文档、注释与说明必须使用**简体中文**撰写，表达应符合中文技术写作习惯。

## 一、总体原则
1. **清晰一致**：所有代码、文档、接口与命名需保持风格统一，可读性优先于简洁性。
2. **规范驱动**：所有开发活动应以规格文件（specs/）为唯一事实来源（Single Source of Truth）。
3. **透明可追溯**：每一项功能、任务与测试结果都需能追溯到相应的规格条目。
4. **迭代式交付**：遵循 Spec-Driven Development 模式，小步迭代、频繁验证。
5. **审查优先**：代码提交前必须通过自测与审查（Code Review）；不允许直接合并未审查代码。

## 二、设计与实现原则
1. **最小可用**。
2. **最少依赖**。
3. **禁止过度设计**。
4. **可删除性**。

## 三、语言与文档规范
1. 所有文档（包括注释、README、接口说明、提交信息）**必须使用简体中文**。
2. 技术术语可保留英文原文，但需在首次出现时提供中文释义。
3. 文档目录：
    + /specs → 项目规格文件（constitution、specify、clarify、plan）
    + /scripts → 构建脚本
    + /docs → 设计、API、部署、用户手册
    + /reports → 生成的质量与性能报告
4. 注释需描述「为什么」而非仅「做什么」，保持简洁、明确。
5. 代码提交信息（commit message）需遵循以下模板：
    + [模块] 简要说明修改目的。示例： [任务模块] 修复 Compare 模式下 BD-Rate 计算错误

## 四、代码规范
1. **语言风格**
    - Python：遵循 PEP8，命名采用下划线小写（snake_case）。
    - JavaScript/TypeScript：遵循 Airbnb 规范，命名采用驼峰（camelCase）。
2. **结构要求**
    - 每个模块必须包含 README.md 简述功能与依赖。
    - 禁止出现“魔法数字”与硬编码路径。
    - 环境变量统一通过 `.env` 管理，不得在代码中直接写死。
3. **日志与异常**
    - 日志需结构化（JSON 或统一模板），包含时间戳、模块、级别与 trace_id。
    - 所有异常需被捕获并返回明确错误信息，不允许裸 `except`。

## 五、测试与质量保证
1. **测试优先（Test-First）原则**
    - 所有功能实现前必须先编写测试用例。
    - 测试流程：编写测试 → 确认测试失败 → 实现功能 → 验证测试通过。
    - 测试类型：
        + **契约测试（Contract Tests）**：验证接口契约与数据格式。
        + **集成测试（Integration Tests）**：验证用户场景与端到端流程。
        + **单元测试（Unit Tests）**：验证独立组件逻辑（按需编写）。
2. **用户故事独立性**
    - 每个功能需分解为独立可测试的用户故事（User Stories）。
    - 每个用户故事需标注优先级（P1、P2、P3...），并可作为独立 MVP 增量交付。
    - 用户故事之间不应存在强依赖关系，确保可并行开发与测试。
3. **质量门禁**
    - 所有代码提交前必须通过以下检查：
        + 所有测试用例通过。
        + 代码风格检查（linting）通过。
        + 宪法合规性验证通过。
    - 不允许合并未通过质量门禁的代码。

## 六、版本管理与变更控制
1. **语义化版本（Semantic Versioning）**
    - 版本号格式：`MAJOR.MINOR.PATCH`
        + **MAJOR**：不兼容的 API 变更或重大架构调整。
        + **MINOR**：向后兼容的功能新增。
        + **PATCH**：向后兼容的问题修复。
2. **破坏性变更（Breaking Changes）**
    - 所有破坏性变更必须：
        + 提供迁移指南（Migration Guide）。
        + 在变更前发布弃用警告（Deprecation Warning）。
        + 在版本号中体现（MAJOR 版本递增）。
3. **变更日志（Changelog）**
    - 每次版本发布需更新 CHANGELOG.md，记录：
        + 新增功能（Added）
        + 变更内容（Changed）
        + 弃用功能（Deprecated）
        + 移除功能（Removed）
        + 修复问题（Fixed）
        + 安全更新（Security）

## 七、工作流程
### 规格阶段（Specification Phase）
1. **功能描述**：用户提供自然语言描述的功能需求。
2. **规格创建**（`/speckit.specify`）：生成技术无关的规格文档，包含用户故事、需求与成功标准。
3. **质量验证**：根据完整性检查清单验证规格；解决澄清问题（最多 3 个）。
4. **澄清**（`/speckit.clarify`）：识别规格中未明确的部分，并将答案编码回规格文档。
5. **审批门禁**：利益相关者批准规格后方可进入规划阶段。

### 规划阶段（Planning Phase）
1. **实施规划**（`/speckit.plan`）：执行规划工作流，生成设计产物（研究、数据模型、契约、快速入门）。
2. **宪法检查**：验证计划是否符合所有原则；在复杂度跟踪中证明任何违规的合理性。
3. **任务生成**（`/speckit.tasks`）：生成按依赖关系排序、按用户故事分组的任务列表。
4. **一致性分析**（`/speckit.analyze`）：跨产物验证一致性与质量。
5. **审批门禁**：审查计划与任务后方可进入实施阶段。

### 实施阶段（Implementation Phase）
1. **测试创建**：为第一个用户故事编写测试；确认测试失败。
2. **实施**（`/speckit.implement`）：按依赖顺序执行任务。
3. **验证**：确保测试通过；独立验证用户故事。
4. **增量交付**：部署/演示已完成的故事；重复下一个优先级。
5. **完善**：所有故事完成后处理跨领域关注点与文档。

## 八、治理（Governance）
### 修订流程
1. **提案**：记录提议的变更及其理由与影响分析。
2. **审查**：利益相关者审查提案并提供反馈。
3. **批准**：需要项目维护者达成共识。
4. **迁移**：更新所有依赖的模板与文档。
5. **版本递增**：根据语义化版本规则递增宪法版本。

### 版本策略
- **MAJOR**：不兼容的治理变更、原则移除或重新定义。
- **MINOR**：新增原则、扩展章节或实质性新指导。
- **PATCH**：澄清、措辞改进、错别字修复、非语义性优化。

### 合规性审查
- 所有规格文档在规划前必须通过质量验证。
- 所有实施计划在任务生成前必须通过宪法检查。
- 所有拉取请求必须验证适用原则的合规性。
- 当违反原则时，必须在复杂度跟踪章节中证明合理性。
- 宪法优先于所有其他实践与约定。

### 运行时指导
有关特定代理的开发指导与最佳实践，请参阅 `.specify/templates/agent-file-template.md` 及项目特定文档。宪法定义治理与原则；运行时指导提供实际实施细节。

**版本**：1.0.0 | **批准日期**：2025-10-25 | **最后修订**：2025-10-25
