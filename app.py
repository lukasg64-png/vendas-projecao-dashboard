import streamlit as st
import pandas as pd
import plotly.express as px

# ======================================================
# CONFIGURAÇÃO BÁSICA DA PÁGINA
# ======================================================
st.set_page_config(
    page_title="📈 FSJ – Painel Black Friday",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ======================================================
# ESTILOS GERAIS (CSS)
# ======================================================
CUSTOM_CSS = """
<style>
/* Fundo geral escuro */
.stApp {
    background: #020b0f;
    color: #f5f5f5;
    font-family: "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Esconder menu e footer do Streamlit para deixar mais clean */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Tela de login - container central */
.login-container {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}

/* Card de login */
.login-card {
    background: radial-gradient(circle at top left, #00c85333, #000000dd);
    border-radius: 18px;
    padding: 26px 26px 22px 26px;
    max-width: 420px;
    width: 90%;
    box-shadow: 0 0 25px rgba(0,0,0,0.6);
    border: 1px solid #00c85355;
}

/* Título principal FSJ */
.logo-title {
    font-size: 1.8rem;
    font-weight: 700;
    color: #ffffff;
    text-align: center;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 0.2rem;
}

/* Slogan animado */
.slogan {
    font-size: 1.05rem;
    font-weight: 600;
    text-align: center;
    color: #00e676;
    margin-bottom: 1.0rem;
    animation: pulseGlow 2.2s infinite;
}

/* Animação do slogan */
@keyframes pulseGlow {
    0%   { text-shadow: 0 0 4px #00e676, 0 0 8px #00e676; }
    50%  { text-shadow: 0 0 14px #00e676, 0 0 26px #00e676; }
    100% { text-shadow: 0 0 4px #00e676, 0 0 8px #00e676; }
}

/* Subtítulo login */
.login-subtitle {
    font-size: 0.9rem;
    text-align: center;
    color: #cfd8dc;
    margin-bottom: 1.4rem;
}

/* Assinatura rodapé login */
.login-footer {
    font-size: 0.75rem;
    text-align: center;
    color: #90a4ae;
    margin-top: 1.2rem;
}

/* Botão estilizado */
.stButton > button {
    width: 100%;
    border-radius: 999px;
    border: 1px solid #00c853;
    background: linear-gradient(90deg, #00c853, #64dd17);
    color: #000;
    font-weight: 600;
    box-shadow: 0 0 12px #00c85388;
}

/* Cartão KPI */
.kpi-card {
    background: linear-gradient(145deg, #071018, #02070b);
    border-radius: 16px;
    padding: 14px 16px 12px 16px;
    border: 1px solid rgba(255,255,255,0.06);
    box-shadow: 0 0 18px rgba(0,0,0,0.55);
}

/* Título KPI */
.kpi-title {
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.10em;
    color: #b0bec5;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

/* Valor KPI principal */
.kpi-value {
    font-size: 1.6rem;
    font-weight: 700;
    margin-top: 4px;
}

/* Subtext KPI */
.kpi-sub {
    font-size: 0.8rem;
    color: #90a4ae;
    margin-top: 4px;
}

/* Badge tonal */
.badge {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 999px;
    font-size: 0.70rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
}

/* Tooltip simples via title */
.kpi-help {
    font-size: 0.9rem;
    margin-left: 6px;
    cursor: help;
}

/* Caixa de texto explicativa */
.text-card {
    background: #020b10;
    border-radius: 12px;
    padding: 14px 16px;
    border: 1px solid rgba(255,255,255,0.06);
}

/* Tabs cabeça mais destacada */
.stTabs [role="tablist"] {
    gap: 8px;
}

.stTabs [role="tab"] {
    padding: 8px 16px !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255,255,255,0.14) !important;
}

/* Título principal após login */
.main-title {
    font-size: 1.6rem;
    font-weight: 700;
    margin-bottom: 0.1rem;
}

.main-subtitle {
    font-size: 0.95rem;
    color: #90a4ae;
    margin-bottom: 0.8rem;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ======================================================
# HELPERS – FORMATAÇÃO E CARDS
# ======================================================

def format_moeda_br(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "R$ 0,00"
    s = f"{v:,.0f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"

def format_num_br(v, decimais=2):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "-"
    s = f"{v:,.{decimais}f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s

def kpi_card(titulo, valor, subtitulo="", cor="#00e676", help_text=None, badge_text=None, badge_color="#37474f"):
    """
    Renderiza um card KPI bonito usando HTML/CSS.
    """
    help_html = ""
    if help_text:
        help_html = f"<span class='kpi-help' title='{help_text}'>ℹ</span>"

    badge_html = ""
    if badge_text:
        badge_html = f"<span class='badge' style='background:{badge_color}; color:#eceff1;'>{badge_text}</span>"

    html = f"""
    <div class="kpi-card">
        <div class="kpi-title">
            <span>{titulo}</span>
            <span>{badge_html}{help_html}</span>
        </div>
        <div class="kpi-value" style="color:{cor};">
            {valor}
        </div>
        <div class="kpi-sub">
            {subtitulo}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# ======================================================
# LOGIN – COM SLOGAN “TEM BLACK NA SÃO JOÃO?”
# ======================================================

# Usuários simples em memória (pode expandir depois)
USERS = {
    "lucas": "black2025",
    "fsj": "blackfriday2025",
    "farmacias": "temblack"
}

def login_screen():
    with st.container():
        st.markdown("<div class='login-container'>", unsafe_allow_html=True)

        st.markdown(
            """
            <div class='login-card'>
                <div class='logo-title'>FARMÁCIAS SÃO JOÃO</div>
                <div class='slogan'>Tem Black na São João? Tem Black na São João.</div>
                <div class='login-subtitle'>
                    Acesso ao painel executivo de projeção de vendas<br>
                    <span style="color:#b0bec5;">Site + App • Black Friday</span>
                </div>
            """,
            unsafe_allow_html=True
        )

        user = st.text_input("Usuário", key="login_user")
        pwd = st.text_input("Senha", type="password", key="login_pwd")

        col_btn, _ = st.columns([2, 1])
        with col_btn:
            if st.button("Entrar no painel"):
                if user in USERS and USERS[user] == pwd:
                    st.session_state["auth"] = True
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos.")

        st.markdown(
            """
                <div class='login-footer'>
                    Feito por: Planejamento & Dados – E-commerce FSJ<br>
                    Versão Black Friday
                </div>
            </div>
            </div>
            """,
            unsafe_allow_html=True
        )

# Inicializar sessão de auth
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    login_screen()
    st.stop()

# ======================================================
# CARREGAR ARQUIVOS CSV (SAÍDAS DO COLAB)
# ======================================================

@st.cache_data
def load_data():
    # Ajuste o caminho se necessário (ex: "saida_grid.csv")
    grid = pd.read_csv("data/saida_grid.csv")
    resumo = pd.read_csv("data/saida_resumo.csv")
    return grid, resumo

df_grid, df_resumo = load_data()

# Garantir que temos uma linha de resumo
if df_resumo.empty:
    st.error("Arquivo 'saida_resumo.csv' está vazio. Gere a saída no Colab e faça upload novamente.")
    st.stop()

res = df_resumo.iloc[0]

# Extrair métricas principais
meta_dia       = res.get("meta_dia", 0.0)
venda_atual    = res.get("venda_atual_ate_slot", 0.0)
projecao_dia   = res.get("projecao_dia", 0.0)
desvio_proj    = res.get("desvio_projecao", 0.0)
total_d1       = res.get("total_d1", 0.0)
total_d7       = res.get("total_d7", 0.0)
ritmo_d1       = res.get("ritmo_vs_d1", 0.0)
ritmo_d7       = res.get("ritmo_vs_d7", 0.0)
ritmo_media    = res.get("ritmo_vs_media", 0.0)
frac_hist      = res.get("percentual_dia_hist", 0.0)
data_ref       = res.get("data_referencia", "")

exp_ritmo      = res.get("explicacao_ritmo", "")
exp_d1         = res.get("explicacao_d1", "")
exp_d7         = res.get("explicacao_d7", "")

# Pequenos status
atinge_meta = projecao_dia >= meta_dia
cor_gap = "#00e676" if desvio_proj >= 0 else "#ff1744"
badge_status = "acima da meta" if atinge_meta else "abaixo da meta"
badge_cor = "#1b5e20" if atinge_meta else "#b71c1c"

# ======================================================
# LAYOUT PRINCIPAL – TABS
# ======================================================

st.markdown(
    f"""
    <div class="main-title">📈 Painel Executivo – FSJ Black Friday</div>
    <div class="main-subtitle">
        Data de referência: <b>{data_ref}</b> • Canal: Site + App
    </div>
    """,
    unsafe_allow_html=True
)

tab1, tab2, tab3 = st.tabs(["Visão Geral", "Curvas & Ritmo", "Simulação de Meta"])

# ======================================================
# TAB 1 – VISÃO GERAL
# ======================================================
with tab1:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        kpi_card(
            "Meta do dia",
            format_moeda_br(meta_dia),
            subtitulo="Meta consolidada Site + App para a data.",
            cor="#00e676",
            help_text="Meta diária total (site + app) definida para o dia de referência."
        )

    with col2:
        kpi_card(
            "Venda atual",
            format_moeda_br(venda_atual),
            subtitulo=f"Equivale a {format_num_br(frac_hist*100,1)}% da curva histórica intradia.",
            cor="#29b6f6",
            help_text="Faturamento acumulado até o último slot de 15 minutos disponível."
        )

    with col3:
        kpi_card(
            "Projeção de fechamento",
            format_moeda_br(projecao_dia),
            subtitulo="Calculada usando a curva intradia histórica e o ritmo atual.",
            cor="#ffa726" if not atinge_meta else "#00e676",
            help_text="Venda atual dividida pela fração histórica do dia no horário atual."
        )

    with col4:
        kpi_card(
            "Gap projetado",
            format_moeda_br(desvio_proj),
            subtitulo="Diferença entre projeção e meta consolidada.",
            cor=cor_gap,
            help_text="Se positivo, projetamos superar a meta. Se negativo, projetamos ficar abaixo.",
            badge_text=badge_status,
            badge_color=badge_cor
        )

    st.markdown("---")

    # Linha de KPIs de ritmo
    st.markdown("### 🔄 Ritmo do dia")

    colr1, colr2, colr3 = st.columns(3)

    with colr1:
        kpi_card(
            "Ritmo vs D-1",
            f"{format_num_br(ritmo_d1, 2)}x",
            subtitulo="> 1,00 indica que hoje estamos na frente de ontem no mesmo horário.",
            cor="#81c784",
            help_text="Venda acumulada hoje / venda acumulada ontem no mesmo slot."
        )
    with colr2:
        kpi_card(
            "Ritmo vs D-7",
            f"{format_num_br(ritmo_d7, 2)}x",
            subtitulo="Comparação direta com o mesmo dia da semana passada.",
            cor="#ba68c8",
            help_text="Venda acumulada hoje / venda acumulada do D-7 no mesmo slot."
        )
    with colr3:
        kpi_card(
            "Ritmo vs média do mês",
            f"{format_num_br(ritmo_media, 2)}x",
            subtitulo="Quanto o dia está acelerado vs o padrão médio do mês.",
            cor="#ffca28",
            help_text="Venda acumulada hoje / venda acumulada da média mensal no mesmo slot."
        )

    # Bloco de explicação do que é “ritmo”
    st.markdown("### ℹ️ Como interpretar o ritmo")
    with st.container():
        st.markdown(
            """
            <div class="text-card">
                <ul>
                    <li><b>Ritmo vs D-1</b>: quanto o dia está mais rápido ou mais lento do que ontem na mesma altura do dia.</li>
                    <li><b>Ritmo vs D-7</b>: compara com o mesmo dia da semana passada (efeito calendário).</li>
                    <li><b>Ritmo vs média do mês</b>: indica se o dia está dentro do "padrão do mês" ou fugindo do comportamento típico.</li>
                </ul>
                <span style="font-size:0.9rem; color:#b0bec5;">
                    • Valores em torno de <b>1,00x</b> indicam ritmo parecido com a base de comparação.<br>
                    • <b>Acima de 1,10x</b> sugerem aceleração (dia forte).<br>
                    • <b>Abaixo de 0,90x</b> sinalizam perda de tração – atenção para slots seguintes.
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("### 🧠 Narrativa executiva do dia")

    coln1, coln2, coln3 = st.columns(3)

    with coln1:
        st.markdown("**Ritmo atual**")
        st.markdown(f"<div class='text-card'>{exp_ritmo}</div>", unsafe_allow_html=True)

    with coln2:
        st.markdown("**Leitura vs ontem (D-1)**")
        st.markdown(f"<div class='text-card'>{exp_d1}</div>", unsafe_allow_html=True)

    with coln3:
        st.markdown("**Leitura vs D-7**")
        st.markdown(f"<div class='text-card'>{exp_d7}</div>", unsafe_allow_html=True)

# ======================================================
# TAB 2 – CURVAS & RITMO
# ======================================================
with tab2:
    st.markdown("### 📊 Curvas intradia – HOJE vs D-1 vs D-7 vs média do mês")

    df_plot = df_grid.copy()
    # Garantir ordem dos slots como string já vem
    df_plot = df_plot.sort_values("SLOT")

    # Gráfico de valores por slot
    fig_val = px.line(
        df_plot,
        x="SLOT",
        y=["valor_hoje", "valor_d1", "valor_d7", "valor_media_mes"],
        labels={"value": "Valor", "SLOT": "Horário", "variable": "Série"},
        template="plotly_dark",
    )
    fig_val.update_layout(
        legend_title_text="Série",
        height=420,
        margin=dict(l=20, r=20, t=40, b=40)
    )
    st.plotly_chart(fig_val, use_container_width=True)

    st.markdown("### 🔍 Desvio de hoje vs curva média do mês (por slot)")

    df_desvio = df_plot.copy()
    df_desvio["desvio_vs_media"] = df_desvio["valor_hoje"] - df_desvio["valor_media_mes"]

    fig_desvio = px.bar(
        df_desvio,
        x="SLOT",
        y="desvio_vs_media",
        labels={"desvio_vs_media": "Desvio (R$)", "SLOT": "Horário"},
        template="plotly_dark",
    )
    fig_desvio.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=40, b=40)
    )
    st.plotly_chart(fig_desvio, use_container_width=True)

    st.markdown("### 📈 Evolução dos ritmos ao longo do dia")

    fig_ritmo = px.line(
        df_plot,
        x="SLOT",
        y=["ritmo_vs_d1", "ritmo_vs_d7", "ritmo_vs_media"],
        labels={"value": "Ritmo (x)", "SLOT": "Horário", "variable": "Comparação"},
        template="plotly_dark",
    )
    fig_ritmo.update_layout(
        legend_title_text="Comparação",
        height=380,
        margin=dict(l=20, r=20, t=40, b=40)
    )
    st.plotly_chart(fig_ritmo, use_container_width=True)

    st.markdown("### 🧮 Tabela detalhada slot a slot")
    st.dataframe(df_grid, use_container_width=True, height=350)

# ======================================================
# TAB 3 – SIMULAÇÃO DE META
# ======================================================
with tab3:
    st.markdown("### 🎯 Simulação de metas e gaps")

    col_sim1, col_sim2 = st.columns([2, 3])

    with col_sim1:
        st.markdown(
            """
            <div class='text-card'>
                <b>Como funciona a simulação?</b><br><br>
                A projeção de fechamento (já calculada no Colab) é mantida fixa aqui.<br>
                Nesta aba, você pode testar metas alternativas e observar:
                <ul>
                    <li>novo gap projetado,</li>
                    <li>percentual de atingimento,</li>
                    <li>status qualitativo (confortável, tensão, crítico).</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )

        meta_sim = st.number_input(
            "Meta simulada (R$)",
            min_value=0.0,
            value=float(meta_dia),
            step=50000.0
        )

        gap_sim = projecao_dia - meta_sim
        perc_ating = projecao_dia / meta_sim if meta_sim > 0 else 0

        if perc_ating >= 1.05:
            status_sim = "Confortável"
            cor_sim = "#00e676"
        elif perc_ating >= 0.95:
            status_sim = "Zona de tensão"
            cor_sim = "#ffeb3b"
        else:
            status_sim = "Crítico"
            cor_sim = "#ff1744"

        st.markdown("#### Resultado da simulação")
        kpi_card(
            "Meta simulada",
            format_moeda_br(meta_sim),
            subtitulo="Meta ajustada para análise de cenário.",
            cor="#29b6f6"
        )
        kpi_card(
            "Gap projetado (simulado)",
            format_moeda_br(gap_sim),
            subtitulo=f"Atingimento projetado: {format_num_br(perc_ating*100, 1)}%.",
            cor=cor_sim,
            badge_text=status_sim,
            badge_color="#263238"
        )

    with col_sim2:
        st.markdown("#### Comparação entre cenário real e simulado")

        df_comp = pd.DataFrame({
            "Cenário": ["Atual (meta oficial)", "Simulado"],
            "Meta (R$)": [meta_dia, meta_sim],
            "Projeção (R$)": [projecao_dia, projecao_dia],
            "Gap (R$)": [desvio_proj, gap_sim]
        })

        # Converter para formato BR apenas na visualização
        df_comp_view = df_comp.copy()
        df_comp_view["Meta (R$)"] = df_comp["Meta (R$)"].apply(format_moeda_br)
        df_comp_view["Projeção (R$)"] = df_comp["Projeção (R$)"].apply(format_moeda_br)
        df_comp_view["Gap (R$)"] = df_comp["Gap (R$)"].apply(format_moeda_br)

        st.dataframe(df_comp_view, use_container_width=True, height=180)

        # Gráfico simples de barras comparando gaps
        fig_gap = px.bar(
            df_comp,
            x="Cenário",
            y="Gap (R$)",
            template="plotly_dark",
            text="Gap (R$)",
        )
        fig_gap.update_traces(texttemplate="%{text:.0f}", textposition="outside")
        fig_gap.update_layout(
            height=360,
            margin=dict(l=20, r=20, t=40, b=40)
        )
        st.plotly_chart(fig_gap, use_container_width=True)
