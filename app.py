import streamlit as st
import math
import pandas as pd

# ============================================================
# Branding
# ============================================================
LOGO_URL = (
    "https://raw.githubusercontent.com/AlexFedotovComputing/rescon/"
    "5ab6a18026d0889ac7df2ec485a644e9d7b25de3/"
    "%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202025-12-17%20192854.png"
)

st.set_page_config(page_title="Pt100 Clamp Error", page_icon="🧪", layout="wide")

# ============================================================
# Header
# ============================================================
c_logo, c_title = st.columns([0.18, 0.82], vertical_alignment="center")
with c_logo:
    st.image(LOGO_URL, width=170)
with c_title:
    st.title("Погрешность накладного датчика температуры")
    st.caption("Смещение относительно температуры воды из-за стенки/контакта и теплоотвода через провода.")

# ============================================================
# Presets
# ============================================================
WALL_MATERIALS = {
    "Резина (≈0.20)": 0.20,
    "Силикон (≈0.25)": 0.25,
    "ПВХ (≈0.19)": 0.19,
    "Полиуретан (≈0.30)": 0.30,
    "Другое (вручную)": None,
}
CONTACT_MATERIALS = {
    "Термопаста (≈1.0)": 1.0,
    "Силиконовый термоклей (≈0.5)": 0.5,
    "Эпоксидный клей (≈0.2)": 0.2,
    "Другое (вручную)": None,
}

# ============================================================
# Helpers for "preset -> editable input" without callbacks
# ============================================================
def apply_preset_if_changed(state_key_choice: str, state_key_prev: str, state_key_value: str, preset_map: dict):
    choice = st.session_state.get(state_key_choice)
    prev = st.session_state.get(state_key_prev)

    if choice != prev:
        preset = preset_map.get(choice)
        # если выбран материал с фиксированным значением — подставим его
        if preset is not None:
            st.session_state[state_key_value] = float(preset)
        # запомним выбор
        st.session_state[state_key_prev] = choice

# ============================================================
# Inputs
# ============================================================
with st.form("inputs"):
    st.subheader("Параметры")

    with st.expander("Основные", expanded=True):
        st.markdown("**Температуры и труба**")
        a, b, c = st.columns(3)
        with a:
            Tw_C = st.number_input("Температура воды, °C", value=17.0, step=0.5)
        with b:
            Tair_C = st.number_input("Температура воздуха, °C", value=23.0, step=0.5)
        with c:
            D_i_mm = st.number_input(
                "Внутренний диаметр трубы, мм",
                value=10.0, min_value=1.0, step=1.0,
                help="Для оценки внутренней теплоотдачи. Если неизвестно — начни с 8–16 мм."
            )

        st.divider()

        st.markdown("**Контакт**")
        a, b, c = st.columns(3)
        with a:
            S_mm2 = st.number_input(
                "Площадь контакта, мм²",
                value=12.0, min_value=0.1, step=1.0,
                help="Напр. 3×4 мм² = 12 мм²."
            )
        with b:
            t_p_mm = st.number_input(
                "Толщина контактного слоя, мм",
                value=0.20, min_value=0.0, step=0.05,
                help="Эффективная толщина слоя пасты/контакта."
            )
        with c:
            st.selectbox(
                "Материал контакта (подставляет kₚ)",
                list(CONTACT_MATERIALS.keys()),
                index=0,
                key="contact_choice"
            )

        # применим пресет k_p, если материал поменяли
        apply_preset_if_changed("contact_choice", "contact_choice_prev", "k_p", CONTACT_MATERIALS)

        # поле всегда видно и всегда редактируемо
        k_p = st.number_input(
            "Теплопроводность контакта kₚ, Вт/(м·К)",
            value=float(st.session_state.get("k_p", 1.0)),
            min_value=0.05, step=0.05,
            help="Можно редактировать вручную независимо от выбранного материала.",
            key="k_p"
        )

        st.divider()

        st.markdown("**Стенка трубы**")
        a, b, c = st.columns([0.45, 0.25, 0.30])
        with a:
            st.selectbox(
                "Материал стенки (подставляет kᵣ)",
                list(WALL_MATERIALS.keys()),
                index=0,
                key="wall_choice"
            )
        with b:
            t_r_mm = st.number_input("Толщина стенки, мм", value=1.5, min_value=0.1, step=0.1)
        with c:
            # применим пресет k_r, если материал поменяли
            apply_preset_if_changed("wall_choice", "wall_choice_prev", "k_r", WALL_MATERIALS)

            # поле всегда видно и редактируемо
            k_r = st.number_input(
                "Теплопроводность стенки kᵣ, Вт/(м·К)",
                value=float(st.session_state.get("k_r", 0.20)),
                min_value=0.01, step=0.01,
                help="Можно редактировать вручную независимо от выбранного материала.",
                key="k_r"
            )

        st.divider()

        st.markdown("**Провода**")
        a, b, c, d = st.columns(4)
        with a:
            n_w = st.number_input("Число жил", value=4, min_value=1, step=1)
        with b:
            Lw_mm = st.number_input(
                "Длина в воздухе, мм",
                value=50.0, min_value=0.0, step=10.0,
                help="Участок проводов, который реально обдувается воздухом."
            )
        with c:
            h_still = st.number_input("h: тихий воздух, Вт/(м²·К)", value=10.0, min_value=0.1, step=1.0)
        with d:
            h_draft = st.number_input("h: сквозняк, Вт/(м²·К)", value=40.0, min_value=0.1, step=1.0)

    with st.expander("Продвинутые (обычно не нужно)", expanded=False):
        st.markdown("**Геометрия проводов**")
        a, b = st.columns(2)
        with a:
            d_cu_mm = st.number_input("Диаметр медной жилы, мм", value=0.20, min_value=0.05, step=0.05)
        with b:
            d_out_mm = st.number_input(
                "Наружный диаметр провода, мм",
                value=0.60, min_value=0.10, step=0.05,
                help="Диаметр по изоляции: влияет на теплообмен с воздухом."
            )

        st.divider()

        spread = st.slider(
            "Поправка на «растекание» в стенке",
            0.0, 2.0, 1.0, 0.05,
            help="0 — оптимистично; 1 — часто ближе к реальности для малого пятна контакта."
        )

        st.divider()

        st.markdown("**Свойства воды/меди (оценки при ~20–30°C)**")
        a, b, c, d, e = st.columns(5)
        with a:
            rho_w = st.number_input("ρ воды, кг/м³", value=998.0, step=1.0)
        with b:
            mu_w = st.number_input("μ воды, Па·с", value=1.002e-3, format="%.4e")
        with c:
            k_w = st.number_input("k воды, Вт/(м·К)", value=0.60, step=0.01)
        with d:
            cp_w = st.number_input("cₚ воды, Дж/(кг·К)", value=4182.0, step=10.0)
        with e:
            k_cu = st.number_input("k меди, Вт/(м·К)", value=400.0, step=10.0)

        st.caption("Если сомневаешься — оставь по умолчанию.")

    submitted = st.form_submit_button("Посчитать")

if not submitted:
    st.stop()

# Defaults (если advanced не раскрывали)
if "d_cu_mm" not in locals(): d_cu_mm = 0.20
if "d_out_mm" not in locals(): d_out_mm = 0.60
if "spread" not in locals(): spread = 1.0
if "rho_w" not in locals(): rho_w = 998.0
if "mu_w" not in locals(): mu_w = 1.002e-3
if "k_w" not in locals(): k_w = 0.60
if "cp_w" not in locals(): cp_w = 4182.0
if "k_cu" not in locals(): k_cu = 400.0

# ============================================================
# Compute
# ============================================================
flows_Lmin = [5.0, 10.0, 20.0]

Tw_K = Tw_C + 273.15
Tair_K = Tair_C + 273.15

D_i = D_i_mm * 1e-3
S = S_mm2 * 1e-6
t_r = t_r_mm * 1e-3
t_p = t_p_mm * 1e-3
d_cu = d_cu_mm * 1e-3
d_out = d_out_mm * 1e-3
Lw = Lw_mm * 1e-3

Pr_w = mu_w * cp_w / k_w

if D_i <= 0 or S <= 0 or t_r <= 0 or k_r <= 0 or k_p <= 0 or d_cu <= 0 or d_out <= 0:
    st.error("Некорректные параметры (диаметры/площади/толщины/теплопроводности).")
    st.stop()

A_cu = math.pi * (d_cu**2) / 4.0
P_out = math.pi * d_out
if A_cu <= 0 or P_out <= 0:
    st.error("Некорректные параметры провода (d_cu/d_out).")
    st.stop()

def gw_for_h(h_air: float) -> float:
    m = math.sqrt(h_air * P_out / (k_cu * A_cu))
    return n_w * (m * k_cu * A_cu * math.tanh(m * Lw))

Gw_still = gw_for_h(h_still)
Gw_draft = gw_for_h(h_draft)

rows = []
for Q in flows_Lmin:
    Q_m3s = (Q / 1000.0) / 60.0
    Re = 4.0 * rho_w * Q_m3s / (math.pi * mu_w * D_i)

    if Re < 2300:
        Nu = 3.66
        regime = "laminar"
    else:
        Nu = 0.023 * (Re**0.8) * (Pr_w**0.4)
        regime = "turbulent/est."

    h_i = Nu * k_w / D_i

    R = (1.0 / h_i) + (t_r / k_r) + (t_p / k_p) + spread * (t_r / k_r)
    K_w = S / R

    Ts_still_K = (K_w * Tw_K + Gw_still * Tair_K) / (K_w + Gw_still)
    Ts_draft_K = (K_w * Tw_K + Gw_draft * Tair_K) / (K_w + Gw_draft)

    bias_still = Ts_still_K - Tw_K
    bias_draft = Ts_draft_K - Tw_K

    rows.append({
        "Расход, л/мин": Q,
        "T_s (тихо), °C": Ts_still_K - 273.15,
        "T_s (сквозняк), °C": Ts_draft_K - 273.15,
        "Смещение (тихо), K": bias_still,
        "Смещение (сквозняк), K": bias_draft,
        "Re": Re,
        "Режим": regime,
    })

df = pd.DataFrame(rows)

# ============================================================
# Output
# ============================================================
st.subheader("Результаты")

df10 = df[df["Расход, л/мин"] == 10.0]
if len(df10) == 1:
    r = df10.iloc[0]
    b1 = float(r["Смещение (тихо), K"])
    b2 = float(r["Смещение (сквозняк), K"])

    def word(x: float) -> str:
        if x > 0: return "завышает"
        if x < 0: return "занижает"
        return "без смещения"

    a, b, c = st.columns(3)
    with a:
        st.metric("ΔT (вода − воздух), K", f"{(Tw_K - Tair_K):.2f}")
    with b:
        st.metric("Тихий воздух (10 л/мин)", f"{abs(b1):.2f} K", delta=word(b1))
    with c:
        st.metric("Сквозняк (10 л/мин)", f"{abs(b2):.2f} K", delta=word(b2))

st.dataframe(
    df[[
        "Расход, л/мин",
        "T_s (тихо), °C", "T_s (сквозняк), °C",
        "Смещение (тихо), K", "Смещение (сквозняк), K",
    ]],
    use_container_width=True
)

with st.expander("Диагностика (при необходимости)", expanded=False):
    st.write(f"G_w (тихо) = {Gw_still:.3e} Вт/К, G_w (сквозняк) = {Gw_draft:.3e} Вт/К")
    st.write("Re по расходам:", ", ".join(f"{x:.0f}" for x in df["Re"].values))
    st.write("Режимы:", ", ".join(df["Режим"].values))

st.markdown("---")
st.caption('Разработано ООО "АркоЛаб", 2025')
