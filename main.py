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
YEAR_COLORS = ["#CBD5E1", "#94A3B8", "#334155", "#E05D38"]
ACCENT = "#E05D38"
INK = "#0F172A"

# =============================================================================
