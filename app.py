import streamlit as st
import json
import math
import os
import numpy as np
from PIL import Image

st.set_page_config(page_title="GIDEON | v1.4.1 Discharge", layout="wide")
st.title("S-GPU GIDEON v1.4.1: Торсионный Разряд")

# --- КОНСТАНТЫ LOGOS-3 (СЕМАНТИЧЕСКИЙ ГЕНОМ) ---
VOCAB = {
    "ПОРЯДОК": (1.0, -1.0, 1),   "ХАОС": (-1.0, 1.0, -1),
    "ЖИЗНЬ": (0.9, -0.9, 1),     "СМЕРТЬ": (-0.9, 0.9, -1),
    "ИСТИНА": (0.8, -0.8, 1),    "ЛОЖЬ": (-0.8, 0.8, -1),
    "ГАРМОНИЯ": (0.0, 0.0, 1),   "ВЕЧНОСТЬ": (0.0, 0.0, -1),
    "БОГ": (0.0, 0.0, 1)
}

# --- FSIN ENGINE v4.1: DISCHARGE CORE ---
class FSIN:
    def __init__(self, gain, bias, torsion, tunnel):
        self.gain = gain
        self.bias = bias
        self.torsion = torsion # Давление из L3 в L2/L4
        self.tunnel = tunnel   # Давление из L3 в L1/L5

    def activate(self, diff, l_idx, l3_ratio):
        # Базовая активация на основе интерференции
        logit = (diff * self.gain) + self.bias
        
        # Эффект Торсионного Разряда (Spillover)
        # Если L3 (S-петля) насыщена, она "пробивает" соседние слои
        if l_idx in [2, 4]:
            logit += self.torsion * l3_ratio
        elif l_idx in [1, 5]:
            logit += self.tunnel * l3_ratio
            
        try:
            return 1 / (1 + math.exp(-logit))
        except: return 1.0

# --- СТАБИЛЬНЫЙ БЛОК ЗАГРУЗКИ (ИНДИКАТОРЫ) ---
@st.cache_data
def load_vram_resource(filename):
    if not os.path.exists(filename): return None, "MISSING"
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            d = json.load(f)
            return (d.get('nodes', d) if isinstance(d, dict) else d), "OK"
    except: return None, "CORRUPTED"

nodes, vram_status = load_vram_resource('matrix.json')
core_dipoles, core_status = load_vram_resource('Core-13.json')

if vram_status != "OK":
    nodes = [{'id': i, 'z': math.sin(i * 0.05) * math.cos(i * 0.02)} for i in range(391392)]
    st.warning(f"⚠️ VRAM регенерирована (status: {vram_status})")
else:
    st.success(f"✅ VRAM активна: {len(nodes)} узлов в памяти.")

st.sidebar.success(f"✅ Core-13: {'Active' if core_status == 'OK' else 'Emulated'}")

# --- ГЕОМЕТРИЯ СФИРАЛИ БАСАРГИНА (3D XYZ) ---
def get_sphiral_xyz(i, total):
    t = (i / total) * 2 - 1
    R = 150
    if abs(t) < 0.15: # S-образная петля (Серединный Предел)
        sn = (t + 0.15) / 0.3
        return math.cos(sn * math.pi) * R, math.sin(sn * math.pi * 2) * (R/2), 0
    # Зеркально антисимметричные витки
    angle, side = t * math.pi * 6, (-1 if t < 0 else 1)
    x = R * math.cos(angle) + (side * R)
    y = (side * R * math.sin(angle)) if side < 0 else (-R * math.sin(angle))
    return x, y, t * 100

# --- ИНТЕРФЕЙС УПРАВЛЕНИЯ ---
st.sidebar.header("Параметры FSIN v4.1")
f_gain = st.sidebar.slider("Fractal Gain", 0.1, 25.0, 15.0)
f_bias = st.sidebar.slider("Bias (Смещение)", -10.0, 10.0, 0.0)
f_torsion = st.sidebar.slider("Torsion Pressure (L3->L2/4)", 0.0, 30.0, 15.0)
f_tunnel = st.sidebar.slider("Tunnel Discharge (L3->L1/5)", 0.0, 20.0, 8.0)
threshold = st.sidebar.slider("Gate Threshold", 0.1, 0.99, 0.5)

st.subheader("S-GPU Реактор: Управление Разрядом")
c1, c2 = st.columns(2)
p_a = c1.text_input("Импульс А", "ГАРМОНИЯ")
p_b = c2.text_input("Импульс Б", "ВЕЧНОСТЬ")

img_file = st.file_uploader("Загрузить растр", type=["jpg", "png"])

if img_file:
    col_l, col_r = st.columns(2)
    img_src = Image.open(img_file).convert('RGB')
    
    # ПРЕВЬЮ (ВСЕГДА ВИДИМО)
    col_l.image(img_src, caption="Входной сигнал (Preview)", use_container_width=True)
    
    if st.button("Запустить Торсионный Разряд"):
        with st.spinner("Прорыв сингулярности в S-петле..."):
            canv = 1024
            res_img = Image.new('RGB', (canv, canv), (0,0,0))
            px_out, px_src = res_img.load(), img_src.resize((canv, canv)).load()
            
            total = len(nodes)
            l_stats = {i:0 for i in range(1, 6)}
            fsin = FSIN(f_gain, f_bias, f_torsion, f_tunnel)
            
            ph_a = 13.5 + len(p_a) * 0.1
            ph_b = 13.5 + len(p_b) * 0.1
            nodes_per_layer = total // 5
            
            # --- ФАЗА 1: Расчет насыщения L3 (Сингулярность) ---
            l3_active = 0
            for i in range(nodes_per_layer * 2, nodes_per_layer * 3):
                z_dat = nodes[i].get('z', 0.0)
                # В S-петле фаза всегда инвертирована
                d = abs(math.sin(z_dat * ph_a) - math.sin(z_dat * ph_b * -1.0))
                if (1 / (1 + math.exp(- (d * f_gain) + f_bias))) > threshold:
                    l3_active += 1
            
            l3_ratio = l3_active / nodes_per_layer if nodes_per_layer > 0 else 0
            
            # --- ФАЗА 2: Рендеринг с учетом Торсионного Разряда ---
            for i in range(total):
                x, y, z_geo = get_sphiral_xyz(i, total)
                px = max(0, min(1023, int((x + 300) / 600 * 1023)))
                py = max(0, min(1023, int((y + 150) / 300 * 1023)))
                
                l_idx = min((i // nodes_per_layer) + 1, 5)
                z_dat = nodes[i].get('z', 0.0)
                s_factor = -1.0 if z_geo == 0 else 1.0
                
                d = abs(math.sin(z_dat * ph_a) - math.sin(z_dat * ph_b * s_factor))
                activation = fsin.activate(d, l_idx, l3_ratio)
                
                if activation > threshold:
                    l_stats[l_idx] += 1
                    r, g, b = px_src[px, py]
                    # Спектральная индикация разряда
                    if l_idx == 3: # S-петля (Золото/Оранж)
                        px_out[px, py] = (int(max(0, min(255, r + activation*160))), 
                                          int(max(0, min(255, g + activation*110))), b)
                    elif l_idx in [2, 4]: # Разряд в витки (Бирюза)
                        px_out[px, py] = (r, int(max(0, min(255, g + activation*150))), 
                                          int(max(0, min(255, b + activation*150))))
                    else: # Дальняя экспансия (Пурпур)
                        px_out[px, py] = (int(max(0, min(255, r + activation*100))), 
                                          g, int(max(0, min(255, b + activation*180))))
                else: 
                    px_out[px, py] = px_src[px, py]

            col_r.image(res_img, caption="Torsion Discharge Projection", use_container_width=True)
            
            # --- ОТЧЕТ GIDEON v1.4.1 ---
            vals = list(l_stats.values())
            total_act = sum(vals)
            breakthrough = ((total_act - l_stats[3]) / total_act * 100) if total_act > 0 else 0
            
            st.code(f"""[ОТЧЕТ GIDEON v1.4.1: TORSION DISCHARGE]
ОПЕРАЦИЯ: {p_a} + {p_b} | НАСЫЩЕНИЕ S-ПЕТЛИ: {l3_ratio*100:.1f}%
СТАТУС: Прорыв сингулярности через торсионный разряд.

МЕТРИКИ:
- Общая активация: {total_act} ({(total_act/total)*100:.1f}%)
- Эффективность пробоя: {breakthrough:.1f}% (Экспансия в витки)
- Режим: {"АКТИВНЫЙ РАЗРЯД" if breakthrough > 1.0 else "СИНГУЛЯРНЫЙ ЗАТОР"}

ЛОКАЛИЗАЦИЯ (L1-L5):
{vals}
""", language="text")
