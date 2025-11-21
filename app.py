import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ======================================================
# CONFIGURAÇÃO GERAL DO APP
# ======================================================
st.set_page_config(
    page_title="FSJ Black Friday 2026 – Projeção de Vendas",
    layout="wide",
    initial_sidebar_state="collapsed",
)

PRIMARY = "#00C853"
DANGER = "#FF1744"
WARNING = "#FFD600"
CARD_BG = "#111111"

# ======================================================
# HELPERS DE FORMATAÇÃO (PADRÃO BR)
# ======================================================

def fmt_number_br(value, decimals=0):
    """Formata número em padrão brasileiro (1.234.567,89)."""
    if value is None or pd.isna(value):
        return "-"
    s = f"{float(value):,.{decimals}f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s

def fmt_currency_br(value, prefix="R$ ", decimals=0):
    if value is None or pd.isna(value):
        return "-"
    return f"{prefix}{fmt_number_br(value, decimals)}"

def fmt_percent_br(value, decimals=1):
    if value is None or pd.isna(value):
        return "-"
    return f"{fmt_number_br(value * 100, decimals)}%"

# ======================================================
# CARREGAMENTO DE DADOS
# ======================================================

@st.cache_data
def load_grid(path: str = "data/saida_grid.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    for col in df.columns:
        if col != "SLOT":
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

@st.cache_data
def load_resumo(path: str = "data/saida_resumo.csv") -> dict:
    df = pd.read_csv(path)
    if df.empty:
        return {}

    row = df.iloc[0].copy()

    resumo = {
        "data_referencia": row.get("data_referencia"),
        "meta_dia": float(row.get("meta_dia", 0)),
        "venda_atual": float(row.get("venda_atual_ate_slot", 0)),
        "percentual_dia_hist": float(row.get("percentual_dia_hist", 0)),
        "tipo_percentual_base": row.get("tipo_percentual_base", ""),
        "projecao": float(row.get("projecao_dia", 0)),
        "gap": float(row.get("desvio_projecao", 0)),
        "total_d1": float(row.get("total_d1", 0)),
        "meta_d1": float(row.get("meta_d1", 0)),
        "desvio_d1": float(row.get("desvio_d1", 0)),
        "total_d7": float(row.get("total_d7", 0)),
        "meta_d7": float(row.get("meta_d7", 0)),
        "desvio_d7": float(row.get("desvio_d7", 0)),
        "ritmo_vs_d1": float(row.get("ritmo_vs_d1", 0)),
        "ritmo_vs_d7": float(row.get("ritmo_vs_d7", 0)),
        "ritmo_vs_media": float(row.get("ritmo_vs_media", 0)),
        "explicacao_ritmo": row.get("explicacao_ritmo", ""),
        "explicacao_d1": row.get("explicacao_d1", ""),
        "explicacao_d7": row.get("explicacao_d7", ""),
    }
    return resumo

@st.cache_data
def load_users(path: str = "data/usuarios.csv") -> pd.DataFrame:
    """
    Esperado: CSV com colunas obrigatórias:
      - usuario
      - senha
    Opcional:
      - nome (para exibir no topo)
    """
    df = pd.read_csv(path, dtype=str)
    df.columns = [c.strip().lower() for c in df.columns]
    return df

# ======================================================
# LOGIN
# ======================================================

def login_screen():
    st.markdown(
        """
        <style>
        .login-card {
            max-width: 420px;
            margin: 6rem auto 0 auto;
            padding: 2.5rem 2rem;
            background: #101010;
            border-radius: 18px;
            box-shadow: 0 0 25px rgba(0,0,0,0.55);
            border: 1px solid #222;
        }
        .login-title {
            font-size: 1.4rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            color: #FFFFFF;
            text-align: center;
        }
        .login-sub {
            font-size: 0.9rem;
            color: #BBBBBB;
            text-align: center;
            margin-bottom: 1.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    with st.container():
        st.markdown(
            """
            <div class="login-card">
                <div class="login-title">🔐 Acesso – FSJ Black Friday 2026</div>
                <div class="login-sub">Painel Executivo de Projeção de Vendas (Site + App)</div>
            """,
            unsafe_allow_html=True,
        )

        users_df = load_users()
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")

        col_a, col_b, _ = st.columns([1, 1, 1])
        with col_a:
            entrar = st.button("Entrar", use_container_width=True)

        with col_b:
            st.caption("Feito por: Planejamento e Dados E-Commerce")

        if entrar:
            if "usuario" not in users_df.columns or "senha" not in users_df.columns:
                st.error("Arquivo de usuários inválido. Verifique as colunas 'usuario' e 'senha'.")
            else:
                linha = users_df[
                    (users_df["usuario"].str.strip() == usuario.strip()) &
                    (users_df["senha"].str.strip() == senha.strip())
                ]
                if linha.empty:
                    st.error("Usuário ou senha incorretos.")
                else:
                    nome = linha.iloc[0].get("nome", usuario).title()
                    st.session_state["logged_in"] = True
                    st.session_state["user_name"] = nome
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

# ======================================================
# COMPONENTES VISUAIS
# ======================================================

def header(resumo: dict):
    data_ref_str = resumo.get("data_referencia")
    try:
        dt = datetime.strptime(str(data_ref_str), "%Y-%m-%d").date()
        data_legivel = dt.strftime("%d/%m/%Y")
    except Exception:
        data_legivel = "None"

    nome_usuario = st.session_state.get("user_name", "Usuário")

    st.markdown(
        f"""
        <style>
        .top-banner {{
            background: linear-gradient(90deg, #00C853 0%, #00BFA5 40%, #004D40 100%);
            padding: 14px 26px;
            border-radius: 0 0 20px 20px;
            margin: -1.5rem -1.5rem 1.2rem -1.5rem;
            color: #FFFFFF;
            box-shadow: 0 4px 18px rgba(0,0,0,0.45);
        }}
        .top-title {{
            font-size: 1.4rem;
            font-weight: 700;
        }}
        .top-sub {{
            font-size: 0.85rem;
            opacity: 0.9;
        }}
        .badge-small {{
            background: rgba(0,0,0,0.25);
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 0.8rem;
            float: right;
            margin-top: -18px;
        }}
        </style>
        <div class="top-banner">
            <div class="top-title">📈 FSJ Black Friday 2026 – Projeção de Vendas (Site + App)</div>
            <div class="top-sub">
                Usuário: <b>{nome_usuario}</b> • Data de referência: <b>{data_legivel}</b>
            </div>
            <div class="badge-small">
                Feito por: <b>Planejamento e Dados E-Commerce</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def kpi_card(title, value, subtitle=None, color=PRIMARY, tooltip=None):
    tooltip_html = ""
    if tooltip:
        tooltip_html = f"""
        <div class="kpi-tooltip">
            ⓘ
            <div class="kpi-tooltip-text">{tooltip}</div>
        </div>
        """

    st.markdown(
        f"""
        <style>
        .kpi-card {{
            background:{CARD_BG};
            padding:16px 18px;
            border-radius:16px;
            border:1px solid #242424;
            box-shadow:0 0 18px rgba(0,0,0,0.40);
            position: relative;
            min-height: 90px;
        }}
        .kpi-tooltip {{
            position: absolute;
            top: 8px;
            right: 8px;
            cursor: pointer;
            color: #AAAAAA;
            font-size: 16px;
        }}
        .kpi-tooltip-text {{
            visibility: hidden;
            opacity: 0;
            width: 260px;
            background-color: #000000EE;
            color: #FFF;
            text-align: left;
            border-radius: 8px;
            padding: 10px;
            position: absolute;
            z-index: 9999;
            right: -10px;
            top: 22px;
            transition: opacity 0.25s ease;
            font-size: 0.75rem;
            border: 1px solid #444;
        }}
        .kpi-tooltip:hover .kpi-tooltip-text {{
            visibility: visible;
            opacity: 1;
        }}
        </style>
        <div class="kpi-card">
            {tooltip_html}
            <div style="font-size:0.8rem;color:#CCCCCC;margin-bottom:4px;">{title}</div>
            <div style="font-size:1.6rem;font-weight:700;color:{color};">{value}</div>
            <div style="font-size:0.75rem;color:#999999;margin-top:6px;">{subtitle or ""}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ======================================================
# TEXTOS DOS TOOLTIPS
# ======================================================

tooltip_meta = "Meta total planejada para o dia, considerando vendas combinadas de site + app. É a referência principal de sucesso do dia."
tooltip_venda = "Valor acumulado de vendas até o último slot de 15 minutos processado. Base real do andamento do dia."
tooltip_proj = (
    "Projeção de fechamento construída a partir da curva intradia histórica do mês. "
    "O motor de projeção compara o quanto já vendemos até agora com o padrão típico de distribuição "
    "ao longo do dia e extrapola o fechamento esperado, sempre em conjunto com a leitura de D-1 e D-7."
)
tooltip_gap = (
    "Diferença entre a projeção de fechamento e a meta do dia. "
    "Valor negativo indica risco de não atingir a meta; positivo indica potencial de superação."
)
tooltip_d1 = (
    "Faturamento total realizado ontem (D-1). Serve como régua de comparação tática para o desempenho intradia de hoje."
)
tooltip_d7 = (
    "Faturamento total realizado no mesmo dia da semana passada (D-7). Ajuda a enxergar a tendência semanal."
)
tooltip_r_d1 = (
    "Relação entre o acumulado de hoje e o acumulado de ontem no mesmo horário. "
    "Acima de 1,0 significa que hoje estamos mais rápidos que D-1; abaixo de 1,0, mais lentos."
)
tooltip_r_d7 = (
    "Compara a velocidade de hoje com o mesmo dia da semana passada no mesmo ponto do dia. "
    "Acima de 1,0 indica aceleração versus D-7; abaixo, desaceleração."
)
tooltip_r_media = (
    "Compara o avanço de hoje com a curva média intradia do mês. "
    "Mostra se estamos acima ou abaixo do comportamento típico do período."
)
tooltip_frac_hist = (
    "Percentual estimado do dia já percorrido segundo a curva intradia histórica do mês. "
    "Exemplo: 35% indica que, historicamente, neste horário cerca de 35% do faturamento do dia já foi realizado."
)

# ======================================================
# DASHBOARD PRINCIPAL
# ======================================================

def main_dashboard():
    grid_df = load_grid()
    resumo = load_resumo()

    if not resumo:
        st.error("Arquivo 'saida_resumo.csv' está vazio ou inválido.")
        return

    # HEADER
    header(resumo)

    st.markdown(
        "<h3 style='margin-bottom:0.5rem;'>🎯 Visão Geral do Dia</h3>",
        unsafe_allow_html=True,
    )

    # ---------- LINHA 1 DE KPIs ----------
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        kpi_card(
            "Meta do Dia",
            fmt_currency_br(resumo["meta_dia"]),
            "Site + App",
            color=PRIMARY,
            tooltip=tooltip_meta
        )

    with col2:
        kpi_card(
            "Venda Atual",
            fmt_currency_br(resumo["venda_atual"]),
            "Faturamento acumulado até o último slot",
            color=PRIMARY,
            tooltip=tooltip_venda
        )

    with col3:
        kpi_card(
            "Projeção de Fechamento",
            fmt_currency_br(resumo["projecao"]),
            "Estimativa baseada na curva intradia histórica do mês",
            color=PRIMARY if resumo["projecao"] >= resumo["meta_dia"] else DANGER,
            tooltip=tooltip_proj
        )

    with col4:
        cor_gap = PRIMARY if resumo["gap"] >= 0 else DANGER
        sinal = "acima" if resumo["gap"] >= 0 else "abaixo"
        kpi_card(
            "Gap Projetado x Meta",
            fmt_currency_br(resumo["gap"]),
            f"Projeção {sinal} da meta do dia",
            color=cor_gap,
            tooltip=tooltip_gap
        )

    # ---------- LINHA 2 DE KPIs ----------
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        kpi_card(
            "Total D-1 (Dia inteiro)",
            fmt_currency_br(resumo["total_d1"]),
            "Fechamento de ontem",
            color=PRIMARY,
            tooltip=tooltip_d1
        )

    with c2:
        kpi_card(
            "Total D-7 (Dia inteiro)",
            fmt_currency_br(resumo["total_d7"]),
            "Mesmo dia da semana passada",
            color=PRIMARY,
            tooltip=tooltip_d7
        )

    with c3:
        kpi_card(
            "Ritmo vs D-1",
            f"{resumo['ritmo_vs_d1']:.2f}x",
            "Hoje vs ontem no mesmo horário",
            color=PRIMARY if resumo["ritmo_vs_d1"] >= 1 else DANGER,
            tooltip=tooltip_r_d1
        )

    with c4:
        kpi_card(
            "Ritmo vs D-7",
            f"{resumo['ritmo_vs_d7']:.2f}x",
            "Hoje vs semana passada no mesmo horário",
            color=PRIMARY if resumo["ritmo_vs_d7"] >= 1 else DANGER,
            tooltip=tooltip_r_d7
        )

    # ---------- LINHA 3 DE KPIs ----------
    st.markdown("<br>", unsafe_allow_html=True)
    c5, c6, _ = st.columns([1.6, 1.4, 1])

    with c5:
        kpi_card(
            "Ritmo vs Média do Mês",
            f"{resumo['ritmo_vs_media']:.2f}x",
            "Comparação com a curva média intradia do mês",
            color=PRIMARY if resumo["ritmo_vs_media"] >= 1 else DANGER,
            tooltip=tooltip_r_media
        )

    with c6:
        kpi_card(
            "Dia já percorrido (curva histórica)",
            fmt_percent_br(resumo["percentual_dia_hist"], 1),
            "Quanto do dia, em % do faturamento, tipicamente já foi realizado neste horário",
            color=WARNING,
            tooltip=tooltip_frac_hist
        )

    # ==================================================
    # INSIGHTS E TEXTO EXECUTIVO
    # ==================================================
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        "<h3>🧠 Insights Estratégicos</h3>",
        unsafe_allow_html=True,
    )

    with st.container():
        st.markdown(
            """
            <div style="
                background:#081018;
                border-radius:16px;
                padding:18px 20px;
                border:1px solid #202733;
                box-shadow:0 0 18px rgba(0,0,0,0.6);
                font-size:0.90rem;
                line-height:1.45;
                ">
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            • {resumo["explicacao_ritmo"]}<br>
            • {resumo["explicacao_d1"]}<br>
            • {resumo["explicacao_d7"]}<br>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <br>
            <b>Como a projeção é calculada?</b><br>
            • Primeiro, reconstruímos a curva intradia histórica do mês, entendendo qual fração do faturamento do dia costuma ocorrer em cada slot de 15 minutos.<br>
            • Em seguida, comparamos o acumulado de hoje até o horário atual com essa curva histórica, estimando qual seria o fechamento coerente com esse padrão.<br>
            • D-1 e D-7 entram como camadas de leitura: não alteram diretamente a fórmula da projeção, mas servem para calibrar a interpretação de risco (se vários dias recentes vieram abaixo da meta, um mesmo valor projetado é lido com mais cautela).<br>
            • A lógica central é: se historicamente neste horário já realizamos, por exemplo, 20% do dia, então a projeção base é:<br>
            &nbsp;&nbsp;&nbsp;&nbsp;<code>Projeção ≈ Venda Atual / Percentual Histórico Acumulado</code>.<br>
            • A partir disso, o painel posiciona o resultado frente à meta, D-1, D-7 e média do mês para transformar número em narrativa de ritmo e risco.<br>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("</div>", unsafe_allow_html=True)

    # ==================================================
    # GRÁFICOS DE CURVA DDT
    # ==================================================
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        "<h3>📊 Curva DDT – Comparativo Site + App</h3>",
        unsafe_allow_html=True,
    )

    df_plot = grid_df.copy()
    df_plot["SLOT_LABEL"] = df_plot["SLOT"]

    # Gráfico 1 – Valor por slot
    long_valor = df_plot.melt(
        id_vars=["SLOT_LABEL"],
        value_vars=["valor_hoje", "valor_d1", "valor_d7", "valor_media_mes"],
        var_name="Série",
        value_name="Valor",
    )
    map_nomes = {
        "valor_hoje": "Hoje",
        "valor_d1": "D-1",
        "valor_d7": "D-7",
        "valor_media_mes": "Média do mês",
    }
    long_valor["Série"] = long_valor["Série"].map(map_nomes)

    fig1 = px.line(
        long_valor,
        x="SLOT_LABEL",
        y="Valor",
        color="Série",
        template="plotly_dark",
        labels={"SLOT_LABEL": "Horário (slot de 15 min)", "Valor": "Faturamento no slot"},
    )
    fig1.update_layout(
        height=420,
        margin=dict(l=10, r=10, t=30, b=10),
        legend_title_text="",
    )
    st.plotly_chart(fig1, use_container_width=True)

    # Gráfico 2 – Faturamento acumulado
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        "<h3>📈 Faturamento Acumulado – Hoje vs D-1, D-7 e Média</h3>",
        unsafe_allow_html=True,
    )

    df_acum = df_plot[["SLOT_LABEL", "acum_hoje", "acum_d1", "acum_d7", "acum_media_mes"]].copy()
    df_acum_long = df_acum.melt(
        id_vars=["SLOT_LABEL"],
        value_vars=["acum_hoje", "acum_d1", "acum_d7", "acum_media_mes"],
        var_name="Série",
        value_name="Faturamento",
    )
    map_nomes_acum = {
        "acum_hoje": "Hoje (acum.)",
        "acum_d1": "D-1 (acum.)",
        "acum_d7": "D-7 (acum.)",
        "acum_media_mes": "Média mês (acum.)",
    }
    df_acum_long["Série"] = df_acum_long["Série"].map(map_nomes_acum)

    fig2 = px.line(
        df_acum_long,
        x="SLOT_LABEL",
        y="Faturamento",
        color="Série",
        template="plotly_dark",
        labels={"SLOT_LABEL": "Horário (slot de 15 min)", "Faturamento": "Faturamento acumulado"},
    )
    fig2.update_layout(
        height=420,
        margin=dict(l=10, r=10, t=30, b=10),
        legend_title_text="",
    )
    st.plotly_chart(fig2, use_container_width=True)

    # Tabela detalhada
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        "<h3>🧮 Tabela Detalhada – DDT Slot a Slot</h3>",
        unsafe_allow_html=True,
    )
    st.dataframe(grid_df, use_container_width=True, height=420)

# ======================================================
# FLUXO PRINCIPAL
# ======================================================

def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login_screen()
        return

    main_dashboard()

if __name__ == "__main__":
    main()
