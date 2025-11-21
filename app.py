import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ============================================================
# CONFIGURAÇÃO BÁSICA DO APP
# ============================================================
st.set_page_config(
    page_title="FSJ Black Friday – Projeção de Vendas",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# CSS GLOBAL (só coisas neutras, ok aparecer antes do login)
# ============================================================
BASE_CSS = """
<style>
body {
    background-color: #05070A;
}
/* Remove o espaço padrão do topo */
.block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
}

/* Banner superior */
.fsj-banner {
    background: linear-gradient(90deg, #00E676, #00B0FF);
    border-radius: 14px;
    padding: 12px 22px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: #fff;
    margin-bottom: 1.5rem;
}
.fsj-banner-title {
    font-size: 1.25rem;
    font-weight: 700;
}
.fsj-banner-sub {
    font-size: 0.85rem;
    opacity: 0.9;
}
.fsj-banner-tag {
    background: rgba(0,0,0,0.3);
    padding: 6px 14px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
}

/* LOGIN */
.login-wrapper {
    min-height: 80vh;
    display: flex;
    align-items: flex-start;
    justify-content: center;
}
.login-card {
    margin-top: 3rem;
    background: #0C1018;
    border-radius: 16px;
    padding: 24px 26px 28px 26px;
    max-width: 420px;
    width: 100%;
    box-shadow: 0 14px 40px rgba(0,0,0,0.65);
    border: 1px solid #1E293B;
}
.login-title {
    font-size: 1.4rem;
    font-weight: 700;
    color: #E5F9FF;
    margin-bottom: 0.25rem;
}
.login-subtitle {
    font-size: 0.9rem;
    color: #B0BEC5;
    margin-bottom: 1.0rem;
}
.login-slogan {
    font-size: 0.95rem;
    font-weight: 600;
    color: #00E676;
    margin-bottom: 1.0rem;
}
.login-footer {
    margin-top: 0.75rem;
    font-size: 0.75rem;
    color: #90A4AE;
    text-align: right;
}

/* Inputs de login */
.stTextInput > div > div > input {
    background-color: #02040A !important;
    border-radius: 8px !important;
}

/* Botão login */
.stButton>button {
    width: 100%;
    border-radius: 999px;
    border: none;
    background: linear-gradient(90deg,#00E676,#00B0FF);
    color: #021017;
    font-weight: 700;
}

/* Títulos de seção */
.section-title {
    font-size: 1.4rem;
    font-weight: 700;
    color: #E5F9FF;
    margin: 0.8rem 0 0.3rem 0;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}

/* Cards KPI */
.kpi-card {
    background: #080C14;
    border-radius: 12px;
    padding: 16px 18px;
    border: 1px solid #1F2933;
    height: 100%;
}
.kpi-label {
    font-size: 0.80rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: #9FA8B3;
    margin-bottom: 0.25rem;
    display: flex;
    align-items: center;
    gap: 0.25rem;
}
.kpi-main {
    font-size: 1.6rem;
    font-weight: 700;
    color: #E5F9FF;
}
.kpi-sub {
    font-size: 0.80rem;
    color: #90A4AE;
    margin-top: 0.25rem;
}
.kpi-pill {
    font-size: 0.75rem;
    border-radius: 999px;
    padding: 2px 8px;
    display: inline-block;
}

/* Texto colorido */
.good   { color: #00E676 !important; }
.bad    { color: #FF1744 !important; }
.neutral{ color: #FFC400 !important; }

/* Tooltipzinho inline: apenas ícone visual, o texto será explicado em cards abaixo */
.kpi-info-icon {
    font-size: 0.75rem;
    opacity: 0.75;
}

/* Caixas de explicação */
.expl-box {
    background: #050A12;
    border-radius: 10px;
    padding: 14px 16px;
    border: 1px solid #1F2933;
    font-size: 0.85rem;
    color: #CFD8DC;
}

/* Tabs mais destacadas */
[data-baseweb="tab"].stTabs_tab {
    font-size: 0.9rem;
}

/* Ajuste do rodapé */
footer {visibility: hidden;}
</style>
"""

st.markdown(BASE_CSS, unsafe_allow_html=True)

# ============================================================
# HELPERS
# ============================================================
@st.cache_data
def load_logins():
    df = pd.read_csv("data/logins.csv")
    return df


@st.cache_data
def load_data():
    grid = pd.read_csv("data/saida_grid.csv")
    resumo = pd.read_csv("data/saida_resumo.csv")
    resumo["data_referencia"] = pd.to_datetime(
        resumo["data_referencia"]
    ).dt.date
    return grid, resumo


def fmt_currency_br(x: float) -> str:
    if pd.isna(x):
        return "-"
    return "R$ " + f"{x:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_number_br(x: float, decimals: int = 2) -> str:
    if pd.isna(x):
        return "-"
    fmt = f"{x:,.{decimals}f}"
    return fmt.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_percent(x: float) -> str:
    if pd.isna(x):
        return "-"
    return fmt_number_br(x * 100, 2) + "%"


def kpi_card(col, label, value, subtitle="", value_class=""):
    with col:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">{label}</div>
                <div class="kpi-main {value_class}">{value}</div>
                <div class="kpi-sub">{subtitle}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def login_screen():
    df_login = load_logins()

    st.markdown(
        """
        <div class="login-wrapper">
          <div class="login-card">
            <div class="login-title">FSJ Black Friday – Painel de Vendas</div>
            <div class="login-subtitle">
              Acompanhe projeção intradia, ritmo vs histórico e gaps de meta em tempo real.
            </div>
            <div class="login-slogan">
              Tem Black na São João? <span style="color:#FFFFFF;">TEM BLACK NA SÃO JOÃO!</span>
            </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form"):
        user = st.text_input("Usuário")
        pwd = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")

    if submitted:
        row = df_login[
            (df_login["usuario"].astype(str) == str(user))
            & (df_login["senha"].astype(str) == str(pwd))
        ]
        if not row.empty:
            st.session_state["auth"] = True
            st.session_state["usuario"] = row.iloc[0]["usuario"]
            st.session_state["nome"] = row.iloc[0].get("nome", row.iloc[0]["usuario"])
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha inválidos. Confira login e senha.")

    st.markdown(
        """
            <div class="login-footer">
              Feito por: <b>Planejamento e Dados E-Commerce</b>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# GATE DE LOGIN
# ============================================================
if "auth" not in st.session_state or not st.session_state["auth"]:
    login_screen()
    st.stop()

# ============================================================
# APÓS LOGIN: CARREGAR DADOS
# ============================================================
grid, resumo = load_data()
res = resumo.iloc[0]

meta_dia = float(res["meta_dia"])
venda_atual = float(res["venda_atual_ate_slot"])
proj = float(res["projecao_dia"])
gap_proj = float(res["desvio_projecao"])

total_d1 = float(res["total_d1"])
meta_d1 = float(res["meta_d1"])
desvio_d1 = float(res["desvio_d1"])

total_d7 = float(res["total_d7"])
meta_d7 = float(res["meta_d7"])
desvio_d7 = float(res["desvio_d7"])

perc_hist = float(res["percentual_dia_hist"])
ritmo_d1 = float(res["ritmo_vs_d1"])
ritmo_d7 = float(res["ritmo_vs_d7"])
ritmo_media = float(res["ritmo_vs_media"])
data_ref = res["data_referencia"]

# KPIs derivados
perc_meta_atual = venda_atual / meta_dia if meta_dia > 0 else np.nan
perc_meta_proj = proj / meta_dia if meta_dia > 0 else np.nan

# ============================================================
# BANNER TOP
# ============================================================
st.markdown(
    f"""
    <div class="fsj-banner">
      <div>
        <div class="fsj-banner-title">📊 Painel Executivo – FSJ Black Friday</div>
        <div class="fsj-banner-sub">
          Data de referência: <b>{data_ref.strftime('%d/%m/%Y')}</b> • Canal: Site + App • Usuário: <b>{st.session_state.get('nome','')}</b>
        </div>
      </div>
      <div class="fsj-banner-tag">
        Feito por: Planejamento e Dados E-Commerce
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# TABS PRINCIPAIS
# ============================================================
aba_visao, aba_curvas, aba_simulacao, aba_metodo = st.tabs(
    ["Visão Geral", "Curvas & Ritmo", "Simulação de Meta", "Metodologia"]
)

# ============================================================
# ABA 1 – VISÃO GERAL
# ============================================================
with aba_visao:
    st.markdown(
        '<div class="section-title">🎯 Visão Geral do Dia</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)

    # Meta do dia
    kpi_card(
        c1,
        "Meta do Dia",
        fmt_currency_br(meta_dia),
        "Meta consolidada Site + App.",
        "good",
    )

    # Venda atual
    kpi_card(
        c2,
        "Venda Atual",
        fmt_currency_br(venda_atual),
        f"Equivale a {fmt_percent(perc_meta_atual)} da meta.",
        "good",
    )

    # Projeção
    proj_class = "good" if proj >= meta_dia else "bad"
    kpi_card(
        c3,
        "Projeção de Fechamento",
        fmt_currency_br(proj),
        f"≈ {fmt_percent(perc_meta_proj)} da meta consolidada.",
        proj_class,
    )

    # Gap projetado
    gap_class = "good" if gap_proj >= 0 else "bad"
    gap_label_extra = "ACIMA da meta" if gap_proj >= 0 else "ABAIXO da meta"
    kpi_card(
        c4,
        "Gap Projetado vs Meta",
        fmt_currency_br(gap_proj),
        f"{gap_label_extra}.",
        gap_class,
    )

    st.markdown(
        '<div class="section-title">⏱️ Ritmo do dia</div>',
        unsafe_allow_html=True,
    )

    r1, r2, r3 = st.columns(3)

    # Ritmo vs D-1
    ritmo_d1_class = "good" if ritmo_d1 >= 1 else "bad"
    kpi_card(
        r1,
        "Ritmo vs D-1",
        fmt_number_br(ritmo_d1, 2) + "x",
        "Relação entre o acumulado de hoje e o acumulado de ontem no mesmo horário.",
        ritmo_d1_class,
    )

    # Ritmo vs D-7
    ritmo_d7_class = "good" if ritmo_d7 >= 1 else "bad"
    kpi_card(
        r2,
        "Ritmo vs D-7",
        fmt_number_br(ritmo_d7, 2) + "x",
        "Compara hoje com o mesmo dia da semana passada, slot a slot.",
        ritmo_d7_class,
    )

    # Ritmo vs média
    ritmo_media_class = "good" if ritmo_media >= 1 else "bad"
    kpi_card(
        r3,
        "Ritmo vs média do mês",
        fmt_number_br(ritmo_media, 2) + "x",
        "Quanto o dia está acelerado vs o padrão médio do mês.",
        ritmo_media_class,
    )

    st.markdown(
        '<div class="section-title">🧠 Insights Estratégicos</div>',
        unsafe_allow_html=True,
    )

    # Caixinha de insights – reaproveitando textos do resumo + interpretação
    exp_ritmo = res.get("explicacao_ritmo", "")
    exp_d1 = res.get("explicacao_d1", "")
    exp_d7 = res.get("explicacao_d7", "")

    ritmo_msg = (
        "Ritmos acima de <b>1,00x</b> indicam aceleração vs a referência; "
        "abaixo de <b>1,00x</b> indicam perda de tração."
    )

    st.markdown(
        f"""
        <div class="expl-box">
          <ul>
            <li>{exp_ritmo}</li>
            <li>{exp_d1}</li>
            <li>{exp_d7}</li>
            <li>{ritmo_msg}</li>
          </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ============================================================
# ABA 2 – CURVAS & RITMO
# ============================================================
with aba_curvas:
    st.markdown(
        '<div class="section-title">📈 Curvas acumuladas – Hoje vs histórico</div>',
        unsafe_allow_html=True,
    )

    # Normalizar curvas acumuladas para comparação (0–1)
    grid_curvas = grid.copy()
    for col_acum, new_col in [
        ("acum_hoje", "curva_hoje"),
        ("acum_d1", "curva_d1"),
        ("acum_d7", "curva_d7"),
        ("acum_media_mes", "curva_media"),
    ]:
        max_val = grid_curvas[col_acum].max()
        if max_val > 0:
            grid_curvas[new_col] = grid_curvas[col_acum] / max_val
        else:
            grid_curvas[new_col] = np.nan

    curvas_long = grid_curvas.melt(
        id_vars="SLOT",
        value_vars=["curva_hoje", "curva_d1", "curva_d7", "curva_media"],
        var_name="Curva",
        value_name="Valor",
    )

    curvas_long["Curva"] = curvas_long["Curva"].map(
        {
            "curva_hoje": "Hoje",
            "curva_d1": "Ontem (D-1)",
            "curva_d7": "Semana passada (D-7)",
            "curva_media": "Média do mês",
        }
    )

    fig_curvas = px.line(
        curvas_long,
        x="SLOT",
        y="Valor",
        color="Curva",
        template="plotly_dark",
        labels={"Valor": "Progresso normalizado", "SLOT": "Horário"},
    )
    fig_curvas.update_layout(
        height=420,
        legend_title_text="Referência",
        margin=dict(l=10, r=10, t=30, b=20),
    )

    st.plotly_chart(fig_curvas, use_container_width=True)

    st.markdown(
        '<div class="section-title">📊 Ritmos ao longo do dia</div>',
        unsafe_allow_html=True,
    )

    # Ritmos slot a slot
    ritmo_df = grid.copy()
    ritmo_df["ritmo_vs_d1_slot"] = ritmo_df["acum_hoje"] / ritmo_df["acum_d1"].replace(
        0, np.nan
    )
    ritmo_df["ritmo_vs_d7_slot"] = ritmo_df["acum_hoje"] / ritmo_df["acum_d7"].replace(
        0, np.nan
    )
    ritmo_df["ritmo_vs_media_slot"] = ritmo_df["acum_hoje"] / ritmo_df[
        "acum_media_mes"
    ].replace(0, np.nan)

    ritmo_long = ritmo_df.melt(
        id_vars="SLOT",
        value_vars=[
            "ritmo_vs_d1_slot",
            "ritmo_vs_d7_slot",
            "ritmo_vs_media_slot",
        ],
        var_name="Tipo",
        value_name="Ritmo",
    )
    ritmo_long["Tipo"] = ritmo_long["Tipo"].map(
        {
            "ritmo_vs_d1_slot": "Ritmo vs D-1",
            "ritmo_vs_d7_slot": "Ritmo vs D-7",
            "ritmo_vs_media_slot": "Ritmo vs média do mês",
        }
    )

    fig_ritmo = px.line(
        ritmo_long,
        x="SLOT",
        y="Ritmo",
        color="Tipo",
        template="plotly_dark",
        labels={"Ritmo": "Ritmo (x)", "SLOT": "Horário"},
    )
    fig_ritmo.update_yaxes(zeroline=True, zerolinewidth=1, zerolinecolor="#555")
    fig_ritmo.update_layout(
        height=420,
        legend_title_text="Comparação",
        margin=dict(l=10, r=10, t=30, b=20),
    )

    st.plotly_chart(fig_ritmo, use_container_width=True)

    st.markdown(
        '<div class="section-title">🧾 Tabela detalhada (slot a slot)</div>',
        unsafe_allow_html=True,
    )

    st.dataframe(
        grid[
            [
                "SLOT",
                "valor_hoje",
                "valor_d1",
                "valor_d7",
                "valor_media_mes",
                "acum_hoje",
                "acum_d1",
                "acum_d7",
                "acum_media_mes",
                "ritmo_vs_d1",
                "ritmo_vs_d7",
                "ritmo_vs_media",
            ]
        ],
        use_container_width=True,
        height=420,
    )

# ============================================================
# ABA 3 – SIMULAÇÃO DE META
# ============================================================
with aba_simulacao:
    st.markdown(
        '<div class="section-title">🧮 Simulação de Meta</div>',
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown("### Ajuste de meta")
        st.write(
            "Altere a meta do dia e veja como mudam o gap projetado e os principais indicadores."
        )

        nova_meta = st.slider(
            "Selecione a meta simulada",
            min_value=int(meta_dia * 0.5),
            max_value=int(meta_dia * 1.5),
            value=int(meta_dia),
            step=10000,
        )

        novo_gap = proj - nova_meta
        novo_perc_proj = proj / nova_meta if nova_meta > 0 else np.nan
        novo_perc_atual = venda_atual / nova_meta if nova_meta > 0 else np.nan

        st.markdown(
            f"""
            <div class="expl-box">
              <ul>
                <li>Meta original: <b>{fmt_currency_br(meta_dia)}</b></li>
                <li>Meta simulada: <b>{fmt_currency_br(nova_meta)}</b></li>
                <li>Projeção permanece em <b>{fmt_currency_br(proj)}</b>.</li>
              </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_right:
        c1, c2, c3 = st.columns(3)
        kpi_card(
            c1,
            "Meta simulada",
            fmt_currency_br(nova_meta),
            "",
            "good",
        )
        proj_class2 = "good" if proj >= nova_meta else "bad"
        kpi_card(
            c2,
            "Projeção (fixa)",
            fmt_currency_br(proj),
            f"≈ {fmt_percent(novo_perc_proj)} da meta simulada.",
            proj_class2,
        )
        gap_class2 = "good" if novo_gap >= 0 else "bad"
        kpi_card(
            c3,
            "Gap simulado",
            fmt_currency_br(novo_gap),
            "Positivo = acima da meta, negativo = abaixo.",
            gap_class2,
        )

        st.markdown(
            f"""
            <div class="expl-box" style="margin-top:0.75rem;">
              <b>Leitura executiva da simulação</b><br><br>
              Com a meta ajustada para {fmt_currency_br(nova_meta)}, a venda atual
              cobre {fmt_percent(novo_perc_atual)} da meta e a projeção cobre
              {fmt_percent(novo_perc_proj)}. O gap projetado torna-se
              <b>{fmt_currency_br(novo_gap)}</b>.
            </div>
            """,
            unsafe_allow_html=True,
        )

# ============================================================
# ABA 4 – METODOLOGIA
# ============================================================
with aba_metodo:
    st.markdown(
        '<div class="section-title">📚 Metodologia de projeção e ritmo</div>',
        unsafe_allow_html=True,
    )

    st.markdown("### 1. Curva intradia histórica")
    st.markdown(
        f"""
        - Para cada slot de 15 minutos, medimos qual fração do faturamento diário costuma estar realizada ao longo do mês.  
        - No horário atual, o histórico indica que em média cerca de **{fmt_percent(perc_hist)}** do dia já deveria estar vendido.  
        """
    )

    st.markdown("### 2. Base matemática de projeção")
    st.markdown(
        f"""
        - Consideramos a venda acumulada de hoje até o último slot: **{fmt_currency_br(venda_atual)}**.  
        - Dividimos esse valor pela fração histórica do horário atual (**{fmt_percent(perc_hist)}**).  
        - Isso gera uma projeção-base de fechamento, que resulta em aproximadamente **{fmt_currency_br(proj)}** para o dia.  
        """
    )

    st.markdown("### 3. Camada de consistência por ritmo")
    st.markdown(
        f"""
        - Em paralelo, monitoramos os ritmos:
          - **Ritmo vs D-1:** {fmt_number_br(ritmo_d1, 2)}x  
          - **Ritmo vs D-7:** {fmt_number_br(ritmo_d7, 2)}x  
          - **Ritmo vs média do mês:** {fmt_number_br(ritmo_media, 2)}x  
        - Ritmos **acima de 1,00x** sugerem aceleração vs a referência; ritmos **abaixo de 1,00x** indicam perda de tração.  
        - Esses indicadores funcionam como uma checagem de consistência da projeção: se o comportamento do dia estiver muito fora do padrão, isso aparece imediatamente nos ritmos.
        """
    )

    st.markdown("### 4. Como interpretar o ritmo, na prática")
    st.markdown(
        """
        - **Ritmo vs D-1 > 1,0x** → estamos vendendo mais que ontem no mesmo horário.  
        - **Ritmo vs D-7 > 1,0x** → estamos acima do mesmo dia da semana passada.  
        - **Ritmo vs média > 1,0x** → o dia está mais forte que o padrão típico do mês.  
        - Combinar os três sinais ajuda a separar “efeitos pontuais” de mudanças reais de tendência.
        """
    )

    st.markdown("### 5. Próximos incrementos possíveis")
    st.markdown(
        """
        - Criar visões específicas de madrugada vs horário nobre.  
        - Incluir alertas automáticos quando o ritmo cair abaixo de limiares críticos.  
        - Expandir a análise por categoria, UF ou canal (app vs site).  
        """
    )
