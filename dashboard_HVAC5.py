# session_state init
# запуск потоков
# создание вкладок
# вызов функций UI

import streamlit as st
import socket, json, time
from datetime import datetime, timedelta
import pandas as pd
import altair as alt
import numpy as np
import threading
import math
import altair as alt
import sqlite3
import pandas as pd

from modules import module_db
from modules import module_Alarms
from modules import module_ui 

# -------------------------------
# Настройки страницы
# -------------------------------

import queue

import base64


##=====================================================================================

def img_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

##airduct = img_to_base64("assets/airduct_HVAC5.png")
##fan_on_base64  = img_to_base64("assets/Fan_Alarm.png")
##fan_off_base64 = img_to_base64("assets/fan_normal.png")
##fan_300x300_base64 = img_to_base64("assets/fan_300x300.png")
#filter_pic = img_to_base64("assets/filter_14x46.png")

#data_queue = queue.Queue()

st.set_page_config(layout="wide")

placeholder = st.empty()

if "queue" not in st.session_state:
    st.session_state.queue = queue.Queue()

data_queue = st.session_state.queue

######################################################
# Слушаем порт
# полученные данные кладем в очередь
######################################################
def udp_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("localhost", 9999))
    sock.settimeout(1)

    while True:
        try:
            raw, _ = sock.recvfrom(1024)
            data = json.loads(raw.decode())
            #data["time"] = time.strftime("%H:%M:%S")
            data["time"] = pd.Timestamp.now()  # добавить в полученные данные поле "time"

            data_queue.put(data)
            print("RECV:", data)

        except socket.timeout:
            pass


###################################
# конектимся к БД и создаем таблицу
###################################
conn = sqlite3.connect("hvac.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS hvac (
    time TEXT,
    T1 REAL,
    T2 REAL,
    T3 REAL,
    T4 REAL,
    T5 REAL,
    T_SP REAL,
    Y1 REAL,
    Y2 REAL,
    n1 REAL,
    B1 REAL,
    air_bypass REAL,
    TEN REAL,
    Alarms INT
)
""")

# --- таблица аварий ---
cursor.execute("""
CREATE TABLE IF NOT EXISTS alarms (
    time TEXT,
    alarm_id TEXT,
    message TEXT,
    level TEXT,
    state TEXT
)
""")

conn.commit()
    
########################################################################
# init
########################################################################
if "data" not in st.session_state:
    st.session_state.data = None
if "history" not in st.session_state:
    st.session_state.history = []
# 👉 ВАЖНО: берём отсюда
data = st.session_state.get("data")
history = st.session_state.get("history", [])

if "archive_df" not in st.session_state:
    st.session_state.archive_df = None

if "active_alarms" not in st.session_state:
    st.session_state.active_alarms = []

##if "data" not in st.session_state:
##    st.session_state.data = None
##if "history" not in st.session_state:
##    st.session_state.history = []

#ЗАПУСК ПОТОКА
if "started" not in st.session_state:
    threading.Thread(target=udp_listener, daemon=True).start()
    st.session_state.started = True
    

# чтение очереди
while not data_queue.empty():
    data = data_queue.get()
    T1 = data["T1"]
    st.session_state.data = data
    st.session_state.history.append(data)

##    st.write("DATA:", st.session_state.get("data"))
##    st.write("QUEUE SIZE:", data_queue.qsize())
    
    if len(st.session_state.history) > 600:
        st.session_state.history = st.session_state.history[-600:]

    data["time"] = datetime.now().isoformat()
    module_db.save_to_db(data)

    new_alarms = module_Alarms.check_alarms(data)
    st.session_state.active_alarms = new_alarms


    if "prev_alarms" not in st.session_state:
        st.session_state.prev_alarms = set()   # множества

    # создаёт словарь (dict) из списка ALARMS
    ALARM_MAP = {a["id"]: a for a in module_Alarms.ALARMS}

    current_ids = {a["id"] for a in new_alarms} # создаем множестваS
    prev_ids = st.session_state.prev_alarms

    # новые аварии
    new_triggered = current_ids - prev_ids # результат множества (set)

    # снятые
    cleared = prev_ids - current_ids   # результат множества (set) сброшеных аварий

##    for alarm_id in new_triggered:
##        module_db.save_alarm_to_db(alarm_id, "ON")

 
    ## установка новых аварий
    for alarm in new_alarms:
        if alarm["id"] in new_triggered:
            module_db.save_alarm_to_db(alarm, "ON")

    # --- снятые аварии ---
    for alarm_id in cleared:
        alarm = ALARM_MAP.get(alarm_id)
        if alarm:
            module_db.save_alarm_to_db(alarm, "OFF")


    st.session_state.prev_alarms = current_ids
   

# --- дальше UI ---
st.title("HVAC Monitor")


tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 Мнемосхема", "История", "📋 Таблица", "🌡 Графики", "Текущие Аварии", "🚨 Журнал Аварий"])

# ---- Вкладка 1 ----
with tab1:
    # -------------------------------
    # Верхняя панель: управление + мнемосхема
    # -------------------------------
    #==========================================
    module_ui.draw_hvac(data)
    #==========================================
    


# ---- Вкладка 2 ----
with tab2:
    st.subheader("📈 Температуры Архив")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        date = st.date_input("Дата", value=datetime.now())

    with col2:
        start_time = st.time_input("Время начала")

    with col3:
        duration_min = st.number_input("Длительность (мин)", 1, 1440, 10)

        start_dt = datetime.combine(date, start_time)
        end_dt = start_dt + timedelta(minutes=duration_min)

    with col4:
        

        st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)

        
        if st.button("Показать",key="btn_show"):
            conn = sqlite3.connect("hvac.db")

            query = """
            SELECT * FROM hvac
            WHERE time BETWEEN ? AND ?
            ORDER BY time
            """

            df = pd.read_sql_query(
                query,
                conn,
                params=(start_dt.isoformat(), end_dt.isoformat())
            )

            conn.close()

            if not df.empty:
                df["time"] = pd.to_datetime(df["time"])
                st.session_state.archive_df = df   # 💥 сохраняем


    df = st.session_state.get("archive_df")

    if df is not None and not df.empty:

        df_plot = df.melt(
            "time",
            value_vars=["T1","T2","T3","T4","T5","T_SP"],
            var_name="sensor",
            value_name="value"
        )

        chart = alt.Chart(df_plot).mark_line().encode(
            x=alt.X('time:T', title ="Время",axis=alt.Axis(format='%H:%M:%S')),
            y=alt.Y('value:Q',title="Температура, °C"),
            color=alt.Color('sensor:N',title="Датчики______")
        )

        st.altair_chart(chart, use_container_width=True)

        df_plot = df.melt(
            "time",
            value_vars=["Y1","Y2","n1","B1","air_bypass","TEN"],
            var_name="sensor",
            value_name="value"
        )

        chart = alt.Chart(df_plot).mark_line().encode(
            x=alt.X('time:T', title ="Время",axis=alt.Axis(format='%H:%M:%S')),
            y=alt.Y('value:Q',title="Значение, %"),
            color=alt.Color('sensor:N',title="ИМ")
        )

        st.altair_chart(chart, use_container_width=True)



# ---- Вкладка 3 ----
with tab3:
    if history:
        df = pd.DataFrame(history).tail(20)

        cols = ["time", "Y1", "Y2", "n1", "B1", "air_bypass", "TEN", "T1", "T2", "T3", "T4", "T5", "T_SP" ]

        st.dataframe(
            df[cols],
            use_container_width=True
        )

        
    else:
        st.info("Нет данных")

# ---- Вкладка 4 ----
with tab4:

    st.subheader("📈 Температуры")

    if history:
        df = pd.DataFrame(history)
        df["time"] = pd.to_datetime(df["time"])

        # --- ФИЛЬТР: последние 10 минут ---
        now = datetime.now()
        cutoff = now - timedelta(minutes=10)

        df = df[df["time"] >= cutoff]        

        df_plot = df.melt("time", value_vars=["T1","T2","T3","T4", "T5", "T_SP"],
                          var_name="sensor", value_name="value")

        chart = alt.Chart(df_plot).mark_line().encode(
            x=alt.X('time:T', axis=alt.Axis(format='%H:%M:%S')),
            y='value:Q',
            color='sensor:N'
        )

        st.altair_chart(chart, use_container_width=True)

        st.subheader("🌀 Вентиляторы и клапаны")
        df_plot = df.melt("time", value_vars=["Y1", "Y2", "n1", "B1", "air_bypass", "TEN"],
                          var_name="sensor", value_name="value")

        chart = alt.Chart(df_plot).mark_line().encode(
            x=alt.X('time:T', axis=alt.Axis(format='%H:%M:%S')),
            y='value:Q',
            color='sensor:N'
        )

        st.altair_chart(chart, use_container_width=True)

        
    else:
        st.info("Нет данных")

# ---- Вкладка 5 ----
with tab5:

    st.subheader("Активные аварии!")

    alarms = st.session_state.get("active_alarms", [])

    if alarms:

        rows = []

        for alarm in alarms:

            rows.append({
                "Время": datetime.now().strftime("%H:%M:%S"),
                "Название": alarm["name"],
                "Критичность": module_Alarms.level_icon(alarm["level"])#alarm["level"]
            })

        df_alarm = pd.DataFrame(rows)

        st.dataframe(
            df_alarm,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.success("Активных аварий нет")


# ---- Вкладка 6 ----
with tab6:

    st.subheader("🚨 Журнал Аварий!")

    conn = sqlite3.connect("hvac.db")

    query = """
    SELECT time, message, level, state
    FROM alarms
    ORDER BY time DESC
    LIMIT 100
    """

    df_alarm = pd.read_sql_query(query, conn)

    conn.close()

    if not df_alarm.empty:

        df_alarm["time"] = pd.to_datetime(df_alarm["time"])

        df_alarm["time"] = df_alarm["time"].dt.strftime("%Y-%m-%d %H:%M:%S")

        # названия столбцов
        df_alarm.columns = [
            "Время",
            "Сообщение",
            "Критичность",
            "Состояние"
        ]

        df_alarm["Состояние"] = df_alarm["Состояние"].apply(module_Alarms.format_state)

        st.dataframe(
            df_alarm,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("История аварий пуста")

    
time.sleep(4)
st.rerun()
#st.experimental_set_query_params(refresh=time.time())



