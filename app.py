import streamlit as st
import json
import math
import os
import numpy as np
from PIL import Image

st.set_page_config(page_title="GIDEON | Mirror Mode Analytical", layout="wide")
st.title("S-GPU GIDEON: Глубинный анализ резонанса")

@st.cache_data
def load_json_direct(filename):
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('nodes', data.get('dipoles', data)) if isinstance(data, dict) else data
        return None
    except Exception as e:
        st.error(f"Ошибка чтения {filename}: {e}")
        return None

# Статусы загрузки
nodes = load_json_direct('matrix.json')
core_dipoles = load_json_direct('Core-13.json')

if nodes:
    st.success(f"✅ VRAM активна: {len(nodes)} узлов.")
else:
    st.error("❌ matrix.json не найден."); st.stop()

if core_dipoles:
    st.sidebar.success(f"✅ Core-13 активен: {len(core_dipoles)} диполей")
else:
    st.sidebar.warning("⚠️ Эмуляция ядра")

# Панель управления
st.sidebar.header("Параметры ядра")
base_energy = st.sidebar.slider("Базовая Энергия", 0.0, 25.0, 18.0)
base_phase = st.sidebar.slider("Базовая Фаза", 0.0, 40.0, 13.5)
threshold = st.sidebar.slider("Порог сепарации", 0.1, 0.98, 0.85)

st.subheader("Дифференциальный ввод (Зеркало)")
col_in_a, col_in_b = st.columns(2)
pulse_a = col_in_a.text_input("Импульс А (Основа)", "ЖИЗНЬ")
pulse_b = col_in_b.text_input("Импульс Б (Сравнение)", "СМЕРТЬ")

def calculate_dynamic_params(text, b_e, b_p):
    vector = sum(ord(c) for c in text) * 0.001 if text else 0.0
    return b_e + (len(text) * 0.2), b_p + (vector * 1.5)

e_a, p_a = calculate_dynamic_params(pulse_a, base_energy, base_phase)
e_b, p_b = calculate_dynamic_params(pulse_b, base_energy, base_phase)

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
            side = int(math.sqrt(total))
            rows = math.ceil(total / side)
            
            diff_count = 0
            layer_diff = {1:0, 2:0, 3:0, 4:0, 5:0}
            nodes_per_layer = total // 5
            
            for i in range(total):
                c_idx, r_idx = i % side, i // side
                px, py = max(0, min(1023, int((c_idx/side)*1023))), max(0, min(1023, int((r_idx/rows)*1023)))
                
                z = nodes[i].get('z', 0.0) if isinstance(nodes[i], dict) else 0.0
                
                int_a = e_a * math.sin(z * p_a)
                int_b = e_b * math.sin(z * p_b)
                diff_signal = abs(int_a - int_b)
                
                if diff_signal > (base_energy * threshold):
                    diff_count += 1
                    layer_diff[min((i // nodes_per_layer) + 1, 5)] += 1
                    
                    r, g, b = rgb_map[px, py]
                    new_r = int(max(0, min(255, r - diff_signal * 5)))
                    new_g = int(max(0, min(255, g + diff_signal * 10)))
                    new_b = int(max(0, min(255, b + diff_signal * 15)))
                else:
                    new_r, new_g, new_b = rgb_map[px, py]
                
                for dx in range(2):
                    for dy in range(2):
                        if px+dx < 1024 and py+dy < 1024:
                            output_pixels[px+dx, py+dy] = (new_r, new_g, new_b)
            
            col2.image(output_img, caption=f"Аналитика: {pulse_a} vs {pulse_b}", use_container_width=True)
            
            # РАСЧЕТ ОБЪЕКТИВНЫХ МЕТРИК
            diff_pct = (diff_count / total) * 100
            coherence = 100 - diff_pct # Коэффициент когерентности
            
            # Индекс девиации (стандартное отклонение активности слоев)
            vals = list(layer_diff.values())
            deviation = np.std(vals) / np.mean(vals) if np.mean(vals) > 0 else 0
            
            st.code(f"""[ОТЧЕТ GIDEON: ANALYTICAL MIRROR]
Сравнение: {pulse_a} / {pulse_b}
Уникальных узлов разности: {diff_count} ({diff_pct:.1f}%)
Коэффициент когерентности (Kc): {coherence:.1f}%
Индекс девиации слоев (Di): {deviation:.4f}

ЛОКАЛИЗАЦИЯ РАЗЛИЧИЙ ПО СЛОЯМ:
L1: {layer_diff[1]} | L2: {layer_diff[2]} | L3: {layer_diff[3]} | L4: {layer_diff[4]} | L5: {layer_diff[5]}
""", language="text")
