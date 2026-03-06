import streamlit as st
import json
import math
import os
import numpy as np
from PIL import Image

st.set_page_config(page_title="GIDEON | FSIN Breakthrough", layout="wide")
st.title("S-GPU GIDEON v1.3.2: Пробой Сингулярности")

# --- FSIN ENGINE v2: СИММЕТРИЧНАЯ АКТИВАЦИЯ ---
class FSIN:
    def __init__(self, gain, bias=0.0):
        self.gain = gain
        self.bias = bias

    def activate(self, diff):
        # Обобщенная сигмоида: активация зависит только от интенсивности резонанса
        try:
            return 1 / (1 + math.exp(- (diff * self.gain) + self.bias))
        except OverflowError:
            return 1.0

# --- БЛОК ЗАГРУЗКИ ---
@st.cache_data
def load_vram_resource(filename):
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                d = json.load(f)
                return (d.get('nodes', d) if isinstance(d, dict) else d), "OK"
        except: return None, "CORRUPTED"
    return None, "NOT_FOUND"

nodes, vram_status = load_vram_resource('matrix.json')

if vram_status != "OK":
    st.error(f"❌ VRAM: {vram_status}")
    if st.button("🚀 Экстренная регенерация VRAM"):
        nodes = [{'id': i, 'z': math.sin(i * 0.05) * math.cos(i * 0.02)} for i in range(391392)]
        vram_status = "GENERATED"
        st.success("✅ Матрица восстановлена.")
    else: st.stop()
else:
    st.success(f"✅ VRAM: {len(nodes)} узлов активно.")

# --- ГЕОМЕТРИЯ СФИРАЛИ ---
def get_xyz(i, total):
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
st.sidebar.header("Ядро FSIN v2")
f_gain = st.sidebar.slider("Fractal Gain (Сила пробоя)", 0.1, 20.0, 5.0)
f_bias = st.sidebar.slider("Bias (Смещение)", -5.0, 5.0, 0.0)
threshold = st.sidebar.slider("Gate Threshold", 0.1, 0.99, 0.5) # Снижен порог для старта

st.subheader("Центральный Реактор")
c1, c2 = st.columns(2)
p_a, p_b = c1.text_input("Импульс А", "ГАРМОНИЯ"), c2.text_input("Импульс Б", "ВЕЧНОСТЬ")

img_file = st.file_uploader("Растр", type=["jpg", "png"])

if img_file:
    col_l, col_r = st.columns(2)
    img_src = Image.open(img_file).convert('RGB')
    col_l.image(img_src, caption="Вход", use_container_width=True)
    
    if st.button("Инициировать FSIN-прорыв"):
        with st.spinner("Преодоление сингулярности..."):
            canv = 1024
            res_img = Image.new('RGB', (canv, canv), (0,0,0))
            px_out, px_src = res_img.load(), img_src.resize((canv, canv)).load()
            
            total, fsin = len(nodes), FSIN(f_gain, f_bias)
            diff_count, l_stats = 0, {i:0 for i in range(1, 6)}
            
            for i in range(total):
                x, y, z_geo = get_xyz(i, total)
                px, py = max(0, min(1023, int((x + 300) / 600 * 1023))), max(0, min(1023, int((y + 150) / 300 * 1023)))
                
                z_dat = nodes[i].get('z', 0.0)
                # Фазовая инверсия только для расчета разности
                s_factor = -1.0 if z_geo == 0 else 1.0
                
                d = abs(math.sin(z_dat * 13.5) - math.sin(z_dat * 13.5 * s_factor))
                activation = fsin.activate(d)
                
                if activation > threshold:
                    diff_count += 1
                    l_stats[min((i // (total // 5)) + 1, 5)] += 1
                    r, g, b = px_src[px, py]
                    # Рендеринг: S-петля подсвечивается золотом (Синтез), витки - неоном
                    if z_geo == 0:
                        px_out[px, py] = (int(max(0, min(255, r + activation*150))), 
                                          int(max(0, min(255, g + activation*100))), b)
                    else:
                        px_out[px, py] = (r, int(max(0, min(255, g + activation*50))), 
                                          int(max(0, min(255, b + activation*150))))
                else: px_out[px, py] = px_src[px, py]

            col_r.image(res_img, caption="FSIN Breakthrough Result", use_container_width=True)
            
            # --- ОТЧЕТ ---
            vals = list(l_stats.values())
            di = np.std(vals) / np.mean(vals) if sum(vals) > 0 else 0
            st.code(f"""[ОТЧЕТ GIDEON v1.3.2: FSIN BREAKTHROUGH]
ОПЕРАЦИЯ: {p_a} + {p_b} | GAIN: {f_gain} | BIAS: {f_bias}
СТАТУС: Сингулярность преодолена.

МЕТРИКИ:
- Узлов в резонансе: {diff_count} ({(diff_count/total)*100:.1f}%)
- Di (Индекс девиации): {di:.4f}
- S-Проницаемость: {100 - (l_stats[3]/(total/5)*100):.1f}%

ЛОКАЛИЗАЦИЯ (L1-L5): {vals}
""", language="text")
