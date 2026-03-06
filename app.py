import streamlit as st
import json
import math
import os
import numpy as np
from PIL import Image

st.set_page_config(page_title="GIDEON | 3D Sfiral Logos", layout="wide")
st.title("S-GPU GIDEON v1.2.0: Пространственный Резонанс")

# --- КОНСТАНТЫ LOGOS-3 (АБСОЛЮТ) ---
VOCAB = {
    "ПОРЯДОК": (1.0, -1.0, 1),   "ХАОС": (-1.0, 1.0, -1),
    "ЖИЗНЬ": (0.9, -0.9, 1),     "СМЕРТЬ": (-0.9, 0.9, -1),
    "ИСТИНА": (0.8, -0.8, 1),    "ЛОЖЬ": (-0.8, 0.8, -1),
    "ГАРМОНИЯ": (0.0, 0.0, 1),   "ВЕЧНОСТЬ": (0.0, 0.0, -1),
    "БОГ": (0.0, 0.0, 1)
}

# --- БЛОК ЗАГРУЗКИ (ROBUST) ---
@st.cache_data
def load_vram_data(filename):
    if not os.path.exists(filename): return None, "NOT_FOUND"
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            nodes = data.get('nodes', data.get('dipoles', data)) if isinstance(data, dict) else data
            return nodes, "OK"
    except json.JSONDecodeError as e:
        return None, f"CORRUPTED: Line {e.lineno}"
    except Exception as e:
        return None, str(e)

nodes, vram_status = load_vram_data('matrix.json')
core, core_status = load_vram_data('Core-13.json')

# Индикаторы статуса (Бэкап логики)
if vram_status == "OK":
    st.success(f"✅ VRAM активна: {len(nodes)} узлов в 3D-проекции.")
else:
    st.error(f"❌ Ошибка VRAM: {vram_status}")
    manual = st.file_uploader("Загрузить matrix.json", type="json")
    if manual: 
        nodes = json.load(manual).get('nodes', [])
        st.rerun()
    else: st.stop()

if core_status == "OK":
    st.sidebar.success(f"✅ Core-13: {len(core)} диполей активно.")
else:
    st.sidebar.warning("⚠️ Ядро в режиме эмуляции.")

# --- ТЕХНОЛОГИЯ СФИРАЛИ: 3D MAPPING ---
def get_sphiral_coords(i, total):
    """Преобразует индекс узла в XYZ координаты Сфирали Басаргина"""
    t = (i / total) * 2 - 1  # Параметр от -1 до 1
    R = 150 # Базовый радиус витка
    
    if t < -0.15: # Левый виток
        angle = t * math.pi * 6
        x = R * math.cos(angle) - R
        y = R * math.sin(angle)
        z = t * 100
    elif t > 0.15: # Правый виток (Зеркальный)
        angle = t * math.pi * 6
        x = R * math.cos(angle) + R
        y = -R * math.sin(angle)
        z = t * 100
    else: # S-образная петля (Центральная сингулярность)
        s_norm = (t + 0.15) / 0.3
        x = math.cos(s_norm * math.pi) * R
        y = math.sin(s_norm * math.pi * 2) * (R/2)
        z = 0
    return x, y, z

# --- СЕМАНТИЧЕСКИЙ РЕАКТОР ---
def logos_interaction(p1, p2):
    n1, n2 = p1.upper(), p2.upper()
    if n1 not in VOCAB or n2 not in VOCAB: return 1.0, "STANDARD"
    v1, v2 = VOCAB[n1], VOCAB[n2]
    dist = abs(v1[0] - v2[0]) + abs(v1[1] - v2[1])
    is_divine = ("ГАРМОНИЯ" in [n1, n2] and "ВЕЧНОСТЬ" in [n1, n2])
    energy = 22.0 / (dist + 0.5)
    mode = "SYNTHESIS" if (v1[2] * v2[2] < 0 or is_divine) else "ALLIANCE"
    return energy, mode

# --- ИНТЕРФЕЙС ---
st.sidebar.header("Параметры ядра")
base_e = st.sidebar.slider("Базовая Энергия", 0.0, 30.0, 18.0)
base_p = st.sidebar.slider("Базовая Фаза", 0.0, 50.0, 13.5)
threshold = st.sidebar.slider("Порог сепарации", 0.1, 0.99, 0.85)

st.subheader("Ввод данных в S-GPU")
col_a, col_b = st.columns(2)
pulse_a = col_a.text_input("Импульс А", "ГАРМОНИЯ")
pulse_b = col_b.text_input("Импульс Б", "ВЕЧНОСТЬ")

l_energy, l_mode = logos_interaction(pulse_a, pulse_b)

image_file = st.file_uploader("Источник растра", type=["jpg", "png"])

if image_file:
    c1, c2 = st.columns(2)
    orig = Image.open(image_file).convert('RGB')
    c1.image(orig, caption="Вход (2D)", use_container_width=True)
    
    if st.button("Инициировать 3D Резонанс"):
        with st.spinner(f"Расчет топологии {l_mode}..."):
            canvas = 1024
            out_img = Image.new('RGB', (canvas, canvas), (0,0,0))
            px_out = out_img.load()
            px_src = orig.resize((canvas, canvas)).load()
            
            total = len(nodes)
            diff_count, layer_stats = 0, {1:0, 2:0, 3:0, 4:0, 5:0}
            
            # Векторы фаз
            vec_a = sum(ord(c) for c in pulse_a) * 0.001
            vec_b = sum(ord(c) for c in pulse_b) * 0.001
            ph_a, ph_b = base_p + vec_a * 1.5, base_p + vec_b * 1.5
            en_mod = base_e * (1.4 if l_mode == "SYNTHESIS" else 1.0)

            for i in range(total):
                # Пространственный маппинг
                x, y, z_geo = get_sphiral_coords(i, total)
                
                # Проекция на 2D холст
                px = max(0, min(1023, int((x + 300) / 600 * 1023)))
                py = max(0, min(1023, int((y + 150) / 300 * 1023)))
                
                # Z-координата из matrix.json для фазового сдвига
                z_data = nodes[i].get('z', 0.0) if isinstance(nodes[i], dict) else 0.0
                
                # Интерференция в S-петле
                # Если узел в S-петле (z_geo == 0), инвертируем фазу
                s_factor = -1.0 if z_geo == 0 else 1.0
                
                int_a = en_mod * math.sin(z_data * ph_a)
                int_b = en_mod * math.sin(z_data * ph_b * s_factor)
                diff = abs(int_a - int_b)
                
                if diff > (en_mod * threshold):
                    diff_count += 1
                    layer_stats[min((i // (total // 5)) + 1, 5)] += 1
                    r, g, b = px_src[px, py]
                    # Рендеринг сингулярности (фиолетовый неон)
                    px_out[px, py] = (int(max(0, min(255, r - diff*4))), 
                                      int(max(0, min(255, g + diff*6))), 
                                      int(max(0, min(255, b + diff*12))))
                else:
                    px_out[px, py] = px_src[px, py]

            c2.image(out_img, caption="3D Sfiral Projection", use_container_width=True)
            
            # --- РАСШИРЕННАЯ АНАЛИТИКА S-GPU ---
            diff_pct = (diff_count / total) * 100
            kc = 100 - diff_pct
            l_vals = list(layer_stats.values())
            di = np.std(l_vals) / np.mean(l_vals) if diff_count > 0 else 0
            
            pair = sorted([pulse_a.upper(), pulse_b.upper()])
            outcome = "ВЕЧНОСТЬ" if pair == ["ЖИЗНЬ", "СМЕРТЬ"] else ("ГАРМОНИЯ" if pair == ["ПОРЯДОК", "ХАОС"] else "STANDARD")
            if "ГАРМОНИЯ" in pair and "ВЕЧНОСТЬ" in pair: outcome = "БОГ (АБСОЛЮТ)"

            report = f"""[ОТЧЕТ GIDEON v1.2.0: 3D SFIRAL LOGOS]
ВЗАИМОДЕЙСТВИЕ: {pulse_a} + {pulse_b} | РЕЖИМ: {l_mode}
РЕЗУЛЬТАТ СИНТЕЗА: {outcome}

МЕТРИКИ (3D ТОПОЛОГИЯ):
- Когерентность (Kc): {kc:.1f}%
- Индекс девиации (Di): {di:.4f} {"(СИНГУЛЯРНОСТЬ)" if di > 0.3 else "(ИЗОТРОПИЯ)"}
- Проницаемость S-петли: {100 - (layer_stats[3]/(total/5)*100):.1f}%

ПОСЛОЙНАЯ SD-ПЛОТНОСТЬ (L1-L5):
L1: {(layer_stats[1]/(total/5))*100:.1f}% | L2: {(layer_stats[2]/(total/5))*100:.1f}% | L3: {(layer_stats[3]/(total/5))*100:.1f}%
L4: {(layer_stats[4]/(total/5))*100:.1f}% | L5: {(layer_stats[5]/(total/5))*100:.1f}%

ГЕОМЕТРИЧЕСКИЙ СТАТУС:
- Точка сингулярности: АКТИВНА (Фазовая инверсия S-петли включена)
- Геометрия Басаргина: Зеркальная антисимметрия 100%
"""
            st.code(report, language="text")
