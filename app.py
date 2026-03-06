import streamlit as st
import json
import math
import os
import numpy as np
from PIL import Image

st.set_page_config(page_title="GIDEON | Robust Analytical", layout="wide")
st.title("S-GPU GIDEON: Глубинный анализ резонанса")

# --- УЛУЧШЕННЫЙ БЛОК ЗАГРУЗКИ ---
@st.cache_data
def load_json_robust(filename, uploaded_file=None):
    """Загрузка с защитой от поврежденных структур"""
    try:
        if uploaded_file:
            data = json.load(uploaded_file)
        elif os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            return None
        
        if isinstance(data, dict):
            return data.get('nodes', data.get('dipoles', data))
        return data
    except json.JSONDecodeError as je:
        st.error(f"❌ Файл {filename} поврежден: {je.msg} (строка {je.lineno})")
        return "CORRUPTED"
    except Exception as e:
        st.error(f"❌ Ошибка доступа: {e}")
        return None

# Инициализация VRAM
nodes = load_json_robust('matrix.json')
core_dipoles = load_json_robust('Core-13.json')

if nodes == "CORRUPTED" or nodes is None:
    st.warning("⚠️ VRAM в репозитории повреждена или отсутствует. Требуется ручная перезагрузка.")
    manual_vram = st.file_uploader("Загрузить исправный matrix.json", type=["json"])
    if manual_vram:
        nodes = load_json_robust('manual', manual_vram)
    else:
        st.stop()

# Статусы в сайдбаре
if core_dipoles and core_dipoles != "CORRUPTED":
    st.sidebar.success(f"✅ Core-13: {len(core_dipoles)} диполей")
else:
    st.sidebar.warning("⚠️ Core-13 в режиме эмуляции")

# --- ПАНЕЛЬ УПРАВЛЕНИЯ ---
st.sidebar.header("Параметры ядра")
base_energy = st.sidebar.slider("Базовая Энергия", 0.0, 25.0, 18.0)
base_phase = st.sidebar.slider("Базовая Фаза", 0.0, 40.0, 13.5)
threshold = st.sidebar.slider("Порог сепарации", 0.1, 0.98, 0.85)

st.subheader("Дифференциальный ввод (Зеркало)")
col_in_a, col_in_b = st.columns(2)
pulse_a = col_in_a.text_input("Импульс А (Основа)", "ЖИЗНЬ")
pulse_b = col_in_b.text_input("Импульс Б (Сравнение)", "СМЕРТЬ")

def get_p(text, b_e, b_p):
    v = sum(ord(c) for c in text) * 0.001 if text else 0.0
    return b_e + (len(text) * 0.2), b_p + (v * 1.5)

e_a, p_a = get_p(pulse_a, base_energy, base_phase)
e_b, p_b = get_p(pulse_b, base_energy, base_phase)

image_file = st.file_uploader("Загрузите растровый источник", type=["jpg", "jpeg", "png"])

if image_file is not None:
    col1, col2 = st.columns(2)
    orig_img = Image.open(image_file).convert('RGB')
    col1.image(orig_img, caption="Входной сигнал (Preview)", use_container_width=True)
    
    if st.button("Запустить аналитический резонанс"):
        with st.spinner("Синхронизация диполей..."):
            canvas_size = 1024
            output_img = Image.new('RGB', (canvas_size, canvas_size), (0, 0, 0))
            output_pixels = output_img.load()
            rgb_map = orig_img.resize((canvas_size, canvas_size)).load()
            
            total = len(nodes)
            side, rows = int(math.sqrt(total)), math.ceil(total / int(math.sqrt(total)))
            diff_count, layer_diff = 0, {1:0, 2:0, 3:0, 4:0, 5:0}
            
            for i in range(total):
                px = max(0, min(1023, int(((i % side) / side) * 1023)))
                py = max(0, min(1023, int(((i // side) / rows) * 1023)))
                z = nodes[i].get('z', 0.0) if isinstance(nodes[i], dict) else 0.0
                
                int_a = e_a * math.sin(z * p_a)
                int_b = e_b * math.sin(z * p_b)
                diff = abs(int_a - int_b)
                
                if diff > (base_energy * threshold):
                    diff_count += 1
                    layer_diff[min((i // (total // 5)) + 1, 5)] += 1
                    r, g, b = rgb_map[px, py]
                    output_pixels[px, py] = (int(max(0, min(255, r - diff*5))), 
                                             int(max(0, min(255, g + diff*10))), 
                                             int(max(0, min(255, b + diff*15))))
                else:
                    output_pixels[px, py] = rgb_map[px, py]

            col2.image(output_img, caption="Результат сепарации", use_container_width=True)
            
            # Аналитика
            diff_pct = (diff_count / total) * 100
            kc = 100 - diff_pct
            vals = list(layer_diff.values())
            di = np.std(vals) / np.mean(vals) if np.mean(vals) > 0 else 0
            
            st.code(f"""[ОТЧЕТ GIDEON: ANALYTICAL MIRROR]
Сравнение: {pulse_a} / {pulse_b}
Разница: {diff_pct:.1f}% | Kc: {kc:.1f}% | Di: {di:.4f}
ЛОКАЛИЗАЦИЯ (L1-L5): {list(layer_diff.values())}""", language="text")
