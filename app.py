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
# HELPERS
# =========================================================

def fmt_number_br(x, decimals=2):
    try:
        return f"{x:.{decimals}f}".replace(".", ",")
    except:
        return "-"

@st.cache_data
def load_logins(path: Path) -> pd.DataFrame:
    if not path.exists():
        df = pd.DataFrame(
            [
                {
                    "usuario": "farmacias_sao_joao",
                    "senha": "blackfriday2025",
                    "nome": "Time E-commerce",
                }
            ]
        )
        return df
    df = pd.read_csv(path, dtype=str).fillna("")
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
    if x is None:
        return "-"
    try:
        if np.isnan(x): return "-"
    except: pass
    fmt = f"{x:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {fmt}"

def fmt_percent_br(x: float, decimals: int = 2) -> str:
    if x is None:
        return "-"
    try:
        if np.isnan(x): return "-"
    except: pass
    pct = x * 100
    fmt = f"{pct:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{fmt}%"


def kpi_card(title, value, subtitle="", color=PRIMARY, tooltip=None):
    info = f"<span style='margin-left:6px; cursor:help;' title='{tooltip}'>ℹ️</span>" if tooltip else ""

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
            {info}
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
            <div style="font-size:0.75rem;color:#012A30;background:rgba(255,255,255,0.85);
                        padding:6px 14px;border-radius:999px;">
                Feito por: Planejamento e Dados E-Commerce
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col = st.columns([1, 1, 1])[1]
    with col:
        st.markdown("<div style='font-size:1.05rem;font-weight:600;margin-bottom:8px;'>🔐 Acesse o painel</div>", unsafe_allow_html=True)

        user = st.text_input("Usuário")
        pwd = st.text_input("Senha", type="password")

        if st.button("Entrar", type="primary", use_container_width=True):
            ok, nome = authenticate(user.strip(), pwd.strip(), df_logins)
            if ok:
                st.session_state["auth"] = True
                st.session_state["user_name"] = nome
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")

        st.caption("Usuários carregados de data/logins.csv")


# =========================================================
# DATA LOADING
# =========================================================
@st.cache_data
def load_grid_and_resumo(gpath, rpath):
    return pd.read_csv(gpath), pd.read_csv(rpath).iloc[0].to_dict()


# =========================================================
# PAINEL TAB 1 – VISÃO GERAL
# =========================================================
def painel_visao_geral(grid, resumo, user_name):
    data_ref = pd.to_datetime(resumo["data_referencia"]).date()

    meta_dia   = float(resumo["meta_dia"])
    venda_atual = float(resumo["venda_atual_ate_slot"])
    projecao   = float(resumo["projecao_dia"])
    gap        = float(resumo["desvio_projecao"])
    total_d1   = float(resumo["total_d1"])
    total_d7   = float(resumo["total_d7"])
    ritmo_d1   = float(resumo["ritmo_vs_d1"])
    ritmo_d7   = float(resumo["ritmo_vs_d7"])
    ritmo_med  = float(resumo["ritmo_vs_media"])
    frac_hist  = float(resumo["percentual_dia_hist"])

    st.markdown(
        f"""
        <div style="margin-bottom:10px;font-size:0.9rem;color:#BBBBBB;">
            Usuário: <b>{user_name}</b> • Data: <b>{data_ref.strftime('%d/%m/%Y')}</b> • Canal: Site + App
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- KPIs linha 1 ---
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Meta do dia", fmt_currency_br(meta_dia), "Meta consolidada de hoje.")
    with c2:
        kpi_card("Venda atual", fmt_currency_br(venda_atual),
                 f"{fmt_percent_br(venda_atual/meta_dia,1)} da meta.")
    with c3:
        kpi_card("Projeção de fechamento", fmt_currency_br(projecao),
                 "Base histórica + ritmo atual.")
    with c4:
        kpi_card("Gap projetado", fmt_currency_br(gap),
                 "Diferença entre projeção e meta.",
                 color=PRIMARY if gap>=0 else DANGER)

    st.markdown("---")

    # --- Ritmos e totais ---
    st.subheader("📈 Ritmo do Dia", divider="gray")

    c5, c6, c7, c8 = st.columns(4)

    with c5:
        kpi_card("Total D-1", fmt_currency_br(total_d1), "Fechamento de ontem.")
    with c6:
        kpi_card("Total D-7", fmt_currency_br(total_d7), "Mesmo dia semana passada.")
    with c7:
        kpi_card("Dia já percorrido", fmt_percent_br(frac_hist,1), "Fraçao histórica até agora.")

    # --- Ritmo Combinado (corrigido!) ---
    with c8:
        ritmo_comb = (ritmo_d1 + ritmo_d7 + ritmo_med) / 3
        legenda = (
            f"vs D-1: {fmt_number_br(ritmo_d1)}x • "
            f"vs D-7: {fmt_number_br(ritmo_d7)}x • "
            f"vs mês: {fmt_number_br(ritmo_med)}x"
        )
        kpi_card(
            "Ritmo combinado",
            f"{fmt_number_br(ritmo_comb)}x",
            legenda,
            color=PRIMARY if ritmo_comb>=1 else WARNING,
            tooltip="Média dos ritmos. Acima de 1,00x = aceleração."
        )


# =========================================================
# PAINEL TAB 2 – CURVAS & RITMO
# =========================================================
def painel_curvas_ritmo(grid, resumo):
    st.subheader("📊 Curvas de venda (DDT)", divider="gray")

    fig_curva = px.line(
        grid,
        x="SLOT",
        y=["valor_hoje","valor_d1","valor_d7","valor_media_mes"],
        labels={"value":"R$","SLOT":"Horário","variable":"Curva"},
    )
    st.plotly_chart(fig_curva, use_container_width=True)

    st.subheader("📈 Ritmos ao longo do dia", divider="gray")

    proj = float(resumo["projecao_dia"])
    grid = grid.copy()
    grid["perc_dia_realizado"] = grid["acum_hoje"]/proj if proj>0 else 0

    df_r = pd.DataFrame({
        "SLOT": grid["SLOT"],
        "Ritmo vs D-1": grid["ritmo_vs_d1"],
        "Ritmo vs D-7": grid["ritmo_vs_d7"],
        "Ritmo vs mês": grid["ritmo_vs_media"],
        "% do dia realizado": grid["perc_dia_realizado"],
    })

    fig_r = px.line(df_r, x="SLOT", y=df_r.columns[1:], labels={"SLOT":"Horário"})
    st.plotly_chart(fig_r, use_container_width=True)

    st.subheader("🔥 Mapa de calor", divider="gray")

    df_heat = grid[["SLOT","valor_hoje","valor_d1","valor_d7","valor_media_mes"]]
    melt = df_heat.melt("SLOT", var_name="Dia", value_name="Valor")
    mat = melt.pivot(index="Dia", columns="SLOT", values="Valor")

    fig_heat = px.imshow(mat, color_continuous_scale="Viridis", aspect="auto")
    st.plotly_chart(fig_heat, use_container_width=True)


# =========================================================
# PAINEL TAB 3 – SIMULAÇÃO
# =========================================================
def painel_simulacao_meta(resumo):
    st.subheader("🎯 Simulação de Meta", divider="gray")

    meta = float(resumo["meta_dia"])
    proj = float(resumo["projecao_dia"])
    venda_atual = float(resumo["venda_atual_ate_slot"])

    nova = st.slider("Nova meta simulada", int(meta*0.5), int(meta*1.5), int(meta), step=50000)

    gap_sim = proj - nova
    cob = proj / nova if nova else 0

    c1, c2, c3 = st.columns(3)
    with c1: kpi_card("Meta oficial", fmt_currency_br(meta))
    with c2: kpi_card("Meta simulada", fmt_currency_br(nova), color=WARNING)
    with c3:
        kpi_card("Gap simulado", fmt_currency_br(gap_sim),
                 f"Cobertura: {fmt_percent_br(cob,1)}",
                 color=PRIMARY if gap_sim>=0 else DANGER)


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

    # Barra topo
    st.markdown(
        """
        <div style="
            padding:14px 20px;
            border-radius:14px;
            background:linear-gradient(90deg,#00E676,#00B0FF);
            margin-bottom:16px;">
            <div style="font-size:1.2rem;font-weight:700;color:#001B20;">
                Painel Executivo – FSJ Black Friday
            </div>
            <div style="font-size:0.85rem;color:#012A30;">
                Monitor diário de vendas, projeção e ritmo.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    grid, resumo = load_grid_and_resumo(GRID_PATH, RESUMO_PATH)

    aba1, aba2, aba3 = st.tabs(["Visão Geral", "Curvas & Ritmo", "Simulação"])

    with aba1: painel_visao_geral(grid, resumo, st.session_state["user_name"])
    with aba2: painel_curvas_ritmo(grid, resumo)
    with aba3: painel_simulacao_meta(resumo)


if __name__ == "__main__":
    main()
