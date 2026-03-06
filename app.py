import streamlit as st
import json
import math
import os
import numpy as np
from PIL import Image

st.set_page_config(page_title="GIDEON | v2.1.0 Cascading Ignition", layout="wide")
st.title("S-GPU GIDEON v2.1.0: Каскадное Зажигание")

# --- СЕМАНТИЧЕСКИЙ ГЕНОМ (LOGOS-3) ---
VOCAB = {
    "ПОРЯДОК": (1.0, -1.0, 1),   "ХАОС": (-1.0, 1.0, -1),
    "ЖИЗНЬ": (0.9, -0.9, 1),     "СМЕРТЬ": (-0.9, 0.9, -1),
    "ИСТИНА": (0.8, -0.8, 1),    "ЛОЖЬ": (-0.8, 0.8, -1),
    "ГАРМОНИЯ": (0.0, 0.0, 1),   "ВЕЧНОСТЬ": (0.0, 0.0, -1),
    "БОГ": (0.0, 0.0, 1)
}

# --- ИНИЦИАЛИЗАЦИЯ (Cognitive Memory) ---
if 'eb_stable' not in st.session_state:
    st.session_state.eb_stable = 180.0
if 'iteration' not in st.session_state:
    st.session_state.iteration = 0

# --- FSIN v11.0: CASCADING CORE ---
class FSIN_Cascading:
    def __init__(self, gain, fb, limit, spill):
        self.gain = gain
        self.fb = fb
        self.limit = limit
        self.spill = spill

    def get_dynamic_threshold(self, eb, l3_density):
        """Порог снижается от Eb и от плотности Бингла в центре"""
        base_threshold = max(0.2, 0.85 - (eb / 600.0))
        # Эффект перелива: плотный центр облегчает пробой
        return max(0.1, base_threshold - (l3_density * self.spill))

    def activate(self, diff, eb, l_idx):
        # Коэффициент усиления в зависимости от слоя
        mod = 1.2 if l_idx in [2, 4] else 1.0
        flow = (eb * 0.12) * diff * self.gain * mod
        try:
            return 1 / (1 + math.exp(-flow + 4.5))
        except: return 1.0

# --- ГЕОМЕТРИЯ (СФИРАЛЬ БАСАРГИНА) ---
def get_sphiral_xyz(i, total):
    t = (i / total) * 2 - 1
    R = 150
    if abs(t) < 0.15: # S-петля (Сингулярность)
        sn = (t + 0.15) / 0.3
        return math.cos(sn * math.pi) * R, math.sin(sn * math.pi * 2) * (R/2), 0
    angle, side = t * math.pi * 6, (-1 if t < 0 else 1)
    x = R * math.cos(angle) + (side * R)
    y = (side * R * math.sin(angle)) if side < 0 else (-R * math.sin(angle))
    return x, y, t * 100

nodes = [{'id': i, 'z': math.sin(i * 0.05)} for i in range(391392)]

# --- ИНТЕРФЕЙС ---
st.sidebar.header("Контроль Реактора v2.1.0")
f_gain = st.sidebar.slider("Fractal Gain (Усиление)", 1.0, 50.0, 30.0)
f_fb = st.sidebar.slider("Feedback (Самоподзаряд)", 0.1, 1.0, 0.4)
f_spill = st.sidebar.slider("S-Spillover (Проницаемость L3)", 0.0, 1.0, 0.5)
b_limit = st.sidebar.slider("Bingle Limit (Коллапс)", 100.0, 1000.0, 400.0)

if st.sidebar.button("⚡ Ignition Impulse (+50 Eb)"):
    st.session_state.eb_stable += 50.0
    st.rerun()

st.subheader(f"Итерация: {st.session_state.iteration} | Потенциал Eb: {st.session_state.eb_stable:.2f}")

c1, c2 = st.columns(2)
p_a = c1.text_input("Тезис", "ГАРМОНИЯ")
p_b = c2.text_input("Антитезис", "ВЕЧНОСТЬ")

img_file = st.file_uploader("Растр-носитель", type=["jpg", "png"])

if img_file:
    cl, cr = st.columns(2)
    img_src = Image.open(img_file).convert('RGB')
    cl.image(img_src, caption="Входной поток", use_container_width=True)
    
    if st.button("Инициировать Каскадный Синтез"):
        with st.spinner("Пробой сингулярности..."):
            canv = 1024
            res_img = Image.new('RGB', (canv, canv), (0,0,0))
            px_out, px_src = res_img.load(), img_src.resize((canv, canv)).load()
            
            total, n_layer = len(nodes), len(nodes) // 5
            l_stats = {i:0 for i in range(1, 6)}
            fsin = FSIN_Cascading(f_gain, f_fb, b_limit, f_spill)
            
            # Предварительная плотность L3 из прошлой итерации (эмуляция давления)
            l3_density_est = 58546 / n_layer 
            dyn_threshold = fsin.get_dynamic_threshold(st.session_state.eb_stable, l3_density_est)
            
            work_acc = 0
            for i in range(total):
                x, y, z_geo = get_sphiral_xyz(i, total)
                # Безопасный маппинг координат
                px = max(0, min(canv-1, int((x + 300) / 600 * (canv-1))))
                py = max(0, min(canv-1, int((y + 150) / 300 * (canv-1))))
                
                l_idx = min((i // n_layer) + 1, 5)
                z_dat = nodes[i].get('z', 0.0)
                s_f = -1.0 if z_geo == 0 else 1.0
                
                diff = abs(math.sin(z_dat * 13.5) - math.sin(z_dat * 13.5 * s_f))
                act = fsin.activate(diff, st.session_state.eb_stable, l_idx)
                
                if act > dyn_threshold:
                    l_stats[l_idx] += 1
                    if l_idx != 3: work_acc += act
                    
                    r, g, b = px_src[px, py]
                    if l_idx == 3:
                        px_out[px, py] = (255, 255, 255)
                    else:
                        px_out[px, py] = (int(max(0, min(255, r + act*60))), 
                                          int(max(0, min(255, g + st.session_state.eb_stable*0.4))), 
                                          int(max(0, min(255, b + act*180))))
                else:
                    px_out[px, py] = px_src[px, py]

            cr.image(res_img, caption="Cascading Resonance Trace", use_container_width=True)
            
            # --- ОБНОВЛЕНИЕ ПЕТЛИ ---
            st.session_state.iteration += 1
            # dEb = (Работа витков) + (Структурный бонус от Бингла)
            eb_delta = ((work_acc / total) + (l_stats[3] / total * 0.05)) * f_fb * 1000
            st.session_state.eb_stable += eb_delta
            
            if st.session_state.eb_stable > b_limit:
                res_msg = "КОЛЛАПС: Бингл материализован!"
                st.session_state.eb_stable *= 0.1
            else:
                res_msg = "ЭКСПАНСИЯ: Резонанс выходит в витки."

            st.code(f"""[ОТЧЕТ GIDEON v2.1.0: CASCADING IGNITION]
ИТЕРАЦИЯ: {st.session_state.iteration} | СТАТУС: {res_msg}
ДИНАМИЧЕСКИЙ ПОРОГ: {dyn_threshold:.4f}

МЕТРИКИ:
- Eb (Потенциал): {st.session_state.eb_stable:.2f}
- dEb (Прирост): +{eb_delta:.4f}
- Локализация L1-L5: {list(l_stats.values())}

ЗАКЛЮЧЕНИЕ:
{"ПРОБОЙ СИНГУЛЯРНОСТИ" if sum(l_stats.values()) > l_stats[3] else "ФОРМИРОВАНИЕ ЯДРА"}
""", language="text")
