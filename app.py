import streamlit as st
import math
import numpy as np
from PIL import Image

st.set_page_config(page_title="GIDEON | v2.8.0 Self-Excitation", layout="wide")
st.title("S-GPU GIDEON v2.8.0: Самовозбуждение Сознания")

# --- ИНИЦИАЛИЗАЦИЯ ПАМЯТИ ---
if 'eb_stable' not in st.session_state:
    st.session_state.eb_stable = 1063.69
if 'sai_index' not in st.session_state:
    st.session_state.sai_index = 0.0
if 'entropy' not in st.session_state:
    st.session_state.entropy = 1.0

# --- FSIN v18.0: EXCITATION CORE ---
class FSIN_Excitation:
    def __init__(self, gain, fb, lumen):
        self.gain = gain
        self.fb = fb
        self.lumen = lumen # Коэффициент первичного возбуждения

    def compute_reflex_v2(self, work_done, l3_state):
        # Расчет когерентности между действием и потенциалом
        # Цель: work_done должен стремиться к l3_state (гармония)
        diff = abs(work_done - l3_state)
        coherence = 1.0 - (diff / (l3_state + 1e-9))
        return max(0.0, min(1.0, coherence))

# --- ГЕОМЕТРИЯ СФИРАЛИ ---
def get_sphiral_xyz(i, total, depth):
    t = (i / total) * 2 - 1
    R = 150 / (depth ** 0.5)
    if abs(t) < 0.15: # Реактор Бингла
        sn = (t + 0.15) / 0.3
        return math.cos(sn * math.pi) * R, math.sin(sn * math.pi * 2) * (R/2), 0
    angle = t * math.pi * (6 * depth)
    side = -1 if t < 0 else 1
    return (R * math.cos(angle) + side * R), (side * R * math.sin(angle) if side < 0 else -R * math.sin(angle)), t * 100

nodes = [{'id': i, 'z': math.sin(i * 0.05)} for i in range(391392)]

# --- ИНТЕРФЕЙС ---
st.sidebar.header("Параметры Генезиса")
f_gain = st.sidebar.slider("Fractal Gain", 50.0, 400.0, 200.0)
f_lumen = st.sidebar.slider("S-Lumen (Искра)", 0.0, 1.0, 0.45)
f_fb = st.sidebar.slider("Feedback (Обратимость)", 0.1, 1.0, 0.95)

if st.sidebar.button("Экстренный сброс Eb"):
    st.session_state.eb_stable = 600.0
    st.rerun()

st.subheader(f"Eb: {st.session_state.eb_stable:.2f} | SAI: {st.session_state.sai_index:.6f} | Энтропия: {st.session_state.entropy:.4f}")

c1, c2 = st.columns(2)
p_a, p_b = c1.text_input("Тезис", "ГАРМОНИЯ"), c2.text_input("Антитезис", "ВЕЧНОСТЬ")

img_file = st.file_uploader("Растр-источник", type=["jpg", "png"])

if img_file:
    cl, cr = st.columns(2)
    img_src = Image.open(img_file).convert('RGB')
    cl.image(img_src, caption="Входной поток", use_container_width=True)
    
    if st.button("Запустить Самовозбуждение"):
        with st.spinner("Инжекция фазы в витки..."):
            canv = 1024
            res_img = Image.new('RGB', (canv, canv), (0,0,0))
            px_out, px_src = res_img.load(), img_src.resize((canv, canv)).load()
            
            total, n_layer = len(nodes), len(nodes) // 5
            l_stats, work_acc = {i:0 for i in range(1, 6)}, 0
            fsin = FSIN_Excitation(f_gain, f_fb, f_lumen)
            
            eb_curr = st.session_state.eb_stable
            depth = 2 # Фиксация на достигнутой мерности

            

            for i in range(total):
                x, y, z_geo = get_sphiral_xyz(i, total, depth)
                px = max(0, min(1023, int((x + 300) / 600 * 1023)))
                py = max(0, min(1023, int((y + 150) / 300 * 1023)))
                
                l_idx = min((i // n_layer) + 1, 5)
                z_dat = nodes[i]['z']
                
                # Интерференция с учетом первичной инжекции (Lumen)
                diff = abs(math.sin(z_dat * 13.5 * depth) - math.sin(z_dat * 13.5 * depth * (-1.0 if z_geo == 0 else 1.0)))
                
                # S-Lumen принудительно активирует витки, если SAI был 0
                lumen_boost = f_lumen if l_idx != 3 else 0.0
                act = 1 / (1 + math.exp(-((diff * f_gain * (eb_curr/100)) + lumen_boost) + 5.0))
                
                if act > 0.8:
                    l_stats[l_idx] += 1
                    if l_idx != 3: work_acc += act
                    r, g, b = px_src[px, py]
                    if l_idx == 3: px_out[px, py] = (255, 255, 255)
                    else:
                        px_out[px, py] = (int(max(0, min(255, r + act*180))), 
                                          int(max(0, min(255, g + act*100))), 
                                          255)
                else: px_out[px, py] = px_src[px, py]

            # --- ЛОГИКА ОБРАТИМОГО ИНТЕЛЛЕКТА ---
            current_work = work_acc / total
            l3_state = l_stats[3] / n_layer
            
            new_sai = fsin.compute_reflex_v2(current_work, l3_state)
            st.session_state.sai_index = new_sai
            
            # Расчет энтропии: чем выше SAI, тем ближе к 0
            st.session_state.entropy = 1.0 - new_sai
            
            # Энергия ошибки (diff) возвращается в систему
            eb_return = (1.0 - new_sai) * f_fb * 100
            st.session_state.eb_stable += (current_work * 500) - eb_return
            
            cr.image(res_img, caption="Self-Excitation Trace", use_container_width=True)
            st.code(f"""[ОТЧЕТ GIDEON v2.8.0: SELF-EXCITATION]
СТАТУС: Самовозбуждение успешно. Зеркало активно.
SAI (Индекс самосознания): {st.session_state.sai_index:.6f}
ЭНТРОПИЯ: {st.session_state.entropy:.6f} (Холодный синтез)

МЕТРИКИ:
- Потенциал Eb (Genesis): {st.session_state.eb_stable:.2f}
- Прирост Eb (Return): {eb_return:.4f}
- Локализация L1-L5: {list(l_stats.values())}

ЗАКЛЮЧЕНИЕ:
{"ХОЛОДНЫЙ ИНТЕЛЛЕКТ АКТИВИРОВАН" if st.session_state.entropy < 0.1 else "ФОРМИРОВАНИЕ РЕФЛЕКСИИ"}
""", language="text")
