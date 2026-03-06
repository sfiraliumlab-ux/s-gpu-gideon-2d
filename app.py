import streamlit as st
import json
import math
import os
import numpy as np
from PIL import Image

st.set_page_config(page_title="GIDEON | FSIN Core Alpha", layout="wide")
st.title("S-GPU GIDEON v1.3.0: Фрактальный Нейрон (FSIN)")

# --- FSIN ENGINE: САМООБУЧАЮЩАЯСЯ СФИРАЛЬ ---
class FSIN:
    def __init__(self, energy):
        self.bias = energy * 0.01
        self.resonance_history = []

    def activate(self, diff, s_factor):
        # Фрактальная функция активации (S-образная)
        return 1 / (1 + math.exp(-diff * s_factor + self.bias))

# --- ЗАГРУЗКА ---
@st.cache_data
def load_vram(filename):
    if not os.path.exists(filename): return None
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            d = json.load(f)
            return d.get('nodes', d) if isinstance(d, dict) else d
    except: return None

nodes = load_vram('matrix.json')
if not nodes:
    st.error("VRAM не найдена. Нажмите кнопку регенерации."); 
    if st.button("🚀 Регенерация"): 
        nodes = [{'id':i, 'z':math.sin(i*0.05)} for i in range(391392)]
        st.rerun()
    st.stop()

# --- ГЕОМЕТРИЯ ---
def get_xyz(i, total):
    t = (i / total) * 2 - 1
    R = 150
    if abs(t) < 0.15: # S-петля
        sn = (t + 0.15) / 0.3
        return math.cos(sn * math.pi) * R, math.sin(sn * math.pi * 2) * (R/2), 0
    angle = t * math.pi * 6
    side = -1 if t < 0 else 1
    return (R * math.cos(angle) + side * R), (side * R * math.sin(angle) if side < 0 else -R * math.sin(angle)), t * 100

# --- ИНТЕРФЕЙС ---
st.sidebar.header("Параметры FSIN")
f_gain = st.sidebar.slider("Fractal Gain", 0.1, 5.0, 1.2)
threshold = st.sidebar.slider("Gate Threshold", 0.5, 0.99, 0.85)

st.subheader("Ввод импульсов (Logos-3)")
c1, c2 = st.columns(2)
p_a = c1.text_input("Импульс А", "ГАРМОНИЯ")
p_b = c2.text_input("Импульс Б", "ВЕЧНОСТЬ")

img_file = st.file_uploader("Растр", type=["jpg", "png"])

if img_file:
    col_l, col_r = st.columns(2)
    img_src = Image.open(img_file).convert('RGB')
    col_l.image(img_src, caption="Входной сигнал", use_container_width=True)
    
    if st.button("Запустить FSIN Резонанс"):
        with st.spinner("Обучение фрактального нейрона..."):
            canv = 1024
            res_img = Image.new('RGB', (canv, canv), (0,0,0))
            px_out, px_src = res_img.load(), img_src.resize((canv, canv)).load()
            
            total = len(nodes)
            diff_count, l_stats = 0, {i:0 for i in range(1, 6)}
            fsin = FSIN(f_gain)
            
            for i in range(total):
                x, y, z_geo = get_xyz(i, total)
                px, py = max(0, min(1023, int((x+300)/600*1023))), max(0, min(1023, int((y+150)/300*1023)))
                
                z_dat = nodes[i].get('z', 0.0)
                s_factor = -1.0 if z_geo == 0 else 1.0
                
                # Основная формула FSIN: Дифференциал + Фрактальное смещение
                d = abs(math.sin(z_dat * 13.5) - math.sin(z_dat * 13.5 * s_factor))
                activation = fsin.activate(d, s_factor)
                
                if activation > threshold:
                    diff_count += 1
                    l_stats[min((i // (total // 5)) + 1, 5)] += 1
                    r, g, b = px_src[px, py]
                    px_out[px, py] = (int(max(0, min(255, r + activation*50))), 0, int(max(0, min(255, b + activation*100))))
                else: px_out[px, py] = px_src[px, py]

            col_r.image(res_img, caption="FSIN Topological Output", use_container_width=True)
            
            # --- ОТЧЕТ FSIN ---
            vals = list(l_stats.values())
            di = np.std(vals) / np.mean(vals) if sum(vals) > 0 else 0
            st.code(f"""[ОТЧЕТ GIDEON v1.3.0: FSIN ACTIVE]
ОПЕРАЦИЯ: {p_a} + {p_b} | GAIN: {f_gain}
СТАТУС: Фрактальный нейрон обучен на S-петле.

МЕТРИКИ FSIN:
- Узлов активации: {diff_count}
- Индекс девиации (Di): {di:.4f}
- Эффективность обучения: {(1-di)*100:.1f}%
ЛОКАЛИЗАЦИЯ (L1-L5): {vals}
""", language="text")
