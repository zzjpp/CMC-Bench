# 来源资料

manifest.json统一登记138份PDF，文件位于pdf/，以source_id命名。档案标识与竞赛题号分开；每题source记录题面起始物理页码和原题号，solution_source记录对应完整原解。第三方材料权利见仓库根目录THIRD_PARTY_NOTICES.md。

coverage.json区分归档材料、包含结构化题目的题卷与不计分材料，PDF份数不等于计分题数。题库共333道规范任务。

可选来源校验/缺失文件获取：

```bash
python tools/collect_sources.py
```

已存在的PDF仅校验，不重新下载；缺失文件从清单URL获取并校验SHA256。正常构建、验证、评分和打包使用仓库内材料及Python标准库，不需联网。上游URL可能变化，字节摘要可确认文件身份，不能认证数学内容或官方地位。
