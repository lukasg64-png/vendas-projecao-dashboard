import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path

# =========================================================
# CONFIG GERAL
# =========================================================
st.set_page_config(
    page_title="FSJ Black Friday – Projeção de Vendas",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DATA_DIR = Path("data")
GRID_PATH = DATA_DIR / "saida_grid.csv"
RESUMO_PATH = DATA_DIR / "saida_resumo.csv"
LOGINS_PATH = DATA_DIR / "logins.csv"

PRIMARY = "#00E676"
DANGER = "#FF1744"
WARNING = "#FFD54F"
CARD_BG = "#111111"

# =========================================================
# HELPERS
# =========================================================
@st.cache_data
def load_logins(path: Path):
    if not path.exists():
        return pd.DataFrame([
            {"usuario": "farmacias_sao_joao", "senha": "blackfriday2025", "nome": "Time E-commerce"}
        ])
    df = pd.read_csv(path, dtype=str).fillna("")
    return df


def authenticate(username: str, password: str, df_logins: pd.DataFrame):
    row = df_logins[
        (df_logins["usuario"] == username) &
        (df_logins["senha"] == password)
    ]
    if not row.empty:
        return True, row.iloc[0]["nome"]
    return False, None


def fmt_currency_br(x, decimals=0):
    try:
        if x is None or np.isnan(x):
            return "-"
    except:
        pass
    fmt = f"{x:,.{decimals}f}"
    fmt = fmt.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {fmt}"


def fmt_number_br(x, decimals=2):
    try:
        if x is None or np.isnan(x):
            return "-"
    except:
        pass
    fmt = f"{x:.{decimals}f}".replace(".", ",")
    return fmt


def fmt_percent_br(x, decimals=2):
    try:
        if x is None or np.isnan(x):
            return "-"
    except:
        pass
    pct = x * 100
    fmt = f"{pct:,.{decimals}f}"
    fmt = fmt.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{fmt}%"


def kpi_card(title, value, subtitle="", color=PRIMARY, tooltip=None):
    info = f"<span title='{tooltip}' style='cursor:help; margin-left:6px;'>ℹ️</span>" if tooltip else ""

    html = f"""
    <div style="
        background:{CARD_BG};
        padding:18px 20px;
        border-radius:12px;
        border:1px solid #333;
        box-shadow:0 0 10px rgba(0,0,0,0.4);
    ">
        <div style="font-size:0.8rem;color:#BBBBBB;display:flex;justify-content:space-between;">
            <span>{title}</span>{info}
        </div>
        <div style="font-size:1.7rem;font-weight:700;margin-top:4px;color:{color};">
            {value}
        </div>
        <div style="font-size:0.75rem;color:#888888;margin-top:6px;">
            {subtitle}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# =========================================================
# LOGIN
# =========================================================
def login_screen(df_logins):
    st.markdown(
        """
        <div style="
            padding:14px 18px;
            border-radius:14px;
            background:linear-gradient(90deg,#00E676,#00B0FF);
            display:flex;
            justify-content:space-between;
            align-items:center;
            margin-bottom:12px;
        ">
            <div>
                <div style="font-size:1.2rem;font-weight:700;color:#001B20;">
                    FSJ Black Friday – Painel de Projeção
                </div>
                <div style="font-size:0.9rem;color:#012A30;margin-top:4px;">
                    Bem-vindo, São João! <b>Tem Black na São João? Tem Black na São João! 🔥</b>
                </div>
            </div>
            <div style="font-size:0.75rem;color:#012A30;background:white;
                        padding:6px 14px;border-radius:999px;">
                Feito por: Planejamento e Dados E-Commerce
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col = st.columns([1, 1, 1])[1]

    with col:
        st.markdown("<div style='font-size:1.05rem;font-weight:600;margin-bottom:8px;'>🔐 Acesse o painel</div>", unsafe_allow_html=True)

        user = st.text_input("Usuário")
        pwd = st.text_input("Senha", type="password")

        if st.button("Entrar", use_container_width=True):
            ok, nome = authenticate(user.strip(), pwd.strip(), df_logins)
            if ok:
                st.session_state["auth"] = True
                st.session_state["user_name"] = nome
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")

        st.caption("Usuários carregados de data/logins.csv.")

# =========================================================
# LOAD DATA
# =========================================================
@st.cache_data
def load_panel_data():
    grid = pd.read_csv(GRID_PATH)
    resumo = pd.read_csv(RESUMO_PATH).iloc[0].to_dict()
    return grid, resumo

# =========================================================
# TAB 1 — VISÃO GERAL
# =========================================================
def painel_visao_geral(grid, resumo, user_name):
    data_ref = pd.to_datetime(resumo["data_referencia"]).date()

    meta = float(resumo["meta_dia"])
    venda = float(resumo["venda_atual_ate_slot"])
    frac_hist = float(resumo["percentual_dia_hist"])
    perc_meta = venda / meta if meta > 0 else 0

    proj = float(resumo["projecao_dia"])
    gap = float(resumo["desvio_projecao"])

    d1 = float(resumo["total_d1"])
    d7 = float(resumo["total_d7"])
    r1 = float(resumo["ritmo_vs_d1"])
    r7 = float(resumo["ritmo_vs_d7"])
    rm = float(resumo["ritmo_vs_media"])

    ritmo_comb = (r1 + r7 + rm) / 3

    st.markdown(
        f"<div style='margin-bottom:10px;color:#BBBBBB;font-size:0.9rem;'>Usuário: <b>{user_name}</b> • Data: <b>{data_ref.strftime('%d/%m/%Y')}</b></div>",
        unsafe_allow_html=True
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        kpi_card("Meta do dia", fmt_currency_br(meta))

    with c2:
        kpi_card(
            "Venda atual",
            fmt_currency_br(venda),
            f"{fmt_percent_br(perc_meta,1)} da meta."
        )

    with c3:
        kpi_card(
            "Projeção de fechamento",
            fmt_currency_br(proj),
            "Base histórica + ritmo atual."
        )

    with c4:
        kpi_card(
            "Gap projetado",
            fmt_currency_br(gap),
            "Diferença entre projeção e meta."
        )

    st.subheader("📈 Ritmo do Dia", divider="gray")
    c5, c6, c7, c8 = st.columns(4)

    with c5:
        kpi_card("Total D-1", fmt_currency_br(d1))

    with c6:
        kpi_card("Total D-7", fmt_currency_br(d7))

    with c7:
        kpi_card("Dia já percorrido", fmt_percent_br(frac_hist, 1))

    with c8:
        subt = f"vs D-1: {fmt_number_br(r1)}x • vs D-7: {fmt_number_br(r7)}x • vs mês: {fmt_number_br(rm)}x"
        kpi_card("Ritmo combinado", f"{fmt_number_br(ritmo_comb)}x", subt)

# =========================================================
# TAB 2 — CURVAS & RITMO
# =========================================================
def painel_curvas_ritmo(grid, resumo):
    st.subheader("📊 Curvas de venda", divider="gray")

    fig = px.line(
        grid,
        x="SLOT",
        y=["valor_hoje", "valor_d1", "valor_d7", "valor_media_mes"],
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📈 Ritmos ao longo do dia", divider="gray")

    proj = float(resumo["projecao_dia"])
    grid = grid.copy()
    grid["perc_dia_realizado"] = grid["acum_hoje"] / proj if proj > 0 else 0

    fig2 = px.line(
        grid,
        x="SLOT",
        y=["ritmo_vs_d1", "ritmo_vs_d7", "ritmo_vs_media", "perc_dia_realizado"],
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("🔥 Mapa de calor", divider="gray")

    dfh = grid[["SLOT", "valor_hoje", "valor_d1", "valor_d7", "valor_media_mes"]]
    dfm = dfh.melt("SLOT")
    pivot = dfm.pivot(index="variable", columns="SLOT", values="value")

    fig3 = px.imshow(pivot, aspect="auto", color_continuous_scale="Viridis")
    st.plotly_chart(fig3, use_container_width=True)

# =========================================================
# TAB 3 — SIMULAÇÃO
# =========================================================
def painel_simulacao_meta(resumo):
    st.subheader("🎯 Simulação de Meta", divider="gray")

    meta = float(resumo["meta_dia"])
    venda = float(resumo["venda_atual_ate_slot"])
    proj = float(resumo["projecao_dia"])

    nova_meta = st.slider(
        "Nova meta simulada",
        int(meta * 0.5), int(meta * 1.5),
        int(meta), step=50000
    )

    gap = proj - nova_meta
    perc = venda / nova_meta if nova_meta > 0 else 0

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("Meta atual", fmt_currency_br(meta))
    with c2:
        kpi_card("Meta simulada", fmt_currency_br(nova_meta))
    with c3:
        kpi_card("Gap simulado", fmt_currency_br(gap))

    st.markdown(
        f"""
        - Venda atual: **{fmt_currency_br(venda)}**  
        - Cobre **{fmt_percent_br(perc,1)}** da meta simulada  
        """
    )

# =========================================================
# MAIN
# =========================================================
def main():

    df_logins = load_logins(LOGINS_PATH)

    if "auth" not in st.session_state:
        st.session_state["auth"] = False

    if not st.session_state["auth"]:
        login_screen(df_logins)
        return

    user_name = st.session_state.get("user_name", "Usuário")

    # HEADER
    st.markdown(
        """
        <div style="
            padding:14px 20px;
            border-radius:14px;
            background:linear-gradient(90deg,#00E676,#00B0FF);
            display:flex;justify-content:space-between;
            margin-bottom:16px;">
            <div>
                <div style="font-size:1.2rem;font-weight:700;color:#001B20;">
                    Painel Executivo – FSJ Black Friday
                </div>
                <div style="font-size:0.85rem;color:#012A30;margin-top:4px;">
                    Monitor de projeção diária, ritmo e curvas intradia.
                </div>
            </div>
            <div style="font-size:0.75rem;color:#012A30;background:white;
                        padding:6px 14px;border-radius:999px;">
                Feito por: Planejamento e Dados E-Commerce
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    grid, resumo = load_panel_data()

    tab1, tab2, tab3 = st.tabs(["Visão Geral", "Curvas & Ritmo", "Simulação"])

    with tab1:
        painel_visao_geral(grid, resumo, user_name)

    with tab2:
        painel_curvas_ritmo(grid, resumo)

    with tab3:
        painel_simulacao_meta(resumo)

if __name__ == "__main__":
    main()
