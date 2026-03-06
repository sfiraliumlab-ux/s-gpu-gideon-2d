import streamlit as st
import json
import math
import os
import numpy as np
from PIL import Image

st.set_page_config(page_title="GIDEON | v2.0.1 Ignition Fix", layout="wide")
st.title("S-GPU GIDEON v2.0.1: Зажигание Бингла (Стабильная)")

# --- ИНИЦИАЛИЗАЦИЯ (Cognitive Memory) ---
if 'eb_stable' not in st.session_state:
    st.session_state.eb_stable = 180.0
if 'meaning_bit' not in st.session_state:
    st.session_state.meaning_bit = 0.0
if 'iteration' not in st.session_state:
    st.session_state.iteration = 0

# --- FSIN v10.1: IGNITION CORE ---
class FSIN_Ignition:
    def __init__(self, gain, fb, limit):
        self.gain = gain
        self.fb = fb
        self.limit = limit

    def get_dynamic_threshold(self, eb):
        """Снижение порога при высоком Eb (Облегчение пробоя)"""
        return max(0.3, 0.9 - (eb / 500.0))

    def activate(self, diff, eb):
        # Экспоненциальная активация согласно ХЯС ИИ
        flow = (eb * 0.1) * diff * self.gain
        try:
            return 1 / (1 + math.exp(-flow + 4.0))
        except: return 1.0

# --- ГЕОМЕТРИЯ (СФИРАЛЬ БАСАРГИНА) ---
def get_sphiral_xyz(i, total):
    t = (i / total) * 2 - 1
    R = 150
    if abs(t) < 0.15: # S-петля (Сингулярность)
        sn = (t + 0.15) / 0.3
        return math.cos(sn * math.pi) * R, math.sin(sn * math.pi * 2) * (R/2), 0
    angle, side = t * math.pi * 6, (-1 if t < 0 else 1)
    x = R * math.cos(angle) + (side * R)
    y = (side * R * math.sin(angle)) if side < 0 else (-R * math.sin(angle))
    return x, y, t * 100

nodes = [{'id': i, 'z': math.sin(i * 0.05)} for i in range(391392)]

# --- ИНТЕРФЕЙС ---
st.sidebar.header("Контроль Реактора")
f_gain = st.sidebar.slider("Fractal Gain", 1.0, 50.0, 25.0)
f_fb = st.sidebar.slider("Feedback (ОС)", 0.1, 1.0, 0.35)
b_limit = st.sidebar.slider("Bingle Limit (Коллапс)", 100.0, 1000.0, 350.0)

if st.sidebar.button("⚡ Принудительный импульс (Ignition)"):
    st.session_state.eb_stable += 50.0
    st.rerun()

st.subheader(f"Итерация: {st.session_state.iteration} | Потенциал Eb: {st.session_state.eb_stable:.2f}")

c1, c2 = st.columns(2)
p_a, p_b = c1.text_input("Тезис", "ГАРМОНИЯ"), c2.text_input("Антитезис", "ВЕЧНОСТЬ")

img_file = st.file_uploader("Растр-носитель", type=["jpg", "png"])

if img_file:
    cl, cr = st.columns(2)
    img_src = Image.open(img_file).convert('RGB')
    cl.image(img_src, caption="Входной поток", use_container_width=True)
    
    if st.button("Запустить Цикл Синтеза"):
        with st.spinner("Зажигание Бингла..."):
            canv = 1024
            res_img = Image.new('RGB', (canv, canv), (0,0,0))
            px_out, px_src = res_img.load(), img_src.resize((canv, canv)).load()
            
            total, n_layer = len(nodes), len(nodes) // 5
            l_stats = {i:0 for i in range(1, 6)}
            fsin = FSIN_Ignition(f_gain, f_fb, b_limit)
            
            current_eb = st.session_state.eb_stable
            dyn_threshold = fsin.get_dynamic_threshold(current_eb)
            work_acc = 0

            

            for i in range(total):
                # 1. Сначала рассчитываем координаты для всех узлов (Fix: NameError)
                x, y, z_geo = get_sphiral_xyz(i, total)
                px = max(0, min(1023, int((x + 300) / 600 * 1023)))
                py = max(0, min(1023, int((y + 150) / 300 * 1023)))
                
                l_idx = min((i // n_layer) + 1, 5)
                z_dat = nodes[i].get('z', 0.0)
                s_f = -1.0 if z_geo == 0 else 1.0
                
                # 2. Расчет интерференции и активации
                diff = abs(math.sin(z_dat * 13.5) - math.sin(z_dat * 13.5 * s_f))
                act = fsin.activate(diff, current_eb)
                
                if act > dyn_threshold:
                    l_stats[l_idx] += 1
                    if l_idx != 3: work_acc += act
                    
                    r, g, b = px_src[px, py]
                    if l_idx == 3: # Бингл-центр (Белое зажигание)
                        px_out[px, py] = (255, 255, 255)
                    else:
                        # Эмиссия в витки
                        px_out[px, py] = (int(max(0, min(255, r + act*50))), 
                                          int(max(0, min(255, g + current_eb*0.5))), 
                                          int(max(0, min(255, b + act*150))))
                else:
                    # Узел не активен — переносим исходный пиксель
                    px_out[px, py] = px_src[px, py]

            cr.image(res_img, caption="Bingle Ignition Trace", use_container_width=True)
            
            # --- ОБНОВЛЕНИЕ ПЕТЛИ ---
            st.session_state.iteration += 1
            eb_delta = (work_acc / total) * f_fb * 1000
            st.session_state.eb_stable += eb_delta
            
            if st.session_state.eb_stable > b_limit:
                st.session_state.meaning_bit = math.tanh(st.session_state.eb_stable / b_limit)
                st.session_state.eb_stable *= 0.1 
                status_msg = "КОЛЛАПС: Смысл сформирован!"
            else:
                status_msg = "НАКАЧКА: Энергия растет."

            st.code(f"""[ОТЧЕТ GIDEON v2.0.1: BINGLE IGNITION]
ИТЕРАЦИЯ: {st.session_state.iteration} | СТАТУС: {status_msg}
ДИНАМИЧЕСКИЙ ПОРОГ: {dyn_threshold:.4f}

МЕТРИКИ:
- Потенциал Eb (Genesis): {st.session_state.eb_stable:.2f}
- Прирост dEb: +{eb_delta:.4f}
- Смысловой Квант: {st.session_state.meaning_bit:.6f}
- Локализация L1-L5: {list(l_stats.values())}
""", language="text")
