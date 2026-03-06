import streamlit as st
import json
import math
import os
import numpy as np
from PIL import Image

st.set_page_config(page_title="GIDEON | v1.4.0 Tunneling", layout="wide")
st.title("S-GPU GIDEON v1.4.0: Квантовое Туннелирование")

# --- КОНСТАНТЫ LOGOS-3 ---
VOCAB = {
    "ПОРЯДОК": (1.0, -1.0, 1),   "ХАОС": (-1.0, 1.0, -1),
    "ЖИЗНЬ": (0.9, -0.9, 1),     "СМЕРТЬ": (-0.9, 0.9, -1),
    "ИСТИНА": (0.8, -0.8, 1),    "ЛОЖЬ": (-0.8, 0.8, -1),
    "ГАРМОНИЯ": (0.0, 0.0, 1),   "ВЕЧНОСТЬ": (0.0, 0.0, -1),
    "БОГ": (0.0, 0.0, 1)
}

# --- FSIN ENGINE v4: TUNNELING CORE ---
class FSIN:
    def __init__(self, gain, bias, torsion, diffusion, tunnel):
        self.gain = gain
        self.bias = bias
        self.torsion = torsion
        self.diffusion = diffusion
        self.tunnel = tunnel

    def activate(self, diff, l_idx, l3_saturated):
        # Если центр перегружен, включаем туннелирование для периферии
        mod = 1.0
        if l_idx == 3: mod = self.torsion
        elif l_idx in [2, 4]: mod = self.diffusion + (self.tunnel if l3_saturated else 0)
        elif l_idx in [1, 5]: mod = 1.0 + (self.tunnel * 0.5 if l3_saturated else 0)
        
        try:
            return 1 / (1 + math.exp(- (diff * self.gain * mod) + self.bias))
        except: return 1.0

# --- СТАБИЛЬНАЯ ЗАГРУЗКА ---
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

st.sidebar.success(f"✅ VRAM: {vram_status}")

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
st.sidebar.header("Параметры FSIN v4.0")
f_gain = st.sidebar.slider("Fractal Gain", 0.1, 25.0, 15.0)
f_bias = st.sidebar.slider("Bias", -5.0, 5.0, 1.0)
f_torsion = st.sidebar.slider("Torsion (L3 Pressure)", 1.0, 10.0, 3.0)
f_diff = st.sidebar.slider("Diffusion", 0.1, 5.0, 1.2)
f_tunnel = st.sidebar.slider("Quantum Tunneling", 0.0, 10.0, 4.0)
threshold = st.sidebar.slider("Gate Threshold", 0.1, 0.99, 0.5)

st.subheader("S-GPU Реактор: Пробой Сингулярности")
c1, c2 = st.columns(2)
p_a, p_b = c1.text_input("Импульс А", "ГАРМОНИЯ"), c2.text_input("Импульс Б", "ВЕЧНОСТЬ")

img_file = st.file_uploader("Загрузить растр", type=["jpg", "png"])

if img_file:
    col_l, col_r = st.columns(2)
    img_src = Image.open(img_file).convert('RGB')
    col_l.image(img_src, caption="Входной сигнал (Preview)", use_container_width=True)
    
    if st.button("Инициировать Квантовый Прорыв"):
        with st.spinner("Туннелирование фазы..."):
            canv = 1024
            res_img = Image.new('RGB', (canv, canv), (0,0,0))
            px_out, px_src = res_img.load(), img_src.resize((canv, canv)).load()
            
            total = len(nodes)
            l_stats = {i:0 for i in range(1, 6)}
            fsin = FSIN(f_gain, f_bias, f_torsion, f_diff, f_tunnel)
            
            # Предварительный расчет насыщенности L3 (базируется на прошлом отчете)
            # Если Kc высокий, считаем L3 насыщенным по умолчанию
            l3_saturated = True 
            
            ph_a, ph_b = 13.5 + len(p_a)*0.1, 13.5 + len(p_b)*0.1

            for i in range(total):
                x, y, z_geo = get_sphiral_xyz(i, total)
                px, py = max(0, min(1023, int((x+300)/600*1023))), max(0, min(1023, int((y+150)/300*1023)))
                
                l_idx = min((i // (total // 5)) + 1, 5)
                z_dat = nodes[i].get('z', 0.0)
                s_factor = -1.0 if z_geo == 0 else 1.0
                
                # Интерференция
                d = abs(math.sin(z_dat * ph_a) - math.sin(z_dat * ph_b * s_factor))
                activation = fsin.activate(d, l_idx, l3_saturated)
                
                if activation > threshold:
                    l_stats[l_idx] += 1
                    r, g, b = px_src[px, py]
                    # Визуализация: Пробитые слои светятся бирюзой
                    if l_idx == 3:
                        px_out[px, py] = (int(max(0, min(255, r + activation*150))), 
                                          int(max(0, min(255, g + activation*100))), b)
                    else:
                        px_out[px, py] = (r, int(max(0, min(255, g + activation*120))), 
                                          int(max(0, min(255, b + activation*200))))
                else: px_out[px, py] = px_src[px, py]

            col_r.image(res_img, caption="Tunneling Breakthrough Output", use_container_width=True)
            
            # --- ОТЧЕТ v1.4.0 ---
            vals = list(l_stats.values())
            total_act = sum(vals)
            breakthrough = (total_act - l_stats[3]) / l_stats[3] * 100 if l_stats[3] > 0 else 0
            
            st.code(f"""[ОТЧЕТ GIDEON v1.4.0: QUANTUM TUNNELING]
ОПЕРАЦИЯ: {p_a} + {p_b} | TUNNEL: {f_tunnel}
СТАТУС: Активное туннелирование фазы из L3 в витки.

МЕТРИКИ:
- Общая активация: {total_act} ({(total_act/total)*100:.1f}%)
- Эффективность пробоя: {breakthrough:.1f}%
- Режим: {"СУПЕР-ДИФФУЗИЯ" if breakthrough > 50 else "СИНГУЛЯРНЫЙ ЗАТОР"}

ЛОКАЛИЗАЦИЯ (L1-L5):
{vals}
""", language="text")
