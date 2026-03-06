import streamlit as st
import json
import math
import os
import numpy as np
from PIL import Image

st.set_page_config(page_title="GIDEON | v1.3.5 Diffusion", layout="wide")
st.title("S-GPU GIDEON v1.3.5: Диффузия Сингулярности")

# --- КОНСТАНТЫ LOGOS-3 ---
VOCAB = {
    "ПОРЯДОК": (1.0, -1.0, 1),   "ХАОС": (-1.0, 1.0, -1),
    "ЖИЗНЬ": (0.9, -0.9, 1),     "СМЕРТЬ": (-0.9, 0.9, -1),
    "ИСТИНА": (0.8, -0.8, 1),    "ЛОЖЬ": (-0.8, 0.8, -1),
    "ГАРМОНИЯ": (0.0, 0.0, 1),   "ВЕЧНОСТЬ": (0.0, 0.0, -1),
    "БОГ": (0.0, 0.0, 1)
}

# --- FSIN ENGINE v3.1: DIFFUSION CORE ---
class FSIN:
    def __init__(self, gain, bias, torsion, diffusion):
        self.gain = gain
        self.bias = bias
        self.torsion = torsion
        self.diffusion = diffusion

    def activate(self, diff, layer_idx):
        # Модуляция усиления в зависимости от слоя
        # L3 - эпицентр, L2/L4 - зоны диффузии
        layer_mod = 1.0
        if layer_idx == 3: layer_mod = self.torsion
        if layer_idx in [2, 4]: layer_mod = self.diffusion
        
        try:
            return 1 / (1 + math.exp(- (diff * self.gain * layer_mod) + self.bias))
        except:
            return 1.0

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
st.sidebar.header("Параметры FSIN v3.1")
f_gain = st.sidebar.slider("Fractal Gain", 0.1, 25.0, 15.0)
f_bias = st.sidebar.slider("Bias (Смещение)", -5.0, 5.0, 1.0)
f_torsion = st.sidebar.slider("Torsion (Сжатие L3)", 1.0, 10.0, 3.0)
f_diff = st.sidebar.slider("Diffusion (Пробой L2/L4)", 0.1, 5.0, 1.2)
threshold = st.sidebar.slider("Gate Threshold", 0.1, 0.99, 0.5)

st.subheader("S-GPU Реактор: Тест Диффузии")
c1, c2 = st.columns(2)
p_a, p_b = c1.text_input("Импульс А", "ГАРМОНИЯ"), c2.text_input("Импульс Б", "ВЕЧНОСТЬ")

img_file = st.file_uploader("Загрузить растр", type=["jpg", "png"])

if img_file:
    col_l, col_r = st.columns(2)
    img_src = Image.open(img_file).convert('RGB')
    col_l.image(img_src, caption="Входной сигнал", use_container_width=True)
    
    if st.button("Запустить Диффузионный Резонанс"):
        with st.spinner("Перенос энергии в витки Сфирали..."):
            canv = 1024
            res_img = Image.new('RGB', (canv, canv), (0,0,0))
            px_out, px_src = res_img.load(), img_src.resize((canv, canv)).load()
            
            total = len(nodes)
            diff_count, l_stats = 0, {i:0 for i in range(1, 6)}
            fsin = FSIN(f_gain, f_bias, f_torsion, f_diff)
            
            ph_a, ph_b = 13.5 + len(p_a)*0.1, 13.5 + len(p_b)*0.1

            
            for i in range(total):
                x, y, z_geo = get_sphiral_xyz(i, total)
                px, py = max(0, min(1023, int((x+300)/600*1023))), max(0, min(1023, int((y+150)/300*1023)))
                
                l_idx = min((i // (total // 5)) + 1, 5)
                z_dat = nodes[i].get('z', 0.0)
                s_factor = -1.0 if z_geo == 0 else 1.0
                
                # Интерференция + Активация
                d = abs(math.sin(z_dat * ph_a) - math.sin(z_dat * ph_b * s_factor))
                activation = fsin.activate(d, l_idx)
                
                if activation > threshold:
                    diff_count += 1
                    l_stats[l_idx] += 1
                    r, g, b = px_src[px, py]
                    # Визуализация диффузии: S-петля (золото), витки (фиолет)
                    if l_idx == 3:
                        px_out[px, py] = (int(max(0, min(255, r + activation*150))), 
                                          int(max(0, min(255, g + activation*100))), b)
                    else:
                        px_out[px, py] = (r, int(max(0, min(255, g + activation*60))), 
                                          int(max(0, min(255, b + activation*160))))
                else: px_out[px, py] = px_src[px, py]

            col_r.image(res_img, caption="Diffusion Wave Output", use_container_width=True)
            
            # --- ОТЧЕТ ---
            vals = list(l_stats.values())
            breakthrough = (sum(vals) - l_stats[3]) / l_stats[3] * 100 if l_stats[3] > 0 else 0
            
            st.code(f"""[ОТЧЕТ GIDEON v1.3.5: DIFFUSION ACTIVE]
ОПЕРАЦИЯ: {p_a} + {p_b} | DIFFUSION: {f_diff}
СТАТУС: Пробой сингулярности через диффузию фаз.

МЕТРИКИ:
- Общая активация: {diff_count} ({(diff_count/total)*100:.1f}%)
- Эффективность пробоя: {breakthrough:.1f}%
- Состояние: {"ГРАДИЕНТНОЕ" if breakthrough > 10 else "СИНГУЛЯРНОЕ"}

ЛОКАЛИЗАЦИЯ (L1-L5):
{vals}
""", language="text")
