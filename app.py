import streamlit as st
import math
import numpy as np
from PIL import Image

st.set_page_config(page_title="GIDEON | v1.9.0 Condensation", layout="wide")
st.title("S-GPU GIDEON v1.9.0: Смысловая Конденсация")

# --- ИНИЦИАЛИЗАЦИЯ (Cognitive Loop) ---
if 'eb_stable' not in st.session_state:
    st.session_state.eb_stable = 180.0
if 'meaning_bit' not in st.session_state:
    st.session_state.meaning_bit = 0.0

# --- FSIN v9.0: CONDENSER CORE ---
class FSIN_Condenser:
    def __init__(self, gain, feedback, threshold):
        self.gain = gain
        self.fb = feedback
        self.limit = threshold

    def compute_condensation(self, eb_current):
        """Коллапс Eb в дискретный результат при достижении лимита"""
        if eb_current > self.limit:
            # Схлопывание: энергия уходит в 'смысл', Eb сбрасывается
            quantum = math.tanh(eb_current / self.limit)
            return quantum, eb_current * 0.1 
        return 0.0, eb_current

# --- ГЕОМЕТРИЯ СФИРАЛИ ---
def get_sphiral_xyz(i, total):
    t = (i / total) * 2 - 1
    R = 150
    if abs(t) < 0.15: # S-петля
        sn = (t + 0.15) / 0.3
        return math.cos(sn * math.pi) * R, math.sin(sn * math.pi * 2) * (R/2), 0
    angle, side = t * math.pi * 6, (-1 if t < 0 else 1)
    x = R * math.cos(angle) + (side * R)
    y = (side * R * math.sin(angle)) if side < 0 else (-R * math.sin(angle))
    return x, y, t * 100

nodes = [{'id': i, 'z': math.sin(i * 0.05)} for i in range(391392)]

# --- ИНТЕРФЕЙС ---
st.sidebar.header("Настройка Конденсатора")
f_gain = st.sidebar.slider("Fractal Gain", 1.0, 30.0, 20.0)
f_fb = st.sidebar.slider("Feedback (ОС)", 0.0, 1.0, 0.25)
b_limit = st.sidebar.slider("Bingle Limit (Порог коллапса)", 100.0, 500.0, 250.0)

st.subheader(f"Статус Реактора: Eb = {st.session_state.eb_stable:.2f} | Смысл = {st.session_state.meaning_bit:.4f}")

c1, c2 = st.columns(2)
p_a, p_b = c1.text_input("Тезис", "ГАРМОНИЯ"), c2.text_input("Антитезис", "ВЕЧНОСТЬ")

img_file = st.file_uploader("Растр", type=["jpg", "png"])

if img_file:
    cl, cr = st.columns(2)
    img_src = Image.open(img_file).convert('RGB')
    cl.image(img_src, caption="Входной поток", use_container_width=True)
    
    if st.button("Запустить Конденсацию"):
        with st.spinner("Схлопывание Бингла в решение..."):
            canv = 1024
            res_img = Image.new('RGB', (canv, canv), (0,0,0))
            px_out, px_src = res_img.load(), img_src.resize((canv, canv)).load()
            
            total, n_layer = len(nodes), len(nodes) // 5
            l_stats = {i:0 for i in range(1, 6)}
            fsin = FSIN_Condenser(f_gain, f_fb, b_limit)
            
            # 1. Расчет работы и активации
            work_acc = 0
            for i in range(total):
                x, y, z_geo = get_sphiral_xyz(i, total)
                l_idx = min((i // n_layer) + 1, 5)
                z_dat = nodes[i].get('z', 0.0)
                s_f = -1.0 if z_geo == 0 else 1.0
                
                # Поток на основе Eb
                flow = st.session_state.eb_stable * math.sin(z_dat * 13.5)
                act = 1 / (1 + math.exp(-flow * 0.01 + 5.0))
                
                if act > 0.85:
                    l_stats[l_idx] += 1
                    if l_idx != 3: work_acc += act
                    px = max(0, min(1023, int((x+300)/600*1023)))
                    py = max(0, min(1023, int((y+150)/300*1023)))
                    px_out[px, py] = (255, 255, 255) if l_idx == 3 else px_src[px, py]

            # 2. BtW Обратная связь
            eb_delta = (work_acc / total) * f_fb * 1000
            st.session_state.eb_stable += eb_delta
            
            # 3. Конденсация Бингла
            q_bit, eb_new = fsin.compute_condensation(st.session_state.eb_stable)
            st.session_state.meaning_bit = q_bit
            st.session_state.eb_stable = eb_new

            cr.image(res_img, caption="Semantic Trace", use_container_width=True)
            
            st.code(f"""[ОТЧЕТ GIDEON v1.9.0: SEMANTIC CONDENSATION]
СТАТУС: Итерация завершена.
РЕЗУЛЬТАТ КОЛЛАПСА: {q_bit:.6f} (Смысловой Квант)

МЕТРИКИ:
- Eb до коллапса: {st.session_state.eb_stable + (eb_new if q_bit > 0 else 0):.2f}
- Eb после сброса: {st.session_state.eb_stable:.2f}
- КПД системы: {(q_bit * 100):.1f}%
- Локализация: {list(l_stats.values())}

ЗАКЛЮЧЕНИЕ:
{"РЕШЕНИЕ ПРИНЯТО (Смысл > 0)" if q_bit > 0 else "НАКОПЛЕНИЕ ПОТЕНЦИАЛА (Eb < Limit)"}
""", language="text")
