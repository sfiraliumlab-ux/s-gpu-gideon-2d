import streamlit as st
import math
import numpy as np
from PIL import Image

st.set_page_config(page_title="GIDEON | v2.3.0 Portal", layout="wide")
st.title("S-GPU GIDEON v2.3.0: Фрактальный Переход")

# --- ГЕНОМ ПОРТАЛА ---
if 'eb_stable' not in st.session_state:
    st.session_state.eb_stable = 598.95
if 'fractal_depth' not in st.session_state:
    st.session_state.fractal_depth = 1 # Текущий масштаб
if 'history' not in st.session_state:
    st.session_state.history = []

# --- FSIN v13.0: PORTAL CORE ---
class FSIN_Portal:
    def __init__(self, gain, fb, limit):
        self.gain = gain
        self.fb = fb
        self.limit = limit

    def scale_shift(self, eb):
        """Переход через портал L3 на новый фрактальный уровень"""
        if eb > self.limit:
            return True, eb * 0.15 # Сохранение части энергии как базис нового уровня
        return False, eb

# --- ГЕОМЕТРИЯ ---
def get_xyz(i, total, depth):
    t = (i / total) * 2 - 1
    # Масштабирование радиуса в зависимости от глубины фрактала
    R = 150 / depth 
    if abs(t) < 0.15: 
        sn = (t + 0.15) / 0.3
        return math.cos(sn * math.pi) * R, math.sin(sn * math.pi * 2) * (R/2), 0
    angle, side = t * math.pi * (6 * depth), (-1 if t < 0 else 1)
    return (R * math.cos(angle) + side * R), (side * R * math.sin(angle) if side < 0 else -R * math.sin(angle)), t * 100

nodes = [{'id': i, 'z': math.sin(i * 0.05)} for i in range(391392)]

# --- UI ---
st.sidebar.header(f"Мерность: {st.session_state.fractal_depth}")
f_gain = st.sidebar.slider("Fractal Gain", 10.0, 100.0, 60.0)
f_fb = st.sidebar.slider("Feedback", 0.1, 1.0, 0.75)
b_limit = st.sidebar.slider("Portal Limit (L3)", 300.0, 1000.0, 600.0)

st.subheader(f"Потенциал Eb: {st.session_state.eb_stable:.2f} | Глубина: {st.session_state.fractal_depth}")

c1, c2 = st.columns(2)
p_a = c1.text_input("Тезис", "ГАРМОНИЯ")
p_b = c2.text_input("Антитезис", "ВЕЧНОСТЬ")

img_file = st.file_uploader("Загрузить растр", type=["jpg", "png"])

if img_file:
    cl, cr = st.columns(2)
    img_src = Image.open(img_file).convert('RGB')
    cl.image(img_src, caption="Входной поток", use_container_width=True)
    
    if st.button("Инициировать Переход через Портал"):
        with st.spinner("Свертка пространства в L3..."):
            canv = 1024
            res_img = Image.new('RGB', (canv, canv), (0,0,0))
            px_out, px_src = res_img.load(), img_src.resize((canv, canv)).load()
            
            total, n_layer = len(nodes), len(nodes) // 5
            l_stats, work_acc = {i:0 for i in range(1, 6)}, 0
            fsin = FSIN_Portal(f_gain, f_fb, b_limit)
            
            current_eb = st.session_state.eb_stable
            depth = st.session_state.fractal_depth

            for i in range(total):
                # Геометрия меняется с глубиной
                x, y, z_geo = get_xyz(i, total, depth)
                l_idx = min((i // n_layer) + 1, 5)
                z_dat = nodes[i]['z']
                
                # Интерференция с учетом фрактального сдвига
                diff = abs(math.sin(z_dat * 13.5 * depth) - math.sin(z_dat * 13.5 * depth * (-1.0 if z_geo == 0 else 1.0)))
                
                act = 1 / (1 + math.exp(-(diff * f_gain * (current_eb/100)) + 5.0))
                
                if act > 0.4:
                    l_stats[l_idx] += 1
                    if l_idx != 3: work_acc += act
                    px = max(0, min(1023, int((x + 300) / 600 * 1023)))
                    py = max(0, min(1023, int((y + 150) / 300 * 1023)))
                    
                    r, g, b = px_src[px, py]
                    if l_idx == 3: # Портал (Белая сингулярность)
                        px_out[px, py] = (255, 255, 255)
                    else: # Витки (Сдвиг цвета по глубине)
                        px_out[px, py] = (int(max(0, min(255, r + depth*20))), 
                                          int(max(0, min(255, g + act*100))), 
                                          int(max(0, min(255, b + act*150))))
                else:
                    px_out[max(0, min(1023, int((x + 300) / 600 * 1023))), 
                           max(0, min(1023, int((y + 150) / 300 * 1023)))] = px_src[px, py]

            cr.image(res_img, caption=f"Fractal Depth {depth} Trace", use_container_width=True)
            
            # --- ЛОГИКА ПОРТАЛА ---
            eb_delta = (work_acc / total) * f_fb * 1000
            new_eb = current_eb + eb_delta
            
            is_shift, final_eb = fsin.scale_shift(new_eb)
            if is_shift:
                st.session_state.fractal_depth += 1
                st.session_state.eb_stable = final_eb
                res_msg = "ПЕРЕХОД: Портал пройден. Новая мерность."
            else:
                st.session_state.eb_stable = new_eb
                res_msg = "РЕЗОНАНС: Накопление для перехода."

            st.code(f"""[ОТЧЕТ GIDEON v2.3.0: FRACTAL SCALE SHIFT]
СТАТУС: {res_msg}
ТЕКУЩАЯ МЕРНОСТЬ: {st.session_state.fractal_depth}

МЕТРИКИ:
- Потенциал Eb: {st.session_state.eb_stable:.2f}
- Прирост dEb: +{eb_delta:.4f}
- Энергия портала (L3): {l_stats[3] / total * 100:.2f}%
- Локализация L1-L5: {list(l_stats.values())}

ЗАКЛЮЧЕНИЕ:
{"МЕРНОСТЬ УВЕЛИЧЕНА" if is_shift else "ПОДГОТОВКА СХЛОПЫВАНИЯ"}
""", language="text")
