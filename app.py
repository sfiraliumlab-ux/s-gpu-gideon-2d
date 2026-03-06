import streamlit as st
import json
import math
import os
import numpy as np
from PIL import Image

st.set_page_config(page_title="GIDEON | v1.5.0 Phasic Tension", layout="wide")
st.title("S-GPU GIDEON v1.5.0: Активное Время (Phasic Tension)")

# --- LOGOS-3 VOCAB ---
VOCAB = {
    "ПОРЯДОК": (1.0, -1.0, 1),   "ХАОС": (-1.0, 1.0, -1),
    "ЖИЗНЬ": (0.9, -0.9, 1),     "СМЕРТЬ": (-0.9, 0.9, -1),
    "ИСТИНА": (0.8, -0.8, 1),    "ЛОЖЬ": (-0.8, 0.8, -1),
    "ГАРМОНИЯ": (0.0, 0.0, 1),   "ВЕЧНОСТЬ": (0.0, 0.0, -1),
    "БОГ": (0.0, 0.0, 1)
}

# --- FSIN v5: TEMPORAL CORE (KOZYREV LOGIC) ---
class FSIN_Temporal:
    def __init__(self, gain, tension):
        self.gain = gain
        self.tension_mod = tension

    def calculate_tension(self, phi_cause, phi_effect, s_factor):
        """Расчет плотности активного времени (по Козыреву)"""
        # Delta t = (phi_cause - phi_effect) / V
        # В Сфирали V модулируется S-фактором
        return abs(phi_cause - phi_effect * s_factor) * self.tension_mod

# --- LOAD & REGEN BLOCK ---
@st.cache_data
def load_resources(filename):
    if not os.path.exists(filename): return None, "MISSING"
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            d = json.load(f)
            return (d.get('nodes', d) if isinstance(d, dict) else d), "OK"
    except: return None, "CORRUPTED"

nodes, vram_status = load_resources('matrix.json')
core, core_status = load_resources('Core-13.json')

if vram_status != "OK":
    nodes = [{'id': i, 'z': math.sin(i * 0.05) * math.cos(i * 0.02)} for i in range(391392)]
    st.warning(f"⚠️ VRAM регенерирована (status: {vram_status})")
else:
    st.success(f"✅ VRAM активна: {len(nodes)} узлов.")

st.sidebar.success(f"✅ Core-13: {'Active' if core_status == 'OK' else 'Emulated'}")

# --- SFIRAL GEOMETRY (3D) ---
def get_sphiral_xyz(i, total):
    t = (i / total) * 2 - 1
    R = 150
    if abs(t) < 0.15: # S-loop (Singularity)
        sn = (t + 0.15) / 0.3
        return math.cos(sn * math.pi) * R, math.sin(sn * math.pi * 2) * (R/2), 0
    angle, side = t * math.pi * 6, (-1 if t < 0 else 1)
    x = R * math.cos(angle) + (side * R)
    y = (side * R * math.sin(angle)) if side < 0 else (-R * math.sin(angle))
    return x, y, t * 100

# --- UI ---
st.sidebar.header("Параметры Активного Времени")
f_gain = st.sidebar.slider("Fractal Gain", 0.1, 20.0, 15.0)
f_tension = st.sidebar.slider("Tension Coefficient", 0.1, 10.0, 4.5)
threshold = st.sidebar.slider("Gate Threshold", 0.1, 0.99, 0.75)

st.subheader("Сфиральный Интерферометр")
c1, c2 = st.columns(2)
p_a = c1.text_input("Причина (Импульс А)", "ГАРМОНИЯ")
p_b = c2.text_input("Следствие (Импульс Б)", "ВЕЧНОСТЬ")

img_file = st.file_uploader("Растр-носитель", type=["jpg", "png"])

if img_file:
    cl, cr = st.columns(2)
    img_src = Image.open(img_file).convert('RGB')
    cl.image(img_src, caption="Входной поток", use_container_width=True)
    
    if st.button("Запустить Фазовый Мониторинг"):
        with st.spinner("Измерение плотности времени..."):
            canv = 1024
            res_img = Image.new('RGB', (canv, canv), (0,0,0))
            px_out, px_src = res_img.load(), img_src.resize((canv, canv)).load()
            
            total = len(nodes)
            l_stats = {i:0 for i in range(1, 6)}
            fsin = FSIN_Temporal(f_gain, f_tension)
            
            # Векторы фаз
            ph_a = 13.5 + len(p_a) * 0.1
            ph_b = 13.5 + len(p_b) * 0.1
            nodes_per_layer = total // 5
            
            total_tension = 0
            
            for i in range(total):
                x, y, z_geo = get_sphiral_xyz(i, total)
                px, py = max(0, min(1023, int((x+300)/600*1023))), max(0, min(1023, int((y+150)/300*1023)))
                
                l_idx = min((i // nodes_per_layer) + 1, 5)
                z_dat = nodes[i].get('z', 0.0)
                s_factor = -1.0 if z_geo == 0 else 1.0
                
                # Козыревский расчет напряжения
                tension = fsin.calculate_tension(ph_a, ph_b, s_factor)
                # Резонанс
                d = abs(math.sin(z_dat * ph_a) - math.sin(z_dat * ph_b * s_factor))
                activation = 1 / (1 + math.exp(- (d * f_gain * tension) + 1.0))
                
                if activation > threshold:
                    l_stats[l_idx] += 1
                    total_tension += tension
                    r, g, b = px_src[px, py]
                    # Рендеринг Активного Времени (Спектр от синего к красному)
                    px_out[px, py] = (int(max(0, min(255, r + tension*10))), 
                                      int(max(0, min(255, g + activation*50))), 
                                      int(max(0, min(255, b + tension*20))))
                else: px_out[px, py] = px_src[px, py]

            cr.image(res_img, caption="Temporal Tension Map", use_container_width=True)
            
            # --- ОТЧЕТ GIDEON v1.5.0 ---
            vals = list(l_stats.values())
            avg_tension = total_tension / sum(vals) if sum(vals) > 0 else 0
            # Коэффициент асимметрии (Левый виток vs Правый)
            asymmetry = abs(vals[0] + vals[1] - (vals[3] + vals[4])) / sum(vals) if sum(vals) > 0 else 0
            
            st.code(f"""[ОТЧЕТ GIDEON v1.5.0: PHASIC TENSION]
ПРИЧИНА: {p_a} | СЛЕДСТВИЕ: {p_b}
СТАТУС: Режим "Активное Время" включен.

МЕТРИКИ ТЕМПОРАЛЬНОЙ СТРУКТУРЫ:
- Среднее напряжение (Tavg): {avg_tension:.4f}
- Коэффициент асимметрии: {asymmetry:.4f} (Антисимметрия Басаргина)
- Индекс когерентности: {100 - (asymmetry*100):.1f}%

ЛОКАЛИЗАЦИЯ (L1-L5):
{vals}

ЗАКЛЮЧЕНИЕ:
{"БАЛАНС ДОСТИГНУТ" if asymmetry < 0.05 else "ФАЗОВЫЙ СДВИГ ОБНАРУЖЕН"}
""", language="text")
