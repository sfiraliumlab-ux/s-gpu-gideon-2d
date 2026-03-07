import streamlit as st
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time

# --- INITIALIZATION ---
st.set_page_config(page_title="GIDEON v5.7.0 | Bingle Vision", layout="wide")

if 'eb_stable' not in st.session_state:
    st.session_state.eb_stable = 1803.59
if 'genetic_code' not in st.session_state:
    st.session_state.genetic_code = "1001110010111110001011010111011000010010001101010101001000010010"
if 'pos' not in st.session_state:
    st.session_state.pos = [0.0, 0.0] # X, Y координаты паука
if 'target' not in st.session_state:
    st.session_state.target = [100.0, 100.0] # Точка цели
if 't_auto' not in st.session_state:
    st.session_state.t_auto = 0.0
if 'walking' not in st.session_state:
    st.session_state.walking = False
if 'eb_history' not in st.session_state:
    st.session_state.eb_history = [1803.59]

# --- ENGINE: S-NAVI ---
class SNaviEngine:
    def __init__(self, code, vurf=1.618):
        self.bits = [int(b) for b in code]
        self.vurf = vurf

    def calculate_kinematics(self, t, leg_idx, amp, heading_offset):
        seg = self.bits[leg_idx*8 : (leg_idx+1)*8]
        phase = sum(seg) * (math.pi / 4) + heading_offset
        
        osc = math.sin(t * self.vurf + phase)
        angle_rad = leg_idx * (math.pi / 3)
        r_base = 35
        
        x0, y0 = math.cos(angle_rad)*r_base, math.sin(angle_rad)*r_base
        ext = r_base + (abs(osc) * amp)
        x1, y1 = math.cos(angle_rad)*ext, math.sin(angle_rad)*ext
        z1 = math.sin(t * 1.5 + phase) * (amp * 0.4)
        
        return [x0, x1], [y0, y1], [0, z1]

# --- UI LAYOUT ---
st.title("S-GPU GIDEON v5.7.0: Bingle-Vision")
st.markdown("---")

tab_core, tab_nav = st.tabs(["☢️ РЕАКТОР И ГЕНОМ", "🕸 НАВИГАЦИЯ ПАУКА"])

with tab_core:
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Eb Potential", f"{st.session_state.eb_stable:.2f}")
        st.metric("SAI", "1.0000")
        st.write("**Генетический отпечаток:**")
        st.code(st.session_state.genetic_code)
    with c2:
        st.subheader("Телеметрия Eb")
        st.line_chart(st.session_state.eb_history[-50:])

with tab_nav:
    col_map, col_ctrl = st.columns([2, 1])
    
    with col_ctrl:
        st.subheader("Параметры Цели")
        target_x = st.number_input("Target X", value=100.0)
        target_y = st.number_input("Target Y", value=100.0)
        st.session_state.target = [target_x, target_y]
        
        vurf_val = st.slider("Vurf Resonance", 1.0, 2.0, 1.618, step=0.001)
        amp_val = st.slider("Step Power", 20, 100, 60)
        
        if st.button("TOGGLE AUTO-WALK", use_container_width=True):
            st.session_state.walking = not st.session_state.walking
        
        dist = math.sqrt((st.session_state.target[0]-st.session_state.pos[0])**2 + (st.session_state.target[1]-st.session_state.pos[1])**2)
        st.write(f"Дистанция до цели: **{dist:.2f}**")
        if dist < 10: st.success("ЦЕЛЬ ДОСТИГНУТА!")

    with col_map:
        # Визуализация карты навигации
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        # Расчет угла поворота к цели (Heading)
        dx = st.session_state.target[0] - st.session_state.pos[0]
        dy = st.session_state.target[1] - st.session_state.pos[1]
        heading = math.atan2(dy, dx)
        
        engine = SNaviEngine(st.session_state.genetic_code, vurf_val)
        
        # Отрисовка паука
        for i in range(6):
            xs, ys, zs = engine.calculate_kinematics(st.session_state.t_auto, i, amp_val, heading)
            # Сдвиг отрисовки в текущую позицию паука
            xs = [x + st.session_state.pos[0] for x in xs]
            ys = [y + st.session_state.pos[1] for y in ys]
            ax.plot(xs, ys, zs, marker='h', markersize=8, linewidth=5, color='#00ffcc' if i%2==0 else '#ff00ff')

        # Отрисовка цели
        ax.scatter([st.session_state.target[0]], [st.session_state.target[1]], [0], color='yellow', s=200, label='TARGET')
        
        ax.set_xlim([-150, 150]); ax.set_ylim([-150, 150]); ax.set_zlim([-80, 80])
        ax.set_axis_off()
        fig.patch.set_facecolor('#0e1117')
        ax.set_facecolor('#0e1117')
        st.pyplot(fig)

# --- NAVIGATION LOOP ---
if st.session_state.walking:
    st.session_state.t_auto += 0.2
    
    # Расчет движения вперед к цели
    dx = st.session_state.target[0] - st.session_state.pos[0]
    dy = st.session_state.target[1] - st.session_state.pos[1]
    dist = math.sqrt(dx**2 + dy**2)
    
    if dist > 5:
        step_size = 2.0 * (1.0 - abs(vurf_val - 1.618)) # Скорость зависит от резонанса
        st.session_state.pos[0] += (dx / dist) * step_size
        st.session_state.pos[1] += (dy / dist) * step_size
    
    # Энергобаланс
    efficiency = 1.0 - abs(vurf_val - 1.618)
    delta = 0.5 if efficiency > 0.98 else -0.8
    st.session_state.eb_stable += delta
    st.session_state.eb_history.append(st.session_state.eb_stable)
    
    if len(st.session_state.eb_history) > 100: st.session_state.eb_history.pop(0)
    
    time.sleep(0.05)
    st.rerun()

# --- REPORT ---
st.markdown("---")
with st.expander("ОТЧЕТ GIDEON v5.7.0 (Vision Ready)", expanded=True):
    rep = f"""[ОТЧЕТ GIDEON v5.7.0]
- Eb: {st.session_state.eb_stable:.2f}
- SAI: 1.0
- Pos: {st.session_state.pos}
- Target: {st.session_state.target}
- Status: {'HUNTING' if st.session_state.walking else 'IDLE'}"""
    st.code(rep)
