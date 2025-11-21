import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# ======================================================
# CONFIG GERAL
# ======================================================
st.set_page_config(
    page_title="FSJ Black Friday 2026 – Projeção de Vendas",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# CSS global (ajusta margens e deixa look mais clean)
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1.5rem;
        max-width: 1200px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.4rem;
    }
    .stTabs [data-baseweb="tab"] {
        padding-top: 0.6rem;
        padding-bottom: 0.6rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ======================================================
# HELPERS DE FORMATAÇÃO
# ======================================================
def fmt_moeda(v):
    if pd.isna(v):
        return "-"
    try:
        v = float(v)
    except Exception:
        return str(v)
    s = f"{v:,.0f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_int(v):
    if pd.isna(v):
        return "-"
    try:
        v = float(v)
    except Exception:
        return str(v)
    s = f"{v:,.0f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_perc(v, casas=1):
    if pd.isna(v):
        return "-"
    try:
        v = float(v)
    except Exception:
        return str(v)
    return f"{v*100:.{casas}f}%".replace(".", ",")


# ======================================================
# CARREGAMENTO DE DADOS
# ======================================================
@st.cache_data
def carregar_logins():
    df = pd.read_csv("data/logins.csv")
    # garante nomes corretos
    df.columns = [c.strip().lower() for c in df.columns]
    return df[["usuario", "senha", "nome"]]


@st.cache_data
def carregar_grid_resumo():
    grid = pd.read_csv("data/saida_grid.csv")
    resumo_df = pd.read_csv("data/saida_resumo.csv")

    # garante tipos
    if "data_referencia" in resumo_df.columns:
        resumo_df["data_referencia"] = pd.to_datetime(
            resumo_df["data_referencia"]
        ).dt.date

    resumo_raw = resumo_df.iloc[0].to_dict()

    resumo = {
        "data_referencia": resumo_raw["data_referencia"],
        "meta_dia": float(resumo_raw["meta_dia"]),
        "venda_atual": float(resumo_raw["venda_atual_ate_slot"]),
        "percentual_dia_hist": float(resumo_raw["percentual_dia_hist"]),
        "projecao": float(resumo_raw["projecao_dia"]),
        "desvio_projecao": float(resumo_raw["desvio_projecao"]),
        "total_d1": float(resumo_raw["total_d1"]),
        "meta_d1": float(resumo_raw["meta_d1"]),
        "desvio_d1": float(resumo_raw["desvio_d1"]),
        "total_d7": float(resumo_raw["total_d7"]),
        "meta_d7": float(resumo_raw["meta_d7"]),
        "desvio_d7": float(resumo_raw["desvio_d7"]),
        "ritmo_vs_d1": float(resumo_raw["ritmo_vs_d1"]),
        "ritmo_vs_d7": float(resumo_raw["ritmo_vs_d7"]),
        "ritmo_vs_media": float(resumo_raw["ritmo_vs_media"]),
    }

    return grid, resumo


# ======================================================
# LOGIN
# ======================================================
def login_screen(logins_df: pd.DataFrame):
    st.markdown(
        """
        <div style="
            background: linear-gradient(90deg,#00c853,#00e5ff);
            padding: 1.3rem 1.6rem;
            border-radius: 0.8rem;
            display:flex;
            align-items:center;
            justify-content:space-between;
        ">
            <div>
                <div style="font-size:0.9rem;color:#E0FFE8;">Bem-vindo ao painel da</div>
                <div style="font-size:1.6rem;font-weight:800;color:#FFFFFF;">
                    Farmácias São João – Black Friday 2026
                </div>
                <div style="font-size:0.9rem;color:#E0FFE8;margin-top:0.2rem;">
                    Tem Black na São João? <b>Tem Black na São João!</b> 🟢
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    col_esq, col_dir = st.columns([1.1, 0.9])

    with col_esq:
        st.markdown(
            """
            <div style="font-size:1.0rem;color:#CCCCCC;margin-top:0.2rem;">
                Para acessar o cockpit executivo, faça login com seu usuário corporativo.<br>
                <ul style="margin-top:0.5rem;">
                    <li>Indicadores 100% baseados na <b>curva intradia histórica</b>;</li>
                    <li>Comparação automática com <b>D-1</b>, <b>D-7</b> e <b>média do mês</b>;</li>
                    <li>Visão específica para decisão em tempo real na Black Friday.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_dir:
        st.markdown(
            "<div style='font-size:1.1rem;font-weight:600;margin-bottom:0.6rem;'>🔐 Acesso restrito</div>",
            unsafe_allow_html=True,
        )
        with st.form("login_form", clear_on_submit=False):
            user = st.text_input("Usuário")
            pwd = st.text_input("Senha", type="password")
            entrar = st.form_submit_button("Entrar 🚀")

        if entrar:
            row = logins_df[
                (logins_df["usuario"] == user) & (logins_df["senha"] == pwd)
            ]
            if not row.empty:
                st.session_state["logado"] = True
                st.session_state["usuario"] = user
                st.session_state["nome"] = row.iloc[0]["nome"]
                st.experimental_rerun()
            else:
                st.error("Usuário ou senha inválidos. Verifique e tente novamente.")


# ======================================================
# COMPONENTES VISUAIS
# ======================================================
def hero_header(resumo, nome_usuario: str):
    data_ref = resumo["data_referencia"]
    data_str = data_ref.strftime("%d/%m/%Y") if isinstance(data_ref, datetime) else str(
        data_ref
    )

    st.markdown(
        f"""
        <div style="
            background: radial-gradient(circle at 0% 0%,#00e676,#00b0ff);
            padding: 1.1rem 1.6rem;
            border-radius: 0.8rem;
            display:flex;
            align-items:center;
            justify-content:space-between;
        ">
            <div>
                <div style="font-size:1.6rem;font-weight:800;color:#FFFFFF;">
                    📊 FSJ Black Friday 2026 – Projeção de Vendas (Site + App)
                </div>
                <div style="font-size:0.9rem;color:#E0FFE8;margin-top:0.25rem;">
                    Usuário: <b>{nome_usuario}</b> • Data de referência: <b>{data_str}</b>
                </div>
            </div>
            <div style="text-align:right;font-size:0.85rem;color:#E0FFE8;">
                Feito por:<br><b>Planejamento e Dados E-Commerce</b><br>
                <span style="font-size:0.8rem;opacity:0.9;">
                    Tem Black na São João? Tem Black na São João! 🟢
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(titulo, valor, subtitulo="", cor="#00E676"):
    return f"""
        <div style="
            background:#101010;
            border-radius:0.8rem;
            padding:0.9rem 1.0rem;
            border:1px solid #222;
            min-height:5.4rem;
        ">
            <div style="font-size:0.80rem;color:#CCCCCC;margin-bottom:0.25rem;">
                {titulo}
            </div>
            <div style="font-size:1.6rem;font-weight:700;color:{cor};">
                {valor}
            </div>
            <div style="font-size:0.75rem;color:#999999;margin-top:0.15rem;">
                {subtitulo}
            </div>
        </div>
    """


# ======================================================
# MAIN
# ======================================================
def main():
    # -------- LOGIN --------
    logins_df = carregar_logins()

    if "logado" not in st.session_state:
        st.session_state["logado"] = False

    if not st.session_state["logado"]:
        login_screen(logins_df)
        return  # não continua enquanto não logar

    # -------- DADOS APÓS LOGIN --------
    grid, resumo = carregar_grid_resumo()
    nome_usuario = st.session_state.get("nome", st.session_state.get("usuario", ""))

    hero_header(resumo, nome_usuario)
    st.markdown("<br>", unsafe_allow_html=True)

    # ==================================================
    # TABS
    # ==================================================
    tab_visao, tab_curva, tab_sim, tab_metodo = st.tabs(
        ["📌 Visão Geral", "📈 Curva DDT", "🎯 Simulador de Meta", "🧠 Metodologia"]
    )

    # --------------------------------------------------
    # TAB 1 – VISÃO GERAL
    # --------------------------------------------------
    with tab_visao:
        st.markdown(
            "<h3 style='margin-bottom:0.8rem;'>🎯 Visão Geral do Dia</h3>",
            unsafe_allow_html=True,
        )

        meta = resumo["meta_dia"]
        venda = resumo["venda_atual"]
        proj = resumo["projecao"]
        gap = resumo["desvio_projecao"]
        d1 = resumo["total_d1"]
        d7 = resumo["total_d7"]
        frac_hist = resumo["percentual_dia_hist"]
        ritmo_d1 = resumo["ritmo_vs_d1"]
        ritmo_d7 = resumo["ritmo_vs_d7"]
        ritmo_med = resumo["ritmo_vs_media"]

        cor_gap = "#00E676" if gap >= 0 else "#FF1744"
        cor_proj = "#00E676" if proj >= meta else "#FF1744"

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(
                kpi_card("Meta do dia", fmt_moeda(meta), "", "#00E676"),
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                kpi_card("Venda atual", fmt_moeda(venda), "", "#00E676"),
                unsafe_allow_html=True,
            )
        with col3:
            st.markdown(
                kpi_card(
                    "Projeção de fechamento",
                    fmt_moeda(proj),
                    "Baseada na curva intradia histórica + ritmo atual.",
                    cor_proj,
                ),
                unsafe_allow_html=True,
            )
        with col4:
            st.markdown(
                kpi_card(
                    "Gap projetado vs meta",
                    fmt_moeda(gap),
                    "Positivo = tende a bater meta; negativo = deve ficar abaixo.",
                    cor_gap,
                ),
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        col5, col6, col7, col8 = st.columns(4)
        with col5:
            st.markdown(
                kpi_card(
                    "Total D-1 (dia inteiro)",
                    fmt_moeda(d1),
                    "Fechamento do dia anterior.",
                    "#FFFFFF",
                ),
                unsafe_allow_html=True,
            )
        with col6:
            st.markdown(
                kpi_card(
                    "Total D-7 (dia inteiro)",
                    fmt_moeda(d7),
                    "Fechamento do mesmo dia da semana passada.",
                    "#FFFFFF",
                ),
                unsafe_allow_html=True,
            )
        with col7:
            st.markdown(
                kpi_card(
                    "Ritmo vs D-1",
                    f"{ritmo_d1:,.2f}x".replace(".", ","),
                    "Acima de 1,0 = melhor que ontem no mesmo horário.",
                    "#FFD600",
                ),
                unsafe_allow_html=True,
            )
        with col8:
            st.markdown(
                kpi_card(
                    "Ritmo vs D-7",
                    f"{ritmo_d7:,.2f}x".replace(".", ","),
                    "Acima de 1,0 = melhor que a semana passada.",
                    "#FFD600",
                ),
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        col9, col10 = st.columns(2)
        with col9:
            st.markdown(
                kpi_card(
                    "Ritmo vs média do mês",
                    f"{ritmo_med:,.2f}x".replace(".", ","),
                    "Acima de 1,0 = acima da média intradia.",
                    "#FFD600",
                ),
                unsafe_allow_html=True,
            )
        with col10:
            st.markdown(
                kpi_card(
                    "Dia já percorrido (curva hist.)",
                    fmt_perc(frac_hist),
                    "Percentual médio do dia já realizado neste horário.",
                    "#FFC400",
                ),
                unsafe_allow_html=True,
            )

        # ------------------------ INSIGHTS ------------------------
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "<h4>🧠 Insights Estratégicos</h4>",
            unsafe_allow_html=True,
        )

        texto_insights = f"""
        - Até agora vendemos **{fmt_moeda(venda)}**, o que representa **{fmt_perc(frac_hist)}**
          da curva intradia histórica para este horário.<br>
        - A projeção de fechamento é de **{fmt_moeda(proj)}**, contra uma meta de
          **{fmt_moeda(meta)}**, resultando em um gap projetado de
          **<span style="color:{cor_gap};">{fmt_moeda(gap)}</span>**.<br>
        - Ontem (D-1) fechamos em **{fmt_moeda(d1)}**; há 7 dias (D-7) fechamos em
          **{fmt_moeda(d7)}**.<br>
        - O ritmo atual está em **{ritmo_d1:,.2f}x** vs D-1, **{ritmo_d7:,.2f}x** vs D-7
          e **{ritmo_med:,.2f}x** vs média do mês
          (valores acima de 1,00x indicam aceleração; abaixo de 1,00x indicam perda de tração).
        """
        st.markdown(
            f"""
            <div style="background:#081018;border-radius:0.8rem;padding:0.9rem 1.0rem;
                        border:1px solid #102030;font-size:0.9rem;color:#D0D0D0;">
                {texto_insights}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # --------------------------------------------------
    # TAB 2 – CURVA DDT
    # --------------------------------------------------
    with tab_curva:
        st.markdown(
            "<h3 style='margin-bottom:0.8rem;'>📈 Curva DDT – Slot a Slot</h3>",
            unsafe_allow_html=True,
        )

        grid_show = grid.copy()
        grid_show["SLOT"] = grid_show["SLOT"].astype(str)

        fig = px.line(
            grid_show,
            x="SLOT",
            y=["acum_hoje", "acum_d1", "acum_d7", "acum_media_mes"],
            labels={"value": "Faturamento acumulado", "SLOT": "Horário"},
        )
        fig.update_layout(
            legend_title_text="",
            height=420,
            margin=dict(l=10, r=10, t=30, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "#### Tabela detalhada (DDT)",
            unsafe_allow_html=True,
        )
        st.dataframe(grid_show, use_container_width=True, height=400)

    # --------------------------------------------------
    # TAB 3 – SIMULADOR DE META
    # --------------------------------------------------
    with tab_sim:
        st.markdown(
            "<h3 style='margin-bottom:0.8rem;'>🎯 Simulador de Meta</h3>",
            unsafe_allow_html=True,
        )

        col_a, col_b = st.columns([1, 1])
        with col_a:
            st.markdown("**Meta atual**")
            st.markdown(f"➡️ {fmt_moeda(meta)}")

            nova_meta = st.number_input(
                "Nova meta simulada (R$)", min_value=0.0, value=float(meta), step=50000.0
            )
        with col_b:
            gap_atual = proj - meta
            novo_gap = proj - nova_meta

            st.markdown("**Projeção de fechamento**")
            st.markdown(f"➡️ {fmt_moeda(proj)}")

            cor_novo_gap = "#00E676" if novo_gap >= 0 else "#FF1744"
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                f"""
                <div style="background:#101010;border-radius:0.8rem;padding:0.8rem 1.0rem;
                            border:1px solid #222;font-size:0.9rem;color:#EEEEEE;">
                    <b>Gap projetado com a nova meta:</b><br>
                    <span style="font-size:1.3rem;font-weight:700;color:{cor_novo_gap};">
                        {fmt_moeda(novo_gap)}
                    </span><br>
                    <span style="font-size:0.8rem;color:#BBBBBB;">
                        Positivo = tendência de bater a nova meta; negativo = tendência de ficar abaixo.
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            """
            <div style="font-size:0.85rem;color:#CCCCCC;">
                Use este simulador para testar metas alternativas ao longo do dia e entender rapidamente
                se o ritmo atual suporta um objetivo mais agressivo ou exige revisão.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # --------------------------------------------------
    # TAB 4 – METODOLOGIA
    # --------------------------------------------------
    with tab_metodo:
        st.markdown(
            "<h3 style='margin-bottom:0.8rem;'>🧠 Como a projeção é calculada</h3>",
            unsafe_allow_html=True,
        )

        frac = resumo["percentual_dia_hist"]
        texto_metodologia = f"""
        A projeção utiliza um modelo em **três camadas** para dar robustez ao número
        apresentado em **“Projeção de fechamento”**:

        **1. Curva intradia histórica**  
        • Para cada slot de 15 minutos, medimos qual fração do faturamento diário costuma estar
        realizada ao longo do mês.  
        • No horário atual, o padrão histórico indica que cerca de **{fmt_perc(frac)}** do dia já
        deveria estar vendido.

        **2. Base matemática de projeção**  
        • Consideramos a venda acumulada de hoje até o último slot: **{fmt_moeda(venda)}**.  
        • Dividimos esse valor pela fração histórica do horário atual, obtendo uma **projeção-base
        de fechamento**.  
        • Essa base resulta em aproximadamente **{fmt_moeda(proj)}** para o dia.

        **3. Camada de consistência por ritmo**  
        • Em paralelo, monitoramos os ritmos:
          • vs D-1: **{resumo['ritmo_vs_d1']:.2f}x** • vs D-7: **{resumo['ritmo_vs_d7']:.2f}x** • vs média do mês: **{resumo['ritmo_vs_media']:.2f}x**.  
        • Ritmos **acima de 1,00x** sugerem aceleração; **abaixo de 1,00x** indicam perda de tração.  
        • Esses indicadores funcionam como uma **checagem de consistência** da projeção: se o dia
          foge muito do padrão, isso aparece imediatamente nos ritmos.

        **Conclusão executiva**  
        Com esse conjunto de sinais, projetamos o fechamento em **{fmt_moeda(proj)}**, o que representa
        um gap de **{fmt_moeda(gap)}** em relação à meta consolidada de **{fmt_moeda(meta)}**.
        """
        st.markdown(
            f"""
            <div style="background:#081018;border-radius:0.8rem;padding:1.0rem 1.1rem;
                        border:1px solid #102030;font-size:0.9rem;color:#D0D0D0;">
                {texto_metodologia}
            </div>
            """,
            unsafe_allow_html=True,
        )


# ======================================================
# RUN
# ======================================================
if __name__ == "__main__":
    main()
