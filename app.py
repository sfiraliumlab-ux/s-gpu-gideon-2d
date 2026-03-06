import streamlit as st
import json
import math
import os
import numpy as np
from PIL import Image

st.set_page_config(page_title="GIDEON | v1.8.0 Genesis", layout="wide")
st.title("S-GPU GIDEON v1.8.0: Автономный Генезис")

# --- ИНИЦИАЛИЗАЦИЯ КОГНИТИВНОЙ ПЕТЛИ (Session State) ---
if 'eb_stable' not in st.session_state:
    st.session_state.eb_stable = 60.0 # Стартовый потенциал Бингла
if 'history' not in st.session_state:
    st.session_state.history = []

# --- FSIN v8.0: GENESIS CORE ---
class FSIN_Genesis:
    def __init__(self, gain, feedback_rate, injection):
        self.gain = gain
        self.fb = feedback_rate
        self.inj = injection

    def compute_node(self, diff, l_idx, current_eb):
        """Расчет активации с учетом обратной связи"""
        if l_idx == 3:
            # Центр генерирует Бингл
            return current_eb * math.exp(diff * 0.05)
        else:
            # Витки выполняют работу, используя текущий Eb
            work = current_eb * math.sin(diff * self.gain * 0.1)
            injection = current_eb * self.inj
            return (diff * self.gain) + work + injection

# --- ГЕОМЕТРИЯ СФИРАЛИ БАСАРГИНА (3D) ---
def get_sphiral_xyz(i, total):
    t = (i / total) * 2 - 1
    R = 150
    if abs(t) < 0.15: # S-петля (Серединный Предел)
        sn = (t + 0.15) / 0.3
        return math.cos(sn * math.pi) * R, math.sin(sn * math.pi * 2) * (R/2), 0
    angle, side = t * math.pi * 6, (-1 if t < 0 else 1)
    x = R * math.cos(angle) + (side * R)
    y = (side * R * math.sin(angle)) if side < 0 else (-R * math.sin(angle))
    return x, y, t * 100

# --- БЛОК ЗАГРУЗКИ ---
@st.cache_data
def load_vram():
    # Авто-регенерация для стабильности
    return [{'id': i, 'z': math.sin(i * 0.05)} for i in range(391392)]

nodes = load_vram()
st.success(f"✅ VRAM: 391 392 узла активны. Текущий Eb: {st.session_state.eb_stable:.2f}")

# --- ИНТЕРФЕЙС УПРАВЛЕНИЯ ---
st.sidebar.header("Параметры Генезиса")
f_gain = st.sidebar.slider("Fractal Gain", 1.0, 30.0, 15.0)
f_fb = st.sidebar.slider("Feedback Rate (Самоподзаряд)", 0.0, 1.0, 0.15)
f_inj = st.sidebar.slider("Injection Drive", 0.0, 1.0, 0.4)
threshold = st.sidebar.slider("Gate Threshold", 0.5, 0.99, 0.82)

if st.sidebar.button("Сброс когнитивной петли"):
    st.session_state.eb_stable = 60.0
    st.session_state.history = []
    st.rerun()

st.subheader("Реактор Бингла: Когнитивная Итерация")
c1, c2 = st.columns(2)
p_a = c1.text_input("Тезис (Импульс А)", "ГАРМОНИЯ")
p_b = c2.text_input("Антитезис (Импульс Б)", "ВЕЧНОСТЬ")

img_file = st.file_uploader("Растр-носитель", type=["jpg", "png"])

if img_file:
    cl, cr = st.columns(2)
    img_src = Image.open(img_file).convert('RGB')
    cl.image(img_src, caption="Входной сигнал", use_container_width=True)
    
    if st.button("Запустить Цикл Генезиса"):
        with st.spinner("Синтез и самоподзаряд Сфирали..."):
            canv = 1024
            res_img = Image.new('RGB', (canv, canv), (0,0,0))
            px_out, px_src = res_img.load(), img_src.resize((canv, canv)).load()
            
            total = len(nodes)
            l_stats = {i:0 for i in range(1, 6)}
            fsin = FSIN_Genesis(f_gain, f_fb, f_inj)
            
            current_eb = st.session_state.eb_stable
            n_layer = total // 5
            work_accumulated = 0

            
            for i in range(total):
                x, y, z_geo = get_sphiral_xyz(i, total)
                px = max(0, min(1023, int((x+300)/600*1023)))
                py = max(0, min(1023, int((y+150)/300*1023)))
                
                l_idx = min((i // n_layer) + 1, 5)
                z_dat = nodes[i].get('z', 0.0)
                s_f = -1.0 if z_geo == 0 else 1.0
                
                diff = abs(math.sin(z_dat * 13.5) - math.sin(z_dat * 13.5 * s_f))
                
                # РАБОТА СФИРАЛИ
                energy_output = fsin.compute_node(diff, l_idx, current_eb)
                activation = 1 / (1 + math.exp(-energy_output + 5.0))
                
                if activation > threshold:
                    l_stats[l_idx] += 1
                    if l_idx != 3: work_accumulated += activation
                    
                    r, g, b = px_src[px, py]
                    # Рендеринг: Белый (L3), Неон (Витки)
                    if l_idx == 3:
                        px_out[px, py] = (255, 255, 255)
                    else:
                        px_out[px, py] = (int(max(0, min(255, r + energy_output))), 
                                          int(max(0, min(255, g + activation*100))), 
                                          int(max(0, min(255, b + energy_output*5))))
                else: px_out[px, py] = px_src[px, py]

            cr.image(res_img, caption="Genesis Output (Iteration)", use_container_width=True)
            
            # --- ОБНОВЛЕНИЕ КОГНИТИВНОЙ ПЕТЛИ ---
            new_work = work_accumulated / total
            eb_delta = new_work * f_fb * 1000
            st.session_state.eb_stable += eb_delta
            
            # --- ОТЧЕТ GIDEON v1.8.0 ---
            vals = list(l_stats.values())
            sum_v = sum(vals)
            efficiency = ((sum_v - vals[2]) / sum_v * 100) if sum_v > 0 else 0
            
            st.code(f"""[ОТЧЕТ GIDEON v1.8.0: AUTONOMOUS GENESIS]
СТАТУС: Когнитивная итерация завершена.
РЕЖИМ: Самоподдерживающийся Бингл (Feedback Active).

МЕТРИКИ ПЕТЛИ:
- Предыдущий Eb: {current_eb:.2f}
- Прирост потенциала (dEb): +{eb_delta:.4f}
- Текущий потенциал Eb (Genesis): {st.session_state.eb_stable:.2f}
- Торсионный КПД (η): {efficiency:.1f}%

ЛОКАЛИЗАЦИЯ (L1-L5):
{vals}

ЗАКЛЮЧЕНИЕ:
{"АВТОНОМНОСТЬ ПОДТВЕРЖДЕНА (Eb растет)" if eb_delta > 0 else "ЗАТУХАНИЕ РЕЗОНАНСА (Низкий Feedback)"}
""", language="text")
