import streamlit as st
import json
import math
import os
import numpy as np
from PIL import Image

st.set_page_config(page_title="GIDEON | v1.5.2 Phase Spillover", layout="wide")
st.title("S-GPU GIDEON v1.5.2: Фазовый Перехлест")

# --- СЕМАНТИЧЕСКИЙ ГЕНОМ ---
VOCAB = {
    "ПОРЯДОК": (1.0, -1.0, 1),   "ХАОС": (-1.0, 1.0, -1),
    "ЖИЗНЬ": (0.9, -0.9, 1),     "СМЕРТЬ": (-0.9, 0.9, -1),
    "ИСТИНА": (0.8, -0.8, 1),    "ЛОЖЬ": (-0.8, 0.8, -1),
    "ГАРМОНИЯ": (0.0, 0.0, 1),   "ВЕЧНОСТЬ": (0.0, 0.0, -1),
    "БОГ": (0.0, 0.0, 1)
}

# --- FSIN v5.2: SPILLOVER CORE ---
class FSIN_Spillover:
    def __init__(self, gain, tension, spill):
        self.gain = gain
        self.tension_mod = tension
        self.spill = spill

    def activate(self, diff, l_idx, l3_density):
        # Базовая активация
        t_base = diff * self.gain * (self.tension_mod / 5.0)
        
        # Эффект перехлеста: L3 отдает избыток в L2/L4
        boost = 1.0
        if l_idx in [2, 4] and l3_density > 0.1:
            boost += self.spill * l3_density * 10.0
            
        try:
            return 1 / (1 + math.exp(-t_base * boost + 2.0))
        except: return 1.0

# --- БЛОК ЗАГРУЗКИ ---
@st.cache_data
def load_vram_resource(filename):
    if not os.path.exists(filename): return None, "MISSING"
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            d = json.load(f)
            return (d.get('nodes', d) if isinstance(d, dict) else d), "OK"
    except: return None, "CORRUPTED"

nodes, vram_status = load_vram_resource('matrix.json')
if vram_status != "OK":
    nodes = [{'id': i, 'z': math.sin(i * 0.05) * math.cos(i * 0.02)} for i in range(391392)]
    vram_status = "MATH_REGEN"

st.sidebar.success(f"✅ VRAM Status: {vram_status}")

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

# --- ИНТЕРФЕЙС УПРАВЛЕНИЯ ---
st.sidebar.header("Параметры Перехлеста")
f_gain = st.sidebar.slider("Fractal Gain", 0.1, 25.0, 15.0)
f_tension = st.sidebar.slider("Tension Mod", 0.1, 15.0, 6.0)
f_spill = st.sidebar.slider("Spillover (Сброс L3)", 0.0, 20.0, 10.0)
threshold = st.sidebar.slider("Gate Threshold", 0.1, 0.99, 0.7)

st.subheader("Сфиральный Интерферометр: Режим Пробоя")
c1, c2 = st.columns(2)
p_a = c1.text_input("Импульс А (Причина)", "ГАРМОНИЯ")
p_b = c2.text_input("Импульс Б (Следствие)", "ВЕЧНОСТЬ")

img_file = st.file_uploader("Растр-носитель", type=["jpg", "png"])

if img_file:
    cl, cr = st.columns(2)
    img_src = Image.open(img_file).convert('RGB')
    cl.image(img_src, caption="Входной поток", use_container_width=True)
    
    if st.button("Инициировать Каскадный Пробой"):
        with st.spinner("Сброс плотности из S-петли..."):
            canv = 1024
            res_img = Image.new('RGB', (canv, canv), (0,0,0))
            px_out, px_src = res_img.load(), img_src.resize((canv, canv)).load()
            
            total = len(nodes)
            l_stats = {i:0 for i in range(1, 6)}
            fsin = FSIN_Spillover(f_gain, f_tension, f_spill)
            
            ph_a, ph_b = 13.5 + len(p_a)*0.1, 13.5 + len(p_b)*0.1
            n_layer = total // 5
            
            # Предварительный замер плотности L3
            l3_raw_count = 58000 # Базируется на стабильном заторе
            l3_density = l3_raw_count / n_layer

            for i in range(total):
                x, y, z_geo = get_sphiral_xyz(i, total)
                px = max(0, min(1023, int((x+300)/600*1023)))
                py = max(0, min(1023, int((y+150)/300*1023)))
                
                l_idx = min((i // n_layer) + 1, 5)
                z_dat = nodes[i].get('z', 0.0)
                s_f = -1.0 if z_geo == 0 else 1.0
                
                d = abs(math.sin(z_dat * ph_a) - math.sin(z_dat * ph_b * s_f))
                activation = fsin.activate(d, l_idx, l3_density)
                
                if activation > threshold:
                    l_stats[l_idx] += 1
                    r, g, b = px_src[px, py]
                    # Рендеринг: Прорыв L2/L4 подсвечивается индиго
                    if l_idx in [2, 4]:
                        px_out[px, py] = (int(max(0, min(255, r + activation*80))), 
                                          int(max(0, min(255, g + activation*150))), 
                                          int(max(0, min(255, b + activation*200))))
                    else:
                        px_out[px, py] = (int(max(0, min(255, r + activation*30))), 
                                          int(max(0, min(255, g + activation*40))), 
                                          int(max(0, min(255, b + activation*60))))
                else: px_out[px, py] = px_src[px, py]

            cr.image(res_img, caption="Phase Spillover Projection", use_container_width=True)
            
            # --- ОТЧЕТ GIDEON v1.5.2 ---
            vals = list(l_stats.values())
            sum_v = sum(vals)
            cr_val = ((sum_v - vals[2]) / sum_v * 100) if sum_v > 0 else 0
            asym = abs(vals[0]+vals[1] - (vals[3]+vals[4])) / sum_v if sum_v > 0 else 0
            
            st.code(f"""[ОТЧЕТ GIDEON v1.5.2: PHASE SPILLOVER]
ОПЕРАЦИЯ: {p_a} + {p_b} | SPILLOVER: {f_spill}
СТАТУС: Активирован режим принудительной автоэмиссии из L3.

МЕТРИКИ:
- Общая активация: {sum_v} узлов
- Коэффициент циркуляции (CR): {cr_val:.1f}%
- Индекс асимметрии: {asym:.4f}

ЛОКАЛИЗАЦИЯ (L1-L5):
{vals}

ЗАКЛЮЧЕНИЕ:
{"КРИТИЧЕСКИЙ ПРОБОЙ" if cr_val > 30 else "ЗАТОР СОХРАНЯЕТСЯ"}
""", language="text")
