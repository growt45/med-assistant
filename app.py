from __future__ import annotations

from datetime import date, datetime, timedelta
from math import ceil

import streamlit as st


st.set_page_config(
    page_title="慢病用药小管家",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

TIME_SLOTS = {
    "早晨": {"time": "08:00"},
    "中午": {"time": "13:00"},
    "晚上": {"time": "20:00"},
}

DEFAULT_PARSE_RESULT = [
    {
        "name": "二甲双胍",
        "strength": "500mg",
        "dose": "1片",
        "frequency": "每日2次，餐后服用",
        "duration": 30,
        "times": ["08:00", "20:00"],
        "inventory": 24,
        "daily_doses": 2,
        "follow_up_days": 30,
    },
    {
        "name": "氨氯地平",
        "strength": "5mg",
        "dose": "1片",
        "frequency": "每日1次，早晨服用",
        "duration": 30,
        "times": ["08:00"],
        "inventory": 18,
        "daily_doses": 1,
        "follow_up_days": 45,
    },
]

SIMULATED_PATIENTS = {
    "刘芳": {
        "condition": "2型糖尿病 / 高血压",
        "start_date": date(2026, 4, 10),
        "follow_up_date": date(2026, 5, 25),
        "prescription_text": "二甲双胍 500mg 每日2次，餐后服用；氨氯地平 5mg 每日1次，早晨服用。",
        "parsed_prescription": [
            {"name": "二甲双胍", "strength": "500mg", "dose": "1片", "frequency": "每日2次，餐后服用", "duration": 30, "times": ["08:00", "20:00"], "inventory": 24, "daily_doses": 2, "follow_up_days": 30},
            {"name": "氨氯地平", "strength": "5mg", "dose": "1片", "frequency": "每日1次，早晨服用", "duration": 30, "times": ["08:00"], "inventory": 18, "daily_doses": 1, "follow_up_days": 45},
        ],
    },
    "王建国": {
        "condition": "高血压 / 高血脂",
        "start_date": date(2026, 3, 28),
        "follow_up_date": date(2026, 5, 18),
        "prescription_text": "缬沙坦 80mg 每日1次，早晨服用；阿托伐他汀 20mg 每日1次，晚间服用。",
        "parsed_prescription": [
            {"name": "缬沙坦", "strength": "80mg", "dose": "1片", "frequency": "每日1次，早晨服用", "duration": 30, "times": ["08:00"], "inventory": 20, "daily_doses": 1, "follow_up_days": 30},
            {"name": "阿托伐他汀", "strength": "20mg", "dose": "1片", "frequency": "每日1次，晚间服用", "duration": 30, "times": ["20:00"], "inventory": 26, "daily_doses": 1, "follow_up_days": 45},
        ],
    },
    "李阿姨": {
        "condition": "冠心病 / 高血压",
        "start_date": date(2026, 4, 2),
        "follow_up_date": date(2026, 5, 12),
        "prescription_text": "阿司匹林肠溶片 100mg 每日1次，早餐后服用；氨氯地平 5mg 每日1次，早晨服用；单硝酸异山梨酯缓释片 40mg 每日1次。",
        "parsed_prescription": [
            {"name": "阿司匹林肠溶片", "strength": "100mg", "dose": "1片", "frequency": "每日1次，早餐后服用", "duration": 30, "times": ["08:00"], "inventory": 25, "daily_doses": 1, "follow_up_days": 30},
            {"name": "氨氯地平", "strength": "5mg", "dose": "1片", "frequency": "每日1次，早晨服用", "duration": 30, "times": ["08:00"], "inventory": 16, "daily_doses": 1, "follow_up_days": 30},
            {"name": "单硝酸异山梨酯缓释片", "strength": "40mg", "dose": "1片", "frequency": "每日1次，晨起服用", "duration": 30, "times": ["08:00"], "inventory": 22, "daily_doses": 1, "follow_up_days": 40},
        ],
    },
}


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --primary: #ffd100;
            --primary-strong: #ffbf00;
            --primary-soft: #fff6cc;
            --accent: #111111;
            --bg: #f5f5f5;
            --card: rgba(255,255,255,0.98);
            --text: #222222;
            --muted: #6b6b6b;
            --border: rgba(17,17,17,0.08);
            --success: #18a058;
            --warn: #ff9f1a;
            --danger: #e5484d;
            --shadow: 0 16px 36px rgba(17, 17, 17, 0.08);
        }
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(255, 209, 0, 0.24), transparent 20%),
                linear-gradient(180deg, #fffbea 0%, #f7f7f2 18%, var(--bg) 100%);
            color: var(--text);
        }
        .block-container { padding-top: 1rem; padding-bottom: 2rem; max-width: 1240px; }
        .hero, .metric-card, .info-card, .suggest-card, .summary-card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 24px;
            padding: 1rem 1.1rem;
            box-shadow: var(--shadow);
        }
        .hero {
            padding: 1.6rem;
            background:
                radial-gradient(circle at top right, rgba(255,255,255,0.42), transparent 28%),
                linear-gradient(135deg, #ffe566 0%, #ffd100 52%, #ffc400 100%);
            margin-bottom: 1.1rem;
            position: relative;
            overflow: hidden;
        }
        .hero::after {
            content: "";
            position: absolute;
            right: -38px;
            top: -30px;
            width: 180px;
            height: 180px;
            border-radius: 50%;
            background: rgba(255,255,255,0.16);
        }
        .hero-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            background: rgba(17,17,17,0.86);
            color: #fff;
            border-radius: 999px;
            padding: 0.35rem 0.75rem;
            font-size: 0.78rem;
            font-weight: 700;
            margin-bottom: 0.9rem;
        }
        .hero h1 {
            font-size: 2.1rem;
            line-height: 1.1;
            margin: 0;
            color: var(--accent);
            position: relative;
            z-index: 1;
        }
        .hero p, .metric-label { color: var(--muted); }
        .hero p {
            max-width: 720px;
            margin: 0.5rem 0 0;
            color: rgba(17,17,17,0.78);
            position: relative;
            z-index: 1;
        }
        .hero-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            margin-top: 1rem;
            position: relative;
            z-index: 1;
        }
        .hero-chip {
            background: rgba(255,255,255,0.72);
            color: #2b2b2b;
            border: 1px solid rgba(17,17,17,0.06);
            border-radius: 999px;
            padding: 0.45rem 0.8rem;
            font-size: 0.88rem;
            font-weight: 700;
            backdrop-filter: blur(6px);
        }
        .section-title {
            font-size: 1.15rem;
            font-weight: 700;
            color: var(--accent);
            margin: 0.35rem 0 0.8rem 0;
        }
        .metric-card {
            border: 0;
            position: relative;
        }
        .metric-card::before {
            content: "";
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
            height: 5px;
            background: linear-gradient(90deg, #ffd100 0%, #ffbe0b 100%);
        }
        .metric-value { color: var(--accent); font-size: 1.7rem; font-weight: 800; margin-top: 0.2rem; }
        .pill {
            display: inline-block; padding: 0.32rem 0.68rem; margin-right: 0.35rem; margin-bottom: 0.4rem;
            border-radius: 999px; background: var(--primary-soft); color: #5c4500; font-size: 0.82rem; font-weight: 700;
        }
        .warn { color: var(--warn); font-weight: 700; }
        .danger { color: var(--danger); font-weight: 700; }
        .success { color: var(--success); font-weight: 700; }
        .info-card, .suggest-card, .summary-card {
            border-color: rgba(17,17,17,0.06);
        }
        .info-card strong, .summary-card strong { color: var(--accent); }
        .suggest-card {
            background: linear-gradient(135deg, #fffdf3 0%, #ffffff 100%);
            border-left: 6px solid var(--primary);
        }
        .summary-row {
            display: flex; justify-content: space-between; gap: 0.8rem; padding: 0.5rem 0;
            border-bottom: 1px dashed rgba(17,17,17,0.1);
        }
        .summary-row:last-child { border-bottom: 0; padding-bottom: 0; }
        div[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #fff9dc 0%, #fffef8 100%);
            border-right: 1px solid rgba(17,17,17,0.08);
        }
        div[data-testid="stSidebar"] .block-container {
            padding-top: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        .sidebar-profile {
            background: linear-gradient(180deg, #ffffff 0%, #fff9e1 100%);
            border: 1px solid rgba(17,17,17,0.08);
            border-radius: 22px;
            padding: 1rem;
            box-shadow: 0 10px 22px rgba(17,17,17,0.06);
        }
        .sidebar-profile .name {
            font-size: 1.1rem;
            font-weight: 800;
            color: #111;
            margin-bottom: 0.25rem;
        }
        .sidebar-profile .tag {
            display: inline-block;
            margin-top: 0.35rem;
            padding: 0.28rem 0.62rem;
            border-radius: 999px;
            background: #fff3b0;
            color: #5b4700;
            font-size: 0.8rem;
            font-weight: 700;
        }
        .sidebar-profile .meta {
            margin-top: 0.7rem;
            color: var(--muted);
            font-size: 0.84rem;
            line-height: 1.75;
        }
        div[data-baseweb="radio"] label,
        div[role="radiogroup"] label {
            background: rgba(255,255,255,0.92);
            border: 1px solid rgba(17,17,17,0.08);
            border-radius: 16px;
            margin-bottom: 0.45rem;
            padding: 0.2rem 0.35rem;
        }
        .stButton > button {
            border-radius: 16px;
            border: 0;
            background: linear-gradient(180deg, var(--primary) 0%, var(--primary-strong) 100%);
            color: #111;
            font-weight: 800;
            box-shadow: 0 10px 20px rgba(255, 209, 0, 0.28);
        }
        .stButton > button:hover {
            background: linear-gradient(180deg, #ffdf3b 0%, #ffc400 100%);
            color: #111;
        }
        .stButton > button:disabled {
            background: #f1f1f1;
            color: #999;
            box-shadow: none;
        }
        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div,
        .stDateInput > div > div,
        .stTextArea textarea {
            border-radius: 16px !important;
            border-color: rgba(17,17,17,0.08) !important;
            background: rgba(255,255,255,0.96) !important;
        }
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #ffd100 0%, #ffb703 100%);
        }
        @media (max-width: 768px) {
            .block-container { padding-top: 0.6rem; }
            .hero { padding: 1.2rem; border-radius: 20px; }
            .hero h1 { font-size: 1.7rem; }
            .hero-meta { gap: 0.5rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def initialize_state() -> None:
    if "medications" not in st.session_state:
        st.session_state.medications = []
    if "parsed_prescription" not in st.session_state:
        st.session_state.parsed_prescription = []
    if "history" not in st.session_state:
        st.session_state.history = []
    if "last_parse_message" not in st.session_state:
        st.session_state.last_parse_message = ""
    if "patient_profile" not in st.session_state:
        st.session_state.patient_profile = {
            "name": "刘芳",
            "condition": "2型糖尿病 / 高血压",
            "follow_up_date": date.today() + timedelta(days=14),
            "start_date": date.today(),
        }
    if "selected_patient" not in st.session_state:
        st.session_state.selected_patient = "刘芳"
    if "current_prescription_text" not in st.session_state:
        st.session_state.current_prescription_text = ""
    if "patient_initialized" not in st.session_state:
        apply_simulated_patient(st.session_state.selected_patient)
        st.session_state.patient_initialized = True


def apply_simulated_patient(patient_name: str) -> None:
    patient = SIMULATED_PATIENTS[patient_name]
    st.session_state.selected_patient = patient_name
    st.session_state.patient_profile = {
        "name": patient_name,
        "condition": patient["condition"],
        "follow_up_date": patient["follow_up_date"],
        "start_date": patient["start_date"],
    }
    st.session_state.current_prescription_text = patient["prescription_text"]
    st.session_state.parsed_prescription = [dict(item) for item in patient["parsed_prescription"]]
    st.session_state.medications = [build_medication(item) for item in st.session_state.parsed_prescription]
    st.session_state.history = []
    st.session_state.last_parse_message = f"已载入 {patient_name} 的模拟处方，共 {len(st.session_state.parsed_prescription)} 种药品。"


def save_patient_profile(name: str, condition: str, start_date: date, follow_up_date: date) -> None:
    st.session_state.patient_profile = {
        "name": name.strip() or st.session_state.patient_profile["name"],
        "condition": condition.strip() or st.session_state.patient_profile["condition"],
        "start_date": start_date,
        "follow_up_date": follow_up_date,
    }


def format_medication_line(med: dict) -> str:
    return f'{med["name"]} {med["strength"]} · 每次{med["dose"]}'


def format_usage_text(med: dict) -> str:
    return f'每次{med["dose"]}，{med["frequency"]}'


def parse_frequency_to_times(frequency: str) -> list[str]:
    lowered = frequency.lower()
    if "three" in lowered or "tid" in lowered:
        return ["08:00", "13:00", "20:00"]
    if "twice" in lowered or "bid" in lowered:
        return ["08:00", "20:00"]
    return ["08:00"]


def build_medication(raw: dict) -> dict:
    times = raw.get("times") or parse_frequency_to_times(raw.get("frequency", ""))
    strength = raw.get("strength") or raw.get("dosage", "")
    dose = raw.get("dose", "1片")
    return {
        "name": raw["name"],
        "strength": strength,
        "dose": dose,
        "frequency": raw["frequency"],
        "duration": int(raw["duration"]),
        "times": times,
        "inventory": int(raw.get("inventory", max(14, int(raw["duration"]) * len(times)))),
        "daily_doses": int(raw.get("daily_doses", len(times))),
        "follow_up_days": int(raw.get("follow_up_days", 30)),
    }


def generate_mock_parse(prescription_text: str) -> list[dict]:
    text = prescription_text.lower()
    meds = []
    if "metformin" in text or "二甲双胍" in text:
        meds.append({"name": "二甲双胍", "strength": "500mg", "dose": "1片", "frequency": "每日2次，餐后服用", "duration": 30, "times": ["08:00", "20:00"], "inventory": 28, "daily_doses": 2, "follow_up_days": 30})
    if "amlodipine" in text or "氨氯地平" in text:
        meds.append({"name": "氨氯地平", "strength": "5mg", "dose": "1片", "frequency": "每日1次，早晨服用", "duration": 30, "times": ["08:00"], "inventory": 18, "daily_doses": 1, "follow_up_days": 45})
    if "atorvastatin" in text or "阿托伐他汀" in text:
        meds.append({"name": "阿托伐他汀", "strength": "20mg", "dose": "1片", "frequency": "每日1次，晚间服用", "duration": 30, "times": ["20:00"], "inventory": 30, "daily_doses": 1, "follow_up_days": 60})
    if "缬沙坦" in text or "valsartan" in text:
        meds.append({"name": "缬沙坦", "strength": "80mg", "dose": "1片", "frequency": "每日1次，早晨服用", "duration": 30, "times": ["08:00"], "inventory": 20, "daily_doses": 1, "follow_up_days": 30})
    if "阿司匹林肠溶片" in text or "aspirin" in text:
        meds.append({"name": "阿司匹林肠溶片", "strength": "100mg", "dose": "1片", "frequency": "每日1次，早餐后服用", "duration": 30, "times": ["08:00"], "inventory": 25, "daily_doses": 1, "follow_up_days": 30})
    if "单硝酸异山梨酯" in text or "isosorbide" in text:
        meds.append({"name": "单硝酸异山梨酯缓释片", "strength": "40mg", "dose": "1片", "frequency": "每日1次，晨起服用", "duration": 30, "times": ["08:00"], "inventory": 22, "daily_doses": 1, "follow_up_days": 40})
    return meds or DEFAULT_PARSE_RESULT


def load_parsed_plan() -> None:
    if not st.session_state.parsed_prescription:
        return
    st.session_state.medications = [build_medication(raw) for raw in st.session_state.parsed_prescription]
    max_follow_up = max(med["follow_up_days"] for med in st.session_state.medications)
    st.session_state.patient_profile["follow_up_date"] = max(
        st.session_state.patient_profile["follow_up_date"],
        date.today() + timedelta(days=max_follow_up),
    )


def combine_schedule(medications: list[dict]) -> list[dict]:
    schedule = []
    for med in medications:
        for med_time in med["times"]:
            schedule.append({"id": f"{date.today().isoformat()}-{med['name']}-{med_time}", "name": med["name"], "strength": med["strength"], "dose": med["dose"], "time": med_time})
    return sorted(schedule, key=lambda item: item["time"])


def today_taken_count() -> int:
    today_str = date.today().isoformat()
    return sum(1 for item in st.session_state.history if item["date"] == today_str)


def history_matches_today(name: str, med_time: str) -> bool:
    today_str = date.today().isoformat()
    return any(record["date"] == today_str and record["name"] == name and record["time"] == med_time for record in st.session_state.history)


def mark_taken(name: str, med_time: str) -> None:
    if history_matches_today(name, med_time):
        return
    st.session_state.history.append({"date": date.today().isoformat(), "name": name, "time": med_time, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")})
    for med in st.session_state.medications:
        if med["name"] == name and med["inventory"] > 0:
            med["inventory"] -= 1
            break


def adherence_rate() -> float:
    scheduled_today = len(combine_schedule(st.session_state.medications))
    if scheduled_today == 0:
        return 0.0
    return min(100.0, (today_taken_count() / scheduled_today) * 100)


def total_remaining_days() -> int:
    days_left = [ceil(med["inventory"] / med["daily_doses"]) for med in st.session_state.medications if med["daily_doses"] > 0]
    return min(days_left) if days_left else 0


def find_next_medication() -> str:
    if not st.session_state.medications:
        return "尚未生成方案"
    now_time = datetime.now().time()
    schedule = combine_schedule(st.session_state.medications)
    for item in schedule:
        item_time = datetime.strptime(item["time"], "%H:%M").time()
        if item_time >= now_time and not history_matches_today(item["name"], item["time"]):
            return f"{item['time']} · {item['name']} {item['strength']}"
    first = schedule[0] if schedule else None
    return f"明天 {first['time']} · {first['name']} {first['strength']}" if first else "尚未生成方案"


def weekly_missed_doses() -> int:
    if not st.session_state.medications:
        return 0
    daily_total = len(combine_schedule(st.session_state.medications))
    planned = daily_total * 7
    return 0 if planned == 0 else max(2, planned - max(len(st.session_state.history), planned - 2))


def ai_suggestions() -> list[str]:
    suggestions = []
    missed = weekly_missed_doses()
    if missed:
        suggestions.append(f"本周您有 {missed} 次漏服，建议开启更严格的提醒。")
    if total_remaining_days() <= 7 and st.session_state.medications:
        suggestions.append("药品库存即将不足，建议尽快补药。")
    follow_up_date = st.session_state.patient_profile["follow_up_date"]
    days_to_follow_up = (follow_up_date - date.today()).days
    if days_to_follow_up <= 10:
        suggestions.append(f"距离下次复诊还有 {days_to_follow_up} 天，请提前做好准备。")
    return suggestions or ["今日用药情况稳定，请继续按方案坚持服药。"]


def hero() -> None:
    profile = st.session_state.patient_profile
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-badge">慢病管理专区</div>
            <h1>慢病用药小管家</h1>
            <p>为 {profile['name']} 提供覆盖处方解析、用药管理、补药提醒与复诊跟进的一站式健康服务，信息更清晰，提醒更直接。</p>
            <div class="hero-meta">
                <span class="hero-chip">{profile['name']}</span>
                <span class="hero-chip">{profile['condition']}</span>
                <span class="hero-chip">下次复诊：{profile['follow_up_date'].isoformat()}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(label: str, value: str, caption: str) -> None:
    st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-label">{caption}</div></div>', unsafe_allow_html=True)


def dashboard_page() -> None:
    st.markdown('<div class="section-title">今日概览</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card("今日用药完成率", f"{int(adherence_rate())}%", "已服次数 / 今日计划次数")
    with c2:
        render_metric_card("下次服药时间", find_next_medication(), "即将到来的用药安排")
    with c3:
        render_metric_card("剩余可服用天数", str(total_remaining_days()), "按当前方案估算的最少余量")
    with c4:
        follow_up_days = (st.session_state.patient_profile["follow_up_date"] - date.today()).days
        render_metric_card("下次复诊日期", st.session_state.patient_profile["follow_up_date"].isoformat(), f"距今还有 {follow_up_days} 天")
    goal_col, prescription_col = st.columns([1, 1])
    with goal_col:
        st.markdown('<div class="section-title">当前患者管理目标</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="summary-card">'
            '<div class="summary-row"><span>目标 01</span><strong>按时服药</strong></div>'
            '<div class="summary-row"><span>目标 02</span><strong>避免重复购药或断药</strong></div>'
            '<div class="summary-row"><span>目标 03</span><strong>按期复诊续方</strong></div>'
            '</div>',
            unsafe_allow_html=True,
        )
    with prescription_col:
        st.markdown('<div class="section-title">当前患者模拟处方</div>', unsafe_allow_html=True)
        prescription_items = "".join(
            [
                f'<div class="summary-row"><span>{med["name"]}</span><strong>{med["strength"]} · 每次{med["dose"]}</strong></div>'
                for med in st.session_state.parsed_prescription
            ]
        )
        st.markdown(
            f'<div class="summary-card">{prescription_items}<div style="margin-top:0.7rem;" class="metric-label">{st.session_state.current_prescription_text}</div></div>',
            unsafe_allow_html=True,
        )
    left, right = st.columns([1.3, 1])
    with left:
        st.markdown('<div class="section-title">今日执行进度</div>', unsafe_allow_html=True)
        st.progress(min(int(adherence_rate()), 100))
        scheduled = combine_schedule(st.session_state.medications)
        if scheduled:
            for item in scheduled:
                taken = history_matches_today(item["name"], item["time"])
                status_class = "success" if taken else "warn"
                status_text = "已服用" if taken else "待服用"
                st.markdown(f'<div class="info-card" style="margin-bottom:0.7rem;"><div style="display:flex;justify-content:space-between;gap:0.8rem;"><div><strong>{item["name"]} {item["strength"]}</strong><br><span class="metric-label">每次{item["dose"]} · 计划服用时间：{item["time"]}</span></div><div class="{status_class}">{status_text}</div></div></div>', unsafe_allow_html=True)
        else:
            st.info("请先上传处方并生成用药方案。")
    with right:
        st.markdown('<div class="section-title">智能提醒</div>', unsafe_allow_html=True)
        for suggestion in ai_suggestions():
            st.markdown(f'<div class="suggest-card" style="margin-bottom:0.7rem;">{suggestion}</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">关键信息</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-card"><div class="summary-row"><span>当前用药种类</span><strong>{len(st.session_state.medications)}</strong></div><div class="summary-row"><span>今日已服次数</span><strong>{today_taken_count()}</strong></div><div class="summary-row"><span>补药风险</span><strong>{"较高" if total_remaining_days() <= 7 and st.session_state.medications else "稳定"}</strong></div><div class="summary-row"><span>复诊倒计时</span><strong>{(st.session_state.patient_profile["follow_up_date"] - date.today()).days} 天</strong></div></div>', unsafe_allow_html=True)


def prescription_page() -> None:
    st.markdown('<div class="section-title">处方上传</div>', unsafe_allow_html=True)
    col1, col2 = st.columns([1.1, 1])
    with col1:
        uploaded_file = st.file_uploader("上传处方图片", type=["png", "jpg", "jpeg"])
        prescription_text = st.text_area("或直接粘贴处方内容", value=st.session_state.current_prescription_text, placeholder="示例：二甲双胍 500mg 每日2次，连用30天；氨氯地平 5mg 每日1次，晨起服用。", height=180)
        if st.button("模拟 AI 解析", use_container_width=True):
            parsed = generate_mock_parse(prescription_text)
            st.session_state.current_prescription_text = prescription_text
            st.session_state.parsed_prescription = parsed
            source = uploaded_file.name if uploaded_file else "文本输入"
            st.session_state.last_parse_message = f"AI 已完成 {source} 解析，共识别出 {len(parsed)} 种药品。"
        if st.session_state.last_parse_message:
            st.success(st.session_state.last_parse_message)
    with col2:
        st.markdown('<div class="info-card"><strong>模拟 AI 能力</strong><div style="margin-top:0.6rem;"><span class="pill">处方识别提取</span><span class="pill">剂量标准化</span><span class="pill">用药风险提示</span></div><p style="margin-top:0.7rem;color:#6f859b;">当前为模拟解析流程，用于展示真实医疗产品中的处方录入体验，无需依赖外部接口。</p></div>', unsafe_allow_html=True)
    if st.session_state.parsed_prescription:
        st.markdown('<div class="section-title">解析结果</div>', unsafe_allow_html=True)
        for med in st.session_state.parsed_prescription:
            st.markdown(f'<div class="info-card" style="margin-bottom:0.7rem;"><strong>药品：{med["name"]}</strong><br><span class="metric-label">规格：{med["strength"]}</span><br><span class="metric-label">用法：每次{med["dose"]}，{med["frequency"]}</span><br><span class="metric-label">疗程：{med["duration"]}天</span></div>', unsafe_allow_html=True)
        if st.button("生成用药方案", type="primary", use_container_width=True):
            load_parsed_plan()
            st.success("已生成用药方案，请前往“用药方案”页面查看和调整。")


def plan_page() -> None:
    st.markdown('<div class="section-title">用药方案</div>', unsafe_allow_html=True)
    if not st.session_state.medications:
        st.info("尚未生成用药方案，请先前往“处方上传”。")
        return
    for index, med in enumerate(st.session_state.medications):
        st.markdown(f'<div class="info-card" style="margin-bottom:0.8rem;"><strong>{format_medication_line(med)}</strong><br><span class="metric-label">可在下方调整规格、每次服用量、疗程、库存和服药时段。</span></div>', unsafe_allow_html=True)
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            med["strength"] = st.text_input("规格", med["strength"], key=f"strength_{index}")
        with col2:
            med["dose"] = st.text_input("每次服用量", med["dose"], key=f"dose_{index}")
        with col3:
            med["duration"] = st.number_input("疗程（天）", min_value=1, value=int(med["duration"]), key=f"duration_{index}")
        with col4:
            med["inventory"] = st.number_input("当前库存（片）", min_value=0, value=int(med["inventory"]), key=f"inventory_{index}")
        with col5:
            selected_slots = st.multiselect("服药时段", options=list(TIME_SLOTS.keys()), default=[slot for slot, meta in TIME_SLOTS.items() if meta["time"] in med["times"]], key=f"times_{index}")
            med["times"] = [TIME_SLOTS[slot]["time"] for slot in selected_slots] or med["times"]
            med["daily_doses"] = max(1, len(med["times"]))
    st.markdown('<div class="section-title">每日计划预览</div>', unsafe_allow_html=True)
    morning, noon, evening = st.columns(3)
    grouped = {"08:00": [], "13:00": [], "20:00": []}
    for med in st.session_state.medications:
        for med_time in med["times"]:
            grouped.setdefault(med_time, []).append(format_medication_line(med))
    for slot_col, slot_time, slot_name in [(morning, "08:00", "早晨"), (noon, "13:00", "中午"), (evening, "20:00", "晚上")]:
        with slot_col:
            meds = grouped.get(slot_time, [])
            content = "<br>".join(meds) if meds else "当前时段暂无用药安排"
            st.markdown(f'<div class="summary-card"><strong>{slot_name}</strong><br><span class="metric-label">{slot_time}</span><p style="margin-top:0.6rem;">{content}</p></div>', unsafe_allow_html=True)


def tracker_page() -> None:
    st.markdown('<div class="section-title">用药打卡</div>', unsafe_allow_html=True)
    schedule = combine_schedule(st.session_state.medications)
    if not schedule:
        st.info("当前暂无有效用药计划，请先生成方案。")
        return
    st.progress(min(int(adherence_rate()), 100))
    st.caption(f"今日服药依从率：{adherence_rate():.0f}%")
    for item in schedule:
        taken = history_matches_today(item["name"], item["time"])
        left, right = st.columns([4, 1])
        with left:
            st.markdown(f'<div class="info-card" style="margin-bottom:0.7rem;"><strong>{item["name"]} {item["strength"]}</strong><br><span class="metric-label">每次{item["dose"]} · 计划服用时间：{item["time"]}</span></div>', unsafe_allow_html=True)
        with right:
            if st.button("已服用" if taken else "标记已服用", key=f'take_{item["name"]}_{item["time"]}', disabled=taken, use_container_width=True):
                mark_taken(item["name"], item["time"])
                st.rerun()


def inventory_page() -> None:
    st.markdown('<div class="section-title">库存监测</div>', unsafe_allow_html=True)
    if not st.session_state.medications:
        st.info("暂无库存数据，请先生成用药方案。")
        return
    for index, med in enumerate(st.session_state.medications):
        remaining_days = ceil(med["inventory"] / max(1, med["daily_doses"]))
        status = "库存偏低" if remaining_days <= 7 else "库存充足"
        status_class = "danger" if remaining_days <= 7 else "success"
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f'<div class="info-card" style="margin-bottom:0.7rem;"><strong>{format_medication_line(med)}</strong><br><span class="metric-label">剩余药量：{med["inventory"]}片</span><br><span class="metric-label">预计还可服用：{remaining_days}天</span><br><span class="{status_class}">{status}</span></div>', unsafe_allow_html=True)
        with c2:
            refill_amount = st.number_input("补充库存（片）", min_value=0, value=0, key=f"refill_{index}")
            if st.button("确认补药", key=f"refill_btn_{index}", use_container_width=True):
                med["inventory"] += int(refill_amount)
                st.rerun()
    if total_remaining_days() <= 7:
        st.warning("补药提醒：当前药品剩余不足7天，请尽快补药。")


def follow_up_page() -> None:
    st.markdown('<div class="section-title">复诊管理</div>', unsafe_allow_html=True)
    if not st.session_state.medications:
        st.info("请先生成用药方案，系统才能计算复诊时间。")
        return
    current_follow_up = st.session_state.patient_profile["follow_up_date"]
    new_date = st.date_input("下次复诊日期", value=current_follow_up)
    st.session_state.patient_profile["follow_up_date"] = new_date
    countdown = (new_date - date.today()).days
    st.markdown(f'<div class="summary-card"><strong>复诊倒计时</strong><div class="metric-value" style="margin-top:0.5rem;">{countdown} 天</div><div class="metric-label">系统根据疗程时长与慢病管理节奏给出建议时间。</div></div>', unsafe_allow_html=True)
    if countdown <= 10:
        st.warning("复诊日期临近，请提前准备检查结果和补药需求。")
    st.markdown('<div class="section-title">复诊提示</div>', unsafe_allow_html=True)
    st.markdown('<div class="suggest-card">建议在复诊前完成以下准备：<br>• 携带血压或血糖记录<br>• 梳理漏服情况和不良反应<br>• 提前确认补药和续方需求</div>', unsafe_allow_html=True)


def sidebar_navigation() -> str:
    with st.sidebar:
        st.markdown("## 当前用户 / 患者档案")
        profile = st.session_state.patient_profile
        selected_patient = st.selectbox("切换模拟患者", options=list(SIMULATED_PATIENTS.keys()), index=list(SIMULATED_PATIENTS.keys()).index(st.session_state.selected_patient))
        if selected_patient != st.session_state.selected_patient:
            apply_simulated_patient(selected_patient)
            profile = st.session_state.patient_profile
        st.markdown(
            f'''
            <div class="sidebar-profile">
                <div class="name">{profile["name"]}</div>
                <div class="tag">{profile["condition"]}</div>
                <div class="meta">
                    建档日期：{profile["start_date"].isoformat()}<br>
                    下次复诊：{profile["follow_up_date"].isoformat()}
                </div>
            </div>
            ''',
            unsafe_allow_html=True,
        )
        with st.form("patient_profile_form", clear_on_submit=False):
            st.markdown("### 患者档案设置")
            edit_name = st.text_input("姓名", value=profile["name"])
            edit_condition = st.text_input("慢病类型", value=profile["condition"])
            edit_start_date = st.date_input("建档日期", value=profile["start_date"])
            edit_follow_up_date = st.date_input("下次复诊日期", value=profile["follow_up_date"])
            if st.form_submit_button("保存患者档案", use_container_width=True):
                save_patient_profile(edit_name, edit_condition, edit_start_date, edit_follow_up_date)
                st.success("患者档案已更新。")
                profile = st.session_state.patient_profile
        st.markdown("---")
        st.markdown("## 页面导航")
        page = st.radio("前往页面", ["首页总览", "处方上传", "用药方案", "用药打卡", "库存监测", "复诊管理"], label_visibility="collapsed")
    return page


def main() -> None:
    inject_css()
    initialize_state()
    hero()
    page = sidebar_navigation()
    if page == "首页总览":
        dashboard_page()
    elif page == "处方上传":
        prescription_page()
    elif page == "用药方案":
        plan_page()
    elif page == "用药打卡":
        tracker_page()
    elif page == "库存监测":
        inventory_page()
    elif page == "复诊管理":
        follow_up_page()


if __name__ == "__main__":
    main()
