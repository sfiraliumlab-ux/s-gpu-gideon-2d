import streamlit as st
import json
import math
import os
from PIL import Image

st.set_page_config(page_title="GIDEON | Mirror Mode Stable", layout="wide")
st.title("S-GPU GIDEON: Дифференциальный анализ (Mirror)")

# --- ЛОГИКА ЗАГРУЗКИ ---
def get_path(filename):
    """Поиск файла в корне или по пути скрипта"""
    if os.path.exists(filename):
        return filename
    base = os.path.dirname(os.path.abspath(__file__))
    full = os.path.join(base, filename)
    return full if os.path.exists(full) else None

@st.cache_data
def load_json(filename):
    path = get_path(filename)
    if not path: return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('nodes', data.get('dipoles', [])) if isinstance(data, dict) else data
    except: return None

# Загрузка и индикаторы (ВОССТАНОВЛЕНО)
nodes = load_json('matrix.json')
core_dipoles = load_json('Core-13.json')

if nodes:
    st.success(f"✅ VRAM активна: {len(nodes)} узлов загружено из репозитария.")
else:
    st.error("❌ Критическая ошибка: 'matrix.json' не найден. Загрузите файл в корень.")
    st.stop()

if core_dipoles:
    st.sidebar.success(f"✅ Процессор Core-13: {len(core_dipoles)} диполей активно.")
else:
    st.sidebar.warning("⚠️ Core-13.json не найден. Ядро в режиме эмуляции.")

# --- ИНТЕРФЕЙС ---
st.sidebar.header("Параметры ядра")
base_energy = st.sidebar.slider("Базовая Энергия", 0.0, 25.0, 18.0)
base_phase = st.sidebar.slider("Базовая Фаза", 0.0, 40.0, 13.5)
# Рекомендованный порог для ЖИЗНЬ/СМЕРТЬ: 0.85
threshold = st.sidebar.slider("Порог сепарации", 0.1, 0.98, 0.85)

st.subheader("Дифференциальный ввод (Зеркало)")
col_in_a, col_in_b = st.columns(2)
pulse_a = col_in_a.text_input("Импульс А (Основа)", "ЖИЗНЬ")
pulse_b = col_in_b.text_input("Импульс Б (Сравнение)", "СМЕРТЬ")

def get_params(text, b_e, b_p):
    vector = sum(ord(c) for c in text) * 0.001 if text else 0.0
    return b_e + (len(text) * 0.2), b_p + (vector * 1.5)

e_a, p_a = get_params(pulse_a, base_energy, base_phase)
e_b, p_b = get_params(pulse_b, base_energy, base_phase)

image_file = st.file_uploader("Загрузите растровый источник", type=["jpg", "jpeg", "png"])

if image_file is not None:
    col1, col2 = st.columns(2)
    orig_img = Image.open(image_file).convert('RGB')
    
    # ПРЕВЬЮ (ВОССТАНОВЛЕНО - вне блока кнопки)
    col1.image(orig_img, caption="Входной сигнал (Preview)", use_container_width=True)
    
    if st.button("Запустить дифференциальный резонанс"):
        with st.spinner("Вычисление топологической разности..."):
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
                px = max(0, min(1023, int((c_idx/side)*1023)))
                py = max(0, min(1023, int((r_idx/rows)*1023)))
                
                z = nodes[i].get('z', 0.0) if isinstance(nodes[i], dict) else 0.0
                
                # Математика Зеркала
                int_a = e_a * math.sin(z * p_a)
                int_b = e_b * math.sin(z * p_b)
                diff_signal = abs(int_a - int_b)
                
                if diff_signal > (base_energy * threshold):
                    diff_count += 1
                    layer_diff[min((i // nodes_per_layer) + 1, 5)] += 1
                    
                    r, g, b = rgb_map[px, py]
                    # Спектральная окраска разности
                    new_r = int(max(0, min(255, r - diff_signal * 5)))
                    new_g = int(max(0, min(255, g + diff_signal * 10)))
                    new_b = int(max(0, min(255, b + diff_signal * 15)))
                else:
                    new_r, new_g, new_b = rgb_map[px, py]
                
                for dx in range(2):
                    for dy in range(2):
                        if px+dx < 1024 and py+dy < 1024:
                            output_pixels[px+dx, py+dy] = (new_r, new_g, new_b)
            
            col2.image(output_img, caption=f"Разница: {pulse_a} vs {pulse_b}", use_container_width=True)
            
            # ОТЧЕТ (ВОССТАНОВЛЕНО)
            st.code(f"""[ОТЧЕТ GIDEON: MIRROR MODE]
Сравнение: {pulse_a} / {pulse_b}
Уникальных узлов разности: {diff_count} ({(diff_count/total)*100:.1f}%)

ЛОКАЛИЗАЦИЯ РАЗЛИЧИЙ ПО СЛОЯМ ВЛОЖЕННОСТИ:
L1 (Поверхность): {layer_diff[1]}
L2 (Транзит):    {layer_diff[2]}
L3 (Медиана):    {layer_diff[3]}
L4 (Глубина):    {layer_diff[4]}
L5 (Ядро VRAM):  {layer_diff[5]}""", language="text")
