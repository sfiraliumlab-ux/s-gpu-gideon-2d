import streamlit as st
import json
import math
import os
from PIL import Image

st.set_page_config(page_title="GIDEON | Mirror Mode Stable", layout="wide")
st.title("S-GPU GIDEON: Дифференциальный анализ (Mirror)")

def get_file_path(filename):
    """Поиск файла в текущей директории или директории скрипта"""
    # Вариант 1: Текущая рабочая директория
    if os.path.exists(filename):
        return filename
    # Вариант 2: Директория, где лежит app.py
    base_path = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_path, filename)
    if os.path.exists(full_path):
        return full_path
    return None

@st.cache_data
def load_json_data(filename):
    path = get_file_path(filename)
    if not path:
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data.get('nodes', data.get('dipoles', []))
            return data
    except Exception as e:
        st.error(f"Ошибка чтения {filename}: {e}")
        return None

# Загрузка компонентов
nodes = load_json_data('matrix.json')
core_dipoles = load_json_data('Core-13.json')

if nodes is None:
    st.error("Критическая ошибка: Файл 'matrix.json' не найден. Проверьте корень репозитория.")
    st.info(f"Список файлов в доступе: {os.listdir('.')}")
    st.stop()

# Панель управления
st.sidebar.header("Параметры ядра")
base_energy = st.sidebar.slider("Базовая Энергия", 0.0, 25.0, 18.0)
base_phase = st.sidebar.slider("Базовая Фаза", 0.0, 40.0, 13.5)
# Для сепарации ЖИЗНЬ/СМЕРТЬ рекомендовано 0.85
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

# Работа с изображением
image_file = st.file_uploader("Загрузите растровый источник", type=["jpg", "jpeg", "png"])

if image_file is not None:
    col1, col2 = st.columns(2)
    orig_img = Image.open(image_file).convert('RGB')
    # Превью отображается сразу после загрузки
    col1.image(orig_img, caption="Входной сигнал (Preview)", use_container_width=True)
    
    if st.button("Запустить дифференциальный резонанс"):
        with st.spinner("Вычисление топологической разности..."):
            canvas_size = 1024
            output_img = Image.new('RGB', (canvas_size, canvas_size), (0, 0, 0))
            output_pixels = output_img.load()
            rgb_map = orig_img.resize((canvas_size, canvas_size)).load()
            
            total_nodes = len(nodes)
            side = int(math.sqrt(total_nodes))
            rows = math.ceil(total_nodes / side)
            
            diff_count = 0
            layer_diff = {1:0, 2:0, 3:0, 4:0, 5:0}
            nodes_per_layer = total_nodes // 5
            
            for i in range(total_nodes):
                c_idx, r_idx = i % side, i // side
                px = max(0, min(1023, int((c_idx/side)*1023)))
                py = max(0, min(1023, int((r_idx/rows)*1023)))
                
                z = nodes[i].get('z', 0.0) if isinstance(nodes[i], dict) else 0.0
                
                int_a = e_a * math.sin(z * p_a)
                int_b = e_b * math.sin(z * p_b)
                diff_signal = abs(int_a - int_b)
                
                if diff_signal > (base_energy * threshold):
                    diff_count += 1
                    layer_diff[min((i // nodes_per_layer) + 1, 5)] += 1
                    
                    r, g, b = rgb_map[px, py]
                    # Сдвиг в бирюзово-фиолетовый спектр для визуализации разности
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
            
            # Отчет
            st.code(f"""[ОТЧЕТ GIDEON: MIRROR MODE]
Сравнение: {pulse_a} / {pulse_b}
Уникальных узлов разности: {diff_count} ({(diff_count/total_nodes)*100:.1f}%)

ЛОКАЛИЗАЦИЯ РАЗЛИЧИЙ ПО СЛОЯМ ВЛОЖЕННОСТИ:
L1 (Поверхность): {layer_diff[1]}
L2 (Транзит):    {layer_diff[2]}
L3 (Медиана):    {layer_diff[3]}
L4 (Глубина):    {layer_diff[4]}
L5 (Ядро VRAM):  {layer_diff[5]}""", language="text")
