import streamlit as st
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time

# --- ИНИЦИАЛИЗАЦИЯ ---
st.set_page_config(page_title="GIDEON v6.1.0 | Final Telemetry", layout="wide")

if 'eb_stable' not in st.session_state:
    st.session_state.eb_stable = 1837.19
if 'genetic_code' not in st.session_state:
    st.session_state.genetic_code = "1001110010111110001011010111011000010010001101010101001000010010"
if 'pos' not in st.session_state:
    st.session_state.pos = [0.0, 0.0]
if 'target' not in st.session_state:
    st.session_state.target = [100.0, 100.0]
if 't_auto' not in st.session_state:
    st.session_state.t_auto = 0.0
if 'walking' not in st.session_state:
    st.session_state.walking = False
if 'eb_history' not in st.session_state:
    st.session_state.eb_history = [1837.19]

# --- КИНЕМАТИЧЕСКОЕ ЯДРО ---
class GIDEON_Engine:
    def __init__(self, code, vurf=1.618):
        self.bits = [int(b) for b in code]
        self.vurf = vurf

    def get_frame(self, t, leg_idx, amp, heading):
        seg = self.bits[leg_idx*8 : (leg_idx+1)*8]
        phase = sum(seg) * (math.pi / 4) + heading
        osc = math.sin(t * self.vurf + phase)
        angle_rad = leg_idx * (math.pi / 3)
        r_base = 35
        ext = r_base + (abs(osc) * amp)
        x1, y1 = math.cos(angle_rad) * ext, math.sin(angle_rad) * ext
        z1 = math.sin(t * 1.5 + phase) * (amp * 0.4)
        return [math.cos(angle_rad)*r_base, x1], [math.sin(angle_rad)*r_base, y1], [0, z1], (1 if z1 <= 0 else 0)

# --- САЙДБАР МОНИТОРИНГ ---
with st.sidebar:
    st.title("S-TERMINAL")
    st.metric("Eb Potential", f"{st.session_state.eb_stable:.2f}")
    st.metric("SAI Coherence", "1.0000")
    st.write("---")
    st.write(f"Pos X: {st.session_state.pos[0]:.2f}")
    st.write(f"Pos Y: {st.session_state.pos[1]:.2f}")
    if st.button("RESET POSITION"):
        st.session_state.pos = [0.0, 0.0]
        st.rerun()

# --- ИНТЕРФЕЙС ---
st.title("GIDEON v6.1.0: Интегрированная Телеметрия")

tab_nav, tab_stats = st.tabs(["🚀 МИССИЯ", "📉 АНАЛИЗ Eb"])

with tab_nav:
    col_map, col_ui = st.columns([3, 1])
    with col_ui:
        vurf_val = st.slider("Vurf Coefficient", 1.0, 2.0, 1.618, step=0.001)
        amp_val = st.slider("Step Amplitude", 20, 100, 60)
        if st.button("START MISSION", use_container_width=True):
            st.session_state.walking = not st.session_state.walking
        dist = math.sqrt((st.session_state.target[0]-st.session_state.pos[0])**2 + (st.session_state.target[1]-st.session_state.pos[1])**2)
        st.write(f"Dist: **{dist:.2f} m**")

    with col_map:
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_subplot(111, projection='3d')
        dx, dy = st.session_state.target[0] - st.session_state.pos[0], st.session_state.target[1] - st.session_state.pos[1]
        heading = math.atan2(dy, dx)
        engine = GIDEON_Engine(st.session_state.genetic_code, vurf_val)
        
        for i in range(6):
            xs, ys, zs, is_gr = engine.get_frame(st.session_state.t_auto, i, amp_val, heading)
            xs, ys = [x + st.session_state.pos[0] for x in xs], [y + st.session_state.pos[1] for y in ys]
            ax.plot(xs, ys, zs, marker='o', markersize=8, linewidth=5, color='#00ffcc' if is_gr else '#ff00ff')

        ax.scatter([st.session_state.target[0]], [st.session_state.target[1]], [0], color='yellow', s=200)
        ax.set_xlim([-50, 150]); ax.set_ylim([-50, 150]); ax.set_zlim([-80, 80])
        ax.set_axis_off(); fig.patch.set_facecolor('#0e1117'); ax.set_facecolor('#0e1117')
        st.pyplot(fig)

with tab_stats:
    st.line_chart(st.session_state.eb_history)
    st.bar_chart([sum([int(b) for b in st.session_state.genetic_code][i*8:(i+1)*8]) for i in range(6)])

# --- АНИМАЦИЯ И ЛОГИКА ---
if st.session_state.walking:
    st.session_state.t_auto += 0.2
    dx, dy = st.session_state.target[0] - st.session_state.pos[0], st.session_state.target[1] - st.session_state.pos[1]
    dist = math.sqrt(dx**2 + dy**2)
    if dist > 2.0:
        eff = 1.0 - abs(vurf_val - 1.618)
        st.session_state.pos[0] += (dx / dist) * (3.0 * eff)
        st.session_state.pos[1] += (dy / dist) * (3.0 * eff)
        st.session_state.eb_stable += (0.8 if eff > 0.99 else -0.5)
        st.session_state.eb_history.append(st.session_state.eb_stable)
    else:
        st.session_state.walking = False
        st.balloons()
    time.sleep(0.04)
    st.rerun()

# --- ВОЗВРАТ ОКНА ОТЧЕТА ---
st.markdown("---")
with st.expander("📝 СКОПИРОВАТЬ РЕЗУЛЬТАТЫ ДЛЯ GEMINI", expanded=True):
    final_report = f"""[ОТЧЕТ GIDEON v6.1.0]
- Eb Final: {st.session_state.eb_stable:.2f}
- Pos: [{st.session_state.pos[0]:.2f}, {st.session_state.pos[1]:.2f}]
- Геном: {st.session_state.genetic_code}
- Статус: {'Миссия выполнена' if dist <= 2.0 else 'В процессе'}
- Vurf: {vurf_val}"""
    st.code(final_report, language="text")
