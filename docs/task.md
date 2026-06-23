# Task Definition

CN-NewsTTS Bench 评估中文新闻裸 TTS 模型的 target-level 读法准确率。

## 输入

每条样本是一段原始中文新闻短句或短段落，保留原始表面形式：

- `117-116`
- `苏-27`
- `80后`
- `3.5%`
- `N·m`
- `AI`

## 输出

参评系统需要为每条样本生成一段音频。

## Raw Model Track

v0.1 只定义 Raw Model Track，并使用：

- `data/dev.jsonl`：200 条，开发调试
- `data/test_public.jsonl`：800 条，公开排行榜

允许：

- TTS 模型自身内部 frontend
- 模型默认 normalization
- 模型默认推理配置

不允许：

- 外部规则前端
- LLM 改写
- 手工修正输入文本
- SSML
- 针对测试集编写的 pronunciation hint

## 主榜范围

主榜只包含普通 ASR 文本可区分的读法目标。

纳入：

- 比分和连字符
- 军事型号和车辆型号
- 百分数、小数、年份区间
- 英文缩写和中英混排品牌
- 单位符号
- 年龄代际标签

暂不纳入主榜：

- 纯同形多音字，例如 `重庆`、`行长`、`增长`

原因是普通 ASR 转写通常仍输出同一个汉字，无法仅凭文本判断真实声调。此类样本可进入 optional audit 或未来的 phoneme/pinyin evaluator。
