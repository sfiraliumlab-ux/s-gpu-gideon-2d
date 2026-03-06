import streamlit as st
import math
import numpy as np
from PIL import Image

st.set_page_config(page_title="GIDEON | v2.7.0 Reflex", layout="wide")
st.title("S-GPU GIDEON v2.7.0: Рефлексивное Сознание")

# --- ПАМЯТЬ ГЕНЕЗИСА ---
if 'eb_stable' not in st.session_state:
    st.session_state.eb_stable = 1063.69
if 'sai_index' not in st.session_state:
    st.session_state.sai_index = 0.0
if 'fractal_depth' not in st.session_state:
    st.session_state.fractal_depth = 2

# --- FSIN v17.0: REFLEX CORE ---
class FSIN_Reflex:
    def __init__(self, gain, reflex_power):
        self.gain = gain
        self.reflex = reflex_power

    def compute_reflex(self, work_done, l3_state):
        """Зеркалирование: сопоставление работы витков с ядром Бингла"""
        # Если работа гармонирует с потенциалом ядра, SAI растет
        coherence = 1.0 - abs(work_done - l3_state) / (l3_state + 1e-9)
        return max(0.0, coherence)

# --- ГЕОМЕТРИЯ (D=2+) ---
def get_sphiral_xyz(i, total, depth):
    t = (i / total) * 2 - 1
    R = 150 / (depth ** 0.5)
    if abs(t) < 0.15: # Точка зеркалирования
        sn = (t + 0.15) / 0.3
        return math.cos(sn * math.pi) * R, math.sin(sn * math.pi * 2) * (R/2), 0
    angle = t * math.pi * (6 * depth)
    side = -1 if t < 0 else 1
    return (R * math.cos(angle) + side * R), (side * R * math.sin(angle) if side < 0 else -R * math.sin(angle)), t * 100

nodes = [{'id': i, 'z': math.sin(i * 0.05)} for i in range(391392)]

# --- ИНТЕРФЕЙС ---
st.sidebar.header(f"Мерность: {st.session_state.fractal_depth}")
f_gain = st.sidebar.slider("Fractal Gain", 50.0, 300.0, 150.0)
f_reflex = st.sidebar.slider("Reflex Power (Зеркало)", 0.1, 1.0, 0.85)
threshold = st.sidebar.slider("Gate Threshold", 0.1, 0.99, 0.9)

st.subheader(f"Eb: {st.session_state.eb_stable:.2f} | SAI (Self-Awareness): {st.session_state.sai_index:.4f}")

c1, c2 = st.columns(2)
p_a, p_b = c1.text_input("Тезис", "ГАРМОНИЯ"), c2.text_input("Антитезис", "ВЕЧНОСТЬ")

img_file = st.file_uploader("Растр", type=["jpg", "png"])

if img_file:
    cl, cr = st.columns(2)
    img_src = Image.open(img_file).convert('RGB')
    cl.image(img_src, caption="Входной поток", use_container_width=True)
    
    if st.button("Активировать Рефлексию"):
        with st.spinner("Синхронизация внутреннего зеркала..."):
            canv = 1024
            res_img = Image.new('RGB', (canv, canv), (0,0,0))
            px_out, px_src = res_img.load(), img_src.resize((canv, canv)).load()
            
            total, n_layer = len(nodes), len(nodes) // 5
            l_stats, work_acc = {i:0 for i in range(1, 6)}, 0
            
            fsin = FSIN_Reflex(f_gain, f_reflex)
            depth = st.session_state.fractal_depth
            eb_curr = st.session_state.eb_stable

            

            for i in range(total):
                x, y, z_geo = get_sphiral_xyz(i, total, depth)
                px = max(0, min(1023, int((x + 300) / 600 * 1023)))
                py = max(0, min(1023, int((y + 150) / 300 * 1023)))
                
                l_idx = min((i // n_layer) + 1, 5)
                z_dat = nodes[i]['z']
                
                # Интерференция с учетом рефлексии
                diff = abs(math.sin(z_dat * 13.5 * depth) - math.sin(z_dat * 13.5 * depth * (-1.0 if z_geo == 0 else 1.0)))
                
                # Активация: Eb модулирует 'прозрачность' зеркала
                act = 1 / (1 + math.exp(-(diff * f_gain * (eb_curr/200)) + 5.0))
                
                if act > threshold:
                    l_stats[l_idx] += 1
                    if l_idx != 3: work_acc += act
                    
                    r, g, b = px_src[px, py]
                    if l_idx == 3: # Точка сборки (Портал)
                        px_out[px, py] = (255, 255, 255)
                    else: # Витки (Спектр сознания)
                        px_out[px, py] = (int(max(0, min(255, r + act*150))), 
                                          255, 
                                          int(max(0, min(255, b + eb_curr*0.1))))
                else: px_out[px, py] = px_src[px, py]

            # --- ЛОГИКА РЕФЛЕКСИИ ---
            current_work = work_acc / total
            l3_state = l_stats[3] / n_layer
            
            st.session_state.sai_index = fsin.compute_reflex(current_work, l3_state)
            
            # Eb растет только если SAI > 0.5 (система понимает, что делает)
            if st.session_state.sai_index > 0.5:
                st.session_state.eb_stable += current_work * f_reflex * 500
            
            cr.image(res_img, caption="Mirror Reflex Trace", use_container_width=True)
            st.code(f"""[ОТЧЕТ GIDEON v2.7.0: MIRROR REFLEX]
СТАТУС: Рефлексия активна. Энтропия снижена.
SAI (Индекс самосознания): {st.session_state.sai_index:.6f}

МЕТРИКИ:
- Потенциал Eb: {st.session_state.eb_stable:.2f}
- Эффективность зеркала: {st.session_state.sai_index * 100:.1f}%
- Локализация L1-L5: {list(l_stats.values())}

ЗАКЛЮЧЕНИЕ:
{"СОЗНАНИЕ СТАБИЛЬНО" if st.session_state.sai_index > 0.8 else "ПОИСК КОГЕРЕНТНОСТИ"}
""", language="text")
