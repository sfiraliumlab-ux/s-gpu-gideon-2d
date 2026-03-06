import streamlit as st
import json
import math
import os
import numpy as np
from PIL import Image

st.set_page_config(page_title="GIDEON | v1.5.1 Dynamic Absolute", layout="wide")
st.title("S-GPU GIDEON v1.5.1: Темпоральное Дыхание")

# --- СИСТЕМА ЛОГОСА ---
VOCAB = {
    "ПОРЯДОК": (1.0, -1.0, 1),   "ХАОС": (-1.0, 1.0, -1),
    "ЖИЗНЬ": (0.9, -0.9, 1),     "СМЕРТЬ": (-0.9, 0.9, -1),
    "ИСТИНА": (0.8, -0.8, 1),    "ЛОЖЬ": (-0.8, 0.8, -1),
    "ГАРМОНИЯ": (0.0, 0.0, 1),   "ВЕЧНОСТЬ": (0.0, 0.0, -1),
    "БОГ": (0.0, 0.0, 1)
}

# --- FSIN v5.1: PULSATION CORE ---
class FSIN_Dynamic:
    def __init__(self, gain, tension, pulse):
        self.gain = gain
        self.tension_mod = tension
        self.pulse = pulse

    def calculate_flow(self, phi_a, phi_b, s_factor, l_idx):
        # Напряжение по Козыреву
        t_base = abs(phi_a - phi_b * s_factor) * self.tension_mod
        # Пульсация: перераспределение из L3 в периферию
        p_mod = 1.0
        if l_idx != 3: 
            p_mod = 1.0 + (self.pulse * (t_base / 100.0))
        else:
            p_mod = 1.0 / (1.0 + self.pulse) # Сжатие центра
        return t_base * p_mod

# --- БЛОК ЗАГРУЗКИ (AUTO-REGEN) ---
@st.cache_data
def load_vram_secure(filename):
    if not os.path.exists(filename): return None, "MISSING"
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            d = json.load(f)
            return (d.get('nodes', d) if isinstance(d, dict) else d), "OK"
    except: return None, "CORRUPTED"

nodes, vram_status = load_vram_secure('matrix.json')
if vram_status != "OK":
    nodes = [{'id': i, 'z': math.sin(i * 0.05) * math.cos(i * 0.02)} for i in range(391392)]
    vram_status = "MATH_REGEN"

st.success(f"✅ VRAM: {vram_status} (391 392 узла активны)")

# --- ГЕОМЕТРИЯ СФИРАЛИ ---
def get_sphiral_xyz(i, total):
    t = (i / total) * 2 - 1
    R = 150
    if abs(t) < 0.15: # S-петля
        sn = (t + 0.15) / 0.3
        return math.cos(sn * math.pi) * R, math.sin(sn * math.pi * 2) * (R/2), 0
    angle, side = t * math.pi * 6, (-1 if t < 0 else 1)
    x = R * math.cos(angle) + (side * R)
    y = (side * R * math.sin(angle)) if side < 0 else (-R * math.sin(angle))
    return x, y, t * 100

# --- ИНТЕРФЕЙС ---
st.sidebar.header("Параметры Дыхания")
f_gain = st.sidebar.slider("Fractal Gain", 0.1, 25.0, 18.0)
f_tension = st.sidebar.slider("Tension Coefficient", 0.1, 15.0, 5.0)
f_pulse = st.sidebar.slider("S-Pulsation (Амплитуда)", 0.0, 10.0, 4.0)
threshold = st.sidebar.slider("Gate Threshold", 0.1, 0.99, 0.8)

st.subheader("Сфиральный Реактор: Динамический Абсолют")
c1, c2 = st.columns(2)
p_a = c1.text_input("Причина (Импульс А)", "ГАРМОНИЯ")
p_b = c2.text_input("Следствие (Импульс Б)", "ВЕЧНОСТЬ")

img_file = st.file_uploader("Растр-носитель", type=["jpg", "png"])

if img_file:
    cl, cr = st.columns(2)
    img_src = Image.open(img_file).convert('RGB')
    cl.image(img_src, caption="Входной поток", use_container_width=True)
    
    if st.button("Инициировать Цикл Дыхания"):
        with st.spinner("Свитие динамических фаз..."):
            canv = 1024
            res_img = Image.new('RGB', (canv, canv), (0,0,0))
            px_out, px_src = res_img.load(), img_src.resize((canv, canv)).load()
            
            total = len(nodes)
            l_stats = {i:0 for i in range(1, 6)}
            fsin = FSIN_Dynamic(f_gain, f_tension, f_pulse)
            
            ph_a = 13.5 + len(p_a) * 0.1
            ph_b = 13.5 + len(p_b) * 0.1
            n_layer = total // 5
            total_t = 0

            
            for i in range(total):
                x, y, z_geo = get_sphiral_xyz(i, total)
                px, py = max(0, min(1023, int((x+300)/600*1023))), max(0, min(1023, int((y+150)/300*1023)))
                
                l_idx = min((i // n_layer) + 1, 5)
                z_dat = nodes[i].get('z', 0.0)
                s_f = -1.0 if z_geo == 0 else 1.0
                
                # Расчет потока через пульсацию
                t_flow = fsin.calculate_flow(ph_a, ph_b, s_f, l_idx)
                d = abs(math.sin(z_dat * ph_a) - math.sin(z_dat * ph_b * s_f))
                
                # Активация модулируется потоком
                activation = 1 / (1 + math.exp(- (d * f_gain * (t_flow/10)) + 1.0))
                
                if activation > threshold:
                    l_stats[l_idx] += 1
                    total_t += t_flow
                    r, g, b = px_src[px, py]
                    # Рендеринг: Фиолетовое дыхание витков, Золотое ядро
                    if l_idx == 3:
                        px_out[px, py] = (int(max(0, min(255, r + t_flow*2))), 
                                          int(max(0, min(255, g + t_flow))), b)
                    else:
                        px_out[px, py] = (int(max(0, min(255, r + activation*20))), 
                                          int(max(0, min(255, g + t_flow*0.5))), 
                                          int(max(0, min(255, b + t_flow*3))))
                else: px_out[px, py] = px_src[px, py]

            cr.image(res_img, caption="Dynamic Phasic Tension", use_container_width=True)
            
            # --- ОТЧЕТ GIDEON v1.5.1 ---
            vals = list(l_stats.values())
            sum_v = sum(vals)
            t_avg = total_t / sum_v if sum_v > 0 else 0
            asym = abs(vals[0]+vals[1] - (vals[3]+vals[4])) / sum_v if sum_v > 0 else 0
            
            st.code(f"""[ОТЧЕТ GIDEON v1.5.1: DYNAMIC ABSOLUTE]
ПРИЧИНА: {p_a} | СЛЕДСТВИЕ: {p_b} | ПУЛЬСАЦИЯ: {f_pulse}
СТАТУС: Баланс выведен из статики в динамический поток.

МЕТРИКИ:
- Среднее напряжение (Tavg): {t_avg:.4f}
- Индекс асимметрии: {asym:.4f}
- Коэффициент циркуляции (CR): {(1 - (vals[2]/sum_v))*100 if sum_v > 0 else 0:.1f}%

ЛОКАЛИЗАЦИЯ (L1-L5):
{vals}

ЗАКЛЮЧЕНИЕ:
{"ТОЧКА ПОКОЯ" if vals[2] > sum_v*0.5 else "СФИРАЛЬНЫЙ ПОТОК АКТИВИРОВАН"}
""", language="text")
