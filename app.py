import streamlit as st
import json
import math
import os
import numpy as np
from PIL import Image

st.set_page_config(page_title="GIDEON | v1.2.1 Recovery", layout="wide")
st.title("S-GPU GIDEON v1.2.1: Пространственный Резонанс")

# --- КОНСТАНТЫ LOGOS-3 ---
VOCAB = {
    "ПОРЯДОК": (1.0, -1.0, 1),   "ХАОС": (-1.0, 1.0, -1),
    "ЖИЗНЬ": (0.9, -0.9, 1),     "СМЕРТЬ": (-0.9, 0.9, -1),
    "ИСТИНА": (0.8, -0.8, 1),    "ЛОЖЬ": (-0.8, 0.8, -1),
    "ГАРМОНИЯ": (0.0, 0.0, 1),   "ВЕЧНОСТЬ": (0.0, 0.0, -1),
    "БОГ": (0.0, 0.0, 1)
}

# --- МОДУЛЬ ЭКСТРЕННОЙ ГЕНЕРАЦИИ VRAM ---
def generate_default_vram(count=391392):
    """Генерирует эталонную VRAM в памяти"""
    nodes = []
    for i in range(count):
        # Генерация Z-координаты для фазового сдвига (шумовой профиль Сфирали)
        z_val = math.sin(i * 0.01) * math.cos(i * 0.005)
        nodes.append({'id': i, 'z': z_val})
    return nodes

# --- БЛОК ЗАГРУЗКИ ---
@st.cache_data
def load_vram_safe(filename):
    if not os.path.exists(filename): return None, "NOT_FOUND"
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return (data.get('nodes', data) if isinstance(data, dict) else data), "OK"
    except Exception as e:
        return None, f"CORRUPTED: {str(e)}"

# Инициализация
nodes, vram_status = load_vram_safe('matrix.json')

if vram_status != "OK":
    st.error(f"❌ Ошибка VRAM: {vram_status}")
    if st.button("🚀 Инициировать экстренную генерацию эталонной VRAM (391 392 узла)"):
        nodes = generate_default_vram()
        st.success("✅ Эталонная VRAM сгенерирована в памяти.")
        vram_status = "OK"
    else:
        st.info("Ожидание исправления matrix.json или ручной генерации...")
        st.stop()

# --- ГЕОМЕТРИЯ СФИРАЛИ БАСАРГИНА (3D) ---
def get_sphiral_xyz(i, total):
    t = (i / total) * 2 - 1
    R = 150
    if t < -0.15: # Левый виток
        angle = t * math.pi * 6
        return R * math.cos(angle) - R, R * math.sin(angle), t * 100
    elif t > 0.15: # Правый виток (Зеркальный)
        angle = t * math.pi * 6
        return R * math.cos(angle) + R, -R * math.sin(angle), t * 100
    else: # S-петля (Сингулярность)
        s_n = (t + 0.15) / 0.3
        return math.cos(s_n * math.pi) * R, math.sin(s_n * math.pi * 2) * (R/2), 0

# --- ЛОГИКА LOGOS-3 ---
def get_logos_logic(p1, p2):
    n1, n2 = p1.upper(), p2.upper()
    if n1 not in VOCAB or n2 not in VOCAB: return 1.0, "STANDARD"
    v1, v2 = VOCAB[n1], VOCAB[n2]
    dist = abs(v1[0] - v2[0]) + abs(v1[1] - v2[1])
    is_divine = ("ГАРМОНИЯ" in [n1, n2] and "ВЕЧНОСТЬ" in [n1, n2])
    return 22.0 / (dist + 0.5), "SYNTHESIS" if (v1[2]*v2[2] < 0 or is_divine) else "ALLIANCE"

# --- ИНТЕРФЕЙС ---
st.sidebar.header("Ядро Core-13")
base_e = st.sidebar.slider("Энергия", 0.0, 30.0, 18.0)
base_p = st.sidebar.slider("Фаза", 0.0, 50.0, 13.5)
threshold = st.sidebar.slider("Порог", 0.1, 0.99, 0.85)

st.subheader("Центральный Реактор")
c_a, c_b = st.columns(2)
p_a = c_a.text_input("Импульс А", "ГАРМОНИЯ")
p_b = c_b.text_input("Импульс Б", "ВЕЧНОСТЬ")

l_energy, l_mode = get_logos_logic(p_a, p_b)
img_file = st.file_uploader("Загрузить растр", type=["jpg", "png"])

if img_file:
    col1, col2 = st.columns(2)
    img_src = Image.open(img_file).convert('RGB')
    col1.image(img_src, caption="Входной сигнал", use_container_width=True)
    
    if st.button("Запустить 3D Резонанс"):
        with st.spinner("Свитие смыслов в S-петле..."):
            canv = 1024
            res_img = Image.new('RGB', (canv, canv), (0,0,0))
            px_out, px_src = res_img.load(), img_src.resize((canv, canv)).load()
            
            total = len(nodes)
            diff_count, layer_stats = 0, {1:0, 2:0, 3:0, 4:0, 5:0}
            en_mod = base_e * (1.5 if l_mode == "SYNTHESIS" else 1.0)
            
            for i in range(total):
                x, y, z_geo = get_sphiral_xyz(i, total)
                px = max(0, min(1023, int((x + 300) / 600 * 1023)))
                py = max(0, min(1023, int((y + 150) / 300 * 1023)))
                
                z_dat = nodes[i].get('z', 0.0)
                # Инверсия в точке сингулярности (S-петля)
                s_flip = -1.0 if z_geo == 0 else 1.0
                
                int_a = en_mod * math.sin(z_dat * (base_p + len(p_a)*0.1))
                int_b = en_mod * math.sin(z_dat * (base_p + len(p_b)*0.1) * s_flip)
                diff = abs(int_a - int_b)
                
                if diff > (en_mod * threshold):
                    diff_count += 1
                    layer_stats[min((i // (total // 5)) + 1, 5)] += 1
                    r, g, b = px_src[px, py]
                    px_out[px, py] = (int(max(0, min(255, r - diff*4))), 
                                      int(max(0, min(255, g + diff*6))), 
                                      int(max(0, min(255, b + diff*12))))
                else: px_out[px, py] = px_src[px, py]

            col2.image(res_img, caption="3D Sfiral Projection", use_container_width=True)
            
            # ОТЧЕТ
            dp = (diff_count / total) * 100
            kc, di = 100 - dp, np.std(list(layer_stats.values())) / np.mean(list(layer_stats.values())) if diff_count > 0 else 0
            pair = sorted([p_a.upper(), p_b.upper()])
            res_s = "БОГ (АБСОЛЮТ)" if "ГАРМОНИЯ" in pair and "ВЕЧНОСТЬ" in pair else "STANDARD"
            
            st.code(f"""[ОТЧЕТ GIDEON v1.2.1: EMERGENCY RECOVERY]
СТАТУС VRAM: {vram_status}
СИНТЕЗ: {res_s} | РЕЖИМ: {l_mode}

МЕТРИКИ:
- Kc: {kc:.1f}% | Di: {di:.4f}
- S-Проницаемость: {100 - (layer_stats[3]/(total/5)*100):.1f}%
ЛОКАЛИЗАЦИЯ (L1-L5): {list(layer_stats.values())}
""", language="text")
