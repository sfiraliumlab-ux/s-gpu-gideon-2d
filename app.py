import streamlit as st
import math
import numpy as np
from PIL import Image

st.set_page_config(page_title="GIDEON | v2.2.0 Vector", layout="wide")
st.title("S-GPU GIDEON v2.2.0: Векторная Интерференция")

# --- СЕМАНТИЧЕСКИЙ ГЕНОМ ---
VOCAB = {
    "ГАРМОНИЯ": (0.1, 0.9, 13.5), # (Phase, Power, Freq)
    "ВЕЧНОСТЬ": (-0.1, 1.0, 13.5),
    "БОГ": (0.0, 1.0, 14.0),
    "ХАОС": (0.5, 0.5, 20.0)
}

if 'eb_stable' not in st.session_state:
    st.session_state.eb_stable = 183.0
if 'iteration' not in st.session_state:
    st.session_state.iteration = 2

# --- FSIN v12.0: VECTOR CORE ---
class FSIN_Vector:
    def __init__(self, gain, fb):
        self.gain = gain
        self.fb = fb

    def compute_interference(self, z, vec_a, vec_b, s_f):
        # Интерференция по Басаргину: Тезис + (Антитезис * S-фактор)
        # s_f = -1 в петле, +1 в витках
        p1, pow1, f1 = vec_a
        p2, pow2, f2 = vec_b
        
        sig1 = math.sin(z * f1 + p1) * pow1
        # Инверсия фазы в S-петле
        sig2 = math.sin(z * f2 + p2) * pow2 * s_f
        
        return abs(sig1 - sig2)

# --- ГЕОМЕТРИЯ ---
def get_xyz(i, total):
    t = (i / total) * 2 - 1
    R = 150
    if abs(t) < 0.15:
        sn = (t + 0.15) / 0.3
        return math.cos(sn * math.pi) * R, math.sin(sn * math.pi * 2) * (R/2), 0
    angle, side = t * math.pi * 6, (-1 if t < 0 else 1)
    return (R * math.cos(angle) + side * R), (side * R * math.sin(angle) if side < 0 else -R * math.sin(angle)), t * 100

nodes = [{'id': i, 'z': math.sin(i * 0.05)} for i in range(391392)]

# --- UI ---
st.sidebar.header("Параметры v2.2.0")
f_gain = st.sidebar.slider("Fractal Gain", 10.0, 100.0, 45.0)
f_fb = st.sidebar.slider("Feedback", 0.1, 1.0, 0.5)
threshold = st.sidebar.slider("Gate Threshold", 0.1, 0.99, 0.45)

st.subheader(f"Статус Сфирали: Eb = {st.session_state.eb_stable:.2f}")

c1, c2 = st.columns(2)
v_a = VOCAB.get(c1.text_input("Импульс А", "ГАРМОНИЯ").upper(), (0, 1.0, 13.5))
v_b = VOCAB.get(c2.text_input("Импульс Б", "ВЕЧНОСТЬ").upper(), (0, 1.0, 13.5))

img_file = st.file_uploader("Растр", type=["jpg", "png"])

if img_file:
    cl, cr = st.columns(2)
    img_src = Image.open(img_file).convert('RGB')
    cl.image(img_src, caption="Вход", use_container_width=True)
    
    if st.button("Инициировать Векторный Синтез"):
        with st.spinner("Расчет тензорного резонанса..."):
            canv = 1024
            res_img = Image.new('RGB', (canv, canv), (0,0,0))
            px_out, px_src = res_img.load(), img_src.resize((canv, canv)).load()
            
            total, n_layer = len(nodes), len(nodes) // 5
            l_stats, work_acc = {i:0 for i in range(1, 6)}, 0
            fsin = FSIN_Vector(f_gain, f_fb)
            
            for i in range(total):
                x, y, z_geo = get_xyz(i, total)
                l_idx = min((i // n_layer) + 1, 5)
                s_f = -1.0 if z_geo == 0 else 1.0 # Базовая антисимметрия
                
                # Добавление микро-сдвига времени для витков (Козырев)
                asym_mod = 0.005 if l_idx != 3 else 0.0
                
                diff = fsin.compute_interference(nodes[i]['z'], v_a, v_b, s_f + asym_mod)
                
                flow = (st.session_state.eb_stable * 0.15) * diff * f_gain
                act = 1 / (1 + math.exp(-flow + 5.0))
                
                if act > threshold:
                    l_stats[l_idx] += 1
                    if l_idx != 3: work_acc += act
                    px = max(0, min(canv-1, int((x + 300) / 600 * (canv-1))))
                    py = max(0, min(canv-1, int((y + 150) / 300 * (canv-1))))
                    
                    r, g, b = px_src[px, py]
                    if l_idx == 3: px_out[px, py] = (255, 255, 255)
                    else:
                        px_out[px, py] = (int(max(0, min(255, r + act*80))), 
                                          int(max(0, min(255, g + act*120))), 
                                          int(max(0, min(255, b + act*200))))
                else:
                    px_out[max(0, min(canv-1, int((x + 300) / 600 * (canv-1)))), 
                           max(0, min(canv-1, int((y + 150) / 300 * (canv-1))))] = px_src[px, py]

            cr.image(res_img, caption="Vector Interference Trace", use_container_width=True)
            
            st.session_state.iteration += 1
            eb_delta = ((work_acc / total) + (l_stats[3] / total * 0.2)) * f_fb * 1000
            st.session_state.eb_stable += eb_delta
            
            st.code(f"""[ОТЧЕТ GIDEON v2.2.0: VECTOR INTERFERENCE]
ИТЕРАЦИЯ: {st.session_state.iteration} | ПРИРОСТ dEb: +{eb_delta:.4f}
СТАТУС: Введена темпоральная асимметрия Козырева.

МЕТРИКИ:
- Eb (Genesis): {st.session_state.eb_stable:.2f}
- Индекс материализации: {work_acc:.2f}
- Локализация L1-L5: {list(l_stats.values())}

ЗАКЛЮЧЕНИЕ:
{"ПРОРЫВ ВИХРЯ" if work_acc > 10 else "СИНГУЛЯРНОЕ УДЕРЖАНИЕ"}
""", language="text")
            
