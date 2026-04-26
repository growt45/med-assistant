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
        "dosage": "500mg",
        "frequency": "每日2次，餐后服用",
        "duration": 30,
        "times": ["08:00", "20:00"],
        "inventory": 24,
        "daily_doses": 2,
        "follow_up_days": 30,
    },
    {
        "name": "氨氯地平",
        "dosage": "5mg",
        "frequency": "每日1次，早晨服用",
        "duration": 30,
        "times": ["08:00"],
        "inventory": 18,
        "daily_doses": 1,
        "follow_up_days": 45,
    },
]


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --primary: #1d6fd8;
            --primary-soft: #edf5ff;
            --accent: #0e4f9c;
            --bg: #f4f8fc;
            --card: rgba(255,255,255,0.92);
            --text: #18324a;
            --muted: #6f859b;
            --border: rgba(29,111,216,0.12);
            --success: #1f9d69;
            --warn: #e6a700;
            --danger: #d84f61;
        }
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(94,164,255,0.18), transparent 25%),
                linear-gradient(180deg, #f8fbff 0%, var(--bg) 48%, #eef5fb 100%);
            color: var(--text);
        }
        .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }
        .hero, .metric-card, .info-card, .suggest-card, .summary-card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 1rem 1.1rem;
            box-shadow: 0 14px 32px rgba(17, 63, 114, 0.06);
        }
        .hero {
            padding: 1.4rem 1.6rem;
            background: linear-gradient(135deg, #e7f1ff 0%, #ffffff 58%, #f0f7ff 100%);
            margin-bottom: 1rem;
        }
        .hero h1 { font-size: 2rem; margin: 0; color: var(--accent); }
        .hero p, .metric-label { color: var(--muted); }
        .section-title {
            font-size: 1.15rem;
            font-weight: 700;
            color: var(--accent);
            margin: 0.2rem 0 0.8rem 0;
        }
        .metric-value { color: var(--accent); font-size: 1.6rem; font-weight: 800; margin-top: 0.15rem; }
        .pill {
            display: inline-block; padding: 0.25rem 0.6rem; margin-right: 0.35rem; margin-bottom: 0.4rem;
            border-radius: 999px; background: var(--primary-soft); color: var(--primary); font-size: 0.82rem; font-weight: 700;
        }
        .warn { color: var(--warn); font-weight: 700; }
        .danger { color: var(--danger); font-weight: 700; }
        .success { color: var(--success); font-weight: 700; }
        .summary-row {
            display: flex; justify-content: space-between; gap: 0.8rem; padding: 0.5rem 0;
            border-bottom: 1px dashed rgba(111,133,155,0.18);
        }
        .summary-row:last-child { border-bottom: 0; padding-bottom: 0; }
        div[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f8fbff 0%, #eff6ff 100%);
            border-right: 1px solid rgba(29,111,216,0.08);
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


def parse_frequency_to_times(frequency: str) -> list[str]:
    lowered = frequency.lower()
    if "three" in lowered or "tid" in lowered:
        return ["08:00", "13:00", "20:00"]
    if "twice" in lowered or "bid" in lowered:
        return ["08:00", "20:00"]
    return ["08:00"]


def build_medication(raw: dict) -> dict:
    times = raw.get("times") or parse_frequency_to_times(raw.get("frequency", ""))
    return {
        "name": raw["name"],
        "dosage": raw["dosage"],
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
        meds.append({"name": "二甲双胍", "dosage": "500mg", "frequency": "每日2次，餐后服用", "duration": 30, "times": ["08:00", "20:00"], "inventory": 28, "daily_doses": 2, "follow_up_days": 30})
    if "amlodipine" in text or "氨氯地平" in text:
        meds.append({"name": "氨氯地平", "dosage": "5mg", "frequency": "每日1次，早晨服用", "duration": 30, "times": ["08:00"], "inventory": 18, "daily_doses": 1, "follow_up_days": 45})
    if "atorvastatin" in text or "阿托伐他汀" in text:
        meds.append({"name": "阿托伐他汀", "dosage": "20mg", "frequency": "每日1次，晚间服用", "duration": 30, "times": ["20:00"], "inventory": 30, "daily_doses": 1, "follow_up_days": 60})
    return meds or DEFAULT_PARSE_RESULT


def load_parsed_plan() -> None:
    if not st.session_state.parsed_prescription:
        return
    st.session_state.medications = [build_medication(raw) for raw in st.session_state.parsed_prescription]
    max_follow_up = max(med["follow_up_days"] for med in st.session_state.medications)
    st.session_state.patient_profile["start_date"] = date.today()
    st.session_state.patient_profile["follow_up_date"] = date.today() + timedelta(days=max_follow_up)


def combine_schedule(medications: list[dict]) -> list[dict]:
    schedule = []
    for med in medications:
        for med_time in med["times"]:
            schedule.append({"id": f"{date.today().isoformat()}-{med['name']}-{med_time}", "name": med["name"], "dosage": med["dosage"], "time": med_time})
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
            return f"{item['time']} · {item['name']}"
    first = schedule[0] if schedule else None
    return f"明天 {first['time']} · {first['name']}" if first else "尚未生成方案"


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
            <h1>慢病用药小管家</h1>
            <p>为 {profile['name']} 提供覆盖处方解析、用药管理、补药提醒与复诊跟进的全流程慢病用药服务。</p>
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
                st.markdown(f'<div class="info-card" style="margin-bottom:0.7rem;"><div style="display:flex;justify-content:space-between;gap:0.8rem;"><div><strong>{item["name"]}</strong> · {item["dosage"]}<br><span class="metric-label">{item["time"]}</span></div><div class="{status_class}">{status_text}</div></div></div>', unsafe_allow_html=True)
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
        prescription_text = st.text_area("或直接粘贴处方内容", placeholder="示例：二甲双胍 500mg 每日2次，连用30天；氨氯地平 5mg 每日1次，晨起服用。", height=180)
        if st.button("模拟 AI 解析", use_container_width=True):
            parsed = generate_mock_parse(prescription_text)
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
            st.markdown(f'<div class="info-card" style="margin-bottom:0.7rem;"><strong>{med["name"]}</strong><br><span class="metric-label">剂量：{med["dosage"]} · 频次：{med["frequency"]} · 疗程：{med["duration"]} 天</span></div>', unsafe_allow_html=True)
        if st.button("生成用药方案", type="primary", use_container_width=True):
            load_parsed_plan()
            st.success("已生成用药方案，请前往“用药方案”页面查看和调整。")


def plan_page() -> None:
    st.markdown('<div class="section-title">用药方案</div>', unsafe_allow_html=True)
    if not st.session_state.medications:
        st.info("尚未生成用药方案，请先前往“处方上传”。")
        return
    for index, med in enumerate(st.session_state.medications):
        st.markdown(f'<div class="info-card" style="margin-bottom:0.8rem;"><strong>{med["name"]}</strong> · {med["dosage"]}<br><span class="metric-label">可在下方调整剂量、疗程、库存和服药时段。</span></div>', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            med["dosage"] = st.text_input("剂量", med["dosage"], key=f"dosage_{index}")
        with col2:
            med["duration"] = st.number_input("疗程（天）", min_value=1, value=int(med["duration"]), key=f"duration_{index}")
        with col3:
            med["inventory"] = st.number_input("当前库存", min_value=0, value=int(med["inventory"]), key=f"inventory_{index}")
        with col4:
            selected_slots = st.multiselect("服药时段", options=list(TIME_SLOTS.keys()), default=[slot for slot, meta in TIME_SLOTS.items() if meta["time"] in med["times"]], key=f"times_{index}")
            med["times"] = [TIME_SLOTS[slot]["time"] for slot in selected_slots] or med["times"]
            med["daily_doses"] = max(1, len(med["times"]))
    st.markdown('<div class="section-title">每日计划预览</div>', unsafe_allow_html=True)
    morning, noon, evening = st.columns(3)
    grouped = {"08:00": [], "13:00": [], "20:00": []}
    for med in st.session_state.medications:
        for med_time in med["times"]:
            grouped.setdefault(med_time, []).append(f"{med['name']} {med['dosage']}")
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
            st.markdown(f'<div class="info-card" style="margin-bottom:0.7rem;"><strong>{item["name"]}</strong> · {item["dosage"]}<br><span class="metric-label">计划服用时间：{item["time"]}</span></div>', unsafe_allow_html=True)
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
            st.markdown(f'<div class="info-card" style="margin-bottom:0.7rem;"><strong>{med["name"]}</strong> · {med["dosage"]}<br><span class="metric-label">剩余药量：{med["inventory"]} 片 · 预计还可服用 {remaining_days} 天</span><br><span class="{status_class}">{status}</span></div>', unsafe_allow_html=True)
        with c2:
            refill_amount = st.number_input("补充库存", min_value=0, value=0, key=f"refill_{index}")
            if st.button("确认补药", key=f"refill_btn_{index}", use_container_width=True):
                med["inventory"] += int(refill_amount)
                st.rerun()
    if total_remaining_days() <= 7:
        st.warning("补药提醒：当前至少有一种药品剩余不足 7 天，请尽快补药。")


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
        st.markdown("## 页面导航")
        page = st.radio("前往页面", ["首页总览", "处方上传", "用药方案", "用药打卡", "库存监测", "复诊管理"], label_visibility="collapsed")
        st.markdown("---")
        st.markdown("### 患者概况")
        profile = st.session_state.patient_profile
        st.caption(profile["name"])
        st.caption(profile["condition"])
        st.caption(f"建档日期：{profile['start_date'].isoformat()}")
        st.caption(f"下次复诊：{profile['follow_up_date'].isoformat()}")
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
