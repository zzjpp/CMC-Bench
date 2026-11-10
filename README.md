# CMC-Bench

全国大学生数学竞赛（CMC）中文数学能力评测集。**333道去重题、8层结构难度、10个学科**。包含212道预赛题、121道决赛题，竞赛周期年份覆盖2009–2020及2025。

题目均有完整中文文本、统一Schema、能力标签、评分点和可回查的原卷。**333道题的完整参考推导均直接写入data/items.jsonl**，reference_solution_format统一为inline_full_solution；评分时不需要另行从PDF提取答案。原解PDF作为可追溯材料保留。

难度依据知识、计算、推理、方法发现和证明要求标注，**尚未通过学生或模型作答数据校准，参考解答也尚未完成双数学专家认证**。当前为可复现的研究评测集；不是CMC官方评测或隐藏测试集。

## 八层难度

| 层级 | 含义 | dev | validation | test | 总计 |
|---|---|---:|---:|---:|---:|
| L1 | 直接应用 | 7 | 3 | 2 | 12 |
| L2 | 常规计算 | 35 | 8 | 16 | 59 |
| L3 | 多步应用 | 29 | 7 | 9 | 45 |
| L4 | 综合推理 | 51 | 9 | 20 | 80 |
| L5 | 关键技巧 | 36 | 8 | 12 | 56 |
| L6 | 深入证明 | 24 | 5 | 14 | 43 |
| L7 | 复杂构造与综合 | 20 | 3 | 8 | 31 |
| L8 | 高阶挑战 | 5 | 1 | 1 | 7 |
| 合计 | | **207** | **44** | **82** | **333** |

L1从标准公式和直接计算开始，逐步增加方法组合、证明跨度、构造与全局论证，L8包含高阶挑战。高年级决赛的基础题也标为低层；不用组别或年份替代难度。每题保留标注理由，细层之外同时报告L1–L2、L3–L4、L5–L6、L7–L8四个粗层。判定规则和锚题见[CALIBRATION.md](docs/CALIBRATION.md)。

最高层样本较少，test中L8仅1题，单层结果须附分母。层级数量不代表经验精度。

## 学科与能力

| 学科 | 题数 |
|---|---:|
| 解析几何 | 29 |
| 高等代数 | 49 |
| 数学分析 | 210 |
| 常微分方程 | 9 |
| 数值分析 | 6 |
| 概率统计 | 6 |
| 复分析 | 6 |
| 实分析 | 6 |
| 微分几何 | 6 |
| 抽象代数 | 6 |

| 能力 | 标准英文标签 | 考察内容 | 涉及题数 |
|---|---|---|---:|
| 数学知识掌握 | Mathematical Knowledge | 定义、定理、概念及适用条件 | 333 |
| 数学计算能力 | Mathematical Computation | 导数、积分、代数与复杂计算 | 166 |
| 数学推理能力 | Mathematical Reasoning | 多步骤推导、条件组合与边界 | 318 |
| 数学证明能力 | Mathematical Proof | 严谨完整的证明和全部子问 | 169 |
| 数学迁移能力 | Mathematical Generalization | 方法在新表示或结构中的应用代理 | 36 |

能力标签允许重叠，得分按对应评分点计算，不重复使用整题总分。迁移有逐题方法证据，但没有受控迁移实验。整体分数受分析类题占比较高的影响，不代表本科数学课程的均衡抽样。

## 数据与来源

```text
data/items.jsonl              完整题库与评分侧参考
data/inputs/{split}.jsonl     只含ID、题面、可选图形的模型输入
data/metadata.jsonl           评分端分类/来源元数据
schema/item.schema.json       统一JSON Schema
splits/                      dev / validation / test的固定ID
sources/pdf/                 138份原卷与参考资料PDF
sources/manifest.json        路径、来源类型、页数、摘要
sources/coverage.json        结构化覆盖与隔离清单
latex/questions.tex          可编辑题目册源文件
assets/                      原题可选PNG图形
qa/                          选定数学核查结果
checksums.json               发布内容哈希
```

历史PDF收集自[IceFerryLing/Math_competition](https://github.com/IceFerryLing/Math_competition)，保留上游路径、Git blob SHA1与本地SHA256。第1–15届共126份历史PDF已归档，其中32份历史题卷有本版结构化条目；**PDF归档不计作题目数**。主要结构化第1–10届预赛、部分决赛及2019/2020/2025题。2021–2024等周期尚未结构化，不宣称穷尽全部历年CMC试题。

其他题源来自[华东师范大学2019资料页](https://math.ecnu.edu.cn/llin/20191026.HTM)、[2020资料页](https://math.ecnu.edu.cn/llin/20201128.HTM)及[大学生数学竞赛网下载目录](https://www.cmathc.org.cn/stxz/)等转载。社区PDF没有被标为官方认证。原权利归属见[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

独立填空可单列；相依证明子问整题保留。9处跨卷同题或重叠任务合并，均只计一道规范题。错误或歧义版本隔离后不计入333题。原卷页码、核查状态和去重规则见[QUALITY.md](docs/QUALITY.md)。完整索引见[CATALOG.md](CATALOG.md)，统计见[statistics.json](statistics.json)。

## 使用与复现

核心工具只需Python 3.10+标准库，不需要API密钥：

```bash
python tools/build.py
python tools/check.py
python tools/prepare_run.py --split validation --model MODEL_VERSION --output runs/validation_requests.jsonl
```

build确定性导出333题、划分、统计和LaTeX。validate检查Schema、源文件/题面/发布哈希、完整解答及引用、唯一ID与别名、题族/整卷划分、八级覆盖及输入隔离。prepare_run只准备请求，不调用模型或产生计费。

自动流程可读取已有回答，也提供只读取题面文件的HTTP解题运行器：

```bash
python tools/run_solver.py --inputs data/inputs/test.jsonl --endpoint https://YOUR_HOST/v1/chat/completions --model SOLVER_MODEL --output-dir runs/solver
python tools/auto_evaluate.py prepare runs/solver/responses.jsonl --split test --output runs/judge_plan.json
python tools/auto_evaluate.py judge runs/judge_plan.json --endpoint https://YOUR_HOST/v1/chat/completions --model JUDGE_MODEL --output-dir runs/judge
```

端点和模型由使用者指定，密钥从CMC_API_KEY环境变量读取。judge会调用外部模型；prepare和测试无需密钥。每题两次独立评分，逐评分点一致时给出自动暂定分数，分歧、接口失败及题面疑问保留待复核；缺答计零，固定分母不变。报告包含难度、学科、能力得分边界和实际接口记录。**自动评分不是形式化证明验证，也不等于双专家认证**。格式、断点续跑和隔离方法见[AUTO_EVALUATION.md](docs/AUTO_EVALUATION.md)。

完成双人审阅后，可另行汇总人工裁定分数：

```bash
python tools/evaluate.py runs/test_grades.jsonl --split test --output runs/test_report.json
```

指标包括完整正确率、归一化分数、八级宏平均、四个粗层、能力评分点得分和样本数。缺题、重复、非裁定评分或严重错误与满分冲突会被拒绝。详见[EVALUATION.md](docs/EVALUATION.md)。dev用于调试，validation用于模型选择，test用于冻结方案后的比较；关联重复题的整卷先并组再划分。

**模型环境仅挂载data/inputs和必要assets。** 完整题库、元数据、解答、原PDF和题源URL属于评分端；实际运行器必须执行隔离。公开test不能保证无预训练污染。

可选数学抽查需SymPy（本次1.14.0）：

```bash
python tools/audit_math.py
```

数学审计含45项选定数学检查，不是333题的完整证明认证。测试使用合成回答与本机模拟HTTP服务，不访问外部模型；合成测试不是模型成绩。没有预置模型成绩或经验难度校准结果。原PDF重新获取与解析工具见[sources/README.md](sources/README.md)，核心复现无需联网或PDF解析库。

更多说明：[数据卡](DATASET_CARD.md)、[字段定义](docs/SCHEMA.md)。软件为MIT许可；第三方题目、原解、PDF及图形未核实开放再许可，代码许可不覆盖这些材料。

## 代码包

data/items.jsonl是唯一完整题库；build只从此文件导出输入、划分、统计、目录和LaTeX。构建和评测统一使用这一入口。

```bash
python tools/package.py
```

生成dist/CMC-Bench.zip及SHA256文件。代码包按checksums.json收录发布文件，包含333题、138份PDF、图形、工具和测试；不收录Git目录、缓存、私有配置或模型运行输出。解压后在CMC-Bench目录运行python tools/check.py即可验证。
