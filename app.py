import streamlit as st
import math
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# --- СИСТЕМНЫЕ НАСТРОЙКИ ---
st.set_page_config(page_title="GIDEON v5.4.0 | 3D Manifest", layout="wide")

if 'eb_stable' not in st.session_state:
    st.session_state.eb_stable = 1803.59
if 'sai_index' not in st.session_state:
    st.session_state.sai_index = 1.0
if 'genetic_code' not in st.session_state:
    st.session_state.genetic_code = "1001110010111110001011010111011000010010001101010101001000010010"

# --- КИНЕМАТИЧЕСКИЙ ДВИЖОК 3D ---
class Spider3D:
    def __init__(self, code, vurf=1.618):
        self.bits = [int(b) for b in code]
        self.vurf = vurf

    def get_joint_coords(self, t, leg_idx, amp):
        # Извлекаем фазу из генома
        seg = self.bits[leg_idx*8 : (leg_idx+1)*8]
        phase = sum(seg) * (math.pi / 4)
        
        # Углы сочленений по Золотому Вурфу
        # $$ \alpha = \sin(t \cdot \text{Vurf} + \phi) $$
        angle = math.sin(t * self.vurf + phase)
        
        # Координаты 3D (Base -> Knee -> Tip)
        x_base = math.cos(leg_idx * math.pi/3) * 20
        y_base = math.sin(leg_idx * math.pi/3) * 20
        
        x_tip = x_base + math.cos(leg_idx * math.pi/3) * abs(angle) * amp
        y_tip = y_base + math.sin(leg_idx * math.pi/3) * abs(angle) * amp
        z_tip = math.sin(t + phase) * (amp * 0.5)
        
        return [x_base, x_tip], [y_base, y_tip], [0, z_tip]

# --- ИНТЕРФЕЙС ---
st.title("GIDEON v5.4.0: Пространственная Манифестация")

tab_core, tab_3d = st.tabs(["☢️ КОНТРОЛЬ ЯДРА", "🕷 3D СИМУЛЯТОР"])

with tab_core:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.metric("Eb Potential", f"{st.session_state.eb_stable:.2f}")
        st.metric("SAI Coherence", st.session_state.sai_index)
        if st.button("Пересчитать Геном"):
            seed = int(st.session_state.eb_stable * 777)
            np.random.seed(seed)
            st.session_state.genetic_code = "".join(map(str, np.random.randint(0, 2, 64)))
    with c2:
        st.write("Текущий Геном (Микрокод):")
        st.code(st.session_state.genetic_code)

with tab_3d:
    st.header("fsin-simulator: 3D-Каркас")
    
    col_in, col_out = st.columns([1, 3])
    
    with col_in:
        vurf_val = st.slider("Золотой Вурф", 1.0, 2.0, 1.618)
        amp_val = st.slider("Размах лап", 10, 100, 50)
        t_cycle = st.slider("Временная фаза", 0.0, 10.0, 0.0, step=0.1)
        st.info("Движение лап синхронизировано с L3 через геном.")

    with col_out:
        spider = Spider3D(st.session_state.genetic_code, vurf_val)
        fig = go.Figure()

        # Отрисовка 6 лап
        for i in range(6):
            x, y, z = spider.get_joint_coords(t_cycle, i, amp_val)
            fig.add_trace(go.Scatter3d(
                x=x, y=y, z=z,
                mode='lines+markers',
                line=dict(color='cyan', width=6),
                name=f'Leg {i+1}'
            ))

        # Настройка камеры
        fig.update_layout(
            scene=dict(
                xaxis=dict(range=[-150, 150]),
                yaxis=dict(range=[-150, 150]),
                zaxis=dict(range=[-100, 100]),
                aspectmode='cube'
            ),
            margin=dict(l=0, r=0, b=0, t=0),
            template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)

# --- ОТЧЕТ ---
st.markdown("---")
with st.expander("ОТЧЕТ ДЛЯ ЧАТА", expanded=True):
    rep = f"""[ОТЧЕТ GIDEON v5.4.0]
- Eb: {st.session_state.eb_stable:.2f}
- SAI: {st.session_state.sai_index}
- Геном: {st.session_state.genetic_code}
- Vurf: {vurf_val}"""
    st.code(rep)
