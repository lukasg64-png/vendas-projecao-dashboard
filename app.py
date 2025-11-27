import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import html

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
DANGER  = "#FF1744"
WARNING = "#FFD54F"
CARD_BG = "#111111"


# =========================================================
# HELPERS: LOADS & AUTENTICAÇÃO
# =========================================================
@st.cache_data
def load_logins(path: Path) -> pd.DataFrame:
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


@st.cache_data
def load_grid_and_resumo(grid_path: Path, resumo_path: Path):
    grid = pd.read_csv(grid_path)
    resumo_df = pd.read_csv(resumo_path)
    return grid, resumo_df.iloc[0].to_dict()


# =========================================================
# HELPERS: FORMATAÇÃO
# =========================================================
def fmt_currency_br(x, decimals: int = 0):
    try:
        if x is None or np.isnan(x):
            return "-"
    except:
        pass
    txt = f"{float(x):,.{decimals}f}"
    txt = txt.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {txt}"


def fmt_percent_br(x, decimals: int = 2):
    try:
        if x is None or np.isnan(x):
            return "-"
    except:
        return "-"
    pct = float(x) * 100
    txt = f"{pct:,.{decimals}f}"
    txt = txt.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{txt}%"


def fmt_number_br(x, decimals: int = 2):
    try:
        if x is None or np.isnan(x):
            return "-"
    except:
        pass
    txt = f"{float(x):,.{decimals}f}"
    txt = txt.replace(",", "X").replace(".", ",").replace("X", ".")
    return txt


# =========================================================
# VISUAIS (CARDS E GAUGES)
# =========================================================
def kpi_card(title, value, subtitle="", color=PRIMARY, tooltip=None):
    info = ""
    if tooltip:
        info = f"<span style='margin-left:6px;cursor:help;' title='{html.escape(tooltip)}'>ℹ️</span>"

    block = f"""
    <div style="
        background:{CARD_BG};
        padding:18px 20px;
        border-radius:12px;
        border:1px solid #333;
        box-shadow:0 0 10px rgba(0,0,0,0.4);
    ">
        <div style="font-size:0.8rem;color:#BBBBBB;display:flex;justify-content:space-between;">
            <span>{html.escape(title)}</span>{info}
        </div>
        <div style="font-size:1.7rem;font-weight:700;margin-top:4px;color:{color};">
            {value}
        </div>
        <div style="font-size:0.75rem;color:#888888;margin-top:6px;">
            {subtitle}
        </div>
    </div>
    """
    st.markdown(block, unsafe_allow_html=True)


# === GAUGES CORRIGIDOS ===
def gauge_ritmo(title: str, valor: float, tooltip: str = ""):

    # cor da barra conforme o ritmo
    bar_color = (
        PRIMARY if valor >= 1
        else WARNING if valor >= 0.8
        else DANGER
    )

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=valor,
            number={"valueformat": ".2f", "font": {"size": 32}},
            title={"text": title, "font": {"size": 16}},
            gauge={
                "axis": {"range": [0, 2.0]},
                "bar": {"color": bar_color},
                "steps": [
                    {"range": [0.0, 0.8], "color": "#2A2A2A"},
                    {"range": [0.8, 1.0], "color": "#424242"},
                    {"range": [1.0, 1.2], "color": "#00695C"},
                    {"range": [1.2, 2.0], "color": "#1B5E20"},
                ],
                "threshold": {
                    "line": {"color": WARNING, "width": 4},
                    "thickness": 0.8,
                    "value": 1.0,
                },
            },
        )
    )

    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        height=260,
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#EEEEEE"},
    )

    if tooltip:
        st.caption(tooltip)

    st.plotly_chart(fig, use_container_width=True)


# =========================================================
# LOGIN
# =========================================================
def login_screen(df_logins: pd.DataFrame):

    st.markdown(
        """
        <div style="
            padding:18px 22px;
            border-radius:14px;
            background:linear-gradient(90deg,#00E676,#00B0FF);
            display:flex;justify-content:space-between;">
            <div>
                <div style="font-size:1.4rem;font-weight:700;color:#001B20;">
                    FSJ Black Friday – Painel de Projeção
                </div>
                <div style="font-size:0.9rem;color:#012A30;margin-top:4px;">
                    Bem-vindo, São João! <b>Tem Black na São João! 🔥</b>
                </div>
            </div>
            <div style="
                font-size:0.75rem;color:#012A30;
                background:rgba(255,255,255,0.85);
                padding:6px 12px;border-radius:999px;">
                Feito por: Planejamento e Dados E-Commerce
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    card = st.columns([1, 2, 1])[1]
    with card:
        st.markdown(
            """
            <div style="
                background:#0F172A;padding:20px 22px;border-radius:14px;
                border:1px solid #1E293B;box-shadow:0 0 20px rgba(0,0,0,0.5);
            ">
                <div style="font-size:1.1rem;font-weight:600;color:#E5E7EB;margin-bottom:10px;">
                    🔐 Acesse o painel
                </div>
            """,
            unsafe_allow_html=True,
        )

        ucol, pcol = st.columns(2)
        username = ucol.text_input("Usuário")
        password = pcol.text_input("Senha", type="password")

        if st.button("Entrar", type="primary", use_container_width=True):
            ok, nome = authenticate(username.strip(), password.strip(), df_logins)
            if ok:
                st.session_state["auth"] = True
                st.session_state["user_name"] = nome
                st.experimental_rerun()
            else:
                st.error("Usuário ou senha inválidos.")

        st.caption("Usuários carregados de `data/logins.csv`.")
        st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# PAINEL 1 — VISÃO GERAL
# =========================================================
def painel_visao_geral(grid, resumo, user_name):

    data_ref = pd.to_datetime(resumo["data_referencia"]).date()
    meta_dia = float(resumo["meta_dia"])
    venda = float(resumo["venda_atual_ate_slot"])
    proj = float(resumo["projecao_dia"])
    gap = float(resumo["desvio_projecao"])
    total_d1 = float(resumo["total_d1"])
    total_d7 = float(resumo["total_d7"])
    r1 = float(resumo["ritmo_vs_d1"])
    r7 = float(resumo["ritmo_vs_d7"])
    rm = float(resumo["ritmo_vs_media"])
    frac = float(resumo["percentual_dia_hist"])

    st.markdown(
        f"""
        <div style="color:#BBB;font-size:0.9rem;margin-bottom:10px;">
            Usuário: <b>{html.escape(user_name)}</b> •
            Data: <b>{data_ref.strftime('%d/%m/%Y')}</b> •
            Canal: Site + App
        </div>
        """, unsafe_allow_html=True
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        kpi_card("Meta do dia", fmt_currency_br(meta_dia),
                 "Meta consolidada Site + App.")

    with c2:
        perc_meta = venda / meta_dia if meta_dia > 0 else 0
        kpi_card("Venda atual", fmt_currency_br(venda),
                 f"{fmt_percent_br(perc_meta,1)} da meta.",
                 PRIMARY if perc_meta >= frac else WARNING)

    with c3:
        kpi_card("Projeção de fechamento", fmt_currency_br(proj),
                 "Base histórica + ritmo atual.",
                 PRIMARY if proj >= meta_dia else WARNING)

    with c4:
        lbl = "Acima da meta" if gap >= 0 else "Abaixo da meta"
        col = PRIMARY if gap >= 0 else DANGER
        kpi_card("Gap projetado", fmt_currency_br(gap), lbl, col)

    st.markdown("---")

    # === RITMOS ===
    st.subheader("📈 Ritmo do dia", divider="gray")

    c5, c6, c7, c8 = st.columns(4)

    with c5:
        kpi_card("Total D-1", fmt_currency_br(total_d1),
                 "Fechamento de ontem.")

    with c6:
        kpi_card("Total D-7", fmt_currency_br(total_d7),
                 "Fechamento semana anterior.")

    with c7:
        kpi_card("Dia já percorrido", fmt_percent_br(frac,1),
                 "Fração média histórica.")

    # === CORRIGIDO: RITMO COMBINADO COM VALOR ===
    with c8:
        ritmo_comb = (r1 + r7 + rm) / 3
        txt = (
            f"vs D-1: {fmt_number_br(r1,2)}x • "
            f"vs D-7: {fmt_number_br(r7,2)}x • "
            f"vs média: {fmt_number_br(rm,2)}x"
        )
        cor = PRIMARY if ritmo_comb >= 1 else WARNING
        kpi_card("Ritmo combinado", f"{fmt_number_br(ritmo_comb,2)}x",
                 txt, cor)

    # explicação
    with st.expander("🧠 Como interpretar os ritmos"):
        st.markdown(
            f"""
            - **Ritmo vs D-1:** {fmt_number_br(r1,2)}x  
            - **Ritmo vs D-7:** {fmt_number_br(r7,2)}x  
            - **Ritmo vs média do mês:** {fmt_number_br(rm,2)}x  
            """
        )

    # === Análise executiva ===
    st.subheader("📝 Análise executiva da projeção", divider="gray")
    frac_txt = fmt_percent_br(frac, 2)

    st.markdown(
        f"""
        ### Como projetamos o fechamento
        - O padrão histórico indica que **{frac_txt}** do dia deveria estar vendido agora.  
        - A venda acumulada é **{fmt_currency_br(venda)}**, projetando **{fmt_currency_br(proj)}**.  
        - Ritmos mostram se estamos acelerando ou desacelerando.  
        - Gap final estimado: **{fmt_currency_br(gap)}**.
        """
    )


# =========================================================
# PAINEL 2 — CURVAS & RITMO
# =========================================================
def painel_curvas_ritmo(grid, resumo):

    st.subheader("📊 Curvas de venda (DDT)", divider="gray")

    fig1 = px.line(
        grid, x="SLOT",
        y=["valor_hoje","valor_d1","valor_d7","valor_media_mes"],
        labels={"value":"Valor (R$)"}
    )
    fig1.update_layout(
        margin=dict(l=20,r=20,t=40,b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color":"#EEE"},
    )
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("📈 Ritmos ao longo do dia", divider="gray")

    proj = float(resumo["projecao_dia"])
    grid2 = grid.copy()
    grid2["perc"] = grid2["acum_hoje"] / proj if proj > 0 else 0

    df_r = pd.DataFrame({
        "SLOT": grid2["SLOT"],
        "Ritmo vs D-1": grid2["ritmo_vs_d1"],
        "Ritmo vs D-7": grid2["ritmo_vs_d7"],
        "Ritmo vs média": grid2["ritmo_vs_media"],
        "% realizado": grid2["perc"],
    })

    fig2 = px.line(df_r, x="SLOT",
                   y=["Ritmo vs D-1","Ritmo vs D-7","Ritmo vs média","% realizado"])
    fig2.update_layout(
        margin=dict(l=20,r=20,t=40,b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color":"#EEE"},
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.caption(
        "- As três primeiras linhas são ritmos.  
        - A última mostra o % do dia já realizado pela projeção."
    )

    # === GAUGES CORRIGIDOS ===
    st.subheader("🧭 Saúde do dia – gauges de ritmo", divider="gray")

    r1 = float(resumo["ritmo_vs_d1"])
    r7 = float(resumo["ritmo_vs_d7"])
    rm = float(resumo["ritmo_vs_media"])

    g1,g2,g3 = st.columns(3)
    with g1:
        gauge_ritmo("Ritmo vs D-1", r1, "1,00x = em linha com ontem.")
    with g2:
        gauge_ritmo("Ritmo vs D-7", r7, "1,00x = em linha com semana passada.")
    with g3:
        gauge_ritmo("Ritmo vs média", rm, "1,00x = comportamento médio do mês.")

    # === HEATMAP ===
    st.subheader("🔥 Mapa de calor – intensidade por horário", divider="gray")

    df_heat = pd.DataFrame({
        "SLOT": grid["SLOT"],
        "Hoje": grid["valor_hoje"],
        "D-1": grid["valor_d1"],
        "D-7": grid["valor_d7"],
        "Média": grid["valor_media_mes"],
    })
    melt = df_heat.melt(id_vars="SLOT")
    heat = melt.pivot(index="variable", columns="SLOT", values="value")

    fig_h = px.imshow(heat, color_continuous_scale="Viridis")
    fig_h.update_layout(
        margin=dict(l=40,r=40,t=40,b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color":"#EEE"},
    )
    st.plotly_chart(fig_h, use_container_width=True)

    with st.expander("🧾 Tabela completa"):
        st.dataframe(grid, use_container_width=True)


# =========================================================
# PAINEL 3 — SIMULAÇÃO
# =========================================================
def painel_simulacao_meta(resumo):

    st.subheader("🎯 Simulação de meta e gap", divider="gray")

    meta = float(resumo["meta_dia"])
    proj = float(resumo["projecao_dia"])
    venda = float(resumo["venda_atual_ate_slot"])

    nova = st.slider(
        "Meta simulada (R$)",
        min_value=int(meta*0.5),
        max_value=int(meta*1.5),
        value=int(meta),
        step=50000,
    )

    gap = proj - nova
    cov = proj / nova if nova else 0

    c1,c2,c3 = st.columns(3)

    with c1:
        kpi_card("Meta atual", fmt_currency_br(meta), "", PRIMARY)
    with c2:
        kpi_card("Meta simulada", fmt_currency_br(nova), "", WARNING)
    with c3:
        kpi_card("Novo gap", fmt_currency_br(gap),
                 f"{fmt_percent_br(cov,1)} de cobertura",
                 PRIMARY if gap>=0 else DANGER)

    st.markdown(
        f"- Venda atual: **{fmt_currency_br(venda)}**  
         - Projeção: **{fmt_currency_br(proj)}**  
         - Gap simulado: **{fmt_currency_br(gap)}**"
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

    user = st.session_state.get("user_name", "")

    st.markdown(
        """
        <div style="
            padding:14px 20px;border-radius:14px;
            background:linear-gradient(90deg,#00E676,#00B0FF);
            display:flex;justify-content:space-between;
            margin-bottom:16px;">
            <div>
                <div style="font-size:1.2rem;font-weight:700;color:#001B20;">
                    Painel Executivo – FSJ Black Friday
                </div>
                <div style="color:#012A30;font-size:0.85rem;">
                    Monitoramento diário de projeção, ritmo e curva intradia.
                </div>
            </div>
            <div style="
                font-size:0.75rem;color:#012A30;
                background:rgba(255,255,255,0.85);
                padding:6px 14px;border-radius:999px;">
                Feito por: Planejamento e Dados E-Commerce
            </div>
        </div>
        """, unsafe_allow_html=True
    )

    grid, resumo = load_grid_and_resumo(GRID_PATH, RESUMO_PATH)

    aba1,aba2,aba3 = st.tabs([
        "Visão Geral",
        "Curvas & Ritmo",
        "Simulação de Meta"
    ])

    with aba1:
        painel_visao_geral(grid, resumo, user)
    with aba2:
        painel_curvas_ritmo(grid, resumo)
    with aba3:
        painel_simulacao_meta(resumo)


if __name__ == "__main__":
    main()
