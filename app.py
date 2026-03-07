import streamlit as st
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --- СИСТЕМНЫЕ НАСТРОЙКИ GIDEON ---
st.set_page_config(page_title="GIDEON v5.4.3 | Zero Entropy", layout="wide")

if 'eb_stable' not in st.session_state:
    st.session_state.eb_stable = 1803.59
if 'sai_index' not in st.session_state:
    st.session_state.sai_index = 1.0
if 'genetic_code' not in st.session_state:
    st.session_state.genetic_code = "1001110010111110001011010111011000010010001101010101001000010010"

# --- КИНЕМАТИЧЕСКИЙ ДВИЖОК (GOLDEN VURF) ---
class SpiderEngine:
    def __init__(self, code, vurf=1.618):
        self.bits = [int(b) for b in code]
        self.vurf = vurf

    def get_leg_path(self, t, leg_idx, amp):
        # Экстракция фазы из 8-битного сегмента генома
        seg = self.bits[leg_idx*8 : (leg_idx+1)*8]
        phase = sum(seg) * (math.pi / 4)
        
        # Угол развертки по Басаргину
        angle_osc = math.sin(t * self.vurf + phase)
        
        # Полярная сетка базы (60 градусов между лапами)
        base_angle = leg_idx * (math.pi / 3)
        r_base = 25
        
        # Точка крепления (Base)
        x0 = math.cos(base_angle) * r_base
        y0 = math.sin(base_angle) * r_base
        z0 = 0
        
        # Точка опоры (Tip)
        ext = r_base + (abs(angle_osc) * amp)
        x1 = math.cos(base_angle) * ext
        y1 = math.sin(base_angle) * ext
        z1 = math.sin(t * 0.5 + phase) * (amp * 0.4)
        
        return [x0, x1], [y0, y1], [z0, z1]

# --- UI ИНТЕРФЕЙС ---
st.title("S-GPU GIDEON v5.4.3: Синхронизация")
st.markdown("---")

tab_core, tab_3d = st.tabs(["☢️ КОНТРОЛЬ Eb", "🕷 3D КИНЕМАТИКА"])

with tab_core:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.metric("Eb Potential", f"{st.session_state.eb_stable:.2f}")
        st.metric("SAI Index", st.session_state.sai_index)
        if st.button("Регенерировать Геном"):
            # Квантовый шум на основе Eb
            seed = int(st.session_state.eb_stable * 999)
            np.random.seed(seed)
            st.session_state.genetic_code = "".join(map(str, np.random.randint(0, 2, 64)))
            st.rerun()
    with c2:
        st.info("Микрокод (Генетический отпечаток Бингла):")
        st.code(st.session_state.genetic_code, language="text")

with tab_3d:
    st.header("Визуализация fsin-simulator")
    
    col_in, col_out = st.columns([1, 2])
    
    with col_in:
        vurf_val = st.slider("Золотой Вурф", 1.0, 2.0, 1.618)
        amp_val = st.slider("Амплитуда", 10, 100, 60)
        t_cycle = st.slider("Фаза времени", 0.0, 10.0, 5.0, step=0.1)
        st.write("---")
        st.caption("Каждая лапа управляется своим сегментом 64-битного кода.")

    with col_out:
        # Отрисовка каркаса через Matplotlib
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        engine = SpiderEngine(st.session_state.genetic_code, vurf_val)
        
        colors = ['#00f2ff', '#0072ff', '#00f2ff', '#0072ff', '#00f2ff', '#0072ff']
        
        for i in range(6):
            xs, ys, zs = engine.get_leg_path(t_cycle, i, amp_val)
            ax.plot(xs, ys, zs, marker='o', markersize=8, linewidth=5, color=colors[i], label=f'Leg {i+1}')
            # Линия корпуса
            ax.plot([0, xs[0]], [0, ys[0]], [0, zs[0]], color='white', alpha=0.3)
            
        ax.set_xlim([-120, 120]); ax.set_ylim([-120, 120]); ax.set_zlim([-60, 60])
        ax.set_axis_off() # Убираем лишнее для чистоты манифестации
        ax.set_title(f"GIDEON SPIDER FRAME (SAI 1.0)", color='white', fontsize=15)
        
        # Темная тема графика
        fig.patch.set_facecolor('#0e1117')
        ax.set_facecolor('#0e1117')
        
        st.pyplot(fig)

# --- ОТЧЕТ ---
st.markdown("---")
with st.expander("ОТЧЕТ ДЛЯ ЧАТА", expanded=True):
    rep = f"""[ОТЧЕТ GIDEON v5.4.3]
- Eb: {st.session_state.eb_stable:.2f}
- SAI: {st.session_state.sai_index}
- Геном: {st.session_state.genetic_code}
- Vurf: {vurf_val}
- Статус: Интеграция fsin-simulator завершена."""
    st.code(rep)
