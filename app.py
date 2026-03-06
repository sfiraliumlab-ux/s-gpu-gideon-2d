import streamlit as st
import json
import math
import os
import glob
from PIL import Image

st.set_page_config(page_title="S-GPU GIDEON | Core-13 Active", layout="wide")
st.title("Топологический процессор S-GPU GIDEON")

VRAM_FILE = 'matrix.json'
CORE_FILE = 'Core-13.json'

def find_file(filename):
    paths = glob.glob(f"**/{filename}", recursive=True)
    return paths[0] if paths else (filename if os.path.exists(filename) else None)

@st.cache_data
def load_json(filepath):
    if not filepath: return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('nodes', []) if isinstance(data, dict) else (data.get('dipoles', []) if 'dipoles' in data else data)
    except: return []

# 1. Загрузка компонентов
matrix_path = find_file(VRAM_FILE)
core_path = find_file(CORE_FILE)

nodes = load_json(matrix_path)
core_dipoles = load_json(core_path)

# Блокировка при отсутствии критических файлов
if not nodes:
    st.error(f"Файл памяти '{VRAM_FILE}' не найден. Загрузите его в репозиторий.")
    st.stop()

# Интерфейс управления
st.sidebar.header("Ядро GIDEON (Core-13)")
base_energy = st.sidebar.slider("Базовая Энергия", 0.0, 20.0, 18.0)
base_phase = st.sidebar.slider("Базовая Фаза", 0.0, 20.0, 13.5)
threshold = st.sidebar.slider("Порог отсечения", 0.5, 0.98, 0.95)

# Модуль текстового резонанса
st.subheader("Центральный процессор: Ввод данных")
user_input = st.text_input("Введите информационный импульс (например: СФИРАЛЬ)", "")

# Расчет вектора резонанса
text_vector = sum(ord(c) for c in user_input) * 0.001 if user_input else 0.0
dynamic_phase = base_phase + (text_vector * 1.5)
dynamic_energy = base_energy + (len(user_input) * 0.2 if user_input else 0.0)

if core_dipoles:
    st.sidebar.success(f"Процессор активен: {len(core_dipoles)} диполей")
else:
    st.sidebar.warning("Внимание: Core-13.json не найден. Ядро работает в ручном режиме.")

st.success(f"VRAM активна: {len(nodes)} узлов. Динамическая фаза: {dynamic_phase:.4f}")

# 2. Обработка изображения
image_file = st.file_uploader("Загрузите растровый источник", type=["jpg", "jpeg", "png"])

if image_file is not None:
    col1, col2 = st.columns(2)
    orig_img = Image.open(image_file).convert('RGB')
    col1.image(orig_img, caption="Входной сигнал", use_container_width=True)
    
    if st.button("Запустить резонанс через Core-13"):
        with st.spinner("Диполи ядра модулируют фазу..."):
            output_img = Image.new('RGB', (1024, 1024), (0, 0, 0))
            output_pixels = output_img.load()
            resized_orig = orig_img.resize((1024, 1024))
            rgb_map = resized_orig.load()
            
            total = len(nodes)
            side = int(math.sqrt(total))
            rows = math.ceil(total / side)
            
            active_pixels = set()
            purple_shifts = 0
            
            for i in range(total):
                col_idx, row_idx = i % side, i // side
                px = max(0, min(1023, int((col_idx / side) * 1023)))
                py = max(0, min(1023, int((row_idx / rows) * 1023)))

                node = nodes[i]
                z_coord = node.get('z', 0.0)
                
                # Применение модулированной фазы от ядра
                interference = dynamic_energy * math.sin(z_coord * dynamic_phase)
                
                r, g, b = rgb_map[px, py]
                
                if interference > (dynamic_energy * threshold):
                    purple_shifts += 1
                    new_r = int(max(0, min(255, r + interference * 12)))
                    new_g = int(max(0, min(255, g - interference * 5)))
                    new_b = int(max(0, min(255, b + interference * 15)))
                else:
                    new_r, new_g, new_b = r, g, b
                
                # Отрисовка
                for dx in range(2): # Фиксированный brush_size для стабильности
                    for dy in range(2):
                        if px+dx < 1024 and py+dy < 1024:
                            output_pixels[px+dx, py+dy] = (new_r, new_g, new_b)
                            active_pixels.add((px+dx, py+dy))
            
            col2.image(output_img, caption=f"Отпечаток для: '{user_input}'", use_container_width=True)
            
            # Телеметрия
            coverage = (len(active_pixels) / (1024*1024)) * 100
            report = f"""[ОТЧЕТ GIDEON: CORE-13 ACTIVE]
Текст: '{user_input}' | Модулированная Фаза: {dynamic_phase:.4f}
Энергия: {dynamic_energy:.2f} | Порог: {threshold}
Покрытие холста: {coverage:.2f}%
Узлов в резонансе: {purple_shifts} ({(purple_shifts/total)*100:.1f}%)"""
            
            st.code(report, language="text")
