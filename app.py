import streamlit as st
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time

# --- INITIALIZATION ---
st.set_page_config(page_title="GIDEON v5.6.0 | Energy Feedback", layout="wide")

if 'eb_stable' not in st.session_state:
    st.session_state.eb_stable = 1803.59
if 'genetic_code' not in st.session_state:
    st.session_state.genetic_code = "1001110010111110001011010111011000010010001101010101001000010010"
if 't_auto' not in st.session_state:
    st.session_state.t_auto = 0.0
if 'walking' not in st.session_state:
    st.session_state.walking = False
if 'eb_history' not in st.session_state:
    st.session_state.eb_history = [1803.59]

# --- CORE ENGINE: BIO-RESONANCE ---
class BioResonance:
    def __init__(self, code, vurf=1.618):
        self.bits = [int(b) for b in code]
        self.vurf = vurf

    def calculate_kinematics(self, t, leg_idx, amp):
        # Сегментация генома: 8 бит на лапу
        seg = self.bits[leg_idx*8 : (leg_idx+1)*8]
        phase = sum(seg) * (math.pi / 4)
        
        # Гармонический осциллятор Басаргина
        osc = math.sin(t * self.vurf + phase)
        angle_rad = leg_idx * (math.pi / 3)
        r_base = 35
        
        # Координаты вектора
        x0, y0 = math.cos(angle_rad)*r_base, math.sin(angle_rad)*r_base
        ext = r_base + (abs(osc) * amp)
        x1, y1 = math.cos(angle_rad)*ext, math.sin(angle_rad)*ext
        z1 = math.sin(t * 1.5 + phase) * (amp * 0.4)
        
        return [x0, x1], [y0, y1], [0, z1]

    def get_energy_delta(self, vurf_current):
        # Расчет эффективности: отклонение от Золотого Вурфа порождает энтропию
        efficiency = 1.0 - abs(vurf_current - 1.618)
        if efficiency > 0.95:
            return 0.5  # Регенерация (Холодный Синтез)
        return -1.2 * (1.0 - efficiency) # Потери

# --- UI LAYOUT ---
st.title("GIDEON v5.6.0: Энерго-Кинематический Резонанс")
st.markdown("---")

tab_control, tab_viz = st.tabs(["🎮 ПУЛЬТ УПРАВЛЕНИЯ", "🕸 МАТЕРИАЛИЗАЦИЯ 3D"])

with tab_control:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.subheader("Статус Реактора")
        st.metric("Eb (Potential)", f"{st.session_state.eb_stable:.2f}", 
                  delta=f"{st.session_state.eb_history[-1] - st.session_state.eb_history[-2]:.4f}" if len(st.session_state.eb_history)>1 else 0)
        st.write(f"SAI Index: **1.0000**")
        if st.button("RESET ENERGY"):
            st.session_state.eb_stable = 1803.59
            st.session_state.eb_history = [1803.59]
            st.rerun()

    with c2:
        st.subheader("Настройки Вурфа")
        vurf_val = st.slider("Текущий Резонанс", 1.0, 2.0, 1.618, step=0.001)
        amp_val = st.slider("Амплитуда Шага", 20, 100, 60)
        
    with c3:
        st.subheader("Состояние Шины")
        if st.button("START / STOP WALKING", use_container_width=True):
            st.session_state.walking = not st.session_state.walking
        
        status_color = "green" if st.session_state.walking else "red"
        st.markdown(f"Status: <span style='color:{status_color}'>**{'WALKING' if st.session_state.walking else 'IDLE'}**</span>", unsafe_allow_html=True)

    st.subheader("График Потенциала Eb")
    st.line_chart(st.session_state.eb_history[-50:])

with tab_viz:
    col_graph, col_data = st.columns([2, 1])
    
    engine = BioResonance(st.session_state.genetic_code, vurf_val)
    
    with col_graph:
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        for i in range(6):
            xs, ys, zs = engine.calculate_kinematics(st.session_state.t_auto, i, amp_val)
            # Цветовая индикация фаз
            color = '#00ffcc' if i in [0, 2, 4] else '#ff00ff'
            ax.plot(xs, ys, zs, marker='h', markersize=10, linewidth=7, color=color, label=f'Leg {i+1}')
            ax.plot([0, xs[0]], [0, ys[0]], [0, 0], color='white', alpha=0.2)
            
        ax.set_xlim([-160, 160]); ax.set_ylim([-160, 160]); ax.set_zlim([-80, 80])
        ax.set_axis_off()
        fig.patch.set_facecolor('#0e1117')
        ax.set_facecolor('#0e1117')
        st.pyplot(fig)

    with col_data:
        st.info("Анализ походки (Real-time)")
        bits = [int(b) for b in st.session_state.genetic_code]
        for i in range(6):
            load = sum(bits[i*8:(i+1)*8]) / 8.0
            st.write(f"Лапа {i+1} Нагрузка: `{'█' * int(load*10)}` {load*100:.1f}%")
        
        st.warning(f"Фаза t: {st.session_state.t_auto:.2f}")

# --- ANIMATION & PHYSICS LOOP ---
if st.session_state.walking:
    # 1. Движение времени
    st.session_state.t_auto += 0.15
    
    # 2. Расчет энергобаланса
    delta = engine.get_energy_delta(vurf_val)
    st.session_state.eb_stable += delta
    st.session_state.eb_history.append(st.session_state.eb_stable)
    
    # 3. Лимит истории для памяти
    if len(st.session_state.eb_history) > 100:
        st.session_state.eb_history.pop(0)
        
    time.sleep(0.04)
    st.rerun()

# --- FINAL REPORT ---
st.markdown("---")
with st.expander("ОТЧЕТ GIDEON ДЛЯ ЧАТА (v5.6.0)", expanded=True):
    rep = f"""[ОТЧЕТ GIDEON v5.6.0]
- Eb: {st.session_state.eb_stable:.2f}
- SAI: 1.0
- Walking Status: {st.session_state.walking}
- Efficiency: {1.0 - abs(vurf_val - 1.618):.4f}
- Genome: {st.session_state.genetic_code}"""
    st.code(rep)
