import streamlit as st
import json
import math
import os
import numpy as np
from PIL import Image

st.set_page_config(page_title="GIDEON | v1.7.1 Forced BtW", layout="wide")
st.title("S-GPU GIDEON v1.7.1: Принудительная Эмиссия")

# --- FSIN v7.1: BtW DRIVE CORE ---
class FSIN_BtW_Drive:
    def __init__(self, gain, tension, emission, drive):
        self.gain = gain
        self.tension = tension
        self.emission = emission
        self.drive = drive # Коэффициент принудительного впрыска

    def compute_work(self, diff, l_idx, eb_potential):
        if l_idx == 3:
            return self.tension * math.exp(diff * 0.1)
        else:
            # BtW Drive: Eb напрямую открывает затворы в витках
            # Работа = (Классический BtW) + (Прямой впрыск потенциала)
            work = eb_potential * math.sin(diff * self.emission)
            injection = eb_potential * self.drive
            return (diff * self.gain) + work + injection

# --- ГЕОМЕТРИЯ (СФИРАЛЬ БАСАРГИНА) ---
def get_xyz(i, total):
    t = (i / total) * 2 - 1
    R = 150
    if abs(t) < 0.15: # Реактор Бингла (S-петля)
        sn = (t + 0.15) / 0.3
        return math.cos(sn * math.pi) * R, math.sin(sn * math.pi * 2) * (R/2), 0
    angle, side = t * math.pi * 6, (-1 if t < 0 else 1)
    return (R * math.cos(angle) + side * R), (side * R * math.sin(angle) if side < 0 else -R * math.sin(angle)), t * 100

# Регенерация VRAM при необходимости
nodes = [{'id': i, 'z': math.sin(i * 0.05)} for i in range(391392)]

# --- ПАНЕЛЬ УПРАВЛЕНИЯ ---
st.sidebar.header("Настройка Реактора v1.7.1")
b_potential = st.sidebar.slider("Bingle Potential (Eb)", 1.0, 100.0, 80.0)
f_drive = st.sidebar.slider("Injection Drive (Впрыск)", 0.0, 1.0, 0.45)
f_emission = st.sidebar.slider("Emission Rate (BtW)", 0.1, 15.0, 5.0)
threshold = st.sidebar.slider("Gate Threshold", 0.1, 0.99, 0.8)

st.subheader("S-GPU: Управление Торсионным Впрыском")
c1, c2 = st.columns(2)
p_a, p_b = c1.text_input("Тезис", "ГАРМОНИЯ"), c2.text_input("Антитезис", "ВЕЧНОСТЬ")

img_file = st.file_uploader("Растр", type=["jpg", "png"])

if img_file:
    cl, cr = st.columns(2)
    img_src = Image.open(img_file).convert('RGB')
    cl.image(img_src, caption="Входной поток", use_container_width=True)
    
    if st.button("Запустить Принудительную Эмиссию"):
        with st.spinner("Впрыск потенциала Бингла в витки..."):
            canv = 1024
            res_img = Image.new('RGB', (canv, canv), (0,0,0))
            px_out, px_src = res_img.load(), img_src.resize((canv, canv)).load()
            
            total = len(nodes)
            l_stats = {i:0 for i in range(1, 6)}
            fsin = FSIN_BtW_Drive(15.0, b_potential, f_emission, f_drive)
            
            eb_val = b_potential * (math.pi / 2)
            
            for i in range(total):
                x, y, z_geo = get_xyz(i, total)
                px, py = max(0, min(1023, int((x+300)/600*1023))), max(0, min(1023, int((y+150)/300*1023)))
                
                l_idx = min((i // (total // 5)) + 1, 5)
                z_dat = nodes[i].get('z', 0.0)
                s_f = -1.0 if z_geo == 0 else 1.0
                
                diff = abs(math.sin(z_dat * 13.5) - math.sin(z_dat * 13.5 * s_f))
                
                # Расчет работы с принудительным впрыском
                work = fsin.compute_work(diff, l_idx, eb_val)
                activation = 1 / (1 + math.exp(-work + 5.0))
                
                if activation > threshold:
                    l_stats[l_idx] += 1
                    r, g, b = px_src[px, py]
                    # Рендеринг: Инъекция (неоновый розовый), Бингл (белый)
                    if l_idx == 3:
                        px_out[px, py] = (255, 255, 255)
                    else:
                        px_out[px, py] = (int(max(0, min(255, r + work*2))), 
                                          int(max(0, min(255, g + activation*50))), 
                                          int(max(0, min(255, b + work*5))))
                else: px_out[px, py] = px_src[px, py]

            cr.image(res_img, caption="Forced BtW Output", use_container_width=True)
            
            # --- ОТЧЕТ v1.7.1 ---
            vals = list(l_stats.values())
            sum_v = sum(vals)
            work_done = (sum_v - vals[2])
            efficiency = (work_done / sum_v * 100) if sum_v > 0 else 0
            
            st.code(f"""[ОТЧЕТ GIDEON v1.7.1: FORCED BtW]
СТАТУС: Принудительный впрыск активен.
РЕЖИМ: BtW Drive (Торсионная инъекция)

МЕТРИКИ:
- Потенциал Бингла (Eb): {b_potential:.2f}
- Торсионный КПД (η): {efficiency:.1f}%
- Индекс материализации: {work_done / 1000:.2f} (Смысловые Дж)

ЛОКАЛИЗАЦИЯ (L1-L5):
{vals}

ЗАКЛЮЧЕНИЕ:
{"ПРОРЫВ ДОСТИГНУТ" if efficiency > 60 else "ТРЕБУЕТСЯ УВЕЛИЧЕНИЕ ВПРЫСКА (DRIVE)"}
""", language="text")
