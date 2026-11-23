# -*- coding: utf-8 -*-
# cd C:\Users\yijen\Python\weather_app .\.venv\Scripts\python.exe -m streamlit run main.py
from __future__ import annotations

import html as _html
from datetime import date, timedelta

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from plotly.subplots import make_subplots

st.set_page_config(page_title="Taiwan Weather Analytics", page_icon="🌤", layout="wide")

# =============================================================================
# 設定
# =============================================================================
API_URL = "https://archive-api.open-meteo.com/v1/archive"
DATA_LAG_DAYS = 3          # 歷史資料約晚 3 天（PDF：今天 11/23 → 資料至 11/20）
RAINY_MM = 1.0             # 雨天定義：日雨量 >= 1mm
MIN_DAYS_PER_MONTH = 20    # 資料不足 20 天的月份不顯示

# 城市：key -> (中文名, 區域 key, 緯度, 經度)
CITIES = {
    "Taipei":     ("台北市", "north",   25.0330, 121.5654),
    "New Taipei": ("新北市", "north",   25.0120, 121.4650),
    "Taoyuan":    ("桃園市", "north",   24.9936, 121.3010),
    "Hsinchu":    ("新竹市", "north",   24.8039, 120.9647),
    "Yilan":      ("宜蘭縣", "east",    24.7570, 121.7530),
    "Taichung":   ("台中市", "central", 24.1477, 120.6736),
    "Chiayi":     ("嘉義市", "south",   23.4801, 120.4491),
    "Tainan":     ("台南市", "south",   22.9999, 120.2270),
    "Kaohsiung":  ("高雄市", "south",   22.6273, 120.3014),
    "Hualien":    ("花蓮縣", "east",    23.9772, 121.6044),
    "Taitung":    ("台東縣", "east",    22.7583, 121.1444),
}

# 換季訊號：(key, 門檻°C, 方向, 搜尋起算 (月,日))
SEASONS = [
    ("spring", 20, "up",   (1, 1)),
    ("summer", 26, "up",   (3, 1)),
    ("autumn", 25, "down", (8, 1)),
    ("winter", 18, "down", (10, 1)),
]

# 穿著溫度帶：(key, 色碼)  由熱到冷
BANDS = [
    ("hot",  "#E0603F"),
    ("warm", "#F0A35E"),
    ("comf", "#D9C56A"),
    ("cool", "#8FC0CF"),
    ("cold", "#6F86A8"),
]

YEAR_COLORS = ["#B8C4D3", "#7B93AE", "#2F4568", "#DA784C"]  # 舊 → 今年
ACCENT = "#DA784C"
INK = "#1C2434"

# =============================================================================
# 多語系
# =============================================================================
T = {
    "zh": {
        "eyebrow": "TAIWAN WEATHER ANALYTICS",
        "app_title": "台灣天氣換季分析",
        "data_until": "資料更新至 {d}",
        "source": "來源：Open-Meteo 歷史氣象",
        "choose_city": "選擇城市",
        "language": "語言 / Language",
        "north": "北部", "central": "中部", "south": "南部", "east": "東部",
        "hero_desc": "以近 3 年每日氣溫與降雨，找出換季節奏、比較今年與往年差異，作為商品上架與檔期規劃的依據。",
        "kpi_temp": "近 30 天均溫",
        "kpi_rain": "近 30 天雨量",
        "kpi_days": "近 30 天雨天",
        "vs_last": "去年同期 {v}",
        "rain_def": "（日雨量 ≥1mm）",
        "day_unit": "天",
        "next_signal": "下一個換季訊號",
        "est_line": "預估 {d} ・ 約 {n} 天後",
        "est_soon": "預估 {d} ・ 即將出現",
        "all_done": "今年換季訊號皆已出現",
        "spring": "春裝上架", "summer": "夏裝主推", "autumn": "秋裝上架", "winter": "冬裝主推",
        "spring_items": "薄長袖、襯衫、輕外套",
        "summer_items": "短袖、短褲、涼感衣",
        "autumn_items": "長袖、針織、薄外套",
        "winter_items": "大衣、毛衣、發熱衣",
        "rule_up": "7日均溫 ≥ {t}°C",
        "rule_down": "7日均溫 < {t}°C",
        "ins_similar": "與去年同期相近",
        "ins_similar_body": "近 30 天均溫差距僅 {d}°C，可沿用去年同期的上架節奏。",
        "ins_warmer": "比去年同期偏暖",
        "ins_warmer_body": "近 30 天均溫較去年同期高 {d}°C，輕薄商品可考慮提早上架。",
        "ins_cooler": "比去年同期偏冷",
        "ins_cooler_body": "近 30 天均溫較去年同期低 {d}°C，保暖商品可考慮提早備貨。",
        "ins_signal": "最近訊號：{s}",
        "ins_signal_body": "今年 {d} 出現，歷年平均約 {a}。主推：{items}。",
        "ins_signal_none": "今年尚無訊號",
        "ins_signal_none_body": "今年的換季訊號尚未出現，請持續觀察 7 日均溫。",
        "ins_wet": "{m}最潮濕",
        "ins_wet_body": "平均月雨量約 {x}mm，適合規劃外套、雨鞋、快乾材質商品。",
        "ins_hot_cold": "最熱 {h} ・ 最冷 {c}",
        "ins_hot_cold_body": "均溫約 {a}°C 與 {b}°C，涼感與發熱商品的庫存高峰可依此安排。",
        "sec1": "01 · 長期走勢",
        "sec1_title": "溫度與降雨週趨勢",
        "sec1_sub": "色帶為每週最低～最高溫，線為週均溫，柱為週雨量。",
        "rng_all": "全部", "rng_1y": "近 1 年", "rng_6m": "近半年",
        "temp_axis": "氣溫 (°C)", "rain_axis": "週雨量 (mm)",
        "week_start": "{d} 起一週",
        "wk_avg": "週均溫", "wk_range": "最低～最高", "wk_rain": "週雨量",
        "sec2": "02 · 年度對比",
        "sec2_title": "同月份逐年比較",
        "sec2_sub": "看今年是偏暖、偏冷，還是偏濕。",
        "m_temp": "溫度", "m_rain": "雨量", "m_days": "雨天數",
        "note_temp": "月均溫 (°C) ・ 資料不足 20 天的月份不顯示",
        "note_rain": "月雨量 (mm) ・ 資料不足 20 天的月份不顯示",
        "note_days": "雨天數 (天) ・ 資料不足 20 天的月份不顯示",
        "year_suffix": "年",
        "sec3": "03 · 換季時機",
        "sec3_title": "換季訊號時間軸",
        "sec3_sub": "以「7 日平均氣溫」首次跨越門檻的日期作為換季訊號，比較每年的提早或延後，並推估今年時間點。",
        "est_legend": "今年預估",
        "season": "訊號",
        "hist_avg": "歷年平均",
        "not_reached": "未達",
        "this_year_found": "今年已出現",
        "est_label": "預估",
        "days_after": "{n} 天後",
        "today": "資料截止",
        "sec4": "04 · 商品企劃",
        "sec4_title": "穿著溫度帶分佈",
        "sec4_sub": "每個月有多少比例的日子落在各溫度帶（近 3 年合計），可作為各月商品組合的參考比重。",
        "hot": "炎熱 ≥28°C", "warm": "溫暖 24–28°C", "comf": "舒適 20–24°C",
        "cool": "微涼 16–20°C", "cold": "寒冷 <16°C",
        "hot_items": "背心、短袖、涼感", "warm_items": "短袖、薄襯衫",
        "comf_items": "薄長袖、針織", "cool_items": "外套、衛衣", "cold_items": "大衣、羽絨、發熱衣",
        "footnote": "溫度為每日 2 公尺氣溫（ERA5 再分析資料），雨天定義為日雨量 ≥ 1mm。換季日期以 7 日均溫首次跨越門檻、且之後 7 天中至少 5 天維持同側判定。",
        "ask_ai": "問天氣 AI",
        "ai_title": "問天氣 AI",
        "ai_placeholder": "例如：今年秋裝上架會比去年早嗎？",
        "ai_send": "送出",
        "ai_thinking": "思考中…",
        "ai_unavailable": "尚未設定 GEMINI_API_KEY。請在 .streamlit/secrets.toml 加入 GEMINI_API_KEY = \"你的金鑰\" 後重新啟動。",
        "ai_error": "AI 回覆失敗：{e}",
        "ai_context": "你是台灣服飾業的天氣分析助理。只能根據下方資料回答，使用繁體中文，簡潔、具體；若資料不足請直說。",
        "load_error": "無法取得天氣資料：{e}",
        "loading": "正在取得 Open-Meteo 歷史氣象資料…",
        "no_data": "資料不足",
        "month_fmt": "{m}月",
    },
    "en": {
        "eyebrow": "TAIWAN WEATHER ANALYTICS",
        "app_title": "Taiwan Seasonal Weather Analytics",
        "data_until": "Data through {d}",
        "source": "Source: Open-Meteo Historical Weather",
        "choose_city": "Choose city",
        "language": "語言 / Language",
        "north": "North", "central": "Central", "south": "South", "east": "East",
        "hero_desc": "Uses 3 years of daily temperature and rainfall to find the seasonal rhythm and compare this year with past years, to guide merchandise launches and campaign planning.",
        "kpi_temp": "30-DAY AVG TEMP",
        "kpi_rain": "30-DAY RAINFALL",
        "kpi_days": "30-DAY RAINY DAYS",
        "vs_last": "Last year {v}",
        "rain_def": "(daily rain ≥1mm)",
        "day_unit": " days",
        "next_signal": "NEXT SEASON SIGNAL",
        "est_line": "Est. {d} · in ~{n} days",
        "est_soon": "Est. {d} · imminent",
        "all_done": "All signals have occurred this year",
        "spring": "Spring launch", "summer": "Summer push", "autumn": "Autumn launch", "winter": "Winter push",
        "spring_items": "Light long sleeves, shirts, light jackets",
        "summer_items": "Tees, shorts, cooling fabrics",
        "autumn_items": "Long sleeves, knits, light outerwear",
        "winter_items": "Coats, sweaters, thermal wear",
        "rule_up": "7-day avg ≥ {t}°C",
        "rule_down": "7-day avg < {t}°C",
        "ins_similar": "Similar to last year",
        "ins_similar_body": "The 30-day mean differs by only {d}°C, so last year's launch timing can be reused.",
        "ins_warmer": "Warmer than last year",
        "ins_warmer_body": "The 30-day mean is {d}°C higher than last year; consider launching light items earlier.",
        "ins_cooler": "Cooler than last year",
        "ins_cooler_body": "The 30-day mean is {d}°C lower than last year; consider stocking warm items earlier.",
        "ins_signal": "Latest signal: {s}",
        "ins_signal_body": "Appeared on {d} this year; historical average {a}. Push: {items}.",
        "ins_signal_none": "No signal yet this year",
        "ins_signal_none_body": "This year's seasonal signals have not appeared yet. Keep watching the 7-day mean.",
        "ins_wet": "{m} is the wettest",
        "ins_wet_body": "Average monthly rainfall is about {x}mm — plan outerwear, rain shoes and quick-dry items.",
        "ins_hot_cold": "Hottest {h} · Coldest {c}",
        "ins_hot_cold_body": "Mean temperatures of about {a}°C and {b}°C — time cooling and thermal inventory peaks accordingly.",
        "sec1": "01 · LONG-TERM TREND",
        "sec1_title": "Weekly temperature & rainfall",
        "sec1_sub": "Band = weekly min–max, line = weekly mean temp, bars = weekly rainfall.",
        "rng_all": "All", "rng_1y": "Last 1 yr", "rng_6m": "Last 6 mo",
        "temp_axis": "Temperature (°C)", "rain_axis": "Weekly rain (mm)",
        "week_start": "Week of {d}",
        "wk_avg": "Weekly mean", "wk_range": "Min–Max", "wk_rain": "Weekly rain",
        "sec2": "02 · YEAR OVER YEAR",
        "sec2_title": "Same-month comparison",
        "sec2_sub": "Is this year warmer, cooler or wetter?",
        "m_temp": "Temp", "m_rain": "Rain", "m_days": "Rainy days",
        "note_temp": "Monthly mean (°C) · months with <20 days of data hidden",
        "note_rain": "Monthly rainfall (mm) · months with <20 days of data hidden",
        "note_days": "Rainy days · months with <20 days of data hidden",
        "year_suffix": "",
        "sec3": "03 · SEASON TIMING",
        "sec3_title": "Season-signal timeline",
        "sec3_sub": "The first date the 7-day mean temperature crosses a threshold is the season signal; compare early/late years and estimate this year.",
        "est_legend": "This year (est.)",
        "season": "Signal",
        "hist_avg": "Hist. avg",
        "not_reached": "Not yet",
        "this_year_found": "Occurred this year",
        "est_label": "Est.",
        "days_after": "in {n} days",
        "today": "Data end",
        "sec4": "04 · MERCHANDISE PLANNING",
        "sec4_title": "Clothing temperature bands",
        "sec4_sub": "Share of days in each month falling into each band (3-year total) — a guide for monthly product mix.",
        "hot": "Hot ≥28°C", "warm": "Warm 24–28°C", "comf": "Comfortable 20–24°C",
        "cool": "Cool 16–20°C", "cold": "Cold <16°C",
        "hot_items": "Tanks, tees, cooling wear", "warm_items": "Tees, light shirts",
        "comf_items": "Light long sleeves, knits", "cool_items": "Jackets, sweatshirts", "cold_items": "Coats, down, thermals",
        "footnote": "Temperature is daily 2 m air temperature (ERA5 reanalysis); a rainy day is daily rainfall ≥ 1mm. A season signal is the first day the 7-day mean crosses the threshold with at least 5 of the next 7 days staying on the same side.",
        "ask_ai": "Ask Weather AI",
        "ai_title": "Ask Weather AI",
        "ai_placeholder": "e.g. Will autumn launch be earlier than last year?",
        "ai_send": "Send",
        "ai_thinking": "Thinking…",
        "ai_unavailable": "GEMINI_API_KEY is not set. Add GEMINI_API_KEY = \"your-key\" to .streamlit/secrets.toml and restart.",
        "ai_error": "AI reply failed: {e}",
        "ai_context": "You are a weather analysis assistant for a Taiwan apparel business. Answer ONLY from the data below, in English, concisely and concretely; say so if data is insufficient.",
        "load_error": "Could not load weather data: {e}",
        "loading": "Fetching Open-Meteo historical weather…",
        "no_data": "Not enough data",
        "month_fmt": "",
    },
}
MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def esc(x) -> str:
    return _html.escape(str(x))


# =============================================================================
# 資料
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


# =============================================================================
# 分析
# =============================================================================
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
    for c in ("temp", "rain", "days"):
        g.loc[g.n < MIN_DAYS_PER_MONTH, c] = np.nan
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
        else:  # 資料尾端：寬鬆判斷
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
    ct = pd.crosstab(d.month, d.band).reindex(index=range(1, 13), columns=["hot", "warm", "comf", "cool", "cold"]).fillna(0)
    total = ct.sum(axis=1).replace(0, np.nan)
    return ct.div(total, axis=0) * 100


# =============================================================================
# 版面 / 樣式
# =============================================================================
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@600;700;900&family=Noto+Sans+TC:wght@400;500;700&family=JetBrains+Mono:wght@400;500;700&display=swap');
html, body, [class*="css"], .stApp { font-family: 'Noto Sans TC', 'Microsoft JhengHei', sans-serif; color: #1C2434; }
.stApp { background: #FDF8F3; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.6rem; padding-bottom: 5rem; max-width: 1180px; }
.eyebrow { font-family: 'JetBrains Mono', monospace; font-size: 11px; letter-spacing: .12em; color: #8A8F9A; text-transform: uppercase; }
.serif { font-family: 'Noto Serif TC', 'PMingLiU', serif; }
.brand-title { font-family: 'Noto Serif TC', serif; font-size: 26px; font-weight: 700; margin-top: 2px; }
.meta { text-align: right; font-size: 12px; color: #6B7280; line-height: 1.5; }
.meta b { font-family: 'JetBrains Mono', monospace; color: #1C2434; }
.hero-region { margin-top: 26px; }
.hero-city { font-family: 'Noto Serif TC', serif; font-size: 58px; font-weight: 900; line-height: 1.15; margin: 4px 0 8px; }
.hero-desc { max-width: 560px; color: #4B5563; font-size: 15px; line-height: 1.7; }
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); margin: 24px 0 14px; border: 1px solid #EADFD3; border-radius: 16px; overflow: hidden; background: #fff; }
.kpi { padding: 18px 22px; border-right: 1px solid #EADFD3; }
.kpi .big { font-family: 'JetBrains Mono', monospace; font-size: 38px; font-weight: 700; margin: 6px 0 2px; }
.kpi .big small { font-size: 16px; font-weight: 500; margin-left: 2px; }
.kpi .sub { font-size: 12.5px; color: #6B7280; }
.kpi .up { color: #DA784C; font-family: 'JetBrains Mono', monospace; }
.kpi.dark { background: #1C2434; color: #fff; border-right: none; }
.kpi.dark .eyebrow { color: #AEB6C4; }
.kpi.dark .name { font-family: 'Noto Serif TC', serif; font-size: 26px; font-weight: 700; margin: 8px 0 4px; }
.kpi.dark .sub { color: #D5DAE3; }
.kpi.dark .items { font-size: 12px; color: #AEB6C4; margin-top: 4px; }
.ins-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 22px; }
.ins { background: #FDF1E8; border: 1px solid #F3DCCB; border-radius: 14px; padding: 14px 16px; }
.ins .ic { color: #DA784C; font-size: 15px; }
.ins .tt { font-weight: 700; font-size: 15px; margin: 6px 0 4px; }
.ins .bd { font-size: 12.5px; color: #4B5563; line-height: 1.6; }
[class*="st-key-sec"] { background: #fff; border: 1px solid #EADFD3; border-radius: 18px; padding: 22px 24px 14px; margin-bottom: 20px; }
.sec-title { font-family: 'Noto Serif TC', serif; font-size: 25px; font-weight: 700; margin: 2px 0 2px; }
.sec-sub { font-size: 13px; color: #6B7280; margin-bottom: 6px; }
.note-right { text-align: right; font-size: 12px; color: #6B7280; }
.season-table { width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 14px; }
.season-table th { text-align: left; font-weight: 500; color: #6B7280; padding: 9px 6px; border-bottom: 1px solid #EEE5DB; }
.season-table td { padding: 10px 6px; border-bottom: 1px solid #F3ECE4; font-family: 'JetBrains Mono', monospace; }
.season-table td:first-child { font-family: 'Noto Sans TC', sans-serif; font-weight: 500; }
.season-table td.avg { font-weight: 700; }
.heat { width: 100%; border-collapse: separate; border-spacing: 5px; table-layout: fixed; margin-top: 6px; }
.heat th { font-size: 11px; font-weight: 400; color: #8A8F9A; text-align: center; padding-bottom: 2px; }
.heat td.cell { height: 40px; border-radius: 8px; text-align: center; font-size: 11px; font-weight: 700; color: #1C2434; }
.heat td.lab { width: 150px; text-align: left; padding-right: 8px; }
.heat .bn { font-size: 13px; font-weight: 700; }
.heat .bi { font-size: 11px; color: #8A8F9A; }
.footnote { font-size: 12px; color: #8A8F9A; margin: 4px 0 24px; }
.st-key-ai_float { position: fixed; right: 24px; bottom: 24px; z-index: 1000; width: auto !important; }
.st-key-ai_float button { background: #1C2434; color: #fff; border-radius: 999px; border: none; padding: 10px 18px; font-weight: 700; }
.st-key-ai_float button:hover { background: #2F4568; color: #fff; }
[data-testid="stPopoverBody"] { min-width: 380px; }
@media (max-width: 900px) {
  .kpi-row, .ins-row { grid-template-columns: 1fr 1fr; }
  .hero-city { font-size: 42px; }
}
</style>
"""


def plotly_show(fig: go.Figure) -> None:
    cfg = {"displayModeBar": False}
    try:
        st.plotly_chart(fig, width="stretch", config=cfg)
    except TypeError:  # 舊版 Streamlit
        st.plotly_chart(fig, use_container_width=True, config=cfg)


def style_fig(fig: go.Figure, height: int) -> None:
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Noto Sans TC, Microsoft JhengHei, sans-serif", size=12, color="#4B5563"),
        legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.12),
        hoverlabel=dict(bgcolor="white", font_size=12),
    )
    fig.update_xaxes(showgrid=False, linecolor="#E5E7EB", tickfont=dict(size=11, color="#8A8F9A"))
    fig.update_yaxes(gridcolor="#F1ECE6", zeroline=False, tickfont=dict(size=11, color="#8A8F9A"))


def section_header(eyebrow: str, title: str, sub: str) -> None:
    st.markdown(
        f'<div class="eyebrow">{esc(eyebrow)}</div><div class="sec-title">{esc(title)}</div>'
        f'<div class="sec-sub">{esc(sub)}</div>', unsafe_allow_html=True)


# =============================================================================
# 圖表
# =============================================================================
def plot_weekly(df: pd.DataFrame, rng: str, t) -> None:
    d = df
    if rng == "1y":
        d = df[df.date >= df.date.max() - pd.DateOffset(years=1)]
    elif rng == "6m":
        d = df[df.date >= df.date.max() - pd.DateOffset(months=6)]
    w = d.set_index("date").resample("7D").agg(
        tmean=("tmean", "mean"), tmax=("tmax", "max"), tmin=("tmin", "min"), rain=("rain", "sum")
    ).reset_index()
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=w.date, y=w.rain, marker_color="rgba(122,170,205,0.55)", name=t("wk_rain"),
                         hoverinfo="skip", showlegend=False), secondary_y=True)
    fig.add_trace(go.Scatter(x=w.date, y=w.tmin, mode="lines", line=dict(width=0), hoverinfo="skip",
                             showlegend=False), secondary_y=False)
    fig.add_trace(go.Scatter(x=w.date, y=w.tmax, mode="lines", line=dict(width=0), fill="tonexty",
                             fillcolor="rgba(218,120,76,0.14)", hoverinfo="skip", showlegend=False),
                  secondary_y=False)
    cd = np.stack([w.tmin, w.tmax, w.rain], axis=-1)
    fig.add_trace(go.Scatter(
        x=w.date, y=w.tmean, mode="lines", line=dict(color=ACCENT, width=2.4), name=t("wk_avg"),
        customdata=cd, showlegend=False,
        hovertemplate=("<b>%{x|%Y-%m-%d}</b><br>" + t("wk_avg") + ": %{y:.1f}°C<br>"
                       + t("wk_range") + ": %{customdata[0]:.1f}~%{customdata[1]:.1f}°C<br>"
                       + t("wk_rain") + ": %{customdata[2]:.1f} mm<extra></extra>")), secondary_y=False)
    style_fig(fig, 380)
    fig.update_layout(hovermode="x", bargap=0.15)
    tmin, tmax = float(w.tmin.min()), float(w.tmax.max())
    fig.update_yaxes(range=[np.floor(tmin) - 2, np.ceil(tmax) + 2], title_text=t("temp_axis"), secondary_y=False)
    fig.update_yaxes(range=[0, max(50.0, float(w.rain.max()) * 2.0)], title_text=t("rain_axis"),
                     showgrid=False, secondary_y=True)
    plotly_show(fig)


def plot_monthly(monthly: pd.DataFrame, years: list[int], metric: str, lang: str, t) -> None:
    col = {"temp": "temp", "rain": "rain", "days": "days"}[metric]
    fig = go.Figure()
    unit = {"temp": "°C", "rain": " mm", "days": ""}[metric]
    for i, y in enumerate(years):
        cur = monthly[monthly.year == y].set_index("month").reindex(range(1, 13))
        ys = cur[col].to_numpy()
        name = f"{y}{t('year_suffix')}"
        hover = f"{name} · %{{x}}<br>%{{y:.1f}}{unit}<extra></extra>" if metric != "days" else \
            f"{name} · %{{x}}<br>%{{y:.0f}}<extra></extra>"
        color = YEAR_COLORS[i]
        xs = [mlabel(m, lang) for m in range(1, 13)]
        if metric == "temp":
            last = (y == years[-1])
            fig.add_trace(go.Scatter(
                x=xs, y=ys, name=name, mode="lines+markers" if last else "lines", line_shape="spline",
                line=dict(color=color, width=3.2 if last else 2),
                marker=dict(size=7, color="white", line=dict(width=2, color=color)),
                connectgaps=False, hovertemplate=hover))
        else:
            fig.add_trace(go.Bar(x=xs, y=ys, name=name, marker_color=color, hovertemplate=hover))
    style_fig(fig, 380)
    fig.update_layout(barmode="group", bargap=0.22, hovermode="x unified" if metric == "temp" else "closest")
    fig.update_xaxes(categoryorder="array", categoryarray=[mlabel(m, lang) for m in range(1, 13)])
    if metric == "temp":
        fig.update_yaxes(rangemode="normal")
    plotly_show(fig)


def plot_timeline(signals: dict, summary: dict, years: list[int], end: pd.Timestamp, lang: str, t) -> None:
    keys = [s[0] for s in SEASONS]
    row_y = {k: len(keys) - 1 - i for i, k in enumerate(keys)}
    fig = go.Figure()
    for k, y in row_y.items():
        fig.add_shape(type="rect", x0=1, x1=366, y0=y - 0.3, y1=y + 0.3, fillcolor="#F8F3ED",
                      line_width=0, layer="below")
    offsets = np.linspace(-0.12, 0.12, len(years))
    for yi, yr in enumerate(years):
        xs, ys, texts = [], [], []
        for k in keys:
            ts = signals[k].get(yr)
            if ts is None:
                continue
            xs.append(norm_doy(ts))
            ys.append(row_y[k] + offsets[yi])
            texts.append(f"{t(k)}<br>{ts.month}/{ts.day}")
        last = (yr == years[-1])
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="markers", name=str(yr), text=texts,
            marker=dict(size=15 if last else 11, color=YEAR_COLORS[yi], line=dict(color="white", width=1.5)),
            hovertemplate=f"{yr} · %{{text}}<extra></extra>"))
    # 今年預估（空心圓）
    ex, ey, et = [], [], []
    for k in keys:
        if signals[k].get(years[-1]) is None and summary[k]["avg_md"]:
            m, d = summary[k]["avg_md"]
            ex.append(date(2001, m, d).timetuple().tm_yday)
            ey.append(row_y[k] + offsets[-1])
            et.append(f"{t(k)}<br>{t('est_label')} {m}/{d}")
    if ex:
        fig.add_trace(go.Scatter(
            x=ex, y=ey, mode="markers", name=t("est_legend"), text=et,
            marker=dict(size=16, color="white", symbol="circle-open", line=dict(color=ACCENT, width=2.4)),
            hovertemplate="%{text}<extra></extra>"))
    # 資料截止線
    fig.add_vline(x=norm_doy(end), line_width=1.2, line_color="#9CA3AF")
    # 右側日期標註
    for k in keys:
        cur = signals[k].get(years[-1])
        if cur is not None:
            label, color = f"<b>{cur.month}/{cur.day}</b><br><span style='font-size:11px'>{t('this_year_found')}</span>", ACCENT
        elif summary[k]["est"]:
            e = summary[k]["est"]
            n = max(0, (pd.Timestamp(e) - end).days)
            label, color = f"<b>{e.month}/{e.day}</b><br><span style='font-size:11px'>{t('est_label')} {t('days_after', n=n)}</span>", INK
        else:
            label, color = f"<b>{t('not_reached')}</b>", "#6B7280"
        fig.add_annotation(xref="paper", x=1.01, xanchor="left", y=row_y[k], yref="y", text=label,
                           showarrow=False, font=dict(color=color, size=14), align="left")
    style_fig(fig, 330)
    fig.update_layout(margin=dict(l=10, r=130, t=40, b=10), hovermode="closest",
                      legend=dict(orientation="h", x=0, xanchor="left", y=1.2))
    fig.update_xaxes(range=[1, 366], tickmode="array",
                     tickvals=[date(2001, m, 1).timetuple().tm_yday for m in range(1, 13)],
                     ticktext=[mlabel(m, lang) for m in range(1, 13)], showgrid=True, gridcolor="#F4EEE8", side="top")
    fig.update_yaxes(range=[-0.6, len(keys) - 0.4], tickmode="array", tickvals=[row_y[k] for k in keys],
                     ticktext=[f"<b>{t(k)}</b>" for k in keys], showgrid=False)
    plotly_show(fig)


def season_rule(key: str, t) -> str:
    for k, thr, direction, _ in SEASONS:
        if k == key:
            return t("rule_up" if direction == "up" else "rule_down", t=thr)
    return ""


def season_table_html(signals, summary, years, lang, t) -> str:
    head = [t("season")] + [str(y) for y in years] + [t("hist_avg")]
    h = '<table class="season-table"><thead><tr>' + "".join(f"<th>{esc(x)}</th>" for x in head) + "</tr></thead><tbody>"
    for k, *_ in SEASONS:
        h += f"<tr><td>{esc(t(k))}</td>"
        for y in years:
            ts = signals[k].get(y)
            h += f"<td>{ts.month}/{ts.day}</td>" if ts is not None else f"<td>{esc(t('not_reached'))}</td>"
        avg = summary[k]["avg_md"]
        h += f'<td class="avg">{avg[0]}/{avg[1]}</td></tr>' if avg else '<td class="avg">—</td></tr>'
    return h + "</tbody></table>"


def hex_rgb(c: str):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


def heatmap_html(df: pd.DataFrame, lang: str, t) -> str:
    pct = temperature_bands(df)
    h = '<table class="heat"><thead><tr><th></th>' + "".join(f"<th>{esc(mlabel(m, lang))}</th>" for m in range(1, 13)) + "</tr></thead><tbody>"
    for key, color in BANDS:
        r, g, b = hex_rgb(color)
        h += f'<tr><td class="lab"><div class="bn">{esc(t(key))}</div><div class="bi">{esc(t(key + "_items"))}</div></td>'
        for m in range(1, 13):
            v = pct.loc[m, key]
            if pd.isna(v) or v < 0.5:
                bg, txt = "rgba(0,0,0,0.045)", ""
                if not pd.isna(v) and v > 0:
                    bg = f"rgba({r},{g},{b},0.10)"
            else:
                alpha = min(0.85, 0.12 + v / 100 * 0.75)
                bg, txt = f"rgba({r},{g},{b},{alpha:.3f})", f"{int(round(v))}%"
            h += f'<td class="cell" style="background:{bg}">{txt}</td>'
        h += "</tr>"
    return h + "</tbody></table>"


def mlabel(m: int, lang: str) -> str:
    return f"{m}月" if lang == "zh" else MONTHS_EN[m - 1]


# =============================================================================
# AI
# =============================================================================
def build_ai_context(city: str, metrics: dict, signals, summary, years, monthly) -> str:
    lines = [f"Location: {CITIES[city][0]} / {city}",
             f"Latest data day: {metrics['end'].date().isoformat()}",
             f"Last 30 days: mean temp {metrics['temp']:.1f} C, rainfall {metrics['rain']:.0f} mm, rainy days {metrics['days']}."]
    if metrics["temp_prev"] is not None:
        lines.append(f"Same window last year: mean temp {metrics['temp_prev']:.1f} C, rainfall {metrics['rain_prev']:.0f} mm, rainy days {metrics['days_prev']}.")
    lines.append("Rainy day = daily precipitation >= 1 mm. Season signal = first day the 7-day mean temperature crosses the threshold.")
    for k, thr, direction, _ in SEASONS:
        parts = [f"{y}: {signals[k][y].date()}" if signals[k][y] is not None else f"{y}: not reached" for y in years]
        avg = summary[k]["avg_md"]
        lines.append(f"{k} (7-day mean {'>=' if direction == 'up' else '<'} {thr} C): " + "; ".join(parts)
                     + (f"; historical avg {avg[0]}/{avg[1]}" if avg else ""))
    for _, r in monthly.dropna(subset=["temp"]).tail(24).iterrows():
        lines.append(f"{int(r.year)}-{int(r.month):02d}: mean {r.temp:.1f} C, rain {r.rain:.0f} mm, rainy days {r.days:.0f}")
    lines.append("No sales data is available.")
    return "\n".join(lines)


def ai_reply(question: str, context: str, t) -> str:
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
        model = st.secrets.get("GEMINI_MODEL", "gemini-2.5-flash")
    except Exception:
        key, model = "", "gemini-2.5-flash"
    if not key or key == "your-gemini-key-here":
        return t("ai_unavailable")
    try:
        from google import genai
        client = genai.Client(api_key=key)
        resp = client.models.generate_content(
            model=model, contents=f"{t('ai_context')}\n\nDATA:\n{context}\n\nQUESTION:\n{question}")
        return resp.text or t("ai_error", e="empty response")
    except Exception as e:  # noqa: BLE001
        return t("ai_error", e=str(e))


# =============================================================================
# 主程式
# =============================================================================
st.markdown(CSS, unsafe_allow_html=True)

# ---- 標題列：品牌 / 資料資訊 / 城市 / 語言 ----
c_brand, c_meta, c_city, c_lang = st.columns([3.2, 1.8, 1.5, 1.2], vertical_alignment="bottom")
with c_lang:
    lang_choice = st.selectbox("Language", ["繁體中文", "English"], key="ui_lang", label_visibility="collapsed")
lang = "zh" if lang_choice == "繁體中文" else "en"


def t(key: str, **kw) -> str:
    s = T[lang][key]
    return s.format(**kw) if kw else s


with c_city:
    city = st.selectbox(
        t("choose_city"), list(CITIES.keys()), index=0, key="ui_city", label_visibility="collapsed",
        format_func=lambda k: CITIES[k][0] if lang == "zh" else k)
with c_brand:
    st.markdown(f'<div class="eyebrow">{t("eyebrow")}</div><div class="brand-title">{esc(t("app_title"))}</div>',
                unsafe_allow_html=True)
meta_ph = c_meta.empty()

# ---- 取資料 ----
today = date.today()
end_req = today - timedelta(days=DATA_LAG_DAYS)
start_req = date(end_req.year - 3, 1, 1)
try:
    with st.spinner(t("loading")):
        df = fetch_weather(city, start_req.isoformat(), end_req.isoformat())
    if df.empty:
        raise ValueError("empty dataset")
except Exception as exc:  # noqa: BLE001
    st.error(t("load_error", e=exc))
    st.stop()

end = df["date"].max()
years = list(range(end.year - 3, end.year + 1))
meta_ph.markdown(
    f'<div class="meta"><b>{esc(t("data_until", d=end.date().isoformat()))}</b><br>{esc(t("source"))}</div>',
    unsafe_allow_html=True)

metrics = last30_metrics(df)
monthly = monthly_table(df)
signals, summary = compute_signals(df, years, end)

# ---- Hero ----
city_name = CITIES[city][0] if lang == "zh" else city
region = t(CITIES[city][1])
st.markdown(
    f'<div class="eyebrow hero-region">{esc(region)} · {years[0]}–{years[-1]}</div>'
    f'<div class="hero-city">{esc(city_name)}</div><div class="hero-desc">{esc(t("hero_desc"))}</div>',
    unsafe_allow_html=True)

# ---- KPI ----
def delta(v, unit: str, dec: int = 1) -> str:
    arrow = "↗" if v > 0 else ("↘" if v < 0 else "→")
    return f'<span class="up">{arrow} {v:+.{dec}f}{unit}</span>'


if metrics["temp_prev"] is not None:
    d_t = metrics["temp"] - metrics["temp_prev"]
    d_r = metrics["rain"] - metrics["rain_prev"]
    sub_t = t("vs_last", v=f'{metrics["temp_prev"]:.1f}°') + " · " + delta(round(d_t, 1), "°")
    sub_r = t("vs_last", v=f'{metrics["rain_prev"]:.0f}mm') + " · " + delta(round(d_r), "mm", 0)
    sub_d = t("vs_last", v=f'{metrics["days_prev"]}{t("day_unit")}') + " " + t("rain_def")
else:
    sub_t = sub_r = sub_d = "—"

next_key = next((k for k, *_ in SEASONS if signals[k].get(years[-1]) is None), None)
if next_key:
    est = summary[next_key]["est"]
    if est:
        n = (pd.Timestamp(est) - end).days
        est_line = t("est_line", d=f"{est.month}/{est.day}", n=n) if n > 0 else t("est_soon", d=f"{est.month}/{est.day}")
    else:
        est_line = t("not_reached")
    dark = (f'<div class="eyebrow">{t("next_signal")}</div><div class="name">{esc(t(next_key))}</div>'
            f'<div class="sub">{esc(est_line)}</div><div class="items">{esc(t(next_key + "_items"))}</div>')
else:
    dark = f'<div class="eyebrow">{t("next_signal")}</div><div class="name" style="font-size:18px">{esc(t("all_done"))}</div>'

days_unit = t("day_unit")
st.markdown(
    '<div class="kpi-row">'
    f'<div class="kpi"><div class="eyebrow">{t("kpi_temp")}</div><div class="big">{metrics["temp"]:.1f}°</div><div class="sub">{sub_t}</div></div>'
    f'<div class="kpi"><div class="eyebrow">{t("kpi_rain")}</div><div class="big" style="color:#2F6DA8">{metrics["rain"]:.0f}<small>mm</small></div><div class="sub">{sub_r}</div></div>'
    f'<div class="kpi"><div class="eyebrow">{t("kpi_days")}</div><div class="big">{metrics["days"]}<small>{esc(days_unit)}</small></div><div class="sub">{sub_d}</div></div>'
    f'<div class="kpi dark">{dark}</div></div>',
    unsafe_allow_html=True)

# ---- 四張洞察卡片 ----
cards = []
# 1) 與去年同期
if metrics["temp_prev"] is not None:
    dd = metrics["temp"] - metrics["temp_prev"]
    if abs(dd) < 0.5:
        cards.append(("↗", t("ins_similar"), t("ins_similar_body", d=f"{abs(dd):.1f}")))
    elif dd > 0:
        cards.append(("↗", t("ins_warmer"), t("ins_warmer_body", d=f"{dd:.1f}")))
    else:
        cards.append(("↘", t("ins_cooler"), t("ins_cooler_body", d=f"{abs(dd):.1f}")))
else:
    cards.append(("↗", t("ins_similar"), t("no_data")))
# 2) 最近訊號
found = [(signals[k][years[-1]], k) for k, *_ in SEASONS if signals[k].get(years[-1]) is not None]
if found:
    ts, k = max(found, key=lambda x: x[0])
    avg = summary[k]["avg_md"]
    cards.append(("❄", t("ins_signal", s=t(k)),
                  t("ins_signal_body", d=f"{ts.month}/{ts.day}", a=f"{avg[0]}/{avg[1]}" if avg else "—", items=t(k + "_items"))))
else:
    cards.append(("❄", t("ins_signal_none"), t("ins_signal_none_body")))
# 3) 最潮濕月份 / 4) 最熱最冷
mm = monthly.dropna(subset=["temp"]).groupby("month").agg(temp=("temp", "mean"), rain=("rain", "mean"))
if not mm.empty:
    wet = int(mm.rain.idxmax())
    hot, cold = int(mm.temp.idxmax()), int(mm.temp.idxmin())
    cards.append(("☂", t("ins_wet", m=mlabel(wet, lang)), t("ins_wet_body", x=f"{mm.rain.max():.0f}")))
    cards.append(("♨", t("ins_hot_cold", h=mlabel(hot, lang), c=mlabel(cold, lang)),
                  t("ins_hot_cold_body", a=f"{mm.temp.max():.1f}", b=f"{mm.temp.min():.1f}")))
else:
    cards.append(("☂", "—", t("no_data")))
    cards.append(("♨", "—", t("no_data")))

st.markdown('<div class="ins-row">' + "".join(
    f'<div class="ins"><div class="ic">{ic}</div><div class="tt">{esc(tt)}</div><div class="bd">{esc(bd)}</div></div>'
    for ic, tt, bd in cards) + "</div>", unsafe_allow_html=True)

# ---- 01 長期走勢 ----
with st.container(key="sec1"):
    a, b = st.columns([3, 1.6], vertical_alignment="bottom")
    with a:
        section_header(t("sec1"), t("sec1_title"), t("sec1_sub"))
    with b:
        rng = st.radio("range", ["all", "1y", "6m"], horizontal=True, key="rng", label_visibility="collapsed",
                       format_func=lambda x: t("rng_" + x))
    plot_weekly(df, rng, t)

# ---- 02 年度對比 ----
with st.container(key="sec2"):
    a, b = st.columns([3, 1.6], vertical_alignment="bottom")
    with a:
        section_header(t("sec2"), t("sec2_title"), t("sec2_sub"))
    with b:
        metric = st.radio("metric", ["temp", "rain", "days"], horizontal=True, key="metric",
                          label_visibility="collapsed", format_func=lambda x: t("m_" + x))
    plot_monthly(monthly, years, metric, lang, t)
    st.markdown(f'<div class="note-right">{esc(t("note_" + metric))}</div>', unsafe_allow_html=True)

# ---- 03 換季時機 ----
with st.container(key="sec3"):
    section_header(t("sec3"), t("sec3_title"), t("sec3_sub"))

    rules = " ｜ ".join(
        f"{t(k)}：{season_rule(k, t)}（{t(k + '_items')}）"
        for k, *_ in SEASONS
    )

    st.caption(rules)
    plot_timeline(signals, summary, years, end, lang, t)
    st.markdown(season_table_html(signals, summary, years, lang, t), unsafe_allow_html=True)

# ---- 04 商品企劃 ----
with st.container(key="sec4"):
    section_header(t("sec4"), t("sec4_title"), t("sec4_sub"))
    st.markdown(heatmap_html(df, lang, t), unsafe_allow_html=True)

st.markdown(f'<div class="footnote">{esc(t("footnote"))}</div>', unsafe_allow_html=True)

# ---- 右下角：問天氣 AI ----
with st.container(key="ai_float"):
    with st.popover("💬 " + t("ask_ai")):
        st.markdown(f"**{t('ai_title')}**")
        q = st.text_area("q", placeholder=t("ai_placeholder"), key="ai_q", label_visibility="collapsed", height=90)
        if st.button(t("ai_send"), key="ai_send"):
            if q.strip():
                with st.spinner(t("ai_thinking")):
                    ctx = build_ai_context(city, metrics, signals, summary, years, monthly)
                    st.session_state["ai_answer"] = ai_reply(q.strip(), ctx, t)
        if st.session_state.get("ai_answer"):
            st.markdown(st.session_state["ai_answer"])
