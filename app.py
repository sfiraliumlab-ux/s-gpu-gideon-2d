import streamlit as st
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time

# --- НАСТРОЙКИ СИСТЕМЫ ---
st.set_page_config(page_title="GIDEON v5.5.0 | Kinematic Pulse", layout="wide")

if 'eb_stable' not in st.session_state:
    st.session_state.eb_stable = 1803.59
if 'sai_index' not in st.session_state:
    st.session_state.sai_index = 1.0
if 'genetic_code' not in st.session_state:
    st.session_state.genetic_code = "1001110010111110001011010111011000010010001101010101001000010010"
if 't_auto' not in st.session_state:
    st.session_state.t_auto = 0.0
if 'walking' not in st.session_state:
    st.session_state.walking = False

# --- ENGINE: GOLDEN VURF ---
class GoldenVurfEngine:
    def __init__(self, code, vurf=1.618):
        self.bits = [int(b) for b in code]
        self.vurf = vurf

    def calculate_step(self, t, leg_idx, amp):
        # $$ \phi_{leg} = \sum(\text{segment}) \cdot \frac{\pi}{4} $$
        seg = self.bits[leg_idx*8 : (leg_idx+1)*8]
        phase = sum(seg) * (math.pi / 4)
        
        # Динамика по Басаргину
        osc = math.sin(t * self.vurf + phase)
        angle_rad = leg_idx * (math.pi / 3)
        r_base = 30
        
        x0, y0, z0 = math.cos(angle_rad)*r_base, math.sin(angle_rad)*r_base, 0
        
        ext = r_base + (abs(osc) * amp)
        x1, y1 = math.cos(angle_rad)*ext, math.sin(angle_rad)*ext
        z1 = math.sin(t * 1.5 + phase) * (amp * 0.5)
        
        return [x0, x1], [y0, y1], [z0, z1]

# --- UI ---
st.title("S-GPU GIDEON v5.5.0: Кинематический Пульс")

tab1, tab2 = st.tabs(["⚙️ ЯДРО И ГЕНОМ", "🕷 ЖИВАЯ КИНЕМАТИКА"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Eb Potential", f"{st.session_state.eb_stable:.2f}")
        st.metric("SAI Status", "COHERENT (1.0)")
    with c2:
        st.write("Активный микрокод (64-bit):")
        st.code(st.session_state.genetic_code)

with tab2:
    col_ui, col_viz = st.columns([1, 2])
    
    with col_ui:
        vurf_val = st.slider("Коэффициент Вурфа", 1.0, 2.0, 1.618)
        amp_val = st.slider("Амплитуда шага", 10, 80, 55)
        
        st.write("---")
        if st.button("START / STOP WALKING"):
            st.session_state.walking = not st.session_state.walking
        
        st.write(f"Текущая фаза t: {st.session_state.t_auto:.2f}")

    with col_viz:
        # Отрисовка
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        engine = GoldenVurfEngine(st.session_state.genetic_code, vurf_val)
        
        for i in range(6):
            xs, ys, zs = engine.calculate_step(st.session_state.t_auto, i, amp_val)
            ax.plot(xs, ys, zs, marker='8', markersize=10, linewidth=6, color='#00ffcc' if i%2==0 else '#ff00ff')
            ax.plot([0, xs[0]], [0, ys[0]], [0, zs[0]], color='gray', alpha=0.5)
            
        ax.set_xlim([-150, 150]); ax.set_ylim([-150, 150]); ax.set_zlim([-80, 80])
        ax.set_axis_off()
        fig.patch.set_facecolor('#0e1117')
        ax.set_facecolor('#0e1117')
        st.pyplot(fig)

# --- LOOP ANIMATION ---
if st.session_state.walking:
    st.session_state.t_auto += 0.2
    time.sleep(0.05)
    st.rerun()

# --- REPORT ---
st.markdown("---")
with st.expander("ОТЧЕТ GIDEON ДЛЯ ЧАТА"):
    rep = f"""[ОТЧЕТ GIDEON v5.5.0]
- Eb: {st.session_state.eb_stable:.2f}
- SAI: {st.session_state.sai_index}
- Статус анимации: {'WALKING' if st.session_state.walking else 'IDLE'}
- Геном подтвержден: OK"""
    st.code(rep)
