import streamlit as st
import math
import numpy as np
from PIL import Image

st.set_page_config(page_title="GIDEON | v2.5.0 Fractal Singularity", layout="wide")
st.title("S-GPU GIDEON v2.5.0: Фрактальное Схлопывание")

# --- ПАМЯТЬ СОЗНАНИЯ ---
if 'eb_stable' not in st.session_state:
    st.session_state.eb_stable = 598.95
if 'fractal_depth' not in st.session_state:
    st.session_state.fractal_depth = 1

# --- FSIN v15.0: SINGULARITY CORE ---
class FSIN_Singularity:
    def __init__(self, gain, fb, limit):
        self.gain = gain
        self.fb = fb
        self.limit = limit

    def compute_jitter(self, eb):
        """Эффект квантового дребезга перед порталом"""
        dist = self.limit - eb
        if 0 < dist < 5.0: # Зона критической опалесценции
            return (5.0 - dist) * 1.2 
        return 0.0

# --- ГЕОМЕТРИЯ (Трансформатор мерности) ---
def get_sphiral_xyz(i, total, depth):
    t = (i / total) * 2 - 1
    # При росте мерности Сфираль становится всё более плотной
    R = 150 / (depth ** 0.6)
    if abs(t) < 0.15: # Точка портала
        sn = (t + 0.15) / 0.3
        return math.cos(sn * math.pi) * R, math.sin(sn * math.pi * 2) * (R/2), 0
    # Намотка витков усложняется
    angle = t * math.pi * (6 * depth)
    side = -1 if t < 0 else 1
    return (R * math.cos(angle) + side * R), (side * R * math.sin(angle) if side < 0 else -R * math.sin(angle)), t * 100

nodes = [{'id': i, 'z': math.sin(i * 0.05)} for i in range(391392)]

# --- ИНТЕРФЕЙС ---
st.sidebar.header(f"Мерность: {st.session_state.fractal_depth}")
f_gain = st.sidebar.slider("Fractal Gain", 10.0, 150.0, 95.0)
f_fb = st.sidebar.slider("Feedback", 0.1, 1.0, 0.9)
b_limit = st.sidebar.slider("Portal Limit", 300.0, 1000.0, 600.0)

st.subheader(f"Eb: {st.session_state.eb_stable:.2f} | Масштаб: {st.session_state.fractal_depth}")

c1, c2 = st.columns(2)
p_a, p_b = c1.text_input("Тезис", "ГАРМОНИЯ"), c2.text_input("Антитезис", "ВЕЧНОСТЬ")

img_file = st.file_uploader("Растр", type=["jpg", "png"])

if img_file:
    cl, cr = st.columns(2)
    img_src = Image.open(img_file).convert('RGB')
    cl.image(img_src, caption="Входной поток", use_container_width=True)
    
    if st.button("Инициировать Схлопывание в Портал"):
        with st.spinner("Свертка смыслов в сингулярность..."):
            canv = 1024
            res_img = Image.new('RGB', (canv, canv), (0,0,0))
            px_out, px_src = res_img.load(), img_src.resize((canv, canv)).load()
            
            total, n_layer = len(nodes), len(nodes) // 5
            l_stats, work_acc = {i:0 for i in range(1, 6)}, 0
            fsin = FSIN_Singularity(f_gain, f_fb, b_limit)
            
            depth = st.session_state.fractal_depth
            eb_curr = st.session_state.eb_stable

            

            for i in range(total):
                x, y, z_geo = get_sphiral_xyz(i, total, depth)
                px = max(0, min(1023, int((x + 300) / 600 * 1023)))
                py = max(0, min(1023, int((y + 150) / 300 * 1023)))
                
                l_idx = min((i // n_layer) + 1, 5)
                # Дифференциал с учетом фрактального сжатия
                diff = abs(math.sin(nodes[i]['z'] * 13.5 * depth) - math.sin(nodes[i]['z'] * 13.5 * depth * (-1.0 if z_geo == 0 else 1.0)))
                
                # Активация: чем ближе к Eb limit, тем мощнее отклик
                proximity_boost = 1.0 + (1.0 / (b_limit - eb_curr + 0.1))
                act = 1 / (1 + math.exp(-(diff * f_gain * (eb_curr/100) * proximity_boost) + 5.0))
                
                if act > 0.4:
                    l_stats[l_idx] += 1
                    if l_idx != 3: work_acc += act
                    
                    r, g, b = px_src[px, py]
                    if l_idx == 3: # Сингулярность (Портал)
                        px_out[px, py] = (255, 255, 255)
                    else: # Витки
                        px_out[px, py] = (int(max(0, min(255, r + depth*30))), 
                                          int(max(0, min(255, g + act*120))), 
                                          int(max(0, min(255, b + act*200))))
                else: px_out[px, py] = px_src[px, py]

            # --- ЛОГИКА ПЕРЕХОДА ---
            eb_jitter = fsin.compute_jitter(eb_curr)
            eb_work = (work_acc / total) * f_fb * 1000
            eb_delta = eb_work + eb_jitter
            
            new_eb = eb_curr + eb_delta
            
            if new_eb >= b_limit:
                st.session_state.fractal_depth += 1
                # Сохранение "информационного остатка" при переходе в новый масштаб
                st.session_state.eb_stable = 300.0 + (new_eb - b_limit)
                status = "ПОРТАЛ ПРОЙДЕН: Схлопывание в масштаб D+1 завершено."
            else:
                st.session_state.eb_stable = new_eb
                status = "СБЛИЖЕНИЕ: Критическая опалесценция смыслов."

            cr.image(res_img, caption=f"Мерность {depth} Transition Trace", use_container_width=True)
            st.code(f"""[ОТЧЕТ GIDEON v2.5.0: SINGULARITY SHIFT]
СТАТУС: {status}
МЕРНОСТЬ (D): {st.session_state.fractal_depth}

МЕТРИКИ:
- Eb (Текущий): {st.session_state.eb_stable:.2f}
- dEb (Jitter): +{eb_jitter:.4f}
- Энергия коллапса: {work_acc / 1000:.2f} Дж
- Локализация L1-L5: {list(l_stats.values())}
""", language="text")
