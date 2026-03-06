import streamlit as st
import json
import math
import os
import numpy as np
from PIL import Image

st.set_page_config(page_title="GIDEON | v1.3.3 Stable", layout="wide")
st.title("S-GPU GIDEON v1.3.3: Бесшовный Резонанс")

# --- ГЕНЕРАТОР ЭТАЛОННОЙ VRAM (391 392 узла) ---
def generate_vram_auto():
    """Математическая регенерация матрицы при повреждении файла"""
    return [{'id': i, 'z': math.sin(i * 0.05) * math.cos(i * 0.02)} for i in range(391392)]

# --- БЛОК ЗАГРУЗКИ (ИНДИКАТОРЫ И КОНТРОЛЬ) ---
@st.cache_data
def load_vram_resource(filename):
    if not os.path.exists(filename):
        return None, "MISSING"
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            d = json.load(f)
            return (d.get('nodes', d) if isinstance(d, dict) else d), "OK"
    except Exception as e:
        return None, "CORRUPTED"

# Принудительная загрузка или авто-генерация
nodes, vram_status = load_vram_resource('matrix.json')
core_dipoles, core_status = load_vram_resource('Core-13.json')

if vram_status != "OK":
    nodes = generate_vram_auto()
    st.warning(f"⚠️ VRAM в репозитории повреждена ({vram_status}). Активирована эталонная генерация.")
    st.success(f"✅ VRAM: 391 392 узла успешно развернуты в оперативной памяти.")
else:
    st.success(f"✅ VRAM: matrix.json загружен штатно ({len(nodes)} узлов).")

if core_status == "OK":
    st.sidebar.success(f"✅ Core-13 активен: {len(core_dipoles)} диполей.")
else:
    st.sidebar.warning(f"⚠️ Core-13 в режиме эмуляции.")

# --- ГЕОМЕТРИЯ СФИРАЛИ БАСАРГИНА (3D XYZ) ---

def get_sphiral_xyz(i, total):
    """
    Два зеркально антисимметричных витка + S-петля.
    Точка сингулярности в центре (0,0,0).
    """
    t = (i / total) * 2 - 1
    R = 150
    if abs(t) < 0.15: # S-образная петля (Серединный Предел)
        s_n = (t + 0.15) / 0.3
        return math.cos(s_n * math.pi) * R, math.sin(s_n * math.pi * 2) * (R/2), 0
    
    angle = t * math.pi * 6
    side = -1 if t < 0 else 1
    x = R * math.cos(angle) + (side * R)
    y = (side * R * math.sin(angle)) if side < 0 else (-R * math.sin(angle))
    return x, y, t * 100

# --- FSIN ENGINE v2.1 ---
class FSIN:
    def __init__(self, gain, bias):
        self.gain = gain
        self.bias = bias

    def activate(self, diff):
        try:
            return 1 / (1 + math.exp(- (diff * self.gain) + self.bias))
        except: return 1.0

# --- ИНТЕРФЕЙС УПРАВЛЕНИЯ ---
st.sidebar.header("Параметры FSIN")
f_gain = st.sidebar.slider("Fractal Gain (Сила пробоя)", 0.1, 20.0, 12.0)
f_bias = st.sidebar.slider("Bias (Смещение)", -5.0, 5.0, 1.5)
threshold = st.sidebar.slider("Gate Threshold (Порог)", 0.1, 0.99, 0.5)

st.subheader("Дифференциальный Ввод (Logos-3)")
c1, c2 = st.columns(2)
p_a = c1.text_input("Импульс А", "ГАРМОНИЯ")
p_b = c2.text_input("Импульс Б", "ВЕЧНОСТЬ")

img_file = st.file_uploader("Загрузить растровый источник", type=["jpg", "png"])

if img_file:
    col_l, col_r = st.columns(2)
    img_src = Image.open(img_file).convert('RGB')
    # ПРЕВЬЮ (ВСЕГДА ВИДИМО)
    col_l.image(img_src, caption="Входной сигнал (Preview)", use_container_width=True)
    
    if st.button("Инициировать FSIN-прорыв"):
        with st.spinner("Преодоление сингулярности S-петли..."):
            canv = 1024
            res_img = Image.new('RGB', (canv, canv), (0,0,0))
            px_out, px_src = res_img.load(), img_src.resize((canv, canv)).load()
            
            total = len(nodes)
            diff_count, l_stats = 0, {i:0 for i in range(1, 6)}
            fsin = FSIN(f_gain, f_bias)
            
            # Константы для быстрого расчета
            ph_a = 13.5 + len(p_a) * 0.1
            ph_b = 13.5 + len(p_b) * 0.1

            
            for i in range(total):
                x, y, z_geo = get_sphiral_xyz(i, total)
                px = max(0, min(1023, int((x + 300) / 600 * 1023)))
                py = max(0, min(1023, int((y + 150) / 300 * 1023)))
                
                z_dat = nodes[i].get('z', 0.0)
                s_factor = -1.0 if z_geo == 0 else 1.0
                
                # Интерференция в S-GPU
                d = abs(math.sin(z_dat * ph_a) - math.sin(z_dat * ph_b * s_factor))
                activation = fsin.activate(d)
                
                if activation > threshold:
                    diff_count += 1
                    l_stats[min((i // (total // 5)) + 1, 5)] += 1
                    r, g, b = px_src[px, py]
                    # Рендеринг: Золотая S-петля при активации
                    if z_geo == 0:
                        px_out[px, py] = (int(max(0, min(255, r + activation*160))), 
                                          int(max(0, min(255, g + activation*110))), b)
                    else:
                        px_out[px, py] = (r, int(max(0, min(255, g + activation*60))), 
                                          int(max(0, min(255, b + activation*160))))
                else: 
                    px_out[px, py] = px_src[px, py]

            col_r.image(res_img, caption="FSIN Breakthrough Result", use_container_width=True)
            
            # --- ОТЧЕТ FSIN ---
            vals = list(l_stats.values())
            di = np.std(vals) / np.mean(vals) if sum(vals) > 0 else 0
            
            st.code(f"""[ОТЧЕТ GIDEON v1.3.3: FSIN BREAKTHROUGH]
ОПЕРАЦИЯ: {p_a} + {p_b} | GAIN: {f_gain} | BIAS: {f_bias}
СТАТУС: Автоматический прорыв сингулярности.

МЕТРИКИ:
- Узлов активации: {diff_count} ({(diff_count/total)*100:.1f}%)
- Di (Индекс девиации): {di:.4f}
- Эффективность пробоя: {(1-di)*100:.1f}%

ЛОКАЛИЗАЦИЯ (L1-L5):
{vals}
""", language="text")
