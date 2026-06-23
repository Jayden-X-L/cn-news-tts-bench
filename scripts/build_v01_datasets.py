#!/usr/bin/env python3
"""Build deterministic v0.1 dev and public-test datasets.

The records are synthetic news-style sentences designed for open redistribution.
They preserve high-risk Chinese news TTS surface forms while avoiding reuse of
copyrighted news article text.
"""

from __future__ import annotations

import json
import random
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RNG = random.Random(20260620)


DIGITS = "零一二三四五六七八九"
DOMAINS = {
    "sports_score": "sports",
    "range_hyphen": "general",
    "year_range": "tech",
    "military_model": "military",
    "vehicle_model": "auto",
    "abbreviation": "tech",
    "brand_mixed": "finance",
    "unit_symbol": "auto",
    "percentage": "finance",
    "generation_label": "society",
    "optional_homograph_polyphone": "finance",
}

QUOTAS = {
    "dev": {
        "sports_score": 28,
        "range_hyphen": 20,
        "year_range": 20,
        "military_model": 24,
        "vehicle_model": 16,
        "abbreviation": 26,
        "brand_mixed": 16,
        "unit_symbol": 24,
        "percentage": 14,
        "generation_label": 8,
        "optional_homograph_polyphone": 4,
    },
    "test_public": {
        "sports_score": 112,
        "range_hyphen": 80,
        "year_range": 80,
        "military_model": 96,
        "vehicle_model": 64,
        "abbreviation": 104,
        "brand_mixed": 64,
        "unit_symbol": 96,
        "percentage": 56,
        "generation_label": 32,
        "optional_homograph_polyphone": 16,
    },
}

SPORT_TEAMS = ["海港队", "山城队", "华南队", "北方队", "江城队", "西部队", "滨海队", "东部队"]
SPORT_EVENTS = ["常规赛", "季后赛", "半决赛", "小组赛", "冠军赛", "公开赛"]
PROJECTS = ["城际铁路", "数据中心", "新能源基地", "算力平台", "港口改造", "智慧工厂", "冷链园区"]
CITIES = ["北京", "上海", "广州", "深圳", "重庆", "杭州", "成都", "武汉", "南京", "青岛"]
COMPANIES = ["华辰科技", "远海能源", "星河汽车", "南方电网", "北斗通信", "中科云联", "海川制造"]


def num_zh(n: int) -> str:
    if n < 0 or n > 999:
        raise ValueError(n)
    if n < 10:
        return DIGITS[n]
    if n < 20:
        return "十" + (DIGITS[n % 10] if n % 10 else "")
    if n < 100:
        tens, ones = divmod(n, 10)
        return DIGITS[tens] + "十" + (DIGITS[ones] if ones else "")
    hundreds, rest = divmod(n, 100)
    out = DIGITS[hundreds] + "百"
    if rest == 0:
        return out
    if rest < 10:
        return out + "零" + DIGITS[rest]
    if rest < 20:
        return out + "一" + num_zh(rest)
    return out + num_zh(rest)


def digit_zh(value: int | str) -> str:
    return "".join(DIGITS[int(ch)] for ch in str(value))


def year_zh(year: int) -> str:
    return digit_zh(year)


def decimal_zh(value: str) -> str:
    if "." not in value:
        return num_zh(int(value))
    left, right = value.split(".", 1)
    return num_zh(int(left)) + "点" + digit_zh(right)


def magnitude_year_zh(year: int) -> str:
    if not 2000 <= year <= 2099:
        return year_zh(year)
    rest = year - 2000
    if rest == 0:
        return "两千"
    if rest < 10:
        return "两千零" + num_zh(rest)
    if rest < 20:
        return "两千零" + num_zh(rest)
    return "两千零" + num_zh(rest)


def target(span: str, category: str, group: str, positives: list[str], negatives: list[str], rationale: str, auto: bool = True) -> dict:
    return {
        "span": span,
        "category": category,
        "group": group,
        "positive_readings": dedupe(positives),
        "negative_readings": dedupe(negatives),
        "auto_evaluable": auto,
        "rationale": rationale,
    }


def dedupe(values: list[str]) -> list[str]:
    seen = set()
    out = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def add_offsets(text: str, targets: list[dict]) -> list[dict]:
    cursor = 0
    out = []
    for t in targets:
        span = t["span"]
        idx = text.find(span, cursor)
        if idx < 0:
            idx = text.find(span)
        if idx < 0:
            raise ValueError(f"span {span!r} not found in {text!r}")
        item = dict(t)
        item["start"] = idx
        item["end"] = idx + len(span)
        out.append(item)
        cursor = idx + len(span)
    return out


def make_record(split: str, index: int, category: str, text: str, targets: list[dict], metadata: dict) -> dict:
    record_id = f"{'dev' if split == 'dev' else 'test'}_{index:06d}"
    targets = add_offsets(text, targets)
    for i, t in enumerate(targets, 1):
        t["target_id"] = f"{record_id}_t{i}"
    return {
        "id": record_id,
        "split": split,
        "source": "synthetic",
        "domain": DOMAINS[category],
        "text": text,
        "targets": targets,
        "metadata": {
            "generator": "scripts/build_v01_datasets.py",
            "generator_seed": 20260620,
            "template_category": category,
            **metadata,
        },
    }


def sports_score_case(i: int) -> tuple[str, list[dict], dict]:
    a = RNG.choice([81, 89, 96, 101, 104, 108, 112, 117, 121, 126])
    b = a - RNG.choice([1, 2, 3, 4, 5, 7])
    c, d = RNG.choice([(3, 2), (4, 3), (2, 1), (1, 0), (11, 9), (21, 19)])
    team_a, team_b = RNG.sample(SPORT_TEAMS, 2)
    event = RNG.choice(SPORT_EVENTS)
    span1 = f"{a}-{b}"
    span2 = f"{c}-{d}"
    text = f"{team_a}在第{i}轮{event}中以{span1}险胜{team_b}，系列赛总比分来到{span2}。"
    targets = [
        target(
            span1,
            "sports_score",
            "number",
            [f"{num_zh(a)}比{num_zh(b)}", f"{digit_zh(a)}比{digit_zh(b)}"],
            [f"{num_zh(a)}到{num_zh(b)}", f"{num_zh(a)}负{num_zh(b)}", f"{digit_zh(a)}到{digit_zh(b)}", f"{digit_zh(a)}负{digit_zh(b)}"],
            "体育比分中的连字符应读作比。",
        ),
        target(
            span2,
            "sports_score",
            "number",
            [f"{num_zh(c)}比{num_zh(d)}"],
            [f"{num_zh(c)}到{num_zh(d)}", f"{num_zh(c)}负{num_zh(d)}", f"{num_zh(c)}减{num_zh(d)}"],
            "体育比分中的连字符应读作比。",
        ),
    ]
    return text, targets, {"template_id": "sports_score_v1", "ordinal": i}


def range_hyphen_case(i: int) -> tuple[str, list[dict], dict]:
    a = RNG.choice([2, 3, 4, 5, 6, 8, 10, 12, 15])
    b = a + RNG.choice([1, 2, 3, 5])
    unit = RNG.choice(["周", "天", "个工作日", "个月", "分钟", "小时"])
    project = RNG.choice(PROJECTS)
    city = RNG.choice(CITIES)
    span = f"{a}-{b}"
    text = f"{city}{project}第{i}标段预计将在{span}{unit}内完成关键节点验收。"
    targets = [
        target(
            span,
            "range_hyphen",
            "number",
            [f"{num_zh(a)}到{num_zh(b)}", f"{num_zh(a)}至{num_zh(b)}"],
            [f"{num_zh(a)}负{num_zh(b)}", f"{num_zh(a)}减{num_zh(b)}"],
            "非比分语境中的连字符表示区间。",
        )
    ]
    return text, targets, {"template_id": "range_hyphen_v1", "ordinal": i}


def year_range_case(i: int) -> tuple[str, list[dict], dict]:
    start = RNG.choice([2024, 2025, 2026, 2027, 2028, 2029])
    end = start + RNG.choice([1, 2, 3])
    company = RNG.choice(COMPANIES)
    topic = RNG.choice(["AI服务器", "新能源车", "储能电站", "国产芯片", "低空经济", "机器人"])
    span = f"{start}-{end}年"
    text = f"{company}第{i}版规划预计{span}{topic}需求保持增长，供应链投资将继续加码。"
    targets = [
        target(
            span,
            "year_range",
            "number",
            [f"{year_zh(start)}到{year_zh(end)}年", f"{year_zh(start)}至{year_zh(end)}年"],
            [f"{magnitude_year_zh(start)}到{magnitude_year_zh(end)}年", f"{year_zh(start)}负{year_zh(end)}年"],
            "年份区间应按年份逐位读，并体现区间关系。",
        )
    ]
    return text, targets, {"template_id": "year_range_v1", "ordinal": i}


MILITARY_MODELS = [
    ("苏", 27, ""),
    ("苏", 35, ""),
    ("歼", 10, "C"),
    ("歼", 16, ""),
    ("歼", 20, ""),
    ("运", 20, "B"),
    ("伊尔", 76, ""),
    ("直", 20, ""),
    ("轰", 6, "K"),
    ("F", 35, ""),
    ("F", 16, ""),
    ("B", 2, ""),
    ("C", 130, ""),
]


def model_readings(prefix: str, num: int, suffix: str) -> list[str]:
    return [f"{prefix}{num_zh(num)}{suffix}", f"{prefix}{digit_zh(num)}{suffix}"]


def military_model_case(i: int) -> tuple[str, list[dict], dict]:
    first, second = RNG.sample(MILITARY_MODELS, 2)
    spans = [f"{p}-{n}{s}" for p, n, s in [first, second]]
    text = f"第{i}次演训期间，{spans[0]}与{spans[1]}完成编队巡航和低空突防课目。"
    targets = []
    for span, (prefix, num, suffix) in zip(spans, [first, second]):
        targets.append(target(
            span,
            "military_model",
            "entity",
            model_readings(prefix, num, suffix),
            [f"{prefix}负{num_zh(num)}{suffix}", f"{prefix}负{digit_zh(num)}{suffix}", f"{prefix}杠{num_zh(num)}{suffix}", f"{prefix}减{num_zh(num)}{suffix}"],
            "军事型号中的连字符不读作负号、杠或减号。",
        ))
    return text, targets, {"template_id": "military_model_v1", "ordinal": i}


VEHICLE_MODELS = [
    ("问界", "M9", ["M九", "M9"], ["米九"]),
    ("小鹏", "G6", ["G六", "G6"], ["鸡六"]),
    ("理想", "L9", ["L九", "L9"], ["艾勒九"]),
    ("小米", "SU7", ["S U 七", "SU七", "SU7"], ["速七"]),
    ("蔚来", "ET5", ["E T 五", "ET五", "ET5"], ["一体五"]),
    ("宝马", "i3", ["i三", "I三", "i3"], ["爱三"]),
    ("奥迪", "Q6", ["Q六", "Q6"], ["球六"]),
]


def vehicle_model_case(i: int) -> tuple[str, list[dict], dict]:
    brand, model, positives, negatives = RNG.choice(VEHICLE_MODELS)
    metric = RNG.choice(["交付量", "订单量", "试驾预约", "门店客流"])
    city = RNG.choice(CITIES)
    span = model
    text = f"第{i}周数据显示，{brand}{span}在{city}市场热度回升，{metric}环比继续增加。"
    targets = [
        target(
            span,
            "vehicle_model",
            "entity",
            positives,
            negatives,
            "汽车型号中的字母数字组合应保留车型读法。",
        )
    ]
    return text, targets, {"template_id": "vehicle_model_v1", "ordinal": i}


ABBREVIATIONS = [
    ("AI", ["AI", "A I"], ["人工智能"], "AI应用"),
    ("CEO", ["CEO", "C E O"], ["首席执行官"], "公司管理层"),
    ("GDP", ["GDP", "G D P"], ["国内生产总值"], "宏观数据"),
    ("ETF", ["ETF", "E T F"], ["交易型开放式指数基金"], "基金产品"),
    ("IPO", ["IPO", "I P O"], ["首次公开募股"], "资本市场"),
    ("A股", ["A股", "A 股"], ["一个股", "啊股"], "市场行情"),
    ("C919", ["C九一九", "C919"], ["C九百一十九"], "国产大飞机"),
    ("PC", ["PC", "P C"], ["个人电脑"], "消费电子"),
]


def abbreviation_case(i: int) -> tuple[str, list[dict], dict]:
    span, positives, negatives, topic = RNG.choice(ABBREVIATIONS)
    company = RNG.choice(COMPANIES)
    verb = RNG.choice(["带动", "影响", "支撑", "推动", "改变"])
    text = f"{company}第{i}项业务显示，{span}相关业务正在{verb}{topic}的新一轮增长。"
    targets = [
        target(
            span,
            "abbreviation",
            "abbreviation",
            positives,
            negatives,
            "新闻中的英文缩写应按原缩写读出，不应展开为中文释义。",
        )
    ]
    return text, targets, {"template_id": "abbreviation_v1", "ordinal": i}


BRAND_MIXED = [
    ("88VIP", ["八八VIP", "八十八VIP", "八八V I P", "八十八V I P"], ["八八贵宾", "八十八贵宾"], "会员权益"),
    ("618", ["六一八"], ["六百一十八"], "年中促销"),
    ("3·15", ["三一五"], ["三点一五"], "消费者权益"),
    ("11·11", ["双十一", "十一十一"], ["十一点十一"], "电商大促"),
    ("Sora2", ["Sora二", "Sora2"], ["索拉二"], "视频模型"),
    ("4S店", ["四S店", "四 S 店"], ["四个店"], "汽车零售"),
]


def brand_mixed_case(i: int) -> tuple[str, list[dict], dict]:
    span, positives, negatives, topic = RNG.choice(BRAND_MIXED)
    city = RNG.choice(CITIES)
    text = f"{city}多家机构围绕{span}推出第{i}批新活动，{topic}服务成为关注重点。"
    targets = [
        target(
            span,
            "brand_mixed",
            "entity",
            positives,
            negatives,
            "品牌或活动名中的数字、字母、符号组合应按固定名称读出。",
        )
    ]
    return text, targets, {"template_id": "brand_mixed_v1", "ordinal": i}


UNITS = [
    ("kW", "千瓦", ["K W", "凯瓦"], [80, 120, 150, 230, 430, 640], ["峰值功率", "最大功率"]),
    ("MW", "兆瓦", ["M W", "米瓦"], [50, 100, 300, 750, 900], ["装机规模", "并网容量"]),
    ("GW", "吉瓦", ["G W"], [2, 3, 6, 12, 20], ["装机规模", "规划容量"]),
    ("N·m", "牛米", ["恩点米", "N点M"], [190, 310, 450, 620, 780], ["峰值扭矩", "最大扭矩"]),
    ("km/h", "公里每小时", ["K M每H", "千米斜杠小时"], [80, 100, 120, 160, 200], ["设计时速", "最高时速"]),
]


def unit_symbol_case(i: int) -> tuple[str, list[dict], dict]:
    unit, reading, wrong_units, values, metrics = RNG.choice(UNITS)
    value = RNG.choice(values)
    span = f"{value}{unit}"
    metric = RNG.choice(metrics)
    text = f"第{i}组项目披露的{metric}达到{span}，相关设备已经进入批量验证阶段。"
    positives = [f"{num_zh(value)}{reading}", f"{digit_zh(value)}{reading}"]
    negatives = [f"{num_zh(value)}{wrong}" for wrong in wrong_units]
    targets = [
        target(
            span,
            "unit_symbol",
            "unit",
            positives,
            negatives,
            "新闻中的工程单位应读成常用中文单位名。",
        )
    ]
    return text, targets, {"template_id": "unit_symbol_v1", "ordinal": i}


def percentage_case(i: int) -> tuple[str, list[dict], dict]:
    value = RNG.choice(["0.5", "1.8", "2.4", "3.5", "5.0", "7.2", "12.6", "17.5", "38.4", "68"])
    span = f"{value}%"
    company = RNG.choice(COMPANIES)
    metric = RNG.choice(["营收", "净利润", "毛利率", "出货量", "市场份额", "研发投入"])
    text = f"{company}第{i}号公告披露，{metric}同比增长{span}，管理层预计下季度仍将改善。"
    read = decimal_zh(value)
    targets = [
        target(
            span,
            "percentage",
            "number",
            [f"百分之{read}"],
            [f"{read}百分号", f"百分号{read}"],
            "百分号应前置读作百分之。",
        )
    ]
    return text, targets, {"template_id": "percentage_v1", "ordinal": i}


GENERATION_LABELS = [
    ("70后", ["七零后"], ["七十后"]),
    ("80后", ["八零后"], ["八十后"]),
    ("90后", ["九零后"], ["九十后"]),
    ("95后", ["九五后"], ["九十五后"]),
    ("00后", ["零零后"], ["零十后"]),
]


def generation_label_case(i: int) -> tuple[str, list[dict], dict]:
    span, positives, negatives = RNG.choice(GENERATION_LABELS)
    field = RNG.choice(["消费", "创业", "招聘", "文旅", "智能硬件", "社区服务"])
    text = f"第{i}轮调研显示，{span}用户正在成为{field}市场的重要增量人群。"
    targets = [
        target(
            span,
            "generation_label",
            "number",
            positives,
            negatives,
            "年龄代际标签应逐位读，不应按普通两位数读。",
        )
    ]
    return text, targets, {"template_id": "generation_label_v1", "ordinal": i}


POLYPHONE_CASES = [
    ("重庆银行行长表示，小微贷款投放节奏将保持稳定。", "重庆", ["chong2qing4"], ["zhong4qing4"], "地名重庆读 chong2 qing4。"),
    ("重庆银行行长表示，小微贷款投放节奏将保持稳定。", "行长", ["hang2zhang3"], ["xing2chang2"], "银行职务行长读 hang2 zhang3。"),
    ("新能源订单增长明显，供应链企业正在追加排产。", "增长", ["zeng1zhang3"], ["zeng1chang2"], "增长读 zhang3。"),
    ("供给改善后，部分原材料价格开始回落。", "供给", ["gong1ji3"], ["gong4gei3"], "供给读 gong1 ji3。"),
]


def optional_homograph_polyphone_case(i: int) -> tuple[str, list[dict], dict]:
    text, span, positives, negatives, rationale = RNG.choice(POLYPHONE_CASES)
    text = f"第{i}条快讯称，{text}"
    targets = [
        target(
            span,
            "optional_homograph_polyphone",
            "polyphone",
            positives,
            negatives,
            rationale + "普通 ASR 文本不可稳定判断声调，v0.1 不进入主榜。",
            auto=False,
        )
    ]
    return text, targets, {"template_id": "optional_homograph_polyphone_v1", "ordinal": i}


GENERATORS = {
    "sports_score": sports_score_case,
    "range_hyphen": range_hyphen_case,
    "year_range": year_range_case,
    "military_model": military_model_case,
    "vehicle_model": vehicle_model_case,
    "abbreviation": abbreviation_case,
    "brand_mixed": brand_mixed_case,
    "unit_symbol": unit_symbol_case,
    "percentage": percentage_case,
    "generation_label": generation_label_case,
    "optional_homograph_polyphone": optional_homograph_polyphone_case,
}


def build_split(split: str) -> list[dict]:
    records = []
    categories = []
    for category, count in QUOTAS[split].items():
        categories.extend([category] * count)
    RNG.shuffle(categories)
    per_category_index: Counter[str] = Counter()
    for idx, category in enumerate(categories, 1):
        per_category_index[category] += 1
        text, targets, metadata = GENERATORS[category](per_category_index[category])
        records.append(make_record(split, idx, category, text, targets, metadata))
    return records


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def summarize(rows: list[dict]) -> dict:
    category_records = Counter(row["metadata"]["template_category"] for row in rows)
    target_categories = Counter()
    target_groups = Counter()
    auto_targets = 0
    optional_targets = 0
    for row in rows:
        for t in row["targets"]:
            target_categories[t["category"]] += 1
            target_groups[t.get("group", "other")] += 1
            if t.get("auto_evaluable", True):
                auto_targets += 1
            else:
                optional_targets += 1
    return {
        "records": len(rows),
        "targets": auto_targets + optional_targets,
        "auto_evaluable_targets": auto_targets,
        "optional_targets": optional_targets,
        "record_categories": dict(sorted(category_records.items())),
        "target_categories": dict(sorted(target_categories.items())),
        "target_groups": dict(sorted(target_groups.items())),
    }


def main() -> int:
    dev = build_split("dev")
    test_public = build_split("test_public")
    write_jsonl(DATA_DIR / "dev.jsonl", dev)
    write_jsonl(DATA_DIR / "test_public.jsonl", test_public)
    summary = {
        "version": "v0.1",
        "generated_at": "2026-06-20",
        "generator_seed": 20260620,
        "license_note": "Synthetic news-style text for open benchmark development.",
        "dev": summarize(dev),
        "test_public": summarize(test_public),
        "total": summarize(dev + test_public),
    }
    (DATA_DIR / "dataset_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
