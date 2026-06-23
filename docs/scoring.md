# Scoring Protocol

## Overview

每个模型提交的音频由三个固定 ASR 系统识别。评分脚本在 target-level 上匹配 positive readings 和 negative readings，然后做三 ASR 投票。

```text
TTS audio
  -> ASR-1 transcript
  -> ASR-2 transcript
  -> ASR-3 transcript
  -> target matcher
  -> vote
  -> leaderboard
```

## Single-ASR Decision

对每个 target 和每个 ASR transcript：

1. 先匹配 negative readings，命中则判 `wrong`
2. 否则匹配 positive readings，命中则判 `correct`
3. 都未命中则判 `unknown`

negative 优先，是为了避免同一 transcript 里同时出现解释性文本或重复转写时被误判为正确。

## Three-ASR Vote

| ASR decisions | Final decision |
|---|---|
| at least 2 correct | correct |
| at least 2 wrong | wrong |
| otherwise | unknown |

## Metrics

主指标：

```text
Strict Auto Accuracy = correct / all_auto_evaluable_targets
```

辅助指标：

```text
Resolved Accuracy = correct / (correct + wrong)
Coverage = (correct + wrong) / all_auto_evaluable_targets
Unknown Rate = unknown / all_auto_evaluable_targets
ASR Disagreement Rate = targets with non-unanimous ASR decisions / all_auto_evaluable_targets
```

`unknown` 不从主榜分母中删除。

## Limitations

本协议是自动化 proxy，不等于人工听评金标准。它适合公开、可复现、低成本横评，但对以下情况存在边界：

- 发音含糊导致三个 ASR 都无法确认
- ASR 语言模型将错误读法自动纠正为原文
- 纯同形多音字无法从普通中文转写中判断声调
- positive / negative readings 覆盖不足

