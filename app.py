import streamlit as st
import json
import math
import os
import numpy as np
from PIL import Image

st.set_page_config(page_title="GIDEON | v1.3.4 Torsion", layout="wide")
st.title("S-GPU GIDEON v1.3.4: Торсионный Прорыв")

# --- КОНСТАНТЫ LOGOS-3 ---
VOCAB = {
    "ПОРЯДОК": (1.0, -1.0, 1),   "ХАОС": (-1.0, 1.0, -1),
    "ЖИЗНЬ": (0.9, -0.9, 1),     "СМЕРТЬ": (-0.9, 0.9, -1),
    "ИСТИНА": (0.8, -0.8, 1),    "ЛОЖЬ": (-0.8, 0.8, -1),
    "ГАРМОНИЯ": (0.0, 0.0, 1),   "ВЕЧНОСТЬ": (0.0, 0.0, -1),
    "БОГ": (0.0, 0.0, 1)
}

# --- FSIN ENGINE v3: TORSION DIFFUSION ---
class FSIN:
    def __init__(self, gain, bias, torsion):
        self.gain = gain
        self.bias = bias
        self.torsion = torsion

    def activate(self, diff, layer_idx):
        # Если слой центральный (L3), добавляем торсионный импульс для пробоя
        boost = self.torsion if layer_idx == 3 else 1.0
        try:
            val = 1 / (1 + math.exp(- (diff * self.gain * boost) + self.bias))
            return val
        except:
            return 1.0

# --- БЛОК ЗАГРУЗКИ (СТАБИЛЬНЫЙ) ---
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
    st.success(f"✅ VRAM активна ({len(nodes)} узлов)")

st.sidebar.success(f"✅ Core-13: {'Active' if core_status == 'OK' else 'Emulated'}")

# --- ГЕОМЕТРИЯ СФИРАЛИ (3D XYZ) ---
def get_sphiral_xyz(i, total):
    t = (i / total) * 2 - 1
    R = 150
    if abs(t) < 0.15: # S-петля (Серединный Предел)
        s_n = (t + 0.15) / 0.3
        return math.cos(s_n * math.pi) * R, math.sin(s_n * math.pi * 2) * (R/2), 0
    angle = t * math.pi * 6
    side = -1 if t < 0 else 1
    x = R * math.cos(angle) + (side * R)
    y = (side * R * math.sin(angle)) if side < 0 else (-R * math.sin(angle))
    return x, y, t * 100

# --- ИНТЕРФЕЙС ---
st.sidebar.header("Параметры Торсиона")
f_gain = st.sidebar.slider("Fractal Gain", 0.1, 25.0, 12.0)
f_bias = st.sidebar.slider("Bias (Смещение)", -5.0, 5.0, 1.5)
f_torsion = st.sidebar.slider("Torsion Pressure (Пробой L3)", 1.0, 10.0, 2.5)
threshold = st.sidebar.slider("Gate Threshold", 0.1, 0.99, 0.6)

st.subheader("S-GPU Реактор: Уровень Абсолюта")
c1, c2 = st.columns(2)
p_a = c1.text_input("Импульс А", "ГАРМОНИЯ")
p_b = c2.text_input("Импульс Б", "ВЕЧНОСТЬ")

img_file = st.file_uploader("Загрузить растр", type=["jpg", "png"])

if img_file:
    col_l, col_r = st.columns(2)
    img_src = Image.open(img_file).convert('RGB')
    col_l.image(img_src, caption="Входной сигнал", use_container_width=True)
    
    if st.button("Инициировать Торсионный Прорыв"):
        with st.spinner("Разворот фазы в точке сингулярности..."):
            canv = 1024
            res_img = Image.new('RGB', (canv, canv), (0,0,0))
            px_out, px_src = res_img.load(), img_src.resize((canv, canv)).load()
            
            total = len(nodes)
            diff_count, l_stats = 0, {i:0 for i in range(1, 6)}
            fsin = FSIN(f_gain, f_bias, f_torsion)
            
            ph_a = 13.5 + sum(ord(c) for c in p_a) * 0.001
            ph_b = 13.5 + sum(ord(c) for c in p_b) * 0.001

            for i in range(total):
                x, y, z_geo = get_sphiral_xyz(i, total)
                px, py = max(0, min(1023, int((x+300)/600*1023))), max(0, min(1023, int((y+150)/300*1023)))
                
                l_idx = min((i // (total // 5)) + 1, 5)
                z_dat = nodes[i].get('z', 0.0)
                
                # S-инверсия: фазовый сдвиг только в петле
                s_factor = -1.0 if z_geo == 0 else 1.0
                
                # Интерференция с учетом антисимметрии
                d = abs(math.sin(z_dat * ph_a) - math.sin(z_dat * ph_b * s_factor))
                activation = fsin.activate(d, l_idx)
                
                if activation > threshold:
                    diff_count += 1
                    l_stats[l_idx] += 1
                    r, g, b = px_src[px, py]
                    # Рендеринг торсионного выброса (бирюзовый/пурпурный)
                    if l_idx == 3: # S-петля
                        px_out[px, py] = (int(max(0, min(255, r + activation*100))), 
                                          int(max(0, min(255, g + activation*180))), b)
                    else: # Витки
                        px_out[px, py] = (int(max(0, min(255, r + activation*50))), 
                                          g, int(max(0, min(255, b + activation*200))))
                else: px_out[px, py] = px_src[px, py]

            col_r.image(res_img, caption="Torsion Wave Output", use_container_width=True)
            
            # --- ОТЧЕТ v1.3.4 ---
            vals = list(l_stats.values())
            avg_act = np.mean(vals)
            di = np.std(vals) / avg_act if avg_act > 0 else 0
            # Эффективность пробоя: отношение активности витков к петле
            breakthrough = (sum(vals) - l_stats[3]) / l_stats[3] * 100 if l_stats[3] > 0 else 0
            
            st.code(f"""[ОТЧЕТ GIDEON v1.3.4: TORSION WAVE]
ОПЕРАЦИЯ: {p_a} + {p_b} | TORSION: {f_torsion}
СТАТУС: Торсионное давление приложено к S-петле.

МЕТРИКИ:
- Общая активация: {diff_count} ({(diff_count/total)*100:.1f}%)
- Di (Индекс девиации): {di:.4f}
- Эффективность пробоя: {breakthrough:.1f}% (Витковая экспансия)

ЛОКАЛИЗАЦИЯ (L1-L5):
{vals}
""", language="text")
