##draw_hvac()
##draw_control_panel()
##draw_alarm_panel()

import streamlit as st
from modules import module_assets

def draw_hvac(data):
    col_left, col_right = st.columns([1, 2])

    # ===== ЛЕВАЯ ПАНЕЛЬ (УПРАВЛЕНИЕ) =====
    with col_left:

        
        st.subheader("🎛️ Управление")

        temp_setpoint = st.number_input("Уставка", value=22)
        mode = st.selectbox("Режим", ["HEAT", "FAN", "COOL"])

        enabled = st.toggle("Ручной режим")
        temp = st.slider("Температура", 18, 40, 22)

        progress = st.progress(70)

        st.metric("Температура", "22 °C", "+1.2")
        
        data = st.session_state.data
        if not data:
            st.info("Жду данные ...")
        else:
            T1 = data.get("T1", None)
            st.write("T1 сейчас:", T1)            
    

        if st.session_state.active_alarms:
            st.error("🚨 Есть аварии")
        else:
            st.success("✅ Всё нормально")

        for alarm in st.session_state.active_alarms:
            st.warning(f"{alarm['name']}")        
        

        col_btn1, col_ind1, col_btn2, col_ind2 = st.columns([4,1,4,1])


        color1 = "green"

        
        with col_btn1:
            
            if st.button("▶ Пуск",key="btn_start", type="secondary", use_container_width=True):
                st.session_state.running = True
                send_udp({
                    "temp_setpoint": temp_setpoint,
                    "mode": mode
                })

            st.markdown("</div>", unsafe_allow_html=True)

        with col_ind1:
            

            st.markdown(f"""
            <div style='
                width:20px;
                height:20px;
                background:{color1};
                border-radius:50%;
                margin-top:10px;
            '></div>
            """, unsafe_allow_html=True)
            
        with col_btn2:
            if st.button("⏹ Стоп", key="btn_stop",type="secondary", use_container_width=True):
                send_udp({
                    "temp_setpoint": temp_setpoint,
                    "mode": mode
                })
                
        with col_ind2:
            color2 = "red" 

            st.markdown(f"""
            <div style='
                width:20px;
                height:20px;
                background:{color2};
                border-radius:50%;
                margin-top:10px;
            '></div>
            """, unsafe_allow_html=True)
    
    # ===== ПРАВАЯ ПАНЕЛЬ (МНЕМОСХЕМА) =====
    with col_right:
        st.subheader("📊 Состояние системы")

        if data:
            T_in = round(data.get("T3", 22.0))
            T_out = data.get("T5", 18.0)
            fan = data.get("fan", 0)
            fan = 1
            

            fan_img = module_assets.fan_300x300_base64
            filter_img = module_assets.filter_pic_base64
            
            animation = "rotate 4s linear infinite" if fan else "none"
            clFan_ind = 'lime' if fan else 'green'
            
            st.markdown(f"""
            <div style='position: relative; width: 1000px;'>
                <!-- ФОН -->
                <img src='data:image/png;base64,{module_assets.airduct}' style='width: 100%;'>
                <!-- ВЕНТИЛЯТОР -->
                <img src='data:image/png;base64,{fan_img}' style='
                    position:absolute;
                    top:57px;
                    left:353px;
                    width:170px;
                    animation: {animation};
                '>                
                <!-- ФИЛЬТР -->
                <img src='data:image/png;base64,{filter_img}' style='
                    position: absolute;
                    top: 56px;
                    left: 232px;
                    width: 14px;
                '>
                <!-- ТЕМПЕРАТУРА -->
                <div style='
                    position: absolute;
                    top: 120px;
                    left: 160px;
                    color: blue;
                    font-size: 20px;
                    font-weight: bold;
                '>
                    {T_out} °C
                </div>
                <!-- ИНДИКАТОР -->
                <div style='
                    position:absolute;
                    top:63px;
                    left:497px;
                    width:20px;
                    height:20px;
                    background-color:{clFan_ind};
                    border-radius:50%;
                '></div>                
            </div>
            <style>
            @keyframes rotate {{
                from {{ transform: rotate(0deg); }}
                to {{ transform: rotate(360deg); }}
            }}
            </style>            
            """, unsafe_allow_html=True)        

        else:
            st.info("Жду данные...")
