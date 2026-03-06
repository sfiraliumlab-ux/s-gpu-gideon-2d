import streamlit as st
import json
import math
import os
import numpy as np
from PIL import Image

st.set_page_config(page_title="GIDEON | v1.7.0 BtW Emission", layout="wide")
st.title("S-GPU GIDEON v1.7.0: Эмиссия Смысла (BtW)")

# --- FSIN v7: BtW CORE (BINGLE-TO-WORK) ---
class FSIN_BtW:
    def __init__(self, gain, tension, emission):
        self.gain = gain
        self.tension = tension
        self.emission = emission # Коэффициент BtW

    def compute_emission_work(self, diff, l_idx, eb_potential):
        """
        Конвертация потенциала Бингла в торсионную работу.
        Eb (из L3) усиливает фазовый сдвиг в витках (L1, L2, L4, L5).
        """
        if l_idx == 3:
            # Генерация Eb (Схлопывание)
            return self.tension * math.exp(diff * 0.1)
        else:
            # Эмиссия: использование потенциала Eb для проворота фазы
            # Работа W = Eb * sin(phi)
            work = eb_potential * math.sin(diff * self.emission)
            return diff * self.gain + work

# --- ГЕОМЕТРИЯ И ЗАГРУЗКА ---
def get_xyz(i, total):
    t = (i / total) * 2 - 1
    R = 150
    if abs(t) < 0.15: # Реактор Бингла
        sn = (t + 0.15) / 0.3
        return math.cos(sn * math.pi) * R, math.sin(sn * math.pi * 2) * (R/2), 0
    angle, side = t * math.pi * 6, (-1 if t < 0 else 1)
    return (R * math.cos(angle) + side * R), (side * R * math.sin(angle) if side < 0 else -R * math.sin(angle)), t * 100

nodes = [{'id': i, 'z': math.sin(i * 0.05)} for i in range(391392)]

# --- ИНТЕРФЕЙС УПРАВЛЕНИЯ ---
st.sidebar.header("Параметры BtW")
b_tension = st.sidebar.slider("Bingle Potential (Eb)", 1.0, 100.0, 60.0)
f_emission = st.sidebar.slider("Emission Rate (BtW)", 0.1, 10.0, 4.5)
f_gain = st.sidebar.slider("Fractal Gain", 1.0, 30.0, 15.0)
threshold = st.sidebar.slider("Gate Threshold", 0.5, 0.99, 0.85)

st.subheader("Сфиральный Реактор: Эмиссия из Бингла")
c1, c2 = st.columns(2)
p_a = c1.text_input("Тезис", "ГАРМОНИЯ")
p_b = c2.text_input("Антитезис", "ВЕЧНОСТЬ")

img_file = st.file_uploader("Растр-носитель", type=["jpg", "png"])

if img_file:
    cl, cr = st.columns(2)
    img_src = Image.open(img_file).convert('RGB')
    cl.image(img_src, caption="Входной поток (2D)", use_container_width=True)
    
    if st.button("Инициировать Эмиссию BtW"):
        with st.spinner("Извлечение работы из Бингла..."):
            canv = 1024
            res_img = Image.new('RGB', (canv, canv), (0,0,0))
            px_out, px_src = res_img.load(), img_src.resize((canv, canv)).load()
            
            total = len(nodes)
            l_stats = {i:0 for i in range(1, 6)}
            fsin = FSIN_BtW(f_gain, b_tension, f_emission)
            
            # Предварительный расчет Eb (потенциал центра)
            eb_potential = b_tension * (math.pi / 2) # Нормализованный потенциал
            
            for i in range(total):
                x, y, z_geo = get_xyz(i, total)
                px, py = max(0, min(1023, int((x+300)/600*1023))), max(0, min(1023, int((y+150)/300*1023)))
                
                l_idx = min((i // (total // 5)) + 1, 5)
                z_dat = nodes[i].get('z', 0.0)
                s_f = -1.0 if z_geo == 0 else 1.0
                
                diff = abs(math.sin(z_dat * 13.5) - math.sin(z_dat * 13.5 * s_f))
                
                # РАБОТА BtW
                energy_output = fsin.compute_emission_work(diff, l_idx, eb_potential)
                activation = 1 / (1 + math.exp(-energy_output + 5.0))
                
                if activation > threshold:
                    l_stats[l_idx] += 1
                    r, g, b = px_src[px, py]
                    # Рендеринг: Работа (ярко-бирюзовый), Бингл (белый)
                    if l_idx == 3:
                        px_out[px, py] = (int(max(0, min(255, r + energy_output))), 255, 255)
                    else:
                        px_out[px, py] = (int(max(0, min(255, r + activation*20))), 
                                          int(max(0, min(255, g + energy_output*5))), 
                                          int(max(0, min(255, b + energy_output*10))))
                else: px_out[px, py] = px_src[px, py]

            cr.image(res_img, caption="Emission Output (BtW)", use_container_width=True)
            
            # --- ОТЧЕТ GIDEON v1.7.0 ---
            vals = list(l_stats.values())
            sum_v = sum(vals)
            # Торсионный КПД: отношение работы в витках к потенциалу Бингла
            work_done = (sum_v - vals[2])
            efficiency = (work_done / sum_v * 100) if sum_v > 0 else 0
            
            st.code(f"""[ОТЧЕТ GIDEON v1.7.0: BINGLE-TO-WORK]
СТАТУС: Эмиссия смысла активна.
РЕЖИМ: BtW (Торсионная работа)

МЕТРИКИ ЭМИССИИ:
- Потенциал Бингла (Eb): {b_tension:.2f}
- Торсионный КПД (η): {efficiency:.1f}%
- Индекс материализации: {work_done / 1000:.2f} (Смысловые Дж)

ЛОКАЛИЗАЦИЯ (L1-L5):
{vals}

ЗАКЛЮЧЕНИЕ:
{"РАБОТА ВЫПОЛНЕНА" if efficiency > 50 else "ЭМИССИЯ ЗАТРУДНЕНА (НИЗКИЙ BtW)"}
""", language="text")
