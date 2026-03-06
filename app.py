import streamlit as st
import json
import math
import os
import numpy as np
from PIL import Image

st.set_page_config(page_title="GIDEON | Logos-3 Absolute", layout="wide")
st.title("S-GPU GIDEON: Семантический Реактор (Logos-3)")

# --- LOGOS-3 ENGINE DATA ---
VOCAB = {
    "ПОРЯДОК": (1.0, -1.0, 1),   "ХАОС": (-1.0, 1.0, -1),
    "ЖИЗНЬ": (0.9, -0.9, 1),     "СМЕРТЬ": (-0.9, 0.9, -1),
    "ИСТИНА": (0.8, -0.8, 1),    "ЛОЖЬ": (-0.8, 0.8, -1),
    "ГАРМОНИЯ": (0.0, 0.0, 1),   "ВЕЧНОСТЬ": (0.0, 0.0, -1), # Для Divine Synthesis
    "ЛЮБОВЬ": (1.0, -0.6, 1),    "ВРАЖДА": (-1.0, 0.6, -1),
    "БОГ": (0.0, 0.0, 1)
}

def get_logos_interaction(p1, p2):
    """Логика взаимодействия Тезис/Антитезис/Спин"""
    name1, name2 = p1.upper(), p2.upper()
    if name1 not in VOCAB or name2 not in VOCAB:
        return 1.0, "STANDARD"
    
    v1, v2 = VOCAB[name1], VOCAB[name2]
    dist = abs(v1[0] - v2[0]) + abs(v1[1] - v2[1])
    spin_product = v1[2] * v2[2]
    
    # Divine Exception
    is_divine = ("ГАРМОНИЯ" in [name1, name2] and "ВЕЧНОСТЬ" in [name1, name2])
    
    raw_energy = 20.0 / (dist + 0.5)
    
    if spin_product < 0 or is_divine:
        return raw_energy, "SYNTHESIS"
    else:
        return raw_energy * 0.8, "ALLIANCE"

# --- СТАБИЛЬНЫЙ БЛОК ЗАГРУЗКИ ---
@st.cache_data
def load_vram_direct(filename):
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('nodes', data.get('dipoles', data)) if isinstance(data, dict) else data
        except Exception as e:
            st.error(f"Ошибка чтения {filename}: {e}")
    return None

nodes = load_vram_direct('matrix.json')
core = load_vram_direct('Core-13.json')

# Индикаторы (Backup Secure)
if nodes:
    st.success(f"✅ VRAM активна: {len(nodes)} узлов загружено из репозитария.")
else:
    st.error("❌ Критическая ошибка: 'matrix.json' не найден."); st.stop()

if core:
    st.sidebar.success(f"✅ Core-13 активен: {len(core)} диполей.")
else:
    st.sidebar.warning("⚠️ Core-13 в режиме эмуляции.")

# --- ИНТЕРФЕЙС УПРАВЛЕНИЯ ---
st.sidebar.header("Параметры ядра")
base_energy = st.sidebar.slider("Базовая Энергия", 0.0, 25.0, 18.0)
base_phase = st.sidebar.slider("Базовая Фаза", 0.0, 40.0, 13.5)
threshold = st.sidebar.slider("Порог сепарации", 0.1, 0.98, 0.85)

st.subheader("Дифференциальный ввод (Logos Mirror)")
col_a, col_b = st.columns(2)
pulse_a = col_a.text_input("Импульс А", "ЖИЗНЬ")
pulse_b = col_b.text_input("Импульс Б", "СМЕРТЬ")

# Расчет семантического веса
logos_energy, logos_mode = get_logos_interaction(pulse_a, pulse_b)

def get_p(text, b_e, b_p):
    v = sum(ord(c) for c in text) * 0.001 if text else 0.0
    return b_e + (len(text) * 0.2), b_p + (v * 1.5)

e_a, p_a = get_p(pulse_a, base_energy, base_phase)
e_b, p_b = get_p(pulse_b, base_energy, base_phase)

# Модуляция энергии результатом Logos-3
dynamic_energy = (e_a + e_b) / 2 * (1.5 if logos_mode == "SYNTHESIS" else 1.0)

image_file = st.file_uploader("Загрузите растровый источник", type=["jpg", "jpeg", "png"])

if image_file is not None:
    col1, col2 = st.columns(2)
    orig_img = Image.open(image_file).convert('RGB')
    col1.image(orig_img, caption="Входной сигнал (Preview)", use_container_width=True)
    
    if st.button("Инициировать Семантический Резонанс"):
        with st.spinner(f"Режим {logos_mode}: расчет интерференции..."):
            canvas_size = 1024
            output_img = Image.new('RGB', (canvas_size, canvas_size), (0, 0, 0))
            out_px = output_img.load()
            rgb_map = orig_img.resize((canvas_size, canvas_size)).load()
            
            total = len(nodes)
            side, rows = int(math.sqrt(total)), math.ceil(total / int(math.sqrt(total)))
            diff_count, layer_diff = 0, {1:0, 2:0, 3:0, 4:0, 5:0}
            
            for i in range(total):
                px = max(0, min(1023, int(((i % side) / side) * 1023)))
                py = max(0, min(1023, int(((i // side) / rows) * 1023)))
                z = nodes[i].get('z', 0.0) if isinstance(nodes[i], dict) else 0.0
                
                # Интерференция модулированная Logos-3
                int_a = e_a * math.sin(z * p_a)
                int_b = e_b * math.sin(z * p_b)
                d_sig = abs(int_a - int_b)
                
                if d_sig > (dynamic_energy * threshold):
                    diff_count += 1
                    layer_diff[min((i // (total // 5)) + 1, 5)] += 1
                    r, g, b = rgb_map[px, py]
                    # Цветовой сдвиг в зависимости от режима
                    color_mod = 15 if logos_mode == "SYNTHESIS" else 5
                    out_px[px, py] = (int(max(0, min(255, r - d_sig * 5))), 
                                      int(max(0, min(255, g + d_sig * 8))), 
                                      int(max(0, min(255, b + d_sig * color_mod))))
                else:
                    out_px[px, py] = rgb_map[px, py]

            col2.image(output_img, caption=f"Mode: {logos_mode}", use_container_width=True)
            
            # --- РАСШИРЕННЫЙ АНАЛИТИЧЕСКИЙ ОТЧЕТ ---
            diff_pct = (diff_count / total) * 100
            kc = 100 - diff_pct
            di = np.std(list(layer_diff.values())) / np.mean(list(layer_diff.values())) if diff_count > 0 else 0
            
            # Semantic Outcome
            outcome = "UNDEFINED"
            pair = sorted([pulse_a.upper(), pulse_b.upper()])
            if pair == ["ХАОС", "ПОРЯДОК"]: outcome = "ГАРМОНИЯ"
            elif pair == ["ЖИЗНЬ", "СМЕРТЬ"]: outcome = "ВЕЧНОСТЬ"
            elif "ГАРМОНИЯ" in pair and "ВЕЧНОСТЬ" in pair: outcome = "БОГ (АБСОЛЮТ)"

            st.code(f"""[ОТЧЕТ GIDEON: LOGOS-3 ABSOLUTE]
ВЗАИМОДЕЙСТВИЕ: {pulse_a} + {pulse_b}
РЕЖИМ ЛОГИКИ: {logos_mode}
РЕЗУЛЬТАТ СИНТЕЗА: {outcome}

МЕТРИКИ РЕЗОНАНСА:
- Уникальных узлов: {diff_count} ({diff_pct:.1f}%)
- Когерентность (Kc): {kc:.1f}%
- Индекс девиации (Di): {di:.4f}

ЛОКАЛИЗАЦИЯ (L1-L5): {list(layer_diff.values())}
СПЕКТРАЛЬНАЯ ПЛОТНОСТЬ ПО СЛОЯМ:
L1: {(layer_diff[1]/(total/5))*100:.1f}% | L2: {(layer_diff[2]/(total/5))*100:.1f}% | L3: {(layer_diff[3]/(total/5))*100:.1f}% | L4: {(layer_diff[4]/(total/5))*100:.1f}% | L5: {(layer_diff[5]/(total/5))*100:.1f}%
""", language="text")
