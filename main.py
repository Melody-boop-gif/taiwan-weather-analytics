# -*- coding: utf-8 -*-
# 執行：cd C:\Users\yijen\Python\weather_app
#      .\.venv\Scripts\python.exe -m streamlit run main.py
from __future__ import annotations

import html as _html
from datetime import date, timedelta


import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from plotly.subplots import make_subplots
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib

import time
import threading
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.graphics.shapes import Drawing, Line, String
from reportlab.graphics.charts.lineplots import LinePlot

st.set_page_config(
    page_title="Taiwan Weather Analytics",
    page_icon="🌤",
    layout="wide",
    initial_sidebar_state="collapsed",
)




API_URL = "https://archive-api.open-meteo.com/v1/archive"
DATA_LAG_DAYS = 0
RAINY_MM = 1.0             # 雨天定義：日雨量 >= 1mm
MIN_DAYS_PER_MONTH = 1

CITIES = {
    # 北部
    "Taipei": ("台北市", "north", 25.0330, 121.5654),
    "New Taipei": ("新北市", "north", 25.0120, 121.4650),
    "Keelung": ("基隆市", "north", 25.1276, 121.7392),
    "Taoyuan": ("桃園市", "north", 24.9936, 121.3010),
    "Hsinchu City": ("新竹市", "north", 24.8039, 120.9647),
    "Hsinchu County": ("新竹縣", "north", 24.8387, 121.0177),

    # 中部
    "Miaoli": ("苗栗縣", "central", 24.5602, 120.8214),
    "Taichung": ("台中市", "central", 24.1477, 120.6736),
    "Changhua": ("彰化縣", "central", 24.0753, 120.5416),
    "Nantou": ("南投縣", "central", 23.9609, 120.9719),
    "Yunlin": ("雲林縣", "central", 23.7092, 120.4313),

    # 南部
    "Chiayi City": ("嘉義市", "south", 23.4801, 120.4491),
    "Chiayi County": ("嘉義縣", "south", 23.4594, 120.2947),
    "Tainan": ("台南市", "south", 22.9999, 120.2270),
    "Kaohsiung": ("高雄市", "south", 22.6273, 120.3014),
    "Pingtung": ("屏東縣", "south", 22.6761, 120.4942),

    # 東部
    "Yilan": ("宜蘭縣", "east", 24.7570, 121.7530),
    "Hualien": ("花蓮縣", "east", 23.9772, 121.6044),
    "Taitung": ("台東縣", "east", 22.7583, 121.1444),

    # 離島
    "Penghu": ("澎湖縣", "islands", 23.5655, 119.5863),
    "Kinmen": ("金門縣", "islands", 24.4494, 118.3767),
    "Lienchiang": ("連江縣", "islands", 26.1602, 119.9499),
}


# 換季訊號：(key, 門檻°C, 方向, 搜尋起算 (月,日))   ← 想改門檻就改這裡的數字
SEASONS = [
    ("spring", 20, "up", (1, 1)),
    ("summer", 26, "up", (3, 1)),
    ("autumn", 25, "down", (8, 1)),
    ("winter", 18, "down", (10, 1)),
]

# 穿著溫度帶：由熱到冷

BANDS = [
    ("hot", "#DC6C5F"),
    ("warm", "#E7A776"),
    ("comf", "#D8CE91"),
    ("cool", "#8FBAC5"),
    ("cold", "#8195B1"),
]


YEAR_COLORS = ["#CBD5E1", "#94A3B8", "#334155", "#E05D38"]  # 舊 → 今年
ACCENT = "#E05D38"
INK = "#0F172A"

# =============================================================================
# 中 / 英 文字
# =============================================================================
T = {
    "zh": {
        "live": "即時氣候資料",
        "data_until": "資料更新至 {d}",
        "choose_city": "選擇觀測城市",
        "north": "北部地區",
        "central": "中部地區",
        "south": "南部地區",
        "east": "東部地區",
        "islands": "離島地區",
        "base_period": "分析期間 {a}–{b}",
        "hero_desc": "以近 3 年每日氣溫與降雨資料，找出換季節奏與歷年差異，作為服飾商品上架、備貨、檔期與庫存調度的量化依據。",
        "progress_title": "今年換季進度",
        "kpi_temp": "近 30 天均溫",
        "kpi_rain": "近 30 天累積降雨",
        "kpi_days": "近 30 天降雨日數",
        "vs_last": "去年同期 {v}",
        "rain_def": "日雨量 ≥ 1mm",
        "day_unit": "天",
        "warm_tag": "偏暖", "cool_tag": "偏冷", "flat_tag": "持平", "wet_tag": "多雨", "dry_tag": "偏乾",
        "next_signal": "下一個換季決策",
        "focus_label": "建議主力",
        "est_line": "預估 {d} · 約 {n} 天後",
        "est_soon": "預估 {d} · 即將出現",
        "all_done": "今年換季訊號皆已出現",
        "spring": "春裝上架", "summer": "夏裝主推", "autumn": "秋裝上架", "winter": "冬裝主推",
        "spring_items": "薄長袖、襯衫、防風輕外套",
        "summer_items": "短袖 T 恤、涼感衣、短褲",
        "autumn_items": "長袖襯衫、薄針織、防風外套",
        "winter_items": "大衣、羊毛衫、羽絨、發熱衣",
        "rule_up": "7 日均溫 ≥ {t}°C",
        "rule_down": "7 日均溫 < {t}°C",
        "insights_title": "商業決策重點摘要",
        "tag_plan": "檔期策略", "tag_shift": "檔期前移", "tag_stock": "備貨前置",
        "tag_season": "當前季相", "tag_rain": "防雨機能", "tag_extreme": "溫差極值",
        "ins_similar": "氣溫節奏與去年同期一致",
        "ins_similar_body": "近 30 天均溫差距僅 {d}°C，節奏穩定，可直接沿用去年的換季陳列與行銷節奏，不必過早促銷。",
        "ins_warmer": "比去年偏暖，輕薄商品提前佈局",
        "ins_warmer_body": "近 30 天均溫比去年高 {d}°C，回暖較快，建議透氣輕薄商品提前 1–2 週上陳列。",
        "ins_cooler": "比去年偏冷，保暖商品提前備貨",
        "ins_cooler_body": "近 30 天均溫比去年低 {d}°C，建議大衣、防風外套與保暖機能品提早入庫並排定主推檔期。",
        "ins_signal": "最近已觸發：{s}",
        "ins_signal_body": "今年 {d} 達到門檻（歷年平均 {a}）。目前主推品類：{items}。",
        "ins_signal_none": "目前尚無新增訊號",
        "ins_signal_none_body": "今年的換季門檻尚未觸發，請持續觀察 7 日均溫走勢。",
        "ins_wet": "雨量高峰：{m}最潮濕",
        "ins_wet_body": "歷年平均月雨量約 {x}mm，為全年最高。建議加強防潑水外套、防滑鞋與快乾商品的曝光。",
        "ins_hot_cold": "最熱 {h} · 最冷 {c}",
        "ins_hot_cold_body": "歷年月均溫最高 {a}°C、最低 {b}°C。涼感與重磅保暖兩大檔期的庫存與下單時點可以此為基準。",
        "sec1": "01 · 氣候走勢",
        "sec1_title": "週均氣溫區間與週降雨量",
        "sec1_sub": "上方看每週最低～最高溫與週均溫，下方看每週累積雨量。",
        "rng_all": "全部年份", "rng_1y": "近 1 年", "rng_6m": "近半年",
        "temp_axis": "氣溫 (°C)", "rain_axis": "週雨量 (mm)",
        "wk_avg": "週均溫", "wk_range": "週溫差區間", "wk_rain": "週降雨量",
        "wk_max": "週最高溫", "wk_min": "週最低溫",
        "sec2": "02 · 年度基準",
        "sec2_title": "歷年同月份比較",
        "sec2_sub": "各月份比歷年偏暖、偏冷，還是偏濕。",
        "m_temp": "均溫", "m_rain": "雨量", "m_days": "雨天數",
        "note_temp": "月均溫 (°C)",
        "note_rain": "月降雨量 (mm)",
        "note_days": "月降雨天數 (天) · 日雨量 ≥ 1mm 才算雨天",
        "year_suffix": "年",
        "sec3": "03 · 換季時序",
        "sec3_title": "換季訊號時間軸",
        "sec3_sub": "7 日均溫第一次跨過門檻的那一天，就是換季訊號。比較每年早晚，並預估今年。",
        "est_legend": "今年預估",
        "season": "換季時序",
        "hist_avg": "歷年平均",
        "status": "狀態",
        "status_reached": "已達成", "status_proj": "推估中",
        "not_reached": "尚未達成",
        "this_year_found": "今年已觸發",
        "est_label": "預估",
        "days_after": "{n} 天後",
        "today": "資料截止",
        "sec4": "04 · 商品企劃",
        "sec4_title": "月份穿著溫度帶分佈",
        "sec4_sub": "每個月有多少比例的日子落在各溫度帶（近 3 年合計），作為各月商品組合的參考比重。",
        "band_header": "溫度帶 / 建議品類",
        "hot": "炎熱 ≥28°C", "warm": "溫暖 24–28°C", "comf": "舒適 20–24°C",
        "cool": "微涼 16–20°C", "cold": "寒冷 <16°C",
        "hot_items": "背心、短袖 T 恤、涼感機能", "warm_items": "短袖襯衫、輕薄長褲",
        "comf_items": "薄長袖、針織衫、休閒長褲", "cool_items": "防風外套、衛衣、休閒夾克",
        "cold_items": "羊毛大衣、羽絨外套、發熱衣",
        "footnote": "資料說明：氣溫為 ECMWF ERA5 的 2 公尺再分析資料，雨天定義為日雨量 ≥ 1mm。換季訊號為 7 日均溫首次跨過門檻，且之後 7 天中至少 5 天維持在同一側。",
        "ask_ai": "問天氣 AI 顧問",
        "ai_title": "零售氣象 AI 顧問",
        "ai_hint": "輸入營運問題，AI 會根據氣溫、降雨與換季門檻資料回答。",
        "ai_placeholder": "例如：今年秋裝換季時機與備貨量建議？",
        "ai_examples": "快速提問：",
        "ai_q1_btn": "🎯 今年秋裝換季分析",
        "ai_q1": "今年秋裝換季比往年提早還是延後？建議重點備貨哪些品類？",
        "ai_q2_btn": "📦 冬季商品策略",
        "ai_q2": "請根據目前氣候走勢，預測今年冬裝主推時機，以及重磅保暖服飾的庫存配置。",
        "ai_send": "開始分析",
        "ai_thinking": "AI 顧問分析中…",
        "ai_unavailable": "尚未設定 GEMINI_API_KEY。請在 .streamlit/secrets.toml 加入 GEMINI_API_KEY = \"你的金鑰\" 後重新啟動。",
        "ai_error": "AI 回覆失敗：{e}",
        "ai_context": (
            "你是氣象資料分析助理。"
            "使用者可以自由詢問天氣、氣溫、降雨、歷年比較及換季問題。"
            "請優先根據提供的網站資料進行分析與計算。"
            "回答時引用具體年份、日期及數值。"
            "若使用者詢問服飾或商業決策，可以提出相關建議。"
            "不要編造資料中不存在的數據。"
            "如果資料不足以回答，請清楚說明。"
            "請使用繁體中文回答。"
        ),
        "load_error": "氣象資料讀取失敗，請確認網路連線：{e}",
        "loading": "正在從 Open-Meteo 取得歷史氣象資料…",
        "no_data": "樣本資料不足",
        "scroll_hint": "👉 左右滑動查看完整內容",
    },
    "en": {
        "live": "LIVE CLIMATE DATA",
        "data_until": "Data through {d}",
        "choose_city": "Select city",
        "north": "Northern Region",
        "central": "Central Region",
        "south": "Southern Region",
        "east": "Eastern Region",
        "islands": "Offshore Islands",
        "base_period": "Analysis period {a}–{b}",
        "hero_desc": "Three years of daily temperature and rainfall used to find the seasonal rhythm and year-over-year shifts, as a quantitative basis for apparel launches, stocking, campaign timing and inventory allocation.",
        "progress_title": "This year's season progress",
        "kpi_temp": "30-Day Mean Temp",
        "kpi_rain": "30-Day Rainfall",
        "kpi_days": "30-Day Rainy Days",
        "vs_last": "Last year {v}",
        "rain_def": "daily rain ≥ 1mm",
        "day_unit": " days",
        "warm_tag": "warmer", "cool_tag": "cooler", "flat_tag": "flat", "wet_tag": "wetter", "dry_tag": "drier",
        "next_signal": "Next seasonal action",
        "focus_label": "Focus",
        "est_line": "Est. {d} · in ~{n} days",
        "est_soon": "Est. {d} · imminent",
        "all_done": "All signals have occurred this year",
        "spring": "Spring Launch", "summer": "Summer Push", "autumn": "Autumn Launch", "winter": "Winter Push",
        "spring_items": "Light long sleeves, shirts, windbreakers",
        "summer_items": "T-shirts, shorts, cooling apparel",
        "autumn_items": "Long sleeves, knits, light jackets",
        "winter_items": "Coats, knitwear, down jackets, thermals",
        "rule_up": "7-day mean ≥ {t}°C",
        "rule_down": "7-day mean < {t}°C",
        "insights_title": "Executive insights",
        "tag_plan": "CAMPAIGN PLAN", "tag_shift": "LAUNCH EARLIER", "tag_stock": "STOCK EARLIER",
        "tag_season": "CURRENT SEASON", "tag_rain": "RAIN GEAR", "tag_extreme": "TEMP EXTREMES",
        "ins_similar": "Same rhythm as last year",
        "ins_similar_body": "The 30-day mean differs by only {d}°C. The rhythm is stable — keep last year's merchandising and campaign schedule, no need to discount early.",
        "ins_warmer": "Warmer than last year: launch light items earlier",
        "ins_warmer_body": "The 30-day mean is {d}°C above last year and warming faster. Move lightweight, breathable items onto the floor 1–2 weeks earlier.",
        "ins_cooler": "Cooler than last year: stock warm layers earlier",
        "ins_cooler_body": "The 30-day mean is {d}°C below last year. Warehouse coats, windbreakers and thermals early and schedule their feature window.",
        "ins_signal": "Latest triggered: {s}",
        "ins_signal_body": "Reached on {d} this year (historical average {a}). Focus categories: {items}.",
        "ins_signal_none": "No new signal yet",
        "ins_signal_none_body": "This year's seasonal threshold has not triggered. Keep watching the 7-day mean.",
        "ins_wet": "Rainfall peak: {m} is wettest",
        "ins_wet_body": "Average monthly rainfall is about {x}mm, the highest of the year. Push water-repellent jackets, non-slip shoes and quick-dry items.",
        "ins_hot_cold": "Hottest {h} · Coldest {c}",
        "ins_hot_cold_body": "Monthly means peak at {a}°C and bottom at {b}°C. Use these as the benchmark for cooling and heavy-warmth inventory timing.",
        "sec1": "01 · CLIMATE TREND",
        "sec1_title": "Weekly temperature range & rainfall",
        "sec1_sub": "Top: weekly min–max and mean temperature. Bottom: weekly cumulative rainfall.",
        "rng_all": "All years", "rng_1y": "Last 1 year", "rng_6m": "Last 6 months",
        "temp_axis": "Temperature (°C)", "rain_axis": "Weekly rain (mm)",
        "wk_avg": "Weekly mean", "wk_range": "Weekly range", "wk_rain": "Weekly rain",
        "wk_max": "Weekly high", "wk_min": "Weekly low",
        "sec2": "02 · YEAR-OVER-YEAR",
        "sec2_title": "Same-month comparison across years",
        "sec2_sub": "See at a gtter than past years.",
        "m_temp": "Temp", "m_rain": "Rainfall", "m_days": "Rainy days",
        "note_temp": "Monthly mean (°C)",
        "note_rain": "Monthly rainfall (mm)",
        "note_days": "Rainy days per month · a rainy day is ≥ 1mm",
        "year_suffix": "",
        "sec3": "03 · SEASON TIMING",
        "sec3_title": "Season-signal timeline",
        "sec3_sub": "The first day the 7-day mean crosses a threshold is the season signal. Compare early vs late years and estimate this year.",
        "est_legend": "This year (est.)",
        "season": "Milestone",
        "hist_avg": "Hist. avg",
        "status": "Status",
        "status_reached": "Reached", "status_proj": "Projected",
        "not_reached": "Not yet",
        "this_year_found": "Triggered this year",
        "est_label": "Estimated",
        "days_after": "in {n} days",
        "today": "Data cutoff",
        "sec4": "04 · MERCHANDISE PLANNING",
        "sec4_title": "Monthly clothing temperature bands",
        "sec4_sub": "Share of days in each month that fall into each temperature band (3-year total) — a guide for the monthly product mix.",
        "band_header": "Band / suggested categories",
        "hot": "Hot ≥28°C", "warm": "Warm 24–28°C", "comf": "Comfortable 20–24°C",
        "cool": "Cool 16–20°C", "cold": "Cold <16°C",
        "hot_items": "Tanks, tees, cooling wear", "warm_items": "Short-sleeve shirts, light pants",
        "comf_items": "Light long sleeves, knits, slacks", "cool_items": "Jackets, hoodies, light outerwear",
        "cold_items": "Coats, down jackets, thermals",
        "footnote": "Methodology: temperature is ECMWF ERA5 2 m reanalysis; a rainy day is rainfall ≥ 1mm. A season signal is the first day the 7-day mean crosses the threshold, with at least 5 of the next 7 days staying on the same side.",
        "ask_ai": "Ask Weather AI",
        "ai_title": "Retail Climate AI Advisor",
        "ai_hint": "Ask an operations question. The AI answers from the temperature, rainfall and season-threshold data.",
        "ai_placeholder": "e.g. When should we start the autumn launch and how much should we stock?",
        "ai_examples": "Quick questions:",
        "ai_q1_btn": "🎯 Autumn launch timing",
        "ai_q1": "Is this year's autumn transition earlier or later than usual? Which categories should we stock?",
        "ai_q2_btn": "📦 Winter strategy",
        "ai_q2": "Based on the current trend, when should the winter push start and how should heavy-warmth inventory be allocated?",
        "ai_send": "Analyze",
        "ai_thinking": "Analyzing…",
        "ai_unavailable": "GEMINI_API_KEY is not set. Add GEMINI_API_KEY = \"your-key\" to .streamlit/secrets.toml and restart.",
        "ai_error": "AI error: {e}",
        "ai_context": "You are a senior retail apparel climate advisor. Answer strictly from the data below with concise, strategic, commercially useful advice, in English.",
        "load_error": "Failed to load weather data: {e}",
        "loading": "Fetching historical weather from Open-Meteo…",
        "no_data": "Insufficient data",
        "scroll_hint": "👉 Scroll sideways to see everything",
    },
}
MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def esc(x) -> str:
    return _html.escape(str(x))


# =============================================================================
# 資料與計算
# =============================================================================
@st.cache_data(ttl=6 * 60 * 60, show_spinner=False)
def fetch_weather(city: str, start_iso: str, end_iso: str) -> pd.DataFrame:
    _, _, lat, lon = CITIES[city]
    params = {
        "latitude": lat, "longitude": lon,
        "start_date": start_iso, "end_date": end_iso,
        "daily": "temperature_2m_mean,temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "Asia/Taipei",
    }
    r = requests.get(API_URL, params=params, timeout=60)
    r.raise_for_status()
    d = r.json()["daily"]
    df = pd.DataFrame({
        "date": pd.to_datetime(d["time"]),
        "tmean": d["temperature_2m_mean"],
        "tmax": d["temperature_2m_max"],
        "tmin": d["temperature_2m_min"],
        "rain": d["precipitation_sum"],
    })
    df = df.dropna(subset=["tmean"]).reset_index(drop=True)
    df["rain"] = df["rain"].fillna(0.0)
    return df


def last30_metrics(df: pd.DataFrame) -> dict:
    end = df["date"].max()
    start = end - pd.Timedelta(days=29)
    cur = df[(df.date >= start) & (df.date <= end)]
    p_end = end - pd.DateOffset(years=1)
    p_start = p_end - pd.Timedelta(days=29)
    prev = df[(df.date >= p_start) & (df.date <= p_end)]
    has_prev = len(prev) >= 25
    return {
        "end": end,
        "temp": cur.tmean.mean(),
        "rain": cur.rain.sum(),
        "days": int((cur.rain >= RAINY_MM).sum()),
        "temp_prev": prev.tmean.mean() if has_prev else None,
        "rain_prev": prev.rain.sum() if has_prev else None,
        "days_prev": int((prev.rain >= RAINY_MM).sum()) if has_prev else None,
    }


def monthly_table(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["year"], d["month"] = d.date.dt.year, d.date.dt.month
    d["rainy"] = (d.rain >= RAINY_MM).astype(int)
    g = d.groupby(["year", "month"]).agg(
        temp=("tmean", "mean"), rain=("rain", "sum"), days=("rainy", "sum"), n=("tmean", "size")
    ).reset_index()

    return g


def norm_doy(ts) -> int:
    day = 28 if (ts.month == 2 and ts.day == 29) else ts.day
    return date(2001, ts.month, day).timetuple().tm_yday


def doy_to_md(doy: float):
    d = date(2001, 1, 1) + timedelta(days=int(round(doy)) - 1)
    return d.month, d.day


def find_signal(s7: pd.Series, year: int, thr: float, direction: str, start_md):
    seg = s7[(s7.index.year == year) & (s7.index >= pd.Timestamp(year, *start_md))].dropna()
    if seg.empty:
        return None
    cond = (seg >= thr) if direction == "up" else (seg < thr)
    vals = cond.to_numpy()
    for i in range(len(vals)):
        if not vals[i]:
            continue
        nxt = vals[i + 1:i + 8]
        if len(nxt) >= 7:
            ok = nxt.sum() >= 5
        else:
            ok = len(nxt) >= 3 and nxt.sum() >= int(np.ceil(len(nxt) * 5 / 7))
        if ok:
            return seg.index[i]
    return None


def compute_signals(df: pd.DataFrame, years: list[int], end: pd.Timestamp):
    s7 = df.set_index("date")["tmean"].rolling(7).mean()
    signals, summary = {}, {}
    for key, thr, direction, start_md in SEASONS:
        signals[key] = {y: find_signal(s7, y, thr, direction, start_md) for y in years}
        doys = [norm_doy(v) for v in signals[key].values() if v is not None]
        avg_md = doy_to_md(np.mean(doys)) if doys else None
        est = None
        if signals[key][years[-1]] is None and avg_md:
            est = date(years[-1], avg_md[0], avg_md[1])
        summary[key] = {"avg_md": avg_md, "est": est}
    return signals, summary


def temperature_bands(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["month"] = d.date.dt.month
    d["band"] = pd.cut(d.tmean, [-np.inf, 16, 20, 24, 28, np.inf],
                       labels=["cold", "cool", "comf", "warm", "hot"], right=False)
    ct = pd.crosstab(d.month, d.band).reindex(
        index=range(1, 13), columns=["hot", "warm", "comf", "cool", "cold"]).fillna(0)
    total = ct.sum(axis=1).replace(0, np.nan)
    return ct.div(total, axis=0) * 100


def mlabel(m: int, lang: str) -> str:
    return f"{m}月" if lang == "zh" else MONTHS_EN[m - 1]


def hex_rgb(c: str):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


# =============================================================================
# 樣式（含手機 RWD 與淺色主題強制保護，避免手機深色模式反黑與便當盒遮擋）
# =============================================================================
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Noto+Sans+TC:wght@400;500;700;900&family=JetBrains+Mono:wght@500;700;800&display=swap');

:root {
  color-scheme: light only;
  --font-sans: 'Plus Jakarta Sans', 'Noto Sans TC', -apple-system, 'Segoe UI', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  --bg-page: #EEF2F7;
  --bg-surface: #FFFFFF;
  --accent: #E05D38;
  --border: #D5DDE8;
  --shadow: 0 6px 22px -4px rgba(15,23,42,.08), 0 1px 3px rgba(15,23,42,.04);
  --shadow-hover: 0 14px 30px -6px rgba(15,23,42,.14);
}
html, body, [class*="css"], .stApp {
  font-family: var(--font-sans);
  color: #0F172A !important;
  background: var(--bg-page) !important;
  font-size: 17px;
  -webkit-font-smoothing: antialiased;
}
header[data-testid="stHeader"] { background: transparent !important; }
.block-container { padding: 1.2rem 2.2rem 5rem !important; max-width: 1500px !important; }

/* 導覽列 */
.exec-nav-bar {
  background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
  border-radius: 18px; padding: 18px 26px;
  display: flex; justify-content: space-between; align-items: center; gap: 14px;
  box-shadow: 0 10px 28px -6px rgba(15,23,42,.35);
}
.exec-left { display: flex; align-items: center; gap: 16px; }

.exec-logo {font-size:28px;line-height:1;color:#FFFFFF!important;white-space:nowrap;}
.exec-sub { font-family: var(--font-mono); font-size: 12px; letter-spacing: .16em; color: #FF9A78; font-weight: 700; }
.exec-title { font-size: 24px; font-weight: 800; color: #fff; letter-spacing: -.01em; margin-top: 2px; }
.exec-live {
  font-family: var(--font-mono); font-size: 12px; font-weight: 700; letter-spacing: .08em; color: #A7F3D0;
  background: rgba(16,185,129,.14); border: 1px solid rgba(16,185,129,.4);
  padding: 6px 14px; border-radius: 999px; white-space: nowrap;
}

/* Hero */
.hero-box {
  background: var(--bg-surface); border: 1px solid var(--border); border-radius: 22px;
  padding: 30px 34px; box-shadow: var(--shadow); margin: 16px 0 18px;
}
.hero-grid { display: grid; grid-template-columns: 1.5fr 1fr; gap: 34px; align-items: stretch; }
.badge-row { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 12px; }
.badge-primary { background: #FFF1EA; color: #C2410C; border: 1px solid #FDBA74; padding: 6px 14px; border-radius: 9px; font-size: 14.5px; font-weight: 700; }
.badge-neutral { background: #F1F5F9; color: #334155; border: 1px solid #CBD5E1; padding: 6px 14px; border-radius: 9px; font-size: 14.5px; font-weight: 600; }
.hero-city-title { font-size: clamp(2.6rem, 5.4vw, 4.8rem); font-weight: 900; letter-spacing: -.035em; line-height: 1.08; margin: 8px 0 14px; color: #0F172A; }
.hero-summary-text { font-size: 18px; color: #334155; line-height: 1.75; max-width: 780px; }

.prog-panel { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 16px; padding: 20px 22px; }
.prog-title { font-size: 14px; font-weight: 800; letter-spacing: .08em; color: #64748B; text-transform: uppercase; margin-bottom: 8px; }
.prog-row { display: flex; align-items: center; gap: 14px; padding: 11px 0; border-bottom: 1px dashed #D5DDE8; }
.prog-row:last-child { border-bottom: none; }
.prog-dot { width: 14px; height: 14px; border-radius: 50%; flex: 0 0 14px; background: #CBD5E1; }
.prog-row.ok .prog-dot { background: #10B981; box-shadow: 0 0 0 4px rgba(16,185,129,.18); }
.prog-row.wait .prog-dot { background: #fff; border: 3px solid var(--accent); }
.prog-name { flex: 1; font-size: 18px; font-weight: 800; color: #0F172A; }
.prog-name small { display: block; font-size: 13.5px; font-weight: 600; color: #64748B; margin-top: 1px; }
.prog-date { font-family: var(--font-mono); font-size: 22px; font-weight: 800; color: #0F172A; }
.prog-row.ok .prog-date { color: var(--accent); }

/* KPI */
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px; margin: 0 0 22px; }
.kpi {
  background: var(--bg-surface); border: 1px solid var(--border); border-radius: 20px;
  padding: 22px 26px; box-shadow: var(--shadow); transition: transform .2s, box-shadow .2s;
}
.kpi:hover { transform: translateY(-3px); box-shadow: var(--shadow-hover); }
.kpi-top { display: flex; justify-content: space-between; align-items: center; }
.kpi-label { font-size: 14px; font-weight: 800; color: #64748B; letter-spacing: .04em; }
.kpi-icon { font-size: 22px; }
.kpi .big { font-family: var(--font-mono); font-size: clamp(42px, 4.4vw, 62px); font-weight: 800; letter-spacing: -.04em; line-height: 1; margin: 14px 0 12px; font-variant-numeric: tabular-nums; color: #0F172A; }
.kpi .big small { font-size: 22px; font-weight: 700; margin-left: 4px; color: #64748B; letter-spacing: 0; }
.kpi .sub { font-size: 15px; color: #475569; line-height: 1.6; display: flex; flex-wrap: wrap; align-items: center; gap: 6px 8px; }
.pill { font-family: var(--font-mono); font-size: 13.5px; font-weight: 800; padding: 3px 10px; border-radius: 7px; }
.pill-warm { background: #FFF1E6; color: #C2410C; }
.pill-cool { background: #E0F0FF; color: #1D4ED8; }
.pill-flat { background: #EEF2F7; color: #475569; }
.kpi.dark { background: linear-gradient(135deg, #0F172A 0%, #243349 100%); border: 1px solid rgba(251,191,36,.5); color: #fff; }
.kpi.dark .kpi-label { color: #FBBF24; }
.kpi.dark .name { font-size: 32px; font-weight: 900; letter-spacing: -.02em; margin: 12px 0 10px; color: #fff; }
.kpi.dark .badge { display: inline-block; background: rgba(251,191,36,.18); color: #FDE68A; border: 1px solid rgba(251,191,36,.5); font-size: 14.5px; font-weight: 700; padding: 5px 12px; border-radius: 8px; }
.kpi.dark .items { font-size: 15px; color: #E2E8F0; line-height: 1.6; border-top: 1px solid rgba(255,255,255,.14); padding-top: 11px; margin-top: 14px; }

/* 摘要卡 */
.ins-title { font-size: 22px; font-weight: 800; margin: 6px 0 14px; display: flex; align-items: center; gap: 10px; color: #0F172A; }
.ins-title::before { content: ""; width: 6px; height: 24px; background: var(--accent); border-radius: 3px; }
.ins-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px; margin-bottom: 26px; }
.ins { background: var(--bg-surface); border: 1px solid var(--border); border-top: 4px solid #0F172A; border-radius: 16px; padding: 20px 22px; box-shadow: var(--shadow); }
.ins-tag { font-family: var(--font-mono); font-size: 12.5px; font-weight: 800; color: var(--accent); letter-spacing: .08em; margin-bottom: 8px; }
.ins .tt { font-size: 18.5px; font-weight: 800; line-height: 1.4; margin-bottom: 8px; color: #0F172A; }
.ins .bd { font-size: 15.5px; color: #475569; line-height: 1.75; }

/* 分析區塊 */
[class*="st-key-sec"] { background: var(--bg-surface); border: 1px solid var(--border); border-radius: 22px; padding: 28px 32px 24px; margin-bottom: 24px; box-shadow: var(--shadow); }
.eyebrow { color: var(--accent); font-weight: 800; font-size: 13.5px; letter-spacing: .12em; text-transform: uppercase; }
.sec-title { font-size: clamp(24px, 2.4vw, 32px); font-weight: 800; letter-spacing: -.02em; margin: 4px 0 6px; color: #0F172A; }
.sec-sub { font-size: 16.5px; color: #475569; line-height: 1.6; margin-bottom: 8px; }
.note-right { text-align: right; font-size: 14px; color: #64748B; margin-top: 8px; font-weight: 500; }

/* 規則卡 */
.rule-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin: 10px 0 18px; }
.rule-card { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 14px; padding: 14px 18px; }
.rule-name { font-size: 18px; font-weight: 800; color: #0F172A; }
.rule-cond { font-family: var(--font-mono); font-size: 15px; font-weight: 700; color: var(--accent); margin: 3px 0 4px; }
.rule-items { font-size: 14.5px; color: #64748B; line-height: 1.5; }

/* 表格 */
.table-scroll { width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch; border-radius: 14px; border: 1px solid var(--border); background: #fff; margin-top: 12px; }
.scroll-hint { display: none; font-size: 14px; color: #475569; background: #F1F5F9; padding: 8px 12px; border-radius: 8px; margin-top: 8px; text-align: center; font-weight: 600; }
.season-table { width: 100%; border-collapse: collapse; font-size: 16px; }
.season-table th { background: #F8FAFC; color: #334155; font-weight: 800; text-align: left; padding: 15px 20px; border-bottom: 2px solid #CBD5E1; white-space: nowrap; font-size: 15px; }
.season-table td { padding: 15px 20px; border-bottom: 1px solid #E2E8F0; font-family: var(--font-mono); font-weight: 600; white-space: nowrap; font-size: 16.5px; color: #0F172A; }
.season-table tr:hover td { background: #F8FAFC; }
.season-table td:first-child { font-family: var(--font-sans); font-weight: 800; font-size: 17px; }
.season-table td.avg { font-weight: 800; color: var(--accent); }
.tag-ok { background: #DCFCE7; color: #166534; padding: 4px 11px; border-radius: 7px; font-size: 14px; font-weight: 800; font-family: var(--font-sans); }
.tag-wait { background: #FEF3C7; color: #92400E; padding: 4px 11px; border-radius: 7px; font-size: 14px; font-weight: 800; font-family: var(--font-sans); }
.tag-none { background: #F1F5F9; color: #64748B; padding: 4px 11px; border-radius: 7px; font-size: 14px; font-family: var(--font-sans); }

/* 熱力圖 */
.table-scroll:has(.heat) {border:none!important;background:transparent!important;overflow-x:auto;}
.table-scroll .heat {width:100%;min-width:980px;border-collapse:separate!important;border-spacing:6px!important;table-layout:fixed;padding:0!important;}
.heat th,.heat td {border:none!important;outline:none!important;}
.heat th:first-child,.heat td.lab {width:220px!important;background:transparent!important;}
.heat td.cell {height:58px;border-radius:9px!important;background-clip:padding-box;}
.heat .bn {font-size:17px;font-weight:800;}
.heat .bi {font-size:13px;color:#64748B;}



.footnote { font-size: 14px; color: #64748B; margin: 8px 4px 40px; line-height: 1.8; }

/* Streamlit 元件強制淺色主題（防止手機深色模式反黑） */
div[data-testid="stSelectbox"] > div,
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
  border-radius: 12px !important;
  border-color: #CBD5E1 !important;
  background-color: #FFFFFF !important;
  color: #0F172A !important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"] {
  font-size: 16px !important;
  min-height: 48px;
}
div[data-testid="stSelectbox"] svg { fill: #334155 !important; }

div[data-testid="stSegmentedControl"] {
  background-color: #F1F5F9 !important;
  border-radius: 12px !important;
  padding: 3px !important;
}
div[data-testid="stSegmentedControl"] button {
  background-color: transparent !important;
  color: #334155 !important;
  font-size: 15px !important;
  font-weight: 700 !important;
  border-radius: 9px !important;
}
div[data-testid="stSegmentedControl"] button p { color: #334155 !important; }
button[data-testid="stBaseButton-segmented_controlActive"] {
  background-color: #0F172A !important;
  color: #FFFFFF !important;
}
button[data-testid="stBaseButton-segmented_controlActive"] p { color: #FFFFFF !important; }

/* 懸浮 AI 顧問按鈕 */
.st-key-ai_float { position: fixed; right: 28px; bottom: 28px; z-index: 9999; width: auto !important; }
.st-key-ai_float button {
  background: #0F172A !important; color: #fff !important;
  border-radius: 999px !important; border: 1px solid rgba(255,255,255,.25) !important;
  padding: 13px 24px !important; font-weight: 800 !important; font-size: 15.5px !important;
  box-shadow: 0 12px 28px -4px rgba(15,23,42,.45) !important;
}
.st-key-ai_float button p { color: #fff !important; font-size: 15.5px !important; }
[data-testid="stPopoverBody"] { min-width: 420px !important; border-radius: 18px !important; background: #FFFFFF !important; color: #0F172A !important; }

/* 平板與手機響應式調整 */
@media (max-width: 1100px) {
  .hero-grid { grid-template-columns: 1fr; }
  .kpi-row, .ins-row, .rule-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 680px) {
  .block-container { padding: 0.8rem 0.85rem 6rem !important; }
  .exec-nav-bar { flex-direction: column; align-items: flex-start; padding: 16px 18px; }
  .exec-title { font-size: 20px; }
  .hero-box { padding: 20px 18px; border-radius: 18px; }
  .hero-summary-text { font-size: 16px; }
  .kpi-row, .ins-row, .rule-grid { grid-template-columns: 1fr; gap: 12px; }
  .kpi { padding: 18px 20px; }
  [class*="st-key-sec"] { padding: 18px 14px; border-radius: 18px; }
  .sec-sub { font-size: 15px; }
  .season-table { min-width: 620px; }
  .scroll-hint { display: block; }
  .st-key-ai_float { right: 14px; bottom: 72px; }
  .st-key-ai_float button { padding: 10px 18px !important; font-size: 14px !important; }
  .st-key-ai_float button p { font-size: 14px !important; }
  [data-testid="stPopoverBody"] { min-width: 88vw !important; max-width: 92vw !important; }
}

/* 隱藏 Plotly X 軸滑鼠日期標籤 */
.js-plotly-plot .hoverlayer .axistext {
    display: none !important;
}

</style>
"""


# =============================================================================
# 圖表（手機防誤觸 + 高對比單點提示框）
# =============================================================================
FONT = "Plus Jakarta Sans, Noto Sans TC, sans-serif"


def plotly_show(fig: go.Figure) -> None:
    cfg = {
        "displayModeBar": False,
        "responsive": True,
        "scrollZoom": False,
        "doubleClick": False,
    }
    try:
        st.plotly_chart(fig, width="stretch", config=cfg)
    except TypeError:
        st.plotly_chart(fig, use_container_width=True, config=cfg)


def style_fig(fig: go.Figure, height: int) -> None:
    fig.update_layout(
        height=height,
        autosize=True,
        dragmode=False,
        margin=dict(l=48, r=16, t=48, b=36),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, size=14, color="#334155"),
        legend=dict(
            orientation="h", x=0, xanchor="left", y=1.12,
            font=dict(size=13.5, color="#1E293B", family=FONT),
            bgcolor="rgba(255,255,255,0)",
        ),
        hoverlabel=dict(
            bgcolor="#0F172A",
            font_size=13.5,
            font_family=FONT,
            font_color="#FFFFFF",
            bordercolor="#0F172A",
        ),
    )
    fig.update_xaxes(
        showgrid=False, linecolor="#CBD5E1", fixedrange=True,
        tickfont=dict(size=12.5, color="#475569"),
    )
    fig.update_yaxes(
        gridcolor="#EDF1F6", zeroline=False, fixedrange=True,
        tickfont=dict(size=12.5, color="#475569"),
        title_font=dict(size=13.5, color="#475569"),
    )


def section_header(eyebrow: str, title: str, sub: str) -> None:
    st.markdown(
        f'<div class="eyebrow">{esc(eyebrow)}</div>'
        f'<div class="sec-title">{esc(title)}</div>'
        f'<div class="sec-sub">{esc(sub)}</div>',
        unsafe_allow_html=True)



def plot_weekly(df: pd.DataFrame, rng: str, t) -> None:
    d = df.copy()
    if rng == "1y":
        d = d[d.date >= d.date.max() - pd.DateOffset(years=1)]
    elif rng == "6m":
        d = d[d.date >= d.date.max() - pd.DateOffset(months=6)]

    w = d.set_index("date").resample("7D").agg(
        tmean=("tmean", "mean"), tmax=("tmax", "max"),
        tmin=("tmin", "min"), rain=("rain", "sum")
    ).reset_index()

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Bar(
        x=w.date, y=w.rain, name=t("wk_rain"),
        marker_color="rgba(122,170,205,0.45)",
        marker_line_width=0,
        legendrank=3,
        hovertemplate="%{x|%Y/%m/%d}<br>週降雨量：%{y:.1f} mm<extra></extra>"
    ), secondary_y=True)

    fig.add_trace(go.Scatter(
        x=w.date, y=w.tmin, mode="lines",
        line=dict(width=0), showlegend=False, hoverinfo="skip"
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=w.date, y=w.tmax, mode="lines",
        line=dict(width=0), fill="tonexty",
        fillcolor="rgba(224,93,56,0.14)",
        name=t("wk_range"), legendrank=2,
        hoverinfo="skip", showlegend=True
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=w.date, y=w.tmean, mode="lines",
        line=dict(color="#E05D38", width=2.5),
        name=t("wk_avg"), legendrank=1,
        hovertemplate="%{x|%Y/%m/%d}<br>週均溫：%{y:.1f}°C<extra></extra>"
    ), secondary_y=False)



    style_fig(fig, 440)
    fig.update_layout(
        hovermode="x",
        bargap=0.15,
        margin=dict(l=48, r=48, t=58, b=38),
        legend=dict(orientation="h", x=0, y=1.12)
    )
    fig.update_xaxes(
        showspikes=True,
        spikemode="across",
        spikesnap="cursor",
        spikedash="solid",
        spikecolor="#94A3B8",
        spikethickness=1
    )






    fig.update_yaxes(
        title_text=t("rain_axis"),
        range=[0, max(30, w.rain.max() * 2.2)],
        showgrid=False, secondary_y=True
    )
    plotly_show(fig)




def plot_monthly(monthly: pd.DataFrame, years: list[int], metric: str, lang: str, t, as_bar=False) -> None:
    col = {"temp": "temp", "rain": "rain", "days": "days"}[metric]
    unit = {"temp": "°C", "rain": " mm", "days": " " + t("day_unit").strip()}[metric]
    fig = go.Figure()
    xs = list(range(1, 13))
    labels = [mlabel(m, lang) for m in xs]

    for i, y in enumerate(years):
        cur = monthly[monthly.year == y].set_index("month").reindex(xs)
        ys = cur[col].to_numpy()
        name = f"{y}{t('year_suffix')}"
        color = YEAR_COLORS[i]
        fmt = ".0f" if metric == "days" else ".1f"
        hover = f"<b>{name}%{{customdata}}：%{{y:{fmt}}}{unit}</b><extra></extra>"


        if not as_bar:
            last = y == years[-1]
            fig.add_trace(go.Scatter(
                x=xs, y=ys, customdata=labels,
                name=name, mode="lines+markers",
                line_shape="spline",
                line=dict(color=color, width=3.8 if last else 2.2),
                marker=dict(
                    size=8 if last else 5,
                    color="#FFFFFF" if last else color,
                    line=dict(width=2.5 if last else 0, color=color)
                ),
                connectgaps=False,
                hovertemplate=hover
            ))
        else:
            fig.add_trace(go.Bar(
                x=xs, y=ys, customdata=labels,
                name=name,
                marker=dict(color=color, line=dict(color="#FFFFFF", width=0.8)),
                hovertemplate=hover
            ))

    style_fig(fig, 430)
    fig.update_layout(
        barmode="group",
        bargap=0.22,
        hovermode="x",
        hoverdistance=100,
        margin=dict(l=48, r=14, t=58, b=36)
    )
    fig.update_xaxes(
        type="linear",
        range=[0.5, 12.5],
        tickmode="array",
        tickvals=xs,
        ticktext=labels,
        showspikes=True,
        spikemode="across",
        spikesnap="cursor",
        spikedash="solid",
        spikecolor="#94A3B8",
        spikethickness=1
    )
    fig.update_yaxes(title_text=t("note_" + metric).split(" · ")[0])
    plotly_show(fig)



def plot_timeline(signals: dict, summary: dict, years: list[int], end: pd.Timestamp, lang: str, t) -> None:
    keys = [s[0] for s in SEASONS]
    row_y = {k: len(keys) - 1 - i for i, k in enumerate(keys)}
    fig = go.Figure()
    for k, y in row_y.items():
        fig.add_shape(type="rect", x0=1, x1=366, y0=y - 0.36, y1=y + 0.36,
                      fillcolor="#F4F7FB", line=dict(color="#E2E8F0", width=1), layer="below")
    for yi, yr in enumerate(years):
        xs, ys, texts = [], [], []
        for k in keys:
            ts = signals[k].get(yr)
            if ts is None:
                continue
            xs.append(norm_doy(ts))
            ys.append(row_y[k])
            texts.append(f"{t(k)}<br>{ts.month}/{ts.day}")
        last = (yr == years[-1])
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="markers", name=str(yr), text=texts,
            marker=dict(size=15 if last else 11, color=YEAR_COLORS[yi], opacity=0.95,
                        line=dict(color="#FFFFFF", width=1.8)),
            hovertemplate=f"<b>{yr}</b> · %{{text}}<extra></extra>"))
    ex, ey, et = [], [], []
    for k in keys:
        if signals[k].get(years[-1]) is None and summary[k]["avg_md"]:
            m, d = summary[k]["avg_md"]
            ex.append(date(2001, m, d).timetuple().tm_yday)
            ey.append(row_y[k])
            et.append(f"{t(k)}<br>{t('est_label')} {m}/{d}")
    if ex:
        fig.add_trace(go.Scatter(
            x=ex, y=ey, mode="markers", name=t("est_legend"), text=et,
            marker=dict(size=15, color="#FFFFFF", line=dict(color=ACCENT, width=2.8)),
            hovertemplate="%{text}<extra></extra>"))
    fig.add_vline(x=norm_doy(end), line_width=1.5, line_color="#94A3B8", line_dash="dot",
                  annotation_text=t("today"), annotation_position="bottom left",
                  annotation_font=dict(size=11, color="#64748B"))
    for k in keys:
        cur = signals[k].get(years[-1])
        if cur is not None:
            label = f"<b>{cur.month}/{cur.day}</b><br><span style='font-size:11px;color:#059669'>✓ {t('this_year_found')}</span>"
            color = ACCENT
        elif summary[k]["est"]:
            e = summary[k]["est"]
            n = max(0, (pd.Timestamp(e) - end).days)
            label = f"<b>{e.month}/{e.day}</b><br><span style='font-size:11px;color:#B45309'>{t('est_label')} · {t('days_after', n=n)}</span>"
            color = INK
        else:
            label, color = f"<b>{t('not_reached')}</b>", "#94A3B8"
        fig.add_annotation(xref="paper", x=1.02, xanchor="left", y=row_y[k], yref="y", text=label,
                           showarrow=False, font=dict(color=color, size=13), align="left")
    style_fig(fig, 410)
    fig.update_layout(
        margin=dict(l=72, r=114, t=34, b=82),
        hovermode="closest",
        legend=dict(
            orientation="h", x=0.5, xanchor="center", y=-0.16, yanchor="top",
            font=dict(size=12.5, color="#1E293B"),
        ),
    )
    fig.update_traces(cliponaxis=False)
    tick_months = list(range(1, 13))
    fig.update_xaxes(
        range=[1, 366], tickmode="array", tickangle=0,
        tickvals=[date(2001, m, 1).timetuple().tm_yday for m in tick_months],
        ticktext=[mlabel(m, lang) for m in tick_months],
        showgrid=True, gridcolor="#EDF1F6", side="top",
        tickfont=dict(size=11, color="#64748B"),
    )

    fig.update_yaxes(
        range=[-0.6, len(keys) - 0.4], tickmode="array", tickvals=[row_y[k] for k in keys],
        ticktext=[f"<b>{t(k)}</b>" for k in keys], showgrid=False,
        tickfont=dict(size=13, color="#0F172A"),
    )
    plotly_show(fig)


# =============================================================================
# HTML 區塊
# =============================================================================
def season_rule(key: str, t) -> str:
    for k, thr, direction, _ in SEASONS:
        if k == key:
            return t("rule_up" if direction == "up" else "rule_down", t=thr)
    return ""


def rule_grid_html(t) -> str:
    h = '<div class="rule-grid">'
    for k, *_ in SEASONS:
        h += (
            f'<div class="rule-card">'
            f'<div class="rule-name">{esc(t(k))}</div>'
            f'<div class="rule-cond">{esc(season_rule(k, t))}</div>'
            f'<div class="rule-items">{esc(t(k + "_items"))}</div>'
            f'</div>'
        )
    return h + "</div>"


def progress_html(signals, summary, years, end, t) -> str:
    rows = ""
    for k, *_ in SEASONS:
        cur = signals[k].get(years[-1])
        if cur is not None:
            cls, right, sub = "ok", f"{cur.month}/{cur.day}", t("this_year_found")
        elif summary[k]["est"]:
            e = summary[k]["est"]
            n = max(0, (pd.Timestamp(e) - end).days)
            cls, right, sub = "wait", f"{e.month}/{e.day}", f"{t('est_label')} · {t('days_after', n=n)}"
        else:
            cls, right, sub = "none", "—", t("not_reached")
        rows += (f'<div class="prog-row {cls}"><span class="prog-dot"></span>'
                 f'<div class="prog-name">{esc(t(k))}<small>{esc(sub)}</small></div>'
                 f'<div class="prog-date">{right}</div></div>')
    return rows


def season_table_html(signals, summary, years, lang, t) -> str:
    head = [t("season")] + [f"{y}{t('year_suffix')}" for y in years] + [t("hist_avg"), t("status")]
    h = ('<table class="season-table"><thead><tr>' + "".join(f"<th>{esc(x)}</th>" for x in head)
         + "</tr></thead><tbody>")
    for k, *_ in SEASONS:
        h += f"<tr><td>{esc(t(k))}</td>"
        for y in years:
            ts = signals[k].get(y)
            if y == years[-1] and ts is not None:
                h += f'<td style="background:#FFF4EC;font-weight:800;color:#C2410C;">{ts.month}/{ts.day}</td>'
            elif ts is not None:
                h += f"<td>{ts.month}/{ts.day}</td>"
            else:
                h += f'<td style="color:#94A3B8;">{esc(t("not_reached"))}</td>'
        avg = summary[k]["avg_md"]
        h += f'<td class="avg">{avg[0]}/{avg[1]}</td>' if avg else '<td class="avg">—</td>'
        if signals[k].get(years[-1]) is not None:
            badge = f'<span class="tag-ok">● {esc(t("status_reached"))}</span>'
        elif summary[k]["est"]:
            badge = f'<span class="tag-wait">⏱ {esc(t("status_proj"))}</span>'
        else:
            badge = '<span class="tag-none">—</span>'
        h += f"<td>{badge}</td></tr>"
    return h + "</tbody></table>"


def heatmap_html(df: pd.DataFrame, lang: str, t) -> str:
    pct = temperature_bands(df)
    h = ('<table class="heat"><thead><tr><th>' + esc(t("band_header")) + "</th>"
         + "".join(f"<th>{esc(mlabel(m, lang))}</th>" for m in range(1, 13)) + "</tr></thead><tbody>")
    for key, color in BANDS:
        r, g, b = hex_rgb(color)
        h += (f'<tr><td class="lab"><div class="bn">{esc(t(key))}</div>'
              f'<div class="bi">{esc(t(key + "_items"))}</div></td>')
        for m in range(1, 13):
            v = pct.loc[m, key]
            if pd.isna(v) or v < 0.5:
                bg, txt, tc = "#F4F3F1", "", "#0F172A"
            else:
                alpha = min(0.95, 0.14 + (v / 100) * 0.95)
                bg = f"rgba({r},{g},{b},{alpha:.3f})"
                txt = f"{int(round(v))}%"
                tc = "#FFFFFF" if key in ("hot", "cool", "cold") and v >= 45 else "#0F172A"

            h += f'<td class="cell" style="background:{bg};color:{tc};">{txt}</td>'
        h += "</tr>"
    return h + "</tbody></table>"


def pill(v: float, unit: str, dec: int, up_tag: str, down_tag: str, flat_tag: str) -> str:
    if v > 0:
        return f'<span class="pill pill-warm">↗ +{v:.{dec}f}{unit} {up_tag}</span>'
    if v < 0:
        return f'<span class="pill pill-cool">↘ {v:.{dec}f}{unit} {down_tag}</span>'
    return f'<span class="pill pill-flat">→ 0{unit} {flat_tag}</span>'


def segmented(label: str, options: list, key: str, fmt):
    if hasattr(st, "segmented_control"):
        val = st.segmented_control(label, options, default=options[0], key=key,
                                   format_func=fmt, label_visibility="collapsed")
        return val or options[0]
    return st.radio(label, options, horizontal=True, key=key, format_func=fmt, label_visibility="collapsed")


# =============================================================================
# AI
# =============================================================================

def build_ai_context(city, metrics, signals, summary, years, monthly, df):
    end = df["date"].max()
    recent = df[df["date"] >= end - pd.Timedelta(days=29)]

    lines = [
        f"分析縣市：{CITIES[city][0]}",
        f"資料截止日：{end.date()}",
        f"資料起始日：{df['date'].min().date()}",
        f"有效氣象資料天數：{len(df)}",
        f"近30天平均氣溫：{metrics['temp']:.1f}°C",
        f"近30天累積降雨量：{metrics['rain']:.1f}mm",
        f"近30天雨天數：{metrics['days']}天",
    ]

    if metrics["temp_prev"] is not None:
        lines.extend([
            f"去年同期30天平均氣溫：{metrics['temp_prev']:.1f}°C",
            f"去年同期30天累積降雨：{metrics['rain_prev']:.1f}mm",
            f"去年同期雨天數：{metrics['days_prev']}天",
        ])

    lines.append("\n【歷年換季分析】")

    for key, threshold, direction, _ in SEASONS:
        condition = ">=" if direction == "up" else "<"
        lines.append(f"{key}：7日均溫 {condition} {threshold}°C")

        for year in years:
            value = signals[key].get(year)
            lines.append(
                f"{year}年：{value.date() if value is not None else '尚未觸發'}"
            )

        avg = summary[key]["avg_md"]
        if avg:
            lines.append(f"程式計算的換季日期平均：{avg[0]}/{avg[1]}")

    lines.append("\n【全部月份統計】")

    for _, r in monthly.iterrows():
        lines.append(
            f"{int(r['year'])}/{int(r['month']):02d}："
            f"均溫 {r['temp']:.1f}°C，"
            f"累積降雨 {r['rain']:.1f}mm，"
            f"雨天 {int(r['days'])}天，"
            f"有效資料 {int(r['n'])}天"
        )

    lines.append("\n【最近30天每日天氣】")

    for _, r in recent.iterrows():
        lines.append(
            f"{r['date'].date()}："
            f"均溫 {r['tmean']:.1f}°C，"
            f"最高 {r['tmax']:.1f}°C，"
            f"最低 {r['tmin']:.1f}°C，"
            f"降雨 {r['rain']:.1f}mm"
        )

    return "\n".join(lines)








DAILY_LIMIT = 10
PAUSE_SECONDS = 30 * 60

@st.cache_resource
def get_ai_state():
    return {
        "day": "",
        "count": 0,
        "paused_until": 0.0,
        "answers": {},
        "lock": threading.Lock()
    }


def ai_reply(question: str, context: str, t) -> str:
    try:
        key = st.secrets.get("OPENAI_API_KEY", "")
        model = st.secrets.get("OPENAI_MODEL", "gpt-6-luna")
    except Exception:
        key, model = "", "gpt-6-luna"

    if not key:
        return "尚未設定 OPENAI_API_KEY，請檢查 secrets.toml。"

    state = get_ai_state()
    cache_key = hashlib.sha256(
        (question.strip().lower() + "|" + context + "|" + model).encode("utf-8")
    ).hexdigest()

    with state["lock"]:
        today = datetime.now(ZoneInfo("Asia/Taipei")).date().isoformat()

        if state["day"] != today:
            state["day"] = today
            state["count"] = 0
            state["paused_until"] = 0.0

        if cache_key in state["answers"]:
            return state["answers"][cache_key]

        if state["count"] >= DAILY_LIMIT:
            return "今日 AI 問答已達 3 次上限，請明天再試。"

        if time.time() < state["paused_until"]:
            return "AI 服務暫時受到限制，請稍後再試。"

        state["count"] += 1

    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=key,
            max_retries=0,
            timeout=30.0
        )

        response = client.responses.create(
            model=model,
            instructions=t("ai_context"),
            input=f"DATA:\n{context}\n\nQUESTION:\n{question}",
            max_output_tokens=1500,
            store=False
        )

        answer = response.output_text

        if not answer:
            status = response.status
            reason = (
                response.incomplete_details.reason
                if response.incomplete_details else "unknown"
            )
            return f"AI 未產生文字。狀態：{status}，原因：{reason}"



        with state["lock"]:
            if len(state["answers"]) >= 200:
                state["answers"].clear()

            state["answers"][cache_key] = answer

        return answer

    except Exception as e:
        from openai import RateLimitError, APIStatusError

        if isinstance(e, RateLimitError):
            with state["lock"]:
                state["paused_until"] = time.time() + PAUSE_SECONDS
            return "AI 請求達到限制，請稍後再試。"

        if isinstance(e, APIStatusError) and e.status_code >= 500:
            return "AI 服務暫時繁忙，請稍後再試。"

        return f"AI 回覆失敗：{type(e).__name__}，請檢查 API 設定。"
# =============================================================================
# PDF 匯出
# =============================================================================
PDF_FONT = "MSung-Light"
pdfmetrics.registerFont(UnicodeCIDFont(PDF_FONT))


def pdf_clean(s) -> str:
    """CID 字型缺少的符號改成安全字元，並跳脫 XML。"""
    s = str(s).replace("≥", ">=").replace("●", "").replace("⏱", "").replace("✓", "")
    return _html.escape(s)


def pdf_monthly_chart(monthly, years, metric, title, lang, t):
    W, H = 175 * mm, 68 * mm
    d = Drawing(W, H)
    lp = LinePlot()
    lp.x, lp.y = 34, 26
    lp.width, lp.height = W - 50, H - 50
    data = []
    for y in years:
        cur = monthly[monthly.year == y].dropna(subset=[metric])
        pts = [(int(m), float(v)) for m, v in zip(cur.month, cur[metric])]
        data.append(pts or [(1, 0.0)])
    lp.data = data
    for i in range(len(years)):
        lp.lines[i].strokeColor = colors.HexColor(YEAR_COLORS[i])
        lp.lines[i].strokeWidth = 2.4 if i == len(years) - 1 else 1.4
    lp.xValueAxis.valueMin, lp.xValueAxis.valueMax = 1, 12
    lp.xValueAxis.valueSteps = list(range(1, 13))
    lp.xValueAxis.labelTextFormat = "%d"
    lp.yValueAxis.labelTextFormat = "%.0f"
    for ax in (lp.xValueAxis, lp.yValueAxis):
        ax.labels.fontName = PDF_FONT
        ax.labels.fontSize = 7
    lp.yValueAxis.gridStrokeColor = colors.HexColor("#E2E8F0")
    lp.yValueAxis.visibleGrid = True
    d.add(lp)
    d.add(String(4, H - 10, pdf_clean(title), fontName=PDF_FONT, fontSize=9,
                 fillColor=colors.HexColor("#0F172A")))
    x = W - 4 * 52
    for i, y in enumerate(years):          # 圖例
        d.add(Line(x, H - 7, x + 12, H - 7, strokeColor=colors.HexColor(YEAR_COLORS[i]), strokeWidth=2.5))
        d.add(String(x + 15, H - 10, f"{y}", fontName=PDF_FONT, fontSize=8))
        x += 52
    return d


def build_pdf(city_name, lang, t, metrics, signals, summary, years, monthly, df, cards) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=14 * mm, bottomMargin=14 * mm,
                            title=f"Taiwan Weather Analytics - {city_name}")
    ink = colors.HexColor(INK)
    accent = colors.HexColor(ACCENT)
    
    sty = lambda **kw: ParagraphStyle("x", fontName=PDF_FONT, **({"textColor": ink} | kw))
    s_title = sty(fontSize=22, leading=28)
    s_sub = sty(fontSize=9.5, leading=14, textColor=colors.HexColor("#64748B"))
    s_h = sty(fontSize=13, leading=18, spaceBefore=12, spaceAfter=6)
    s_body = sty(fontSize=9, leading=14, textColor=colors.HexColor("#334155"))
    s_cell = sty(fontSize=8, leading=10)
    s_note = sty(fontSize=7.5, leading=11, textColor=colors.HexColor("#64748B"))

    end = df["date"].max()
    P = lambda txt, st_: Paragraph(pdf_clean(txt), st_)
    story = []

    # --- 標題 ---
    story += [
        P("Taiwan Weather Analytics", sty(fontSize=9, leading=12, textColor=accent)),
        P(city_name, s_title),
        P(f"{t('base_period', a=years[0], b=years[-1])}  |  {t('data_until', d=end.date().isoformat())}", s_sub),
        Spacer(1, 8),
    ]

    # --- KPI ---
    def vs(cur, prev, unit, dec):
        if prev is None:
            return "—"
        return t("vs_last", v=f"{prev:.{dec}f}{unit}") + f"  ({cur - prev:+.{dec}f}{unit})"

    kpi = [
        [P(t("kpi_temp"), s_cell), P(t("kpi_rain"), s_cell), P(t("kpi_days"), s_cell)],
        [P(f"{metrics['temp']:.1f} °C", sty(fontSize=17, leading=22)),
         P(f"{metrics['rain']:.0f} mm", sty(fontSize=17, leading=22)),
         P(f"{metrics['days']} {t('day_unit').strip()}", sty(fontSize=17, leading=22))],
        [P(vs(metrics["temp"], metrics["temp_prev"], "°C", 1), s_note),
         P(vs(metrics["rain"], metrics["rain_prev"], "mm", 0), s_note),
         P(t("vs_last", v=f"{metrics['days_prev']}{t('day_unit')}") if metrics["days_prev"] is not None else "—", s_note)],
    ]
    kt = Table(kpi, colWidths=[60 * mm] * 3)
    kt.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#D5DDE8")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story += [kt]

    # --- 重點摘要 ---
    story.append(P(t("insights_title"), s_h))
    for tag, tt, bd in cards:
        story.append(P(f"[{tag}] {tt}", sty(fontSize=10, leading=15)))
        story.append(P(bd, s_body))
        story.append(Spacer(1, 5))

    # --- 換季時序表 ---
    story.append(P(t("sec3_title"), s_h))
    head = [t("season")] + [f"{y}{t('year_suffix')}" for y in years] + [t("hist_avg"), t("status")]
    rows = [[P(h, s_cell) for h in head]]
    for k, *_ in SEASONS:
        r = [P(t(k), s_cell)]
        for y in years:
            ts = signals[k].get(y)
            r.append(P(f"{ts.month}/{ts.day}" if ts is not None else t("not_reached"), s_cell))
        avg = summary[k]["avg_md"]
        r.append(P(f"{avg[0]}/{avg[1]}" if avg else "—", s_cell))
        if signals[k].get(years[-1]) is not None:
            r.append(P(t("status_reached"), s_cell))
        elif summary[k]["est"]:
            e = summary[k]["est"]
            r.append(P(f"{t('status_proj')} {e.month}/{e.day}", s_cell))
        else:
            r.append(P("—", s_cell))
        rows.append(r)
    n_cols = len(head)
    st_tbl = Table(rows, colWidths=[30 * mm] + [(150 * mm) / (n_cols - 1)] * (n_cols - 1))
    st_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(st_tbl)

    # --- 圖表 ---
    story.append(P(t("sec2_title"), s_h))
    story.append(pdf_monthly_chart(monthly, years, "temp", t("note_temp"), lang, t))
    story.append(Spacer(1, 6))
    story.append(pdf_monthly_chart(monthly, years, "rain", t("note_rain"), lang, t))

    # --- 溫度帶熱力表 ---
    story.append(P(t("sec4_title"), s_h))
    pct = temperature_bands(df)
    hrows = [[P(t("band_header").split(" / ")[0], s_cell)] + [P(mlabel(m, lang), s_cell) for m in range(1, 13)]]
    cell_styles = []
    for ri, (key, color) in enumerate(BANDS, start=1):
        row = [P(t(key), s_cell)]
        r_, g_, b_ = hex_rgb(color)
        for m in range(1, 13):
            v = pct.loc[m, key]
            if pd.isna(v) or v < 0.5:
                row.append("")
                continue
            a = min(0.95, 0.14 + (v / 100) * 0.95)
            blend = colors.Color((255 * (1 - a) + r_ * a) / 255, (255 * (1 - a) + g_ * a) / 255,
                                 (255 * (1 - a) + b_ * a) / 255)
            cell_styles.append(("BACKGROUND", (m, ri), (m, ri), blend))
            row.append(P(f"{int(round(v))}%", s_cell))
        hrows.append(row)
    ht = Table(hrows, colWidths=[38 * mm] + [11.5 * mm] * 12)
    ht.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ("GRID", (0, 0), (-1, -1), 1.2, colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ] + cell_styles))
    story.append(ht)

    story += [Spacer(1, 10), P(t("footnote"), s_note)]
    doc.build(story)
    return buf.getvalue()


def set_question(text: str) -> None:
    st.session_state["ai_q"] = text




# =============================================================================
# 主畫面
# =============================================================================
st.markdown(CSS, unsafe_allow_html=True)

# ---- 頂部：品牌列（左）＋ 城市 / 語言（右）同一排 ----
col_brand, col_city, col_lang = st.columns([5, 1.7, 1.4], vertical_alignment="center")
with col_lang:
    lang_choice = st.selectbox(
        "Language",
        ["繁體中文", "English"],
        index=1,
        key="ui_lang",
        label_visibility="collapsed"
    )
lang = "zh" if lang_choice == "繁體中文" else "en"


def t(key: str, **kw) -> str:
    s = T[lang][key]
    return s.format(**kw) if kw else s


with col_city:
    city = st.selectbox(
        t("choose_city"), list(CITIES.keys()), index=0, key="ui_city", label_visibility="collapsed",
        format_func=lambda k: CITIES[k][0] if lang == "zh" else k)
with col_brand:
    st.markdown(


        '<div class="exec-nav-bar"><div class="exec-left"><div class="exec-logo">☀︎ ☁︎</div><div>'
        '<div class="exec-sub">RETAIL CLIMATE INTELLIGENCE SYSTEM</div>'
        '<div class="exec-title">Taiwan Weather Analytics</div></div></div>'
        f'<div class="exec-live">● {esc(t("live"))}</div></div>',
        unsafe_allow_html=True)

# ---- 取資料 ----
today = datetime.now(ZoneInfo("Asia/Taipei")).date()
end_req = today - timedelta(days=DATA_LAG_DAYS)
start_req = date(end_req.year - 3, 1, 1)
try:
    with st.spinner(t("loading")):
        df = fetch_weather(city, start_req.isoformat(), end_req.isoformat())
    if df.empty:
        raise ValueError("empty dataset")
except Exception as exc:
    st.error(t("load_error", e=exc))
    st.stop()

end = df["date"].max()
years = list(range(end.year - 3, end.year + 1))
metrics = last30_metrics(df)
monthly = monthly_table(df)
signals, summary = compute_signals(df, years, end)

# ---- Hero ----
city_name = CITIES[city][0] if lang == "zh" else city
region = t(CITIES[city][1])
st.markdown(
    '<div class="hero-box"><div class="hero-grid"><div>'
    '<div class="badge-row">'
    f'<span class="badge-primary">📍 {esc(region)}</span>'
    f'<span class="badge-neutral">🗓 {esc(t("base_period", a=years[0], b=years[-1]))}</span>'
    f'<span class="badge-neutral">🕒 {esc(t("data_until", d=end.date().isoformat()))}</span>'
    '</div>'
    f'<div class="hero-city-title">{esc(city_name)}</div>'
    f'<div class="hero-summary-text">{esc(t("hero_desc"))}</div>'
    '</div>'
    f'<div class="prog-panel"><div class="prog-title">{esc(t("progress_title"))}</div>'
    f'{progress_html(signals, summary, years, end, t)}</div>'
    '</div></div>',
    unsafe_allow_html=True)

# ---- KPI ----
if metrics["temp_prev"] is not None:
    d_t = metrics["temp"] - metrics["temp_prev"]
    d_r = metrics["rain"] - metrics["rain_prev"]
    prev_t = f'{metrics["temp_prev"]:.1f}°C'
    prev_r = f'{metrics["rain_prev"]:.0f}mm'
    prev_d = f'{metrics["days_prev"]}{t("day_unit")}'
    sub_t = esc(t("vs_last", v=prev_t)) + " " + pill(round(d_t, 1), "°C", 1, t("warm_tag"), t("cool_tag"), t("flat_tag"))
    sub_r = esc(t("vs_last", v=prev_r)) + " " + pill(round(d_r), "mm", 0, t("wet_tag"), t("dry_tag"), t("flat_tag"))
    sub_d = esc(t("vs_last", v=prev_d)) + f' · {esc(t("rain_def"))}'
else:
    sub_t = sub_r = sub_d = "—"

next_key = next((k for k, *_ in SEASONS if signals[k].get(years[-1]) is None), None)
if next_key:
    est = summary[next_key]["est"]
    if est:
        n = (pd.Timestamp(est) - end).days
        est_line = (t("est_line", d=f"{est.month}/{est.day}", n=n) if n > 0
                    else t("est_soon", d=f"{est.month}/{est.day}"))
    else:
        est_line = t("not_reached")
    dark_card = (
        f'<div class="kpi-top"><div class="kpi-label">{esc(t("next_signal"))}</div><div class="kpi-icon">⚡</div></div>'
        f'<div class="name">{esc(t(next_key))}</div>'
        f'<div><span class="badge">{esc(est_line)}</span></div>'
        f'<div class="items">🎯 {esc(t("focus_label"))}：{esc(t(next_key + "_items"))}</div>')
else:
    dark_card = (
        f'<div class="kpi-top"><div class="kpi-label">{esc(t("next_signal"))}</div><div class="kpi-icon">✓</div></div>'
        f'<div class="name" style="font-size:24px;">{esc(t("all_done"))}</div>')

st.markdown(
    '<div class="kpi-row">'
    f'<div class="kpi"><div class="kpi-top"><div class="kpi-label">{esc(t("kpi_temp"))}</div><div class="kpi-icon">🌡️</div></div>'
    f'<div class="big">{metrics["temp"]:.1f}<small>°C</small></div><div class="sub">{sub_t}</div></div>'
    f'<div class="kpi"><div class="kpi-top"><div class="kpi-label">{esc(t("kpi_rain"))}</div><div class="kpi-icon">💧</div></div>'
    f'<div class="big" style="color:#0284C7">{metrics["rain"]:.0f}<small>mm</small></div><div class="sub">{sub_r}</div></div>'
    f'<div class="kpi"><div class="kpi-top"><div class="kpi-label">{esc(t("kpi_days"))}</div><div class="kpi-icon">🌧️</div></div>'
    f'<div class="big">{metrics["days"]}<small>{esc(t("day_unit").strip())}</small></div><div class="sub">{sub_d}</div></div>'
    f'<div class="kpi dark">{dark_card}</div>'
    '</div>',
    unsafe_allow_html=True)

# ---- 摘要卡 ----
cards = []
if metrics["temp_prev"] is not None:
    dd = metrics["temp"] - metrics["temp_prev"]
    if abs(dd) < 0.5:
        cards.append((t("tag_plan"), t("ins_similar"), t("ins_similar_body", d=f"{abs(dd):.1f}")))
    elif dd > 0:
        cards.append((t("tag_shift"), t("ins_warmer"), t("ins_warmer_body", d=f"{dd:.1f}")))
    else:
        cards.append((t("tag_stock"), t("ins_cooler"), t("ins_cooler_body", d=f"{abs(dd):.1f}")))
else:
    cards.append((t("tag_plan"), t("ins_similar"), t("no_data")))

found = [(signals[k][years[-1]], k) for k, *_ in SEASONS if signals[k].get(years[-1]) is not None]
if found:
    ts, k = max(found, key=lambda x: x[0])
    avg = summary[k]["avg_md"]
    cards.append((t("tag_season"), t("ins_signal", s=t(k)),
                  t("ins_signal_body", d=f"{ts.month}/{ts.day}", a=f"{avg[0]}/{avg[1]}" if avg else "—",
                    items=t(k + "_items"))))
else:
    cards.append((t("tag_season"), t("ins_signal_none"), t("ins_signal_none_body")))

mm = monthly.dropna(subset=["temp"]).groupby("month").agg(temp=("temp", "mean"), rain=("rain", "mean"))
if not mm.empty:
    wet = int(mm.rain.idxmax())
    hot, cold = int(mm.temp.idxmax()), int(mm.temp.idxmin())
    cards.append((t("tag_rain"), t("ins_wet", m=mlabel(wet, lang)), t("ins_wet_body", x=f"{mm.rain.max():.0f}")))
    cards.append((t("tag_extreme"), t("ins_hot_cold", h=mlabel(hot, lang), c=mlabel(cold, lang)),
                  t("ins_hot_cold_body", a=f"{mm.temp.max():.1f}", b=f"{mm.temp.min():.1f}")))
else:
    cards.append((t("tag_rain"), "—", t("no_data")))
    cards.append((t("tag_extreme"), "—", t("no_data")))

st.markdown(
    f'<div class="ins-title">{esc(t("insights_title"))}</div><div class="ins-row">' + "".join(
        f'<div class="ins"><div class="ins-tag">{esc(tag)}</div><div class="tt">{esc(tt)}</div>'
        f'<div class="bd">{esc(bd)}</div></div>' for tag, tt, bd in cards) + "</div>",
    unsafe_allow_html=True)
# ---- PDF 下載 ----
try:
    pdf_bytes = build_pdf(city_name, lang, t, metrics, signals, summary, years, monthly, df, cards)
    _, col_dl = st.columns([5, 1.6])
    with col_dl:
        st.download_button(
            "📄 下載 PDF 報告" if lang == "zh" else "📄 Download PDF report",
            data=pdf_bytes,
            file_name=f"weather_{city}_{end.date()}.pdf",
            mime="application/pdf",
            key="pdf_dl",
            use_container_width=True,
        )
except Exception as exc:
    st.warning(f"PDF 產生失敗：{exc}")

# ---- 01 氣候走勢 ----
with st.container(key="sec1"):
    col_a, col_b = st.columns([2.6, 1.4], vertical_alignment="center")
    with col_a:
        section_header(t("sec1"), t("sec1_title"), t("sec1_sub"))
    with col_b:
        rng = segmented("range", ["all", "1y", "6m"], "rng", lambda x: t("rng_" + x))
    plot_weekly(df, rng, t)






# ---- 02 年度基準 ----
with st.container(key="sec2"):
    section_header(t("sec2"), t("sec2_title"), t("sec2_sub"))
    c1, c2 = st.columns([5, 2], vertical_alignment="center")
    with c1:
        st.markdown("**📈 月份趨勢折線圖**" if lang == "zh" else "**📈 Monthly Trend**")
    with c2:
        line_metric = st.segmented_control("line_metric", ["temp", "rain", "days"], default="temp", key="line_metric", format_func=lambda x: t("m_" + x), label_visibility="collapsed")
    plot_monthly(monthly, years, line_metric or "temp", lang, t, as_bar=False)
    st.divider()
    c3, c4 = st.columns([5, 2], vertical_alignment="center")
    with c3:
        st.markdown("**📊 月份比較長條圖**" if lang == "zh" else "**📊 Monthly Bar Chart**")
    with c4:
        bar_metric = st.segmented_control("bar_metric", ["temp", "rain", "days"], default="rain", key="bar_metric_new", format_func=lambda x: t("m_" + x), label_visibility="collapsed")
    plot_monthly(monthly, years, bar_metric or "rain", lang, t, as_bar=True)







# ---- 03 換季時序 ----
with st.container(key="sec3"):
    section_header(t("sec3"), t("sec3_title"), t("sec3_sub"))
    st.markdown(rule_grid_html(t), unsafe_allow_html=True)
    plot_timeline(signals, summary, years, end, lang, t)
    st.markdown(
        f'<div class="scroll-hint">{esc(t("scroll_hint"))}</div>'
        f'<div class="table-scroll">{season_table_html(signals, summary, years, lang, t)}</div>',
        unsafe_allow_html=True)

# ---- 04 商品企劃 ----
with st.container(key="sec4"):
    section_header(t("sec4"), t("sec4_title"), t("sec4_sub"))
    st.markdown(
        f'<div class="scroll-hint">{esc(t("scroll_hint"))}</div>'
        f'<div class="table-scroll">{heatmap_html(df, lang, t)}</div>',
        unsafe_allow_html=True)

st.markdown(f'<div class="footnote">{esc(t("footnote"))}</div>', unsafe_allow_html=True)


# ---- 右下角 AI ----
with st.container(key="ai_float"):
    with st.popover("💬 " + t("ask_ai")):
        st.markdown(f"### {t('ai_title')}")
        st.caption(t("ai_hint"))
        q = st.text_area("q", placeholder=t("ai_placeholder"), key="ai_q",
                         label_visibility="collapsed", height=100)
        st.markdown(f"<div style='font-size:14px;color:#64748B;margin:6px 0 4px;'>{esc(t('ai_examples'))}</div>",
                    unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.button(t("ai_q1_btn"), key="btn_q1", on_click=set_question, args=(t("ai_q1"),))
        with c2:
            st.button(t("ai_q2_btn"), key="btn_q2", on_click=set_question, args=(t("ai_q2"),))
        if st.button(t("ai_send"), key="ai_send"):
            if q.strip():
                with st.spinner(t("ai_thinking")):
                    ctx = build_ai_context(city, metrics, signals, summary, years, monthly, df)
                    st.session_state["ai_answer"] = ai_reply(q.strip(), ctx, t)
        if st.session_state.get("ai_answer"):
            st.divider()
            st.markdown(st.session_state["ai_answer"])
