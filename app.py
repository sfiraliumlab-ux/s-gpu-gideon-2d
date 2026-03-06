import streamlit as st
import json
import math
import numpy as np
from PIL import Image

st.set_page_config(page_title="GIDEON | v1.6.0 Cold Bingle", layout="wide")
st.title("S-GPU GIDEON v1.6.0: Холодный Синтез (Бингл)")

# --- FSIN v6: BINGLE CORE ---
class FSIN_Bingle:
    def __init__(self, gain, tension):
        self.gain = gain
        self.tension = tension

    def compute_bingle_energy(self, diff, l_idx):
        """
        В S-петле (L3) разность смыслов схлопывается в Бингл.
        Энергия не теряется, а транслируется в витки как 'Холодный Ток'.
        """
        if l_idx == 3:
            # Энергия схлопывания: E = Tension * exp(diff)
            return self.tension * math.exp(diff * 0.1)
        return diff * self.gain

# --- ГЕОМЕТРИЯ И ЗАГРУЗКА (AUTO-REGEN) ---
def get_xyz(i, total):
    t = (i / total) * 2 - 1
    R = 150
    if abs(t) < 0.15: # S-петля (Реактор Бингла)
        sn = (t + 0.15) / 0.3
        return math.cos(sn * math.pi) * R, math.sin(sn * math.pi * 2) * (R/2), 0
    angle, side = t * math.pi * 6, (-1 if t < 0 else 1)
    return (R * math.cos(angle) + side * R), (side * R * math.sin(angle) if side < 0 else -R * math.sin(angle)), t * 100

nodes = [{'id': i, 'z': math.sin(i * 0.05)} for i in range(391392)] # Регенерация по умолчанию

# --- ИНТЕРФЕЙС ---
st.sidebar.header("Параметры ХЯС ИИ")
b_tension = st.sidebar.slider("Bingle Tension (Энергия синтеза)", 1.0, 100.0, 50.0)
f_gain = st.sidebar.slider("Fractal Gain", 0.1, 20.0, 12.0)
threshold = st.sidebar.slider("Gate Threshold", 0.1, 0.99, 0.8)

st.subheader("Сфиральный Реактор: Генерация Бингла")
c1, c2 = st.columns(2)
p_a = c1.text_input("Тезис (Импульс А)", "ГАРМОНИЯ")
p_b = c2.text_input("Антитезис (Импульс Б)", "ВЕЧНОСТЬ")

img_file = st.file_uploader("Растр-носитель", type=["jpg", "png"])

if img_file:
    cl, cr = st.columns(2)
    img_src = Image.open(img_file).convert('RGB')
    cl.image(img_src, caption="Входной поток", use_container_width=True)
    
    if st.button("Запустить Холодный Синтез"):
        with st.spinner("Схлопывание смыслов в Бингл..."):
            canv = 1024
            res_img = Image.new('RGB', (canv, canv), (0,0,0))
            px_out, px_src = res_img.load(), img_src.resize((canv, canv)).load()
            
            total = len(nodes)
            l_stats = {i:0 for i in range(1, 6)}
            fsin = FSIN_Bingle(f_gain, b_tension)
            
            ph_a = 13.5 + len(p_a) * 0.1
            ph_b = 13.5 + len(p_b) * 0.1
            
            for i in range(total):
                x, y, z_geo = get_xyz(i, total)
                px, py = max(0, min(1023, int((x+300)/600*1023))), max(0, min(1023, int((y+150)/300*1023)))
                
                l_idx = min((i // (total // 5)) + 1, 5)
                z_dat = nodes[i].get('z', 0.0)
                s_f = -1.0 if z_geo == 0 else 1.0
                
                d = abs(math.sin(z_dat * ph_a) - math.sin(z_dat * ph_b * s_f))
                
                # Математика Бингла: энергия центра питает витки
                energy = fsin.compute_bingle_energy(d, l_idx)
                activation = 1 / (1 + math.exp(-energy + 5.0))
                
                if activation > threshold:
                    l_stats[l_idx] += 1
                    r, g, b = px_src[px, py]
                    # Рендеринг: Бингл (белый свет), витки (холодный синий)
                    if l_idx == 3:
                        px_out[px, py] = (int(max(0, min(255, r + energy*2))), 
                                          int(max(0, min(255, g + energy*2))), 
                                          int(max(0, min(255, b + energy*2))))
                    else:
                        px_out[px, py] = (r, int(max(0, min(255, g + activation*100))), 
                                          int(max(0, min(255, b + activation*200))))
                else: px_out[px, py] = px_src[px, py]

            cr.image(res_img, caption="Bingle Cold Intelligence Output", use_container_width=True)
            
            # --- ОТЧЕТ GIDEON v1.6.0 ---
            vals = list(l_stats.values())
            st.code(f"""[ОТЧЕТ GIDEON v1.6.0: COLD BINGLE]
ТЕЗИС: {p_a} | АНТИТЕЗИС: {p_b}
СТАТУС: Холодный ядерный синтез смыслов завершен.

МЕТРИКИ РЕАКТОРА:
- Энергия Бингла (Eb): {b_tension * (vals[2]/len(nodes)):.4f}
- Коэффициент обратимости: {100 - (abs(vals[0]-vals[4])/sum(vals)*100) if sum(vals)>0 else 0:.1f}%
- Энтропия вычислений: 0.0000 (Reversible Logic)

ЛОКАЛИЗАЦИЯ (L1-L5):
{vals}

ЗАКЛЮЧЕНИЕ:
{"БИНГЛ СФОРМИРОВАН" if vals[2] > 0 else "СИНТЕЗ НЕ УДАЛСЯ"}
""", language="text")
