import streamlit as st
import json
import math
import os
import glob
from PIL import Image

st.set_page_config(page_title="S-GPU GIDEON | Core-13 Debug", layout="wide")
st.title("Топологический процессор S-GPU GIDEON")

# --- СЛУЖЕБНЫЙ БЛОК: УМНЫЙ ПОИСК ---
def diagnostic_load(filename):
    """Ищет файл и возвращает (данные, путь, ошибка)"""
    # 1. Поиск во всех подпапках
    matches = glob.glob(f"**/{filename}", recursive=True)
    path = matches[0] if matches else None
    
    if not path and os.path.exists(filename):
        path = filename

    if path:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                content = data.get('nodes', data.get('dipoles', data)) if isinstance(data, dict) else data
                return content, path, None
        except Exception as e:
            return None, path, str(e)
    return None, None, "Файл не найден"

# --- ЗАГРУЗКА КОМПОНЕНТОВ ---
nodes, vram_path, vram_err = diagnostic_load('matrix.json')
core_dipoles, core_path, core_err = diagnostic_load('Core-13.json')

# Интерфейс ручной дозагрузки при сбое
if nodes is None:
    st.error(f"Память VRAM ('matrix.json') не обнаружена.")
    st.info(f"Файлы в корне сервера: {os.listdir('.')}")
    u_vram = st.file_uploader("Загрузить matrix.json вручную", type=["json"])
    if u_vram:
        data = json.load(u_vram)
        nodes = data.get('nodes', data) if isinstance(data, dict) else data
    else: st.stop()

if core_dipoles is None:
    st.sidebar.warning("⚠️ Ядро Core-13.json не найдено. Ожидание загрузки...")
    u_core = st.sidebar.file_uploader("Загрузить Core-13.json", type=["json"])
    if u_core:
        data = json.load(u_core)
        core_dipoles = data.get('dipoles', data) if isinstance(data, dict) else data
        st.sidebar.success("Ядро загружено вручную")
else:
    st.sidebar.success(f"Процессор Core-13 активен ({len(core_dipoles)} диполей)")

st.success(f"Система готова. VRAM: {len(nodes)} узлов.")

# --- ПАНЕЛЬ УПРАВЛЕНИЯ ---
st.sidebar.header("Параметры резонанса")
base_energy = st.sidebar.slider("Базовая Энергия", 0.0, 25.0, 19.4)
base_phase = st.sidebar.slider("Базовая Фаза", 0.0, 40.0, 13.5)
threshold = st.sidebar.slider("Порог отсечения (Gate)", 0.5, 0.98, 0.95)

st.subheader("Центральный процессор: Ввод данных")
user_input = st.text_input("Введите информационный импульс", "ГЕОМЕТРИЯ ПУСТОТЫ")

# Динамическая модуляция
text_vector = sum(ord(c) for c in user_input) * 0.001 if user_input else 0.0
dynamic_phase = base_phase + (text_vector * 1.5)
dynamic_energy = base_energy + (len(user_input) * 0.2 if user_input else 0.0)

image_file = st.file_uploader("Загрузите растровый источник", type=["jpg", "jpeg", "png"])

if image_file is not None:
    col1, col2 = st.columns(2)
    orig_img = Image.open(image_file).convert('RGB')
    col1.image(orig_img, caption="Входной сигнал", use_container_width=True)
    
    if st.button("Запустить глубокий резонанс"):
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

                current_layer = min((i // nodes_per_layer) + 1, 5)
                z_coord = nodes[i].get('z', 0.0) if isinstance(nodes[i], dict) else 0.0
                
                # Интерференция модулированная ядром
                interference = dynamic_energy * math.sin(z_coord * dynamic_phase)
                
                if interference > (dynamic_energy * threshold):
                    purple_shifts += 1
                    layer_stats[current_layer] += 1
                    r, g, b = rgb_map[px, py]
                    new_r = int(max(0, min(255, r + interference * 12)))
                    new_g = int(max(0, min(255, g - interference * 5)))
                    new_b = int(max(0, min(255, b + interference * 15)))
                else:
                    new_r, new_g, new_b = rgb_map[px, py]
                
                for dx in range(2):
                    for dy in range(2):
                        if px+dx < 1024 and py+dy < 1024:
                            output_pixels[px+dx, py+dy] = (new_r, new_g, new_b)
            
            col2.image(output_img, caption=f"Резонанс Core-13: {user_input}", use_container_width=True)
            
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
