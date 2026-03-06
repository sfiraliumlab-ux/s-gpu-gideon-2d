import streamlit as st
import json
import math
import os
import numpy as np
from PIL import Image

st.set_page_config(page_title="GIDEON | Logos-3 Robust", layout="wide")
st.title("S-GPU GIDEON: Семантический Реактор (v1.1.1)")

# --- БЛОК ЗАГРУЗКИ С ОБРАБОТКОЙ ПОВРЕЖДЕНИЙ ---
@st.cache_data
def load_json_safe(filename, uploaded_file=None):
    try:
        if uploaded_file:
            data = json.load(uploaded_file)
        elif os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            return None, "NOT_FOUND"
        
        nodes = data.get('nodes', data.get('dipoles', data)) if isinstance(data, dict) else data
        return nodes, "OK"
    except json.JSONDecodeError as e:
        return None, f"CORRUPTED: Line {e.lineno}, Col {e.colno}"
    except Exception as e:
        return None, str(e)

# Инициализация VRAM
nodes, vram_status = load_json_safe('matrix.json')
core_dipoles, core_status = load_json_safe('Core-13.json')

# Интерфейс статуса и аварийный загрузчик
if vram_status == "OK":
    st.success(f"✅ VRAM активна: {len(nodes)} узлов загружено из репозитария.")
else:
    st.error(f"❌ Сбой VRAM: {vram_status}")
    manual_vram = st.file_uploader("Загрузите исправный matrix.json вручную", type=["json"])
    if manual_vram:
        nodes, vram_status = load_json_safe('manual', manual_vram)
        if vram_status == "OK": st.rerun()
    else: st.stop()

if core_status == "OK":
    st.sidebar.success(f"✅ Core-13 активен: {len(core_dipoles)} диполей")
else:
    st.sidebar.warning(f"⚠️ Core-13: {core_status}. Режим эмуляции.")

# --- LOGOS-3 ENGINE (СИНТЕЗ АБСОЛЮТА) ---
VOCAB = {
    "ПОРЯДОК": (1.0, -1.0, 1),   "ХАОС": (-1.0, 1.0, -1),
    "ЖИЗНЬ": (0.9, -0.9, 1),     "СМЕРТЬ": (-0.9, 0.9, -1),
    "ИСТИНА": (0.8, -0.8, 1),    "ЛОЖЬ": (-0.8, 0.8, -1),
    "ГАРМОНИЯ": (0.0, 0.0, 1),   "ВЕЧНОСТЬ": (0.0, 0.0, -1),
    "БОГ": (0.0, 0.0, 1)
}

def get_logos_logic(p1, p2):
    n1, n2 = p1.upper(), p2.upper()
    if n1 not in VOCAB or n2 not in VOCAB: return 1.0, "STANDARD"
    v1, v2 = VOCAB[n1], VOCAB[n2]
    dist = abs(v1[0] - v2[0]) + abs(v1[1] - v2[1])
    is_divine = ("ГАРМОНИЯ" in [n1, n2] and "ВЕЧНОСТЬ" in [n1, n2])
    energy = 20.0 / (dist + 0.5)
    mode = "SYNTHESIS" if (v1[2] * v2[2] < 0 or is_divine) else "ALLIANCE"
    return energy, mode

# --- ИНТЕРФЕЙС УПРАВЛЕНИЯ ---
st.sidebar.header("Параметры ядра")
base_energy = st.sidebar.slider("Базовая Энергия", 0.0, 25.0, 18.0)
base_phase = st.sidebar.slider("Базовая Фаза", 0.0, 40.0, 13.5)
threshold = st.sidebar.slider("Порог сепарации", 0.1, 0.98, 0.85)

st.subheader("Дифференциальный анализ (Logos Mirror)")
col_a, col_b = st.columns(2)
pulse_a = col_a.text_input("Импульс А", "ЖИЗНЬ")
pulse_b = col_b.text_input("Импульс Б", "СМЕРТЬ")

l_energy, l_mode = get_logos_logic(pulse_a, pulse_b)

def get_p(text, b_e, b_p):
    v = sum(ord(c) for c in text) * 0.001 if text else 0.0
    return b_e + (len(text) * 0.2), b_p + (v * 1.5)

e_a, p_a = get_p(pulse_a, base_energy, base_phase)
e_b, p_b = get_p(pulse_b, base_energy, base_phase)
dynamic_energy = (e_a + e_b) / 2 * (1.5 if l_mode == "SYNTHESIS" else 1.0)

image_file = st.file_uploader("Загрузите растровый источник", type=["jpg", "jpeg", "png"])

if image_file is not None:
    col1, col2 = st.columns(2)
    orig_img = Image.open(image_file).convert('RGB')
    col1.image(orig_img, caption="Входной сигнал (Preview)", use_container_width=True)
    
    if st.button("Инициировать Семантический Резонанс"):
        with st.spinner(f"Расчет {l_mode}..."):
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
                
                int_a = e_a * math.sin(z * p_a)
                int_b = e_b * math.sin(z * p_b)
                d_sig = abs(int_a - int_b)
                
                if d_sig > (dynamic_energy * threshold):
                    diff_count += 1
                    layer_diff[min((i // (total // 5)) + 1, 5)] += 1
                    r, g, b = rgb_map[px, py]
                    color_mod = 15 if l_mode == "SYNTHESIS" else 5
                    out_px[px, py] = (int(max(0, min(255, r - d_sig * 5))), 
                                      int(max(0, min(255, g + d_sig * 8))), 
                                      int(max(0, min(255, b + d_sig * color_mod))))
                else:
                    out_px[px, py] = rgb_map[px, py]

            col2.image(output_img, caption=f"Mode: {l_mode}", use_container_width=True)
            
            # АНАЛИТИЧЕСКИЙ ОТЧЕТ
            diff_pct = (diff_count / total) * 100
            kc, di = 100 - diff_pct, np.std(list(layer_diff.values())) / np.mean(list(layer_diff.values())) if diff_count > 0 else 0
            
            pair = sorted([pulse_a.upper(), pulse_b.upper()])
            outcome = "ВЕЧНОСТЬ" if pair == ["ЖИЗНЬ", "СМЕРТЬ"] else ("ГАРМОНИЯ" if pair == ["ПОРЯДОК", "ХАОС"] else "STANDARD")
            if "ГАРМОНИЯ" in pair and "ВЕЧНОСТЬ" in pair: outcome = "БОГ (АБСОЛЮТ)"

            st.code(f"""[ОТЧЕТ GIDEON: ANALYTICAL LOGOS]
ВЗАИМОДЕЙСТВИЕ: {pulse_a} + {pulse_b} | РЕЖИМ: {l_mode}
РЕЗУЛЬТАТ СИНТЕЗА: {outcome}

МЕТРИКИ:
- Узлов разности: {diff_count} ({diff_pct:.1f}%)
- Когерентность (Kc): {kc:.1f}% | Девиация (Di): {di:.4f}
ЛОКАЛИЗАЦИЯ (L1-L5): {list(layer_diff.values())}
""", language="text")
