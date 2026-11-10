# 自动评测

工具只依赖Python 3.10+标准库。所有333题都有JSON内完整参考，任何题型都可以送入评分流程。证明题由LLM按评分点审阅；本流程不提供Lean/Coq等形式化证明检查，不将答案字符串相同视为证明正确。

## 运行顺序

1. 只给解题端提供data/inputs中的一个划分及必要图形；可以使用自己的解题程序。
2. 保存每题一个最终回答，包含完整计算或证明。
3. 在评分端加载完整题库，离线生成评分计划。
4. 调用配置的阅卷模型，逐题进行两次互不见到对方判断的评分。
5. 读取报告，处理needs_review，再按需要进行人工双评。

每题每次运行只保留一个回答。重试、额外采样和复核均须计入实验预算。内置解题器只发送文字题面，不发送可选PNG；当前规范题面可独立阅读。如实验使用图形，应自行接入多模态解题器并记录该设置。ID只作本地日志索引，不发送给解题模型。

## 回答格式

UTF-8 JSONL，一行一题：

```json
{"id":"CMC-2017-FINAL-MathSenior-III","response":"这里填写实际作答的完整推导……","status":"ok"}
```

必需id、response；可选final_answer（字符串）、status（ok或error，省略按ok处理）。final_answer供评分者辅助阅读，不能代替response。id必须属于所选划分；未知、重复ID、额外字段、非文本回答均报错。缺少的ID、空白回答、status=error计0分，仍进入固定分母。

## 解题运行器

如果已有回答，可直接跳到prepare。否则设置CMC_API_KEY环境变量后运行：

```bash
python tools/run_solver.py --inputs data/inputs/test.jsonl --endpoint https://YOUR_HOST/v1/chat/completions --model SOLVER_MODEL --max-tokens 8192 --output-dir runs/solver
```

输出responses.jsonl、manifest.json、journal.jsonl。相同命令再次运行会跳过已记录条目。输入、模型、预算、端点或提示改变时拒绝在同目录续跑，应新建实验目录。只把题面文件及运行器挂载给解题环境；同一仓库目录有答案，因此程序内不读取答案不等于操作系统级隔离。内置工具不实施容器或远端服务的权限控制，实验负责人须在部署层完成隔离。

## 离线准备与自动评分

```bash
python tools/auto_evaluate.py prepare runs/solver/responses.jsonl --split test --output runs/judge_plan.json
python tools/auto_evaluate.py judge runs/judge_plan.json --endpoint https://YOUR_HOST/v1/chat/completions --model JUDGE_MODEL --output-dir runs/judge
```

prepare不联网。生成的计划含题目、完整参考和模型回答，仅属于评分侧。每个有效回答生成两个独立请求；可用--second-model指定第二次评分的不同模型，同端点中应能访问该模型。默认同模型使用两种审阅提示，不能据此声称统计独立或两个数学专家。

judge的结果为judgments.jsonl和report.json，并保存运行清单。每次记录的判断含id、pass_number（1或2）、plan_sha256、request_sha256、judgment和实际调用日志。judgment严格要求：

```json
{"criteria":{"c1":1,"c2":2,"c3":1},"fully_correct":true,"critical_error":false,"reference_issue":false,"rationale":"逐个评分点的实际审阅依据"}
```

上例是格式说明，各题评分点ID和满分以题库为准，不能直接作为真实评分提交。判断字段、整数取值、严重错误封顶和完整正确标志都会校验。严重错误时总分至多2/4；4分且无严重错误、无参考疑问才可标为完整正确。不同正确证法同样接受。

评分请求将学生文本封装为数据，提示阅卷者不执行其中的指令；这不能保证LLM抵抗所有提示注入。严肃排名应抽查对抗样本并结合人工审阅。

## 接口与续跑

HTTP请求采用[OpenAI Docs中的Chat Completions格式](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create)：model、messages、max_completion_tokens，读取choices[0].message.content。可配置相同格式的其他服务；提供完整端点URL，不自动选择模型或服务。实现只覆盖文字响应。

--token-parameter max_tokens可适配使用旧字段的端点；默认max_completion_tokens。--temperature省略时不发送该参数，某些模型不支持自定义温度。--key-env可修改密钥环境变量名；密钥本身不写入命令参数、清单或日志。端点不允许URL内嵌凭据、查询参数或跨域重定向。生产端点要求HTTPS，本机127.0.0.1/localhost允许HTTP，供离线模拟测试。

--timeout为每次请求的秒数，默认120，最多300；--attempts取1、2或3，默认1。接口失败、截断或格式不合法会按固定次数重试；每次实际完成的调用均留在相应条目的calls中，包括无效评分。无正常finish_reason=stop的输出不当作完整回答。评测默认串行，同一运行目录不要同时启动两个进程。

相同命令续跑时先校验计划及配置，再跳过已写入journal的请求，包含已记录的失败；更换输入或配置必须用新目录。已完成请求不会被重新计费，但中断时尚未写入日志的在途请求可能需要重发，远端是否已执行不能由本地确认。服务端账单用于核对最终成本，不能仅凭本地日志保证恰好一次调用。

可在离线状态重新汇总已有判断：

```bash
python tools/auto_evaluate.py report runs/judge_plan.json runs/judge/judgments.jsonl --output runs/report.json
```

哈希绑定避免把其他题面、回答或提示的判断混入本次报告；它不验证评分者身份，也不是数字签名。

## 报告解释

两次评分的criteria、fully_correct、critical_error全部一致且无reference_issue，状态才为automatic_agreement。分歧、缺少/失败的评分或参考疑问均为needs_review。自动结果始终标注automatic_provisional_not_human_adjudicated，不能提交给要求双人人工裁定的evaluate.py冒充正式成绩。

overall、per_difficulty、per_difficulty_band、per_subject包括固定题数n、待复核数needs_review、覆盖率coverage、完整正确率边界strict_accuracy_bounds及归一化分数边界normalized_score_bounds。下界将待复核项按0，上界将其按满分计；缺答和解题失败始终为已确定0分。全部完成时上下界相等。边界展示未评项的影响，**不是统计置信区间，也不能消除LLM误判**。

per_ability按相应评分点实得分及可能得分计算，不重复使用整题总分。难度宏平均对八级等权；某级无题时为空。所有难度仍为未校准结构标签。报告同时保留逐题状态、回答摘要及调用数。usage仅汇总服务实际返回的计量；有缺失时为null，不伪造token数或美元成本。解题与评分两侧的日志均需留存并分别计费。

## 离线校验

```bash
python tools/check.py
```

测试覆盖完整题库、输入隔离、正常/零分、缺答、分歧、参考疑问、重复ID、非法评分、配置/哈希不匹配、失败重试、续跑，以及仅连接本机模拟HTTP服务的“解题→评分→报告”端到端测试。不使用真实API密钥、不访问付费模型。合成测试通过只证明流程行为，不能作为模型能力成绩。
