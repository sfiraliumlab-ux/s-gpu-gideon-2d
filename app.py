import streamlit as st
import json
import math
import os
from PIL import Image

st.set_page_config(page_title="S-GPU GIDEON | Final Stable", layout="wide")
st.title("Топологический процессор S-GPU GIDEON")

# --- ПРЯМАЯ ЗАГРУЗКА ИЗ КОРНЯ ---
def load_vram_and_core():
    vram_data = None
    core_data = None
    
    # Прямые пути (согласно списку файлов сервера)
    vram_path = os.path.join(os.getcwd(), 'matrix.json')
    core_path = os.path.join(os.getcwd(), 'Core-13.json')

    try:
        if os.path.exists(vram_path):
            with open(vram_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                vram_data = data.get('nodes', data) if isinstance(data, dict) else data
        
        if os.path.exists(core_path):
            with open(core_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                core_data = data.get('dipoles', data) if isinstance(data, dict) else data
    except Exception as e:
        st.error(f"Ошибка при чтении файлов: {e}")
        
    return vram_data, core_data

nodes, core_dipoles = load_vram_and_core()

# Проверка состояния системы
if nodes is None:
    st.error("Критическая ошибка: 'matrix.json' виден в системе, но не может быть прочитан.")
    st.stop()

if core_dipoles is None:
    st.sidebar.warning("Core-13.json не активирован. Работа в режиме эмуляции.")
else:
    st.sidebar.success(f"Процессор Core-13 активен: {len(core_dipoles)} диполей")

st.success(f"VRAM активна: {len(nodes)} узлов.")

# --- УПРАВЛЕНИЕ РЕЗОНАНСОМ ---
st.sidebar.header("Параметры ядра")
base_energy = st.sidebar.slider("Базовая Энергия", 0.0, 25.0, 19.4)
base_phase = st.sidebar.slider("Базовая Фаза", 0.0, 40.0, 13.5)
threshold = st.sidebar.slider("Порог отсечения (Gate)", 0.5, 0.98, 0.95)

st.subheader("Ввод информационного импульса")
user_input = st.text_input("Текст для модуляции", "ГЕОМЕТРИЯ ПУСТОТЫ")

# Расчет динамических параметров
text_vector = sum(ord(c) for c in user_input) * 0.001 if user_input else 0.0
dynamic_phase = base_phase + (text_vector * 1.5)
dynamic_energy = base_energy + (len(user_input) * 0.2 if user_input else 0.0)

image_file = st.file_uploader("Загрузите источник (PNG/JPG)", type=["jpg", "jpeg", "png"])

if image_file is not None:
    col1, col2 = st.columns(2)
    orig_img = Image.open(image_file).convert('RGB')
    col1.image(orig_img, caption="Входной сигнал", use_container_width=True)
    
    if st.button("Инициировать глубокий резонанс"):
        with st.spinner("Анализ прохождения через слои L1-L5..."):
            canvas_size = 1024
            output_img = Image.new('RGB', (canvas_size, canvas_size), (0, 0, 0))
            output_pixels = output_img.load()
            rgb_map = orig_img.resize((canvas_size, canvas_size)).load()
            
            total_nodes = len(nodes)
            side = int(math.sqrt(total_nodes))
            rows = math.ceil(total_nodes / side)
            
            purple_shifts = 0
            layer_stats = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            nodes_per_layer = total_nodes // 5
            
            for i in range(total_nodes):
                c_idx, r_idx = i % side, i // side
                px = max(0, min(1023, int((c_idx / side) * 1023)))
                py = max(0, min(1023, int((r_idx / rows) * 1023)))

                # Послойный расчет
                current_layer = min((i // nodes_per_layer) + 1, 5)
                node = nodes[i]
                z_coord = node.get('z', 0.0) if isinstance(node, dict) else 0.0
                
                interference = dynamic_energy * math.sin(z_coord * dynamic_phase)
                
                if interference > (dynamic_energy * threshold):
                    purple_shifts += 1
                    layer_stats[current_layer] += 1
                    r, g, b = rgb_map[px, py]
                    # Спектральный сдвиг (фиолетовый неон)
                    new_r = int(max(0, min(255, r + interference * 12)))
                    new_g = int(max(0, min(255, g - interference * 5)))
                    new_b = int(max(0, min(255, b + interference * 15)))
                else:
                    new_r, new_g, new_b = rgb_map[px, py]
                
                # Отрисовка блока 2x2
                for dx in range(2):
                    for dy in range(2):
                        if px+dx < 1024 and py+dy < 1024:
                            output_pixels[px+dx, py+dy] = (new_r, new_g, new_b)
            
            col2.image(output_img, caption=f"Резонанс: {user_input}", use_container_width=True)
            
            # Послойный отчет
            res_percent = (purple_shifts / total_nodes) * 100
            st.code(f"""[ОТЧЕТ GIDEON: LAYER ANALYSIS]
Импульс: '{user_input}' | Фаза: {dynamic_phase:.4f}
Общий резонанс системы: {res_percent:.1f}%

АКТИВНОСТЬ ПО СЛОЯМ ВЛОЖЕННОСТИ:
L1 (Поверхность): {layer_stats[1]} узлов
L2 (Транзит):    {layer_stats[2]} узлов
L3 (Медиана):    {layer_stats[3]} узлов
L4 (Глубина):    {layer_stats[4]} узлов
L5 (Ядро VRAM):  {layer_stats[5]} узлов""", language="text")
