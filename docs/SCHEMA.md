# 统一题目 Schema

主文件为UTF-8 JSONL，一行一道独立任务。权威定义为[item.schema.json](../schema/item.schema.json)，schema_version为1.0.0。

| 模块 | 字段 | 含义 |
|---|---|---|
| 基础 | id / year / category / track / stage | 唯一ID、竞赛周期的预赛年份、数学/非数学、原组别、预赛/决赛 |
| 题目 | title / question / question_latex | 导航标题、中文题面、Unicode数学及有分隔符的LaTeX |
| 分类 | subject / knowledge_points / prerequisites | 主学科、知识点及粗粒度前置知识 |
| 能力 | ability_tags / ability_evidence | 五个英文能力标签及评分证据，可重叠 |
| 难度 | difficulty / difficulty_annotation | L1–L8、逐题理由、标注者、校准状态、不确定性；部分题有五轴描述 |
| 解答 | reference_solution / final_answer | 直接写入JSON的完整参考推导、最终结论；333道均为完整推导 |
| 原解追溯 | solution_source / reference_solution_format | 可选原解PDF、SHA256及原题号；形式固定为inline_full_solution |
| 评分 | scoring_rubric / score_max / critical_errors | 评分点、英文能力、权重和证据，总分4 |
| 核查 | verification_method / verification_status | 已做来源核查及未完成的人类认证状态 |
| 来源 | source / source_occurrences | 原卷、URL、哈希、原题号、从1开始的PDF物理题面页码、跨卷出现记录 |
| 划分 | split / family_id / aliases | dev/validation/test、重复任务族及合并ID |
| 暴露 | model_exposure / generalization_status | 公开原题暴露；迁移仅代理证据 |
| 图形 | assets | 可选PNG、原页码、用途；contains_solution=false |
| 追溯 | notes / statement_sha256 | 规范化说明及实际输入题面的UTF-8哈希 |

例如CMC-2017-FINAL-MathSenior-III中year=2017是第九届预赛周期，决赛实际于2018年举办，不能把ID年份当作决赛日期。原PDF卷头保留实际日期。MathJunior/MathSenior按年级分组保留，不追溯改名数学A/B。

reference_solution完整提供逐步计算或证明，不以PDF路径代替正文。solution_source.pages_one_based定位到原解相应题目的物理页，page_scope标记为item_localized；它是来源追溯，不是对原解数学正确性的保证。题面逐题记录起始页，多页题继续阅读后页。

question仅移去美元分隔符，仍可能含LaTeX命令。question_latex包含规范化中文、Unicode数学与LaTeX，不声称逐字OCR。数学分隔符、下标、上标、花括号会做程序检查；原PDF用于回查排版。

独立填空小题可分开，相依证明子问整题保留。同题跨卷及加强/提示变体只计一次，划分前合并其关联试卷。canonical为计分版本，identical为同题，assisted_variant也包括实质重叠的规范化变体。尚无覆盖所有数学方法同构关系的自动语义去重。

verification_status区分单代理推导核查与来源支持，均未获双专家认证。verification_method中的two_human_reviewers_required_for_certification是未完成事项。

模型回答文件每行使用id、response，允许final_answer及status（ok/error）；题库字段不得混入回答文件。自动评分计划、判断记录与报告的字段和哈希绑定见[AUTO_EVALUATION.md](AUTO_EVALUATION.md)。
