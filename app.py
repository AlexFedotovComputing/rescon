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
# Header (bigger logo)
# ============================================================
c_logo, c_title = st.columns([0.14, 0.86], vertical_alignment="center")
with c_logo:
    st.image(LOGO_URL, width=120)  # <-- увеличь/уменьши здесь (например 96..160)
with c_title:
    st.title("Pt100: погрешность накладного датчика на трубе")
    st.markdown(
        "Оценка смещения показаний накладного Pt100 относительно температуры воды "
        "из-за теплопередачи через стенку/термопасту и теплоотвода через провода."
    )

# ============================================================
# Inputs (no sidebar, split basic/advanced)
# ============================================================
with st.form("inputs"):
    st.subheader("Параметры")

    with st.expander("Основные параметры", expanded=True):
        # --- Temperatures / geometry (most important first) ---
        c1, c2, c3 = st.columns(3)
        with c1:
            Tw_C = st.number_input(
                "Температура воды T_w, °C",
                value=17.0, step=0.5,
                help="Истинная температура воды в трубе."
            )
        with c2:
            Tair_C = st.number_input(
                "Температура воздуха T_air, °C",
                value=23.0, step=0.5,
                help="Температура воздуха рядом с датчиком/проводами."
            )
        with c3:
            D_i_mm = st.number_input(
                "Внутренний диаметр трубы Dᵢ, мм",
                value=10.0, min_value=1.0, step=1.0,
                help="Нужен для оценки hᵢ (внутренней теплоотдачи). Если не знаешь — начни с 8–16 мм."
            )

        st.divider()

        # --- Contact / wall / paste ---
        c1, c2, c3 = st.columns(3)
        with c1:
            S_mm2 = st.number_input(
                "Площадь контакта датчика S, мм²",
                value=12.0, min_value=0.1, step=1.0,
                help="Напр. 3×4 мм² = 12 мм²."
            )
            t_r_mm = st.number_input(
                "Толщина стенки трубы tᵣ, мм",
                value=1.5, min_value=0.1, step=0.1
            )
            k_r = st.number_input(
                "Теплопроводность резины kᵣ, Вт/(м·К)",
                value=0.20, min_value=0.01, step=0.01,
                help="Типично 0.15–0.25 Вт/(м·К)."
            )
        with c2:
            t_p_mm = st.number_input(
                "Толщина термопасты tₚ, мм",
                value=0.20, min_value=0.0, step=0.05,
                help="Эффективная толщина слоя пасты/контакта."
            )
            k_p = st.number_input(
                "Теплопроводность пасты kₚ, Вт/(м·К)",
                value=1.0, min_value=0.05, step=0.1,
                help="Типично 0.7–3 Вт/(м·К)."
            )
        with c3:
            st.markdown("**Провода (канал теплообмена с воздухом)**")
            n_w = st.number_input(
                "Число жил",
                value=4, min_value=1, step=1
            )
            Lw_mm = st.number_input(
                "Длина участка провода в воздухе Lw, мм",
                value=50.0, min_value=0.0, step=10.0
            )

        st.divider()

        # --- Air regimes around wires ---
        c1, c2 = st.columns(2)
        with c1:
            h_still = st.number_input(
                "h для проводов: тихий воздух, Вт/(м²·К)",
                value=10.0, min_value=0.1, step=1.0
            )
        with c2:
            h_draft = st.number_input(
                "h для проводов: сквозняк, Вт/(м²·К)",
                value=40.0, min_value=0.1, step=1.0
            )

    with st.expander("Продвинутые параметры (обычно можно не трогать)", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            spread = st.slider(
                "Фактор «растекания» тепла в стенке",
                0.0, 2.0, 1.0, 0.05,
                help=(
                    "0 — оптимистично (1D теплопередача под пятном). "
                    "1 — добавить к сопротивлению примерно ещё один вклад tᵣ/kᵣ "
                    "(часто ближе к реальности для маленького пятна 3×4 мм²)."
                )
            )
        with c2:
            d_cu_mm = st.number_input(
                "Диаметр медной жилы d_cu, мм",
                value=0.20, min_value=0.05, step=0.05,
                help="Типично 0.15–0.30 мм."
            )
        with c3:
            d_out_mm = st.number_input(
                "Наружный диаметр провода d_out, мм",
                value=0.60, min_value=0.10, step=0.05,
                help="Диаметр по изоляции: влияет на теплоотдачу провода в воздух."
            )

        st.divider()
        st.caption("Свойства воды/меди для оценок при ~20–30 °C")
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            rho_w = st.number_input("ρ воды, кг/м³", value=998.0, step=1.0)
        with c2:
            mu_w = st.number_input("μ воды, Па·с", value=1.002e-3, format="%.4e")
        with c3:
            k_w = st.number_input("k воды, Вт/(м·К)", value=0.60, step=0.01)
        with c4:
            cp_w = st.number_input("cₚ воды, Дж/(кг·К)", value=4182.0, step=10.0)
        with c5:
            k_cu = st.number_input("k меди, Вт/(м·К)", value=400.0, step=10.0)

        st.divider()
        st.caption("Расходы (фиксированные, как в постановке)")
        flows_Lmin = [5.0, 10.0, 20.0]
        st.write("Расходы:", flows_Lmin, "л/мин")

    submitted = st.form_submit_button("Посчитать")

if not submitted:
    st.stop()

# ============================================================
# Defaults for advanced params if user didn't open expander
# (Streamlit всё равно создаёт переменные, но на всякий случай)
# ============================================================
if "spread" not in locals():
    spread = 1.0
if "d_cu_mm" not in locals():
    d_cu_mm = 0.20
if "d_out_mm" not in locals():
    d_out_mm = 0.60
if "rho_w" not in locals():
    rho_w = 998.0
if "mu_w" not in locals():
    mu_w = 1.002e-3
if "k_w" not in locals():
    k_w = 0.60
if "cp_w" not in locals():
    cp_w = 4182.0
if "k_cu" not in locals():
    k_cu = 400.0

# ============================================================
# Compute
# ============================================================
flows_Lmin = [5.0, 10.0, 20.0]

Tw_K = Tw_C + 273.15
Tair_K = Tair_C + 273.15
dT_sys = Tw_K - Tair_K

D_i = D_i_mm * 1e-3
S = S_mm2 * 1e-6
t_r = t_r_mm * 1e-3
t_p = t_p_mm * 1e-3
d_cu = d_cu_mm * 1e-3
d_out = d_out_mm * 1e-3
Lw = Lw_mm * 1e-3

Pr_w = mu_w * cp_w / k_w

# Guards
if D_i <= 0 or S <= 0 or k_r <= 0 or k_p <= 0 or d_cu <= 0 or d_out <= 0:
    st.error("Некорректные параметры (проверьте диаметры/площади/теплопроводности).")
    st.stop()

# Gw through fin model (per wire * number of wires)
A_cu = math.pi * (d_cu**2) / 4.0
P_out = math.pi * d_out
if A_cu <= 0 or P_out <= 0:
    st.error("Некорректные параметры провода (d_cu / d_out).")
    st.stop()

m_still = math.sqrt(h_still * P_out / (k_cu * A_cu))
Gw_still = n_w * (m_still * k_cu * A_cu * math.tanh(m_still * Lw))

m_draft = math.sqrt(h_draft * P_out / (k_cu * A_cu))
Gw_draft = n_w * (m_draft * k_cu * A_cu * math.tanh(m_draft * Lw))

rows = []
for Q in flows_Lmin:
    Q_m3s = (Q / 1000.0) / 60.0

    # Re = 4 rho Q / (pi mu D)
    Re = 4.0 * rho_w * Q_m3s / (math.pi * mu_w * D_i)

    # Nu: laminar vs turbulent (rough)
    if Re < 2300:
        Nu = 3.66
        regime = "laminar (very rough)"
    elif Re < 4000:
        Nu = 0.023 * (Re**0.8) * (Pr_w**0.4)
        regime = "transition (use with caution)"
    else:
        Nu = 0.023 * (Re**0.8) * (Pr_w**0.4)
        regime = "turbulent"

    h_i = Nu * k_w / D_i

    # R = 1/hi + tr/kr + tp/kp + spread*(tr/kr)
    R = (1.0 / h_i) + (t_r / k_r) + (t_p / k_p) + spread * (t_r / k_r)

    # Conductance to water (W/K)
    K_w = S / R

    # Sensor temperature: Ts = (K_w*Tw + Gw*Tair)/(K_w+Gw)
    Ts_still_K = (K_w * Tw_K + Gw_still * Tair_K) / (K_w + Gw_still)
    Ts_draft_K = (K_w * Tw_K + Gw_draft * Tair_K) / (K_w + Gw_draft)

    Ts_still_C = Ts_still_K - 273.15
    Ts_draft_C = Ts_draft_K - 273.15

    bias_still = Ts_still_K - Tw_K  # Ts - Tw
    bias_draft = Ts_draft_K - Tw_K

    rows.append({
        "Расход, л/мин": Q,
        "Re": Re,
        "Режим": regime,
        "hᵢ, Вт/(м²·К)": h_i,
        "R, м²К/Вт": R,
        "K_w, Вт/К": K_w,
        "G_w (тихо), Вт/К": Gw_still,
        "G_w (сквозняк), Вт/К": Gw_draft,
        "T_s (тихо), °C": Ts_still_C,
        "T_s (сквозняк), °C": Ts_draft_C,
        "Смещение T_s−T_w (тихо), K": bias_still,
        "Смещение T_s−T_w (сквозняк), K": bias_draft,
        "|смещение| (тихо), K": abs(bias_still),
        "|смещение| (сквозняк), K": abs(bias_draft),
    })

df = pd.DataFrame(rows)

# ============================================================
# Output
# ============================================================
st.subheader("Результаты")

df10 = df[df["Расход, л/мин"] == 10.0]
if len(df10) == 1:
    r = df10.iloc[0]
    b1 = float(r["Смещение T_s−T_w (тихо), K"])
    b2 = float(r["Смещение T_s−T_w (сквозняк), K"])

    def word(x: float) -> str:
        if x > 0:
            return "завышает"
        if x < 0:
            return "занижает"
        return "не смещает"

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("ΔT (вода − воздух), K", f"{(Tw_K - Tair_K):.2f}")
    with c2:
        st.info(f"**Тихий воздух (10 л/мин):** датчик {word(b1)} примерно на **{abs(b1):.2f} K**")
    with c3:
        st.warning(f"**Сквозняк (10 л/мин):** датчик {word(b2)} примерно на **{abs(b2):.2f} K**")

st.dataframe(df, use_container_width=True)

plot_df = df[["Расход, л/мин", "Смещение T_s−T_w (тихо), K", "Смещение T_s−T_w (сквозняк), K"]].copy()
plot_df = plot_df.set_index("Расход, л/мин")
st.line_chart(plot_df)

with st.expander("Модель и формулы (коротко)", expanded=False):
    st.markdown(
        r"""
**Стационарный баланс тепловых потоков.**

Приведённое сопротивление от воды к датчику:
\[
R=\frac{1}{h_i}+\frac{t_r}{k_r}+\frac{t_p}{k_p}+\text{spread}\cdot\frac{t_r}{k_r}.
\]
Проводимость к воде: \(K_w=S/R\) (Вт/К).

Теплоотвод в воздух только через провода с проводимостью \(G_w\) (Вт/К).  
\(G_w\) оценена моделью ребра (fin) и умножена на число жил.

Температура сенсора:
\[
T_s=\frac{K_w T_w + G_w T_{air}}{K_w+G_w},
\qquad
\Delta = T_s - T_w.
\]

**Ограничения модели:** не учтён теплообмен корпуса датчика с воздухом; контакт может быть неидеален
(микрозазоры/неравномерная паста); прокладка проводов вдоль трубы под изоляцией может резко уменьшить \(G_w\).
"""
    )

st.caption(
    "Подсказка: если смещение в несколько K, чаще всего виноваты провода (G_w) и малая площадь контакта S. "
    "Помогают: увеличить S, уменьшить Lw, вести первые сантиметры проводов в тепловом контакте с трубой и под изоляцией."
)

st.markdown("---")
st.caption('Разработано ООО "АркоЛаб", 2025')
