import streamlit as st
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time

# --- INITIALIZATION ---
st.set_page_config(page_title="GIDEON v5.8.0 | Stability", layout="wide")

if 'eb_stable' not in st.session_state:
    st.session_state.eb_stable = 1803.59
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
    st.session_state.eb_history = [1803.59]

# --- ENGINE: STABILITY & KINEMATICS ---
class SStabilityEngine:
    def __init__(self, code, vurf=1.618):
        self.bits = [int(b) for b in code]
        self.vurf = vurf

    def get_dynamics(self, t, leg_idx, amp, heading):
        seg = self.bits[leg_idx*8 : (leg_idx+1)*8]
        phase = sum(seg) * (math.pi / 4) + heading
        
        # Модифицированный осциллятор для стабильности
        osc = math.sin(t * self.vurf + phase)
        angle_rad = leg_idx * (math.pi / 3)
        r_base = 35
        
        ext = r_base + (abs(osc) * amp)
        x1, y1 = math.cos(angle_rad)*ext, math.sin(angle_rad)*ext
        z1 = math.sin(t * 1.5 + phase) * (amp * 0.4)
        
        # Возвращаем координаты и 'вес' лапы (опора/перенос)
        is_grounded = 1 if z1 <= 0 else 0
        return [math.cos(angle_rad)*r_base, x1], [math.sin(angle_rad)*r_base, y1], [0, z1], is_grounded

# --- UI ---
st.title("S-GPU GIDEON v5.8.0: Анализ Устойчивости")
st.markdown("---")

tab_nav, tab_analyst = st.tabs(["🕷 АВТОНОМНЫЙ ПАУК", "📊 АНАЛИТИКА ТЯГИ"])

with tab_nav:
    col_map, col_ui = st.columns([2, 1])
    
    with col_ui:
        vurf_val = st.slider("Резонанс Вурфа", 1.0, 2.0, 1.618, step=0.001)
        amp_val = st.slider("Амплитуда", 20, 100, 65)
        if st.button("АКТИВИРОВАТЬ МИССИЮ", use_container_width=True):
            st.session_state.walking = not st.session_state.walking
        
        st.metric("Eb Potential", f"{st.session_state.eb_stable:.2f}")
        dist = math.sqrt((st.session_state.target[0]-st.session_state.pos[0])**2 + (st.session_state.target[1]-st.session_state.pos[1])**2)
        st.write(f"До цели: **{dist:.2f} m**")

    with col_map:
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        dx, dy = st.session_state.target[0] - st.session_state.pos[0], st.session_state.target[1] - st.session_state.pos[1]
        heading = math.atan2(dy, dx)
        
        engine = SStabilityEngine(st.session_state.genetic_code, vurf_val)
        grounded_points = []
        
        for i in range(6):
            xs, ys, zs, is_gr = engine.get_dynamics(st.session_state.t_auto, i, amp_val, heading)
            xs = [x + st.session_state.pos[0] for x in xs]
            ys = [y + st.session_state.pos[1] for y in ys]
            
            # Цвет лапы: в воздухе - маджента, на земле - бирюза
            color = '#00ffcc' if is_gr else '#ff00ff'
            ax.plot(xs, ys, zs, marker='o', markersize=10, linewidth=6, color=color)
            if is_gr: grounded_points.append([xs[1], ys[1]])

        # Визуализация Центра Масс (CoM)
        if grounded_points:
            com_x = np.mean([p[0] for p in grounded_points])
            com_y = np.mean([p[1] for p in grounded_points])
            ax.scatter([com_x], [com_y], [-20], color='lime', s=100, label='CoM')

        ax.scatter([st.session_state.target[0]], [st.session_state.target[1]], [0], color='yellow', s=300)
        ax.set_xlim([-50, 200]); ax.set_ylim([-50, 200]); ax.set_zlim([-100, 100])
        ax.set_axis_off()
        fig.patch.set_facecolor('#0e1117')
        ax.set_facecolor('#0e1117')
        st.pyplot(fig)

with tab_analyst:
    st.subheader("Мониторинг Холодного Синтеза")
    st.line_chart(st.session_state.eb_history[-100:])
    st.write("Смещение фаз (8-bit segments):")
    bits = [int(b) for b in st.session_state.genetic_code]
    st.bar_chart([sum(bits[i*8:(i+1)*8]) for i in range(6)])

# --- LOOP ---
if st.session_state.walking:
    st.session_state.t_auto += 0.2
    dx, dy = st.session_state.target[0] - st.session_state.pos[0], st.session_state.target[1] - st.session_state.pos[1]
    dist = math.sqrt(dx**2 + dy**2)
    
    if dist > 3:
        # Скорость завязана на КПД Вурфа
        efficiency = 1.0 - abs(vurf_val - 1.618)
        step = 2.5 * efficiency
        st.session_state.pos[0] += (dx / dist) * step
        st.session_state.pos[1] += (dy / dist) * step
        
        # Энергобаланс
        st.session_state.eb_stable += (0.6 if efficiency > 0.99 else -0.5)
        st.session_state.eb_history.append(st.session_state.eb_stable)
    else:
        st.session_state.walking = False
        st.success("МИССИЯ ЗАВЕРШЕНА: ЦЕЛЬ ДОСТИГНУТА")

    if len(st.session_state.eb_history) > 200: st.session_state.eb_history.pop(0)
    time.sleep(0.04)
    st.rerun()
