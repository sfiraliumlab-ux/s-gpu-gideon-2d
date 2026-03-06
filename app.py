import streamlit as st
import json
import math
import os
from PIL import Image

# Настройка страницы
st.set_page_config(page_title="S-GPU GIDEON | Core-13 Active", layout="wide")
st.title("Топологический процессор S-GPU GIDEON")

# Константы путей
VRAM_FILE = 'matrix.json'
CORE_FILE = 'Core-13.json'

@st.cache_data
def load_json_data(file_path):
    """Надежная загрузка JSON из файла"""
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Возвращаем список узлов/диполей в зависимости от структуры
            if isinstance(data, dict):
                return data.get('nodes', data.get('dipoles', []))
            return data
    except Exception as e:
        st.error(f"Ошибка чтения {file_path}: {e}")
        return None

# --- БЛОК ЗАГРУЗКИ КОМПОНЕНТОВ ---

# 1. Попытка автозагрузки VRAM
nodes = load_json_data(VRAM_FILE)

# 2. Попытка автозагрузки Core-13
core_dipoles = load_json_data(CORE_FILE)

# Если автозагрузка не удалась, выводим интерфейс ручной загрузки
if nodes is None:
    st.warning(f"⚠️ Файл '{VRAM_FILE}' не найден в корне репозитория.")
    # Диагностика: показываем пользователю, что вообще видит сервер
    files_in_root = os.listdir('.')
    st.info(f"Доступные файлы в корне: {', '.join(files_in_root)}")
    
    uploaded_vram = st.file_uploader("Загрузите 'matrix.json' вручную (18.6 МБ)", type=["json"])
    if uploaded_vram:
        try:
            data = json.load(uploaded_vram)
            nodes = data.get('nodes', data) if isinstance(data, dict) else data
        except:
            st.error("Ошибка формата загруженного файла.")
            st.stop()
    else:
        st.stop() # Остановка, пока нет памяти

if core_dipoles is None:
    st.sidebar.warning(f"Core-13.json не найден. Ядро в режиме эмуляции.")
else:
    st.sidebar.success(f"Процессор Core-13 активен: {len(core_dipoles)} диполей")

st.success(f"VRAM активна: {len(nodes)} узлов.")

# --- ИНТЕРФЕЙС УПРАВЛЕНИЯ ---

st.sidebar.header("Параметры резонанса")
base_energy = st.sidebar.slider("Базовая Энергия", 0.0, 20.0, 18.0)
base_phase = st.sidebar.slider("Базовая Фаза", 0.0, 20.0, 13.5)
threshold = st.sidebar.slider("Порог отсечения", 0.5, 0.98, 0.95)

# Модуль текстового резонанса
st.subheader("Центральный процессор: Ввод данных")
user_input = st.text_input("Введите информационный импульс (например: СФИРАЛЬ)", "")

# Расчет вектора резонанса (модуляция параметров текстом)
text_vector = sum(ord(c) for c in user_input) * 0.001 if user_input else 0.0
dynamic_phase = base_phase + (text_vector * 1.5)
dynamic_energy = base_energy + (len(user_input) * 0.2 if user_input else 0.0)

st.info(f"Динамическая фаза системы: {dynamic_phase:.4f}")

# --- ВЫЧИСЛИТЕЛЬНЫЙ ПРОЦЕСС ---

image_file = st.file_uploader("Загрузите растровый источник", type=["jpg", "jpeg", "png"])

if image_file is not None:
    col1, col2 = st.columns(2)
    orig_img = Image.open(image_file).convert('RGB')
    col1.image(orig_img, caption="Входной сигнал", use_container_width=True)
    
    if st.button("Запустить резонанс через Core-13"):
        with st.spinner("Диполи ядра модулируют фазу..."):
            # Подготовка холста 1024x1024
            canvas_size = 1024
            output_img = Image.new('RGB', (canvas_size, canvas_size), (0, 0, 0))
            output_pixels = output_img.load()
            
            # Подготовка источника
            resized_orig = orig_img.resize((canvas_size, canvas_size))
            rgb_map = resized_orig.load()
            
            total_nodes = len(nodes)
            side = int(math.sqrt(total_nodes))
            rows = math.ceil(total_nodes / side)
            
            active_pixels_count = 0
            purple_shifts = 0
            
            for i in range(total_nodes):
                col_idx = i % side
                row_idx = i // side
                
                # Масштабирование координат в 1024x1024
                px = max(0, min(1023, int((col_idx / side) * 1023)))
                py = max(0, min(1023, int((row_idx / rows) * 1023)))

                # Получение Z-координаты узла
                node = nodes[i]
                z_coord = node.get('z', 0.0) if isinstance(node, dict) else 0.0
                
                # Формула интерференции S-GPU
                interference = dynamic_energy * math.sin(z_coord * dynamic_phase)
                
                r, g, b = rgb_map[px, py]
                
                # Фильтр пиковых резонансов
                if interference > (dynamic_energy * threshold):
                    purple_shifts += 1
                    # Спектральный сдвиг
                    new_r = int(max(0, min(255, r + interference * 12)))
                    new_g = int(max(0, min(255, g - interference * 5)))
                    new_b = int(max(0, min(255, b + interference * 15)))
                else:
                    new_r, new_g, new_b = r, g, b
                
                # Отрисовка узла (размер 2x2 для плотности)
                for dx in range(2):
                    for dy in range(2):
                        nx, ny = px + dx, py + dy
                        if nx < canvas_size and ny < canvas_size:
                            output_pixels[nx, ny] = (new_r, new_g, new_b)
            
            col2.image(output_img, caption=f"Отпечаток для импульса: '{user_input}'", use_container_width=True)
            
            # Телеметрия
            res_percent = (purple_shifts / total_nodes) * 100
            report = f"""[ОТЧЕТ GIDEON: CORE-13 ACTIVE]
Текст: '{user_input}' | Фаза модуля: {dynamic_phase:.4f}
Энергия: {dynamic_energy:.2f} | Порог: {threshold}
Узлов в резонансе: {purple_shifts} ({res_percent:.1f}%)"""
            
            st.code(report, language="text")
