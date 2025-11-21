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

PRIMARY = "#00E676"   # verde principal
DANGER  = "#FF1744"   # vermelho
WARNING = "#FFD54F"   # amarelo
CARD_BG = "#111111"

# =========================================================
# HELPERS (FORMATAÇÃO / KPI / AUTENTICAÇÃO)
# =========================================================
@st.cache_data
def load_logins(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(
            [{"usuario": "farmacias_sao_joao",
              "senha": "blackfriday2025",
              "nome": "Time E-commerce"}]
        )
    df = pd.read_csv(path, dtype=str)
    df = df.fillna("")
    return df

def authenticate(username: str, password: str, df_logins: pd.DataFrame):
    row = df_logins[
        (df_logins["usuario"] == username) &
        (df_logins["senha"] == password)
    ]
    if not row.empty:
        return True, row["nome"].iloc[0]
    return False, None

def fmt_currency_br(x: float, decimals: int = 0) -> str:
    try:
        fmt = f"{x:,.{decimals}f}"
        fmt = fmt.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {fmt}"
    except:
        return "-"

def fmt_percent_br(x: float, decimals: int = 2) -> str:
    try:
        pct = x * 100
        fmt = f"{pct:,.{decimals}f}"
        fmt = fmt.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{fmt}%"
    except:
        return "-"

def fmt_number_br(x: float, decimals: int = 2) -> str:
    try:
        fmt = f"{x:,.{decimals}f}"
        fmt = fmt.replace(",", "X").replace(".", ",").replace("X", ".")
        return fmt
    except:
        return "-"

def kpi_card(title, value, subtitle="", color=PRIMARY, tooltip=None):
    info_html = f"<span style='margin-left:6px; cursor:help;' title='{tooltip}'>ℹ️</span>" if tooltip else ""
    html = f"""
    <div style="
        background:{CARD_BG};
        padding:18px 20px;
        border-radius:12px;
        border:1px solid #333;
        box-shadow:0 0 10px rgba(0,0,0,0.4);
    ">
        <div style="font-size:0.8rem;color:#BBBBBB;display:flex;align-items:center;justify-content:space-between;">
            <span>{title}</span>
            {info_html}
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
# LOGIN SCREEN
# =========================================================
def login_screen(df_logins):
    st.markdown(
        """
        <div style="
            padding:14px 18px;
            border-radius:14px;
            background:linear-gradient(90deg,#00E676,#00B0FF);
            display:flex;
            align-items:center;
            justify-content:space-between;
            margin-bottom:10px;
        ">
            <div>
                <div style="font-size:1.2rem;font-weight:700;color:#001B20;">
                    FSJ Black Friday – Painel de Projeção
                </div>
                <div style="font-size:0.9rem;color:#012A30;margin-top:4px;">
                    Bem-vindo, São João! <b>Tem Black na São João? Tem Black na São João! 🔥</b>
                </div>
            </div>
            <div style="font-size:0.8rem;color:#012A30;background:rgba(255,255,255,0.8);
                        padding:6px 14px;border-radius:999px;">
                Feito por: Planejamento e Dados E-Commerce
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col = st.columns([1,2,1])[1]
    with col:
        st.markdown("### 🔐 Login")
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")

        if st.button("Entrar", use_container_width=True):
            ok, nome = authenticate(username.strip(), password.strip(), df_logins)
            if ok:
                st.session_state["auth"] = True
                st.session_state["user"] = nome
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")

# =========================================================
# LOAD DATA
# =========================================================
@st.cache_data
def load_grid_and_resumo(grid_path, resumo_path):
    grid = pd.read_csv(grid_path)
    resumo = pd.read_csv(resumo_path).iloc[0].to_dict()
    return grid, resumo

# =========================================================
# PAINEL 1 — VISÃO GERAL
# =========================================================
def painel_visao_geral(grid, resumo, user_name):

    data_ref = resumo["data_referencia"]
    meta_dia = float(resumo["meta_dia"])
    venda_atual = float(resumo["venda_atual_ate_slot"])
    projecao = float(resumo["projecao_dia"])
    gap = float(resumo["desvio_projecao"])
    ritmo_d1 = float(resumo["ritmo_vs_d1"])
    ritmo_d7 = float(resumo["ritmo_vs_d7"])
    ritmo_med = float(resumo["ritmo_vs_media"])
    total_d1 = float(resumo["total_d1"])
    total_d7 = float(resumo["total_d7"])
    frac_hist = float(resumo["percentual_dia_hist"])

    st.markdown(
        f"<div style='color:#BBB;margin-bottom:8px;'>Usuário: <b>{user_name}</b> • Data: <b>{data_ref}</b></div>",
        unsafe_allow_html=True,
    )

    c1,c2,c3,c4 = st.columns(4)

    with c1:
        kpi_card("Meta do dia", fmt_currency_br(meta_dia), tooltip="Meta consolidada Site + App.")

    with c2:
        perc_meta = venda_atual / meta_dia if meta_dia>0 else 0
        kpi_card("Venda atual", fmt_currency_br(venda_atual),
                 f"{fmt_percent_br(perc_meta,1)} da meta",
                 color=PRIMARY if perc_meta>=frac_hist else WARNING)

    with c3:
        kpi_card("Projeção do dia", fmt_currency_br(projecao),
                 "Base histórica e ritmo atual",
                 color=PRIMARY if projecao>=meta_dia else WARNING)

    with c4:
        kpi_card("Gap projetado", fmt_currency_br(gap),
                 "vs meta",
                 color=PRIMARY if gap>=0 else DANGER)

    st.markdown("---")

    st.subheader("📈 Ritmo do Dia")

    c5,c6,c7,c8 = st.columns(4)

    with c5:
        kpi_card("Total D-1", fmt_currency_br(total_d1))

    with c6:
        kpi_card("Total D-7", fmt_currency_br(total_d7))

    with c7:
        kpi_card("Dia já percorrido", fmt_percent_br(frac_hist,1))

    with c8:
        ritmo_combinado = (ritmo_d1 + ritmo_d7 + ritmo_med) / 3
        texto_ritmo = (
            f"vs D-1: {fmt_number_br(ritmo_d1)}x • "
            f"vs D-7: {fmt_number_br(ritmo_d7)}x • "
            f"vs média: {fmt_number_br(ritmo_med)}x"
        )
        cor_ritmo = PRIMARY if ritmo_combinado>=1 else WARNING
        kpi_card(
            "Ritmo combinado",
            f"{fmt_number_br(ritmo_combinado)}x",
            texto_ritmo,
            color=cor_ritmo,
            tooltip="Média dos ritmos vs D-1, D-7 e média mensal."
        )

# =========================================================
# PAINEL 2 — CURVAS E RITMOS
# =========================================================
def painel_curvas_ritmo(grid, resumo):
    st.subheader("📊 Curvas DDT")

    fig = px.line(
        grid,
        x="SLOT",
        y=["valor_hoje","valor_d1","valor_d7","valor_media_mes"],
        labels={"value":"Valor (R$)","SLOT":"Horário"},
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📈 Ritmos do Dia")

    projecao = float(resumo["projecao_dia"])
    grid["perc_dia_realizado"] = grid["acum_hoje"] / projecao

    df_r = pd.DataFrame({
        "SLOT":grid["SLOT"],
        "Ritmo D-1":grid["ritmo_vs_d1"],
        "Ritmo D-7":grid["ritmo_vs_d7"],
        "Ritmo média":grid["ritmo_vs_media"],
        "% realizado":grid["perc_dia_realizado"],
    })

    fig2 = px.line(df_r, x="SLOT", y=df_r.columns[1:])
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("🔥 Heatmap")

    df_h = grid[["SLOT","valor_hoje","valor_d1","valor_d7","valor_media_mes"]]
    df_m = df_h.melt(id_vars="SLOT", var_name="Dia", value_name="Valor")
    matrix = df_m.pivot(index="Dia", columns="SLOT", values="Valor")

    fig3 = px.imshow(matrix, color_continuous_scale="Viridis")
    st.plotly_chart(fig3, use_container_width=True)

# =========================================================
# PAINEL 3 — SIMULAÇÃO
# =========================================================
def painel_simulacao_meta(resumo):

    st.subheader("🎯 Simulação de Meta")

    meta_atual = float(resumo["meta_dia"])
    projecao = float(resumo["projecao_dia"])
    venda_atual = float(resumo["venda_atual_ate_slot"])

    nova_meta = st.slider(
        "Nova Meta",
        int(meta_atual*0.5),
        int(meta_atual*1.5),
        int(meta_atual),
        step=50000
    )

    gap = projecao - nova_meta
    perc_cobertura = projecao/nova_meta if nova_meta>0 else 0

    c1,c2,c3 = st.columns(3)
    with c1:
        kpi_card("Meta atual", fmt_currency_br(meta_atual))
    with c2:
        kpi_card("Meta simulada", fmt_currency_br(nova_meta), color=WARNING)
    with c3:
        kpi_card("Gap simulado", fmt_currency_br(gap),
                 fmt_percent_br(perc_cobertura,1),
                 color=PRIMARY if gap>=0 else DANGER)

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

    st.markdown(
        """
        <div style="
            padding:14px 20px;
            border-radius:14px;
            background:linear-gradient(90deg,#00E676,#00B0FF);
            display:flex;
            justify-content:space-between;
            margin-bottom:15px;
        ">
            <div>
                <div style="font-size:1.2rem;font-weight:700;color:#001B20;">
                    Painel Executivo – FSJ Black Friday
                </div>
                <div style="font-size:0.85rem;color:#012A30;margin-top:4px;">
                    Monitor de projeção diária e ritmos intradia.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True
    )

    grid, resumo = load_grid_and_resumo(GRID_PATH, RESUMO_PATH)

    aba1, aba2, aba3 = st.tabs(["Visão Geral","Curvas & Ritmo","Simulação"])

    with aba1:
        painel_visao_geral(grid, resumo, st.session_state["user"])

    with aba2:
        painel_curvas_ritmo(grid, resumo)

    with aba3:
        painel_simulacao_meta(resumo)


if __name__ == "__main__":
    main()
