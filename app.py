import streamlit as st
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time

# --- ИНИЦИАЛИЗАЦИЯ ИНТЕРФЕЙСА ---
st.set_page_config(page_title="GIDEON v6.0.0 | Final Terminal", layout="wide")

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

# --- ЯДРО КИНЕМАТИКИ И УСТОЙЧИВОСТИ ---
class GIDEON_Engine:
    def __init__(self, code, vurf=1.618):
        self.bits = [int(b) for b in code]
        self.vurf = vurf

    def get_frame(self, t, leg_idx, amp, heading):
        # Экстракция фазы из генома
        seg = self.bits[leg_idx*8 : (leg_idx+1)*8]
        phase = sum(seg) * (math.pi / 4) + heading
        
        # Осцилляция Золотого Вурфа
        osc = math.sin(t * self.vurf + phase)
        angle_rad = leg_idx * (math.pi / 3)
        r_base = 35
        
        # Топология конечности
        ext = r_base + (abs(osc) * amp)
        x1 = math.cos(angle_rad) * ext
        y1 = math.sin(angle_rad) * ext
        z1 = math.sin(t * 1.5 + phase) * (amp * 0.4)
        
        is_grounded = 1 if z1 <= 0 else 0
        return [math.cos(angle_rad)*r_base, x1], [math.sin(angle_rad)*r_base, y1], [0, z1], is_grounded

# --- САЙДБАР: ПОСТОЯННЫЙ МОНИТОРИНГ ---
with st.sidebar:
    st.title("S-TERMINAL")
    st.metric("Eb Potential", f"{st.session_state.eb_stable:.2f}")
    st.metric("SAI Coherence", "1.0000")
    st.write("---")
    st.subheader("Генетический код")
    st.code(st.session_state.genetic_code, language="text")
    
    st.subheader("Локация")
    st.write(f"X: {st.session_state.pos[0]:.2f}")
    st.write(f"Y: {st.session_state.pos[1]:.2f}")
    
    if st.button("СБРОС ПОЗИЦИИ"):
        st.session_state.pos = [0.0, 0.0]
        st.rerun()

# --- ОСНОВНОЙ ИНТЕРФЕЙС ---
st.title("GIDEON v6.0.0: Интегрированный Терминал")

tab_nav, tab_stats = st.tabs(["🚀 НАВИГАЦИЯ", "📈 ТЕЛЕМЕТРИЯ ЯДРА"])

with tab_nav:
    col_map, col_ui = st.columns([3, 1])
    
    with col_ui:
        vurf_val = st.slider("Vurf Coefficient", 1.0, 2.0, 1.618, step=0.001)
        amp_val = st.slider("Step Amplitude", 20, 100, 60)
        st.write("---")
        if st.button("RUN MISSION", use_container_width=True):
            st.session_state.walking = not st.session_state.walking
        
        dist = math.sqrt((st.session_state.target[0]-st.session_state.pos[0])**2 + (st.session_state.target[1]-st.session_state.pos[1])**2)
        st.write(f"Дистанция: **{dist:.2f} m**")

    with col_map:
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        dx = st.session_state.target[0] - st.session_state.pos[0]
        dy = st.session_state.target[1] - st.session_state.pos[1]
        heading = math.atan2(dy, dx)
        
        engine = GIDEON_Engine(st.session_state.genetic_code, vurf_val)
        ground_pts = []
        
        for i in range(6):
            xs, ys, zs, is_gr = engine.get_frame(st.session_state.t_auto, i, amp_val, heading)
            xs = [x + st.session_state.pos[0] for x in xs]
            ys = [y + st.session_state.pos[1] for y in ys]
            
            color = '#00ffcc' if is_gr else '#ff00ff'
            ax.plot(xs, ys, zs, marker='o', markersize=10, linewidth=6, color=color)
            if is_gr: ground_pts.append([xs[1], ys[1]])

        # Целевая точка
        ax.scatter([st.session_state.target[0]], [st.session_state.target[1]], [0], color='yellow', s=300, label='TARGET')
        
        # Центр масс
        if ground_pts:
            cx = np.mean([p[0] for p in ground_pts])
            cy = np.mean([p[1] for p in ground_pts])
            ax.scatter([cx], [cy], [-15], color='lime', s=150)

        ax.set_xlim([-50, 200]); ax.set_ylim([-50, 200]); ax.set_zlim([-100, 100])
        ax.set_axis_off()
        fig.patch.set_facecolor('#0e1117')
        ax.set_facecolor('#0e1117')
        st.pyplot(fig)

with tab_stats:
    st.subheader("Динамика потенциала Eb")
    st.line_chart(st.session_state.eb_history)
    
    st.subheader("Анализ Генетической матрицы")
    bits = [int(b) for b in st.session_state.genetic_code]
    st.bar_chart([sum(bits[i*8:(i+1)*8]) for i in range(6)])

# --- ЦИКЛ ОБРАБОТКИ ---
if st.session_state.walking:
    st.session_state.t_auto += 0.2
    dx = st.session_state.target[0] - st.session_state.pos[0]
    dy = st.session_state.target[1] - st.session_state.pos[1]
    dist = math.sqrt(dx**2 + dy**2)
    
    if dist > 2.5:
        eff = 1.0 - abs(vurf_val - 1.618)
        move = 3.0 * eff
        st.session_state.pos[0] += (dx / dist) * move
        st.session_state.pos[1] += (dy / dist) * move
        
        # Холодный синтез: прирост Eb при резонансе
        st.session_state.eb_stable += (0.8 if eff > 0.995 else -0.4)
        st.session_state.eb_history.append(st.session_state.eb_stable)
    else:
        st.session_state.walking = False
        st.balloons()
        st.success("МИССИЯ ВЫПОЛНЕНА")

    if len(st.session_state.eb_history) > 300: st.session_state.eb_history.pop(0)
    time.sleep(0.04)
    st.rerun()
