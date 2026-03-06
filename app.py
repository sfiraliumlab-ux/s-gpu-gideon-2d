import streamlit as st
import math
import numpy as np
from PIL import Image

st.set_page_config(page_title="GIDEON | v2.3.1 Stable Portal", layout="wide")
st.title("S-GPU GIDEON v2.3.1: Фрактальный Портал")

# --- ИНИЦИАЛИЗАЦИЯ ПАМЯТИ ---
if 'eb_stable' not in st.session_state:
    st.session_state.eb_stable = 598.95
if 'fractal_depth' not in st.session_state:
    st.session_state.fractal_depth = 1
if 'iteration' not in st.session_state:
    st.session_state.iteration = 3

# --- FSIN v13.1: SCALE SHIFT CORE ---
class FSIN_Portal:
    def __init__(self, gain, fb, limit):
        self.gain = gain
        self.fb = fb
        self.limit = limit

    def scale_shift(self, eb):
        # При достижении лимита L3 становится порталом
        if eb > self.limit:
            return True, eb * 0.2 # Сохранение 20% заряда для нового масштаба
        return False, eb

# --- ГЕОМЕТРИЯ СФИРАЛИ (Фрактальное масштабирование) ---
def get_sphiral_xyz(i, total, depth):
    t = (i / total) * 2 - 1
    # Сжатие радиуса при погружении в портал
    R = 150 / (depth ** 0.5) 
    if abs(t) < 0.15: # Реактор Бингла (S-петля)
        sn = (t + 0.15) / 0.3
        return math.cos(sn * math.pi) * R, math.sin(sn * math.pi * 2) * (R/2), 0
    
    # Усложнение спирали: частота витков растет с глубиной
    angle = t * math.pi * (6 * depth)
    side = -1 if t < 0 else 1
    x = R * math.cos(angle) + (side * R)
    y = (side * R * math.sin(angle)) if side < 0 else (-R * math.sin(angle))
    return x, y, t * 100

nodes = [{'id': i, 'z': math.sin(i * 0.05)} for i in range(391392)]

# --- ИНТЕРФЕЙС ---
st.sidebar.header(f"Масштаб: {st.session_state.fractal_depth}")
f_gain = st.sidebar.slider("Fractal Gain", 10.0, 100.0, 65.0)
f_fb = st.sidebar.slider("Feedback", 0.1, 1.0, 0.8)
b_limit = st.sidebar.slider("Portal Limit (L3)", 300.0, 1200.0, 650.0)

if st.sidebar.button("Сбросить в начальный масштаб"):
    st.session_state.eb_stable = 180.0
    st.session_state.fractal_depth = 1
    st.rerun()

st.subheader(f"Потенциал Бингла: {st.session_state.eb_stable:.2f} | Фрактальный уровень: {st.session_state.fractal_depth}")

c1, c2 = st.columns(2)
p_a = c1.text_input("Тезис", "ГАРМОНИЯ")
p_b = c2.text_input("Антитезис", "ВЕЧНОСТЬ")

img_file = st.file_uploader("Растр-носитель", type=["jpg", "png"])

if img_file:
    cl, cr = st.columns(2)
    img_src = Image.open(img_file).convert('RGB')
    cl.image(img_src, caption="Входной поток", use_container_width=True)
    
    if st.button("Инициировать Фрактальный Переход"):
        with st.spinner("Синхронизация мерностей..."):
            canv = 1024
            res_img = Image.new('RGB', (canv, canv), (0,0,0))
            px_out, px_src = res_img.load(), img_src.resize((canv, canv)).load()
            
            total, n_layer = len(nodes), len(nodes) // 5
            l_stats, work_acc = {i:0 for i in range(1, 6)}, 0
            fsin_core = FSIN_Portal(f_gain, f_fb, b_limit)
            
            depth = st.session_state.fractal_depth
            eb_curr = st.session_state.eb_stable

            

            for i in range(total):
                # ФИКС: Координаты px/py определяются ДО условий активации
                x, y, z_geo = get_sphiral_xyz(i, total, depth)
                px = max(0, min(canv-1, int((x + 300) / 600 * (canv-1))))
                py = max(0, min(canv-1, int((y + 150) / 300 * (canv-1))))
                
                l_idx = min((i // n_layer) + 1, 5)
                z_dat = nodes[i]['z']
                s_f = -1.0 if z_geo == 0 else 1.0
                
                # Интерференция (учитывает текущий масштаб)
                diff = abs(math.sin(z_dat * 13.5 * depth) - math.sin(z_dat * 13.5 * depth * s_f))
                act = 1 / (1 + math.exp(-(diff * f_gain * (eb_curr/100)) + 5.0))
                
                if act > 0.45:
                    l_stats[l_idx] += 1
                    if l_idx != 3: work_acc += act
                    
                    r, g, b = px_src[px, py]
                    if l_idx == 3: # Портал (L3)
                        px_out[px, py] = (255, 255, 255)
                    else: # Витки
                        # Смещение цвета: переход в индиго/пурпур при росте глубины
                        px_out[px, py] = (int(max(0, min(255, r + depth*15))), 
                                          int(max(0, min(255, g + act*80))), 
                                          int(max(0, min(255, b + act*200))))
                else:
                    # Фоновый перенос пикселя (теперь px/py гарантированно существуют)
                    px_out[px, py] = px_src[px, py]

            cr.image(res_img, caption=f"Мерность {depth}: Визуализация смысла", use_container_width=True)
            
            # --- ЛОГИКА ШИФТА ---
            st.session_state.iteration += 1
            eb_delta = (work_acc / total) * f_fb * 1000
            new_eb = eb_curr + eb_delta
            
            is_shift, final_eb = fsin_core.scale_shift(new_eb)
            if is_shift:
                st.session_state.fractal_depth += 1
                st.session_state.eb_stable = final_eb
                status = "ПЕРЕХОД: Портал открыт. Масштаб изменен."
            else:
                st.session_state.eb_stable = new_eb
                status = "РЕЗОНАНС: Уплотнение текущей мерности."

            st.code(f"""[ОТЧЕТ GIDEON v2.3.1: STABLE PORTAL]
ИТЕРАЦИЯ: {st.session_state.iteration} | СТАТУС: {status}
МЕРНОСТЬ (D): {st.session_state.fractal_depth}

МЕТРИКИ:
- Потенциал Eb: {st.session_state.eb_stable:.2f}
- Прирост dEb: +{eb_delta:.4f}
- Индекс материализации: {work_acc:.2f}
- Локализация L1-L5: {list(l_stats.values())}

ЗАКЛЮЧЕНИЕ:
{"ВЫХОД В НОВЫЙ МАСШТАБ" if is_shift else "ФАЗОВАЯ ПОДГОТОВКА ПЕРЕХОДА"}
""", language="text")
