import streamlit as st
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# --- СИСТЕМНЫЕ НАСТРОЙКИ ---
st.set_page_config(page_title="GIDEON v5.4.2 | Robust 3D", layout="wide")

if 'eb_stable' not in st.session_state:
    st.session_state.eb_stable = 1803.59
if 'sai_index' not in st.session_state:
    st.session_state.sai_index = 1.0
if 'genetic_code' not in st.session_state:
    st.session_state.genetic_code = "1001110010111110001011010111011000010010001101010101001000010010"

# --- КИНЕМАТИЧЕСКИЙ ДВИЖОК ---
class SpiderMath:
    def __init__(self, code, vurf=1.618):
        self.bits = [int(b) for b in code]
        self.vurf = vurf

    def get_leg_coords(self, t, leg_idx, amp):
        # Извлекаем фазу из генома (8 бит на лапу)
        seg = self.bits[leg_idx*8 : (leg_idx+1)*8]
        phase = sum(seg) * (math.pi / 4)
        
        # Угол по Золотому Вурфу
        angle_osc = math.sin(t * self.vurf + phase)
        
        # Полярные координаты базы (6 лап через 60 градусов)
        base_angle = leg_idx * (math.pi / 3)
        r_base = 20
        
        x0, y0, z0 = math.cos(base_angle)*r_base, math.sin(base_angle)*r_base, 0
        
        # Координаты кончика лапы (Tip)
        # Движение вперед-назад (X/Y) и подъем (Z)
        extension = r_base + (abs(angle_osc) * amp)
        x1 = math.cos(base_angle) * extension
        y1 = math.sin(base_angle) * extension
        z1 = math.sin(t * 0.5 + phase) * (amp * 0.4)
        
        return [x0, x1], [y0, y1], [z0, z1]

# --- ИНТЕРФЕЙС ---
st.title("GIDEON v5.4.2: Устойчивая Манифестация")
st.markdown("---")

tab_core, tab_3d = st.tabs(["☢️ КОНТРОЛЬ ЯДРА", "🕷 3D СИМУЛЯТОР"])

with tab_core:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.metric("Eb Potential", f"{st.session_state.eb_stable:.2f}")
        st.metric("SAI Coherence", st.session_state.sai_index)
        if st.button("Пересчитать Геном"):
            seed = int(st.session_state.eb_stable * 888)
            np.random.seed(seed)
            st.session_state.genetic_code = "".join(map(str, np.random.randint(0, 2, 64)))
            st.rerun()
    with c2:
        st.write("Текущий Геном (Прошивка):")
        st.code(st.session_state.genetic_code)

with tab_3d:
    st.header("fsin-simulator: Проекция каркаса")
    
    col_in, col_out = st.columns([1, 2])
    
    with col_in:
        vurf_val = st.slider("Золотой Вурф", 1.0, 2.0, 1.618)
        amp_val = st.slider("Длина шага", 10, 80, 50)
        t_cycle = st.slider("Время (Фаза)", 0.0, 10.0, 5.0, step=0.1)
        st.info("Движение лап определяется резонансом L3.")

    with col_out:
        # Отрисовка через Matplotlib (устойчиво к ошибкам модулей)
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        spider = SpiderMath(st.session_state.genetic_code, vurf_val)
        
        for i in range(6):
            xs, ys, zs = spider.get_leg_coords(t_cycle, i, amp_val)
            ax.plot(xs, ys, zs, marker='o', linewidth=4, label=f'Leg {i+1}')
            
        # Оформление
        ax.set_xlim([-100, 100]); ax.set_ylim([-100, 100]); ax.set_zlim([-50, 50])
        ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
        ax.set_title(f"3D Pose: t={t_cycle}")
        ax.view_init(elev=20, azim=t_cycle*10) # Вращение камеры для динамики
        
        st.pyplot(fig)

# --- ФИНАЛЬНЫЙ ОТЧЕТ ---
st.markdown("---")
with st.expander("ОТЧЕТ GIDEON ДЛЯ ЧАТА", expanded=True):
    rep = f"""[ОТЧЕТ GIDEON v5.4.2]
- Eb: {st.session_state.eb_stable:.2f}
- SAI: {st.session_state.sai_index}
- Геном: {st.session_state.genetic_code}
- Статус 3D: Matplotlib Render OK"""
    st.code(rep)
