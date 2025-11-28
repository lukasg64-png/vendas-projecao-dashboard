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

PRIMARY = "#00E676"   # verde principal
DANGER  = "#FF1744"   # vermelho
WARNING = "#FFD54F"   # amarelo
CARD_BG = "#111111"


# =========================================================
# GLOBAL CSS (ANIMAÇÕES & ESTILO)
# =========================================================
def inject_global_css():
    st.markdown(
        """
        <style>
        /* ===== Scrollbar dark ===== */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #050816;
        }
        ::-webkit-scrollbar-thumb {
            background: #283046;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #3f4d71;
        }

        /* ===== Top banner animado ===== */
        .top-banner {
            background-size: 300% 300% !important;
            animation: fsjGradientMove 8s ease-in-out infinite;
        }
        @keyframes fsjGradientMove {
            0%   { background-position: 0% 50%; }
            50%  { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        /* ===== KPI cards com efeito “show” ===== */
        .kpi-card {
            position: relative;
            overflow: hidden;
            transform: translateY(0px) scale(1.0);
            transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
        }

        .kpi-card::before {
            content: "";
            position: absolute;
            top: -40%;
            left: -40%;
            width: 180%;
            height: 180%;
            background: conic-gradient(
                from 0deg,
                rgba(0, 230, 118, 0.0),
                rgba(0, 230, 118, 0.35),
                rgba(0, 176, 255, 0.35),
                rgba(255, 255, 255, 0.0)
            );
            opacity: 0;
            animation: fsjShimmer 3s linear infinite;
            pointer-events: none;
        }

        .kpi-card:hover::before {
            opacity: 0.6;
        }

        .kpi-card:hover {
            transform: translateY(-4px) scale(1.01);
            box-shadow: 0 0 22px rgba(0, 230, 118, 0.25);
            border-color: rgba(0, 230, 118, 0.7) !important;
        }

        @keyframes fsjShimmer {
            0%   { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Linha neon no rodapé do card */
        .kpi-card::after {
            content: "";
            position: absolute;
            left: 0;
            bottom: 0;
            width: 0%;
            height: 3px;
            background: linear-gradient(90deg, #00E676, #00B0FF, #FFEB3B);
            box-shadow: 0 0 12px rgba(0, 230, 118, 0.8);
            transition: width 0.35s ease;
        }

        .kpi-card:hover::after {
            width: 100%;
        }

        /* Número grande dentro do card com leve glow */
        .kpi-main-value {
            text-shadow: 0 0 10px rgba(0, 230, 118, 0.4);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


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
        nome = row["nome"].iloc[0]
        return True, nome
    return False, None


@st.cache_data
def load_grid_and_resumo(grid_path: Path, resumo_path: Path):
    grid = pd.read_csv(grid_path)
    resumo_df = pd.read_csv(resumo_path)
    resumo = resumo_df.iloc[0].to_dict()
    return grid, resumo


# =========================================================
# HELPERS: FORMATAÇÃO
# =========================================================
def fmt_currency_br(x, decimals: int = 0) -> str:
    try:
        if x is None or np.isnan(x):
            return "-"
    except TypeError:
        pass
    fmt = f"{float(x):,.{decimals}f}"
    fmt = fmt.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {fmt}"


def fmt_percent_br(x, decimals: int = 2) -> str:
    try:
        if x is None or np.isnan(x):
            return "-"
    except TypeError:
        return "-"
    pct = float(x) * 100
    fmt = f"{pct:,.{decimals}f}"
    fmt = fmt.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{fmt}%"


def fmt_number_br(x, decimals: int = 2) -> str:
    try:
        if x is None or np.isnan(x):
            return "-"
    except TypeError:
        pass
    fmt = f"{float(x):,.{decimals}f}"
    fmt = fmt.replace(",", "X").replace(".", ",").replace("X", ".")
    return fmt


# =========================================================
# HELPERS: COMPONENTES VISUAIS
# =========================================================
def kpi_card(
    title: str,
    value: str,
    subtitle: str = "",
    color: str = PRIMARY,
    tooltip: str | None = None,
):
    """KPI em formato de card, estilizado com HTML + animações."""
    info_html = ""
    if tooltip:
        safe_tip = html.escape(tooltip, quote=True)
        info_html = (
            f"<span style='margin-left:6px; cursor:help;' title='{safe_tip}'>ℹ️</span>"
        )

    html_block = f"""
    <div class="kpi-card" style="
        background:{CARD_BG};
        padding:18px 20px;
        border-radius:12px;
        border:1px solid #333;
        box-shadow:0 0 10px rgba(0,0,0,0.4);
        min-height:90px;
    ">
        <div style="font-size:0.8rem;color:#BBBBBB;display:flex;align-items:center;justify-content:space-between;">
            <span>{html.escape(title)}</span>
            {info_html}
        </div>
        <div class="kpi-main-value" style="font-size:1.7rem;font-weight:700;margin-top:4px;color:{color};">
            {value}
        </div>
        <div style="font-size:0.75rem;color:#888888;margin-top:6px;">
            {subtitle}
        </div>
    </div>
    """
    st.markdown(html_block, unsafe_allow_html=True)


def gauge_ritmo(title: str, valor: float, tooltip: str = ""):
    """Gauge centralizado e com tamanho uniforme, sem alterar mais nada do app."""
    
    max_range = max(1.6, abs(valor) * 1.3)

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=valor,
            number={"valueformat": ".2f", "font": {"size": 38}},
            title={"text": title, "font": {"size": 16}},
            gauge={
                "axis": {"range": [0, max_range], "tickwidth": 1, "tickcolor": "#666"},
                "bar": {"color": PRIMARY},
                "steps": [
                    {"range": [0, 0.8], "color": "#1E1E1E"},
                    {"range": [0.8, 1.0], "color": "#424242"},
                    {"range": [1.0, 1.2], "color": "#004D40"},
                    {"range": [1.2, max_range], "color": "#1B5E20"},
                ],
                "threshold": {
                    "line": {"color": WARNING, "width": 3},
                    "thickness": 0.75,
                    "value": 1.0,
                },
            },
        )
    )

    fig.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),
        height=260,
        width=330,
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#EEEEEE", "family": "sans-serif"},
    )

    # 🔥 Centraliza o gauge sem alterar nada no layout
    st.markdown(
        "<div style='width:340px; margin:auto; text-align:center;'>",
        unsafe_allow_html=True,
    )

    st.plotly_chart(
        fig,
        use_container_width=False,
        config={"displayModeBar": False},
    )

    st.markdown("</div>", unsafe_allow_html=True)

    if tooltip:
        st.caption(tooltip)



# =========================================================
# TELA DE LOGIN
# =========================================================
def login_screen(df_logins: pd.DataFrame):
    inject_global_css()

    # Banner topo
    st.markdown(
        """
        <div class="top-banner" style="
            padding:18px 22px;
            border-radius:14px;
            background:linear-gradient(90deg,#00E676,#00B0FF);
            display:flex;
            align-items:center;
            justify-content:space-between;
            margin-bottom:18px;
        ">
            <div>
                <div style="font-size:1.4rem;font-weight:700;color:#001B20;">
                    FSJ Black Friday – Painel de Projeção
                </div>
                <div style="font-size:0.9rem;color:#012A30;margin-top:4px;">
                    Bem-vindo, São João! <b>Tem Black na São João? Tem Black na São João! 🔥</b>
                </div>
            </div>
            <div style="font-size:0.75rem;color:#012A30;background:rgba(255,255,255,0.8);
                        padding:6px 12px;border-radius:999px;">
                Feito por: Planejamento e Dados E-Commerce
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Card de login central
    login_col = st.columns([1, 2, 1])[1]
    with login_col:
        st.markdown(
            """
            <div style="
                background:#0F172A;
                padding:20px 22px;
                border-radius:14px;
                border:1px solid #1E293B;
                box-shadow:0 0 18px rgba(0,0,0,0.5);
                margin-top:4px;
            ">
                <div style="font-size:1.1rem;font-weight:600;margin-bottom:10px;color:#E5E7EB;">
                    🔐 Acesse o painel
                </div>
            """,
            unsafe_allow_html=True,
        )

        col_user, col_pwd = st.columns(2)
        with col_user:
            username = st.text_input("Usuário", key="login_user")
        with col_pwd:
            password = st.text_input("Senha", type="password", key="login_pwd")

        col_btn, col_info = st.columns([0.5, 0.5])
        with col_btn:
            if st.button("Entrar", type="primary", use_container_width=True):
                ok, nome = authenticate(username.strip(), password.strip(), df_logins)
                if ok:
                    st.session_state["auth"] = True
                    st.session_state["user"] = username.strip()
                    st.session_state["user_name"] = nome
                    st.experimental_rerun()
                else:
                    st.error(
                        "Usuário ou senha inválidos. Confira os dados ou fale com o time de Dados."
                    )

        with col_info:
            st.caption("Usuários e perfis são carregados de `data/logins.csv`.")

        st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# PAINEL 1 – VISÃO GERAL
# =========================================================
def painel_visao_geral(grid: pd.DataFrame, resumo: dict, user_name: str):
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
            Usuário: <b>{html.escape(user_name)}</b> • Data de referência:
            <b>{data_ref.strftime('%d/%m/%Y')}</b> • Canal: Site + App
        </div>
        """,
        unsafe_allow_html=True,
    )

    # === KPIs PRINCIPAIS ===
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card(
            "Meta do dia",
            fmt_currency_br(meta_dia),
            "Meta consolidada Site + App para a data.",
            color=PRIMARY,
            tooltip="Meta financeira total do dia, considerando todos os canais digitais (site + app).",
        )

    with c2:
        perc_meta = venda_atual / meta_dia if meta_dia > 0 else 0
        kpi_card(
            "Venda atual",
            fmt_currency_br(venda_atual),
            f"Equivalente a {fmt_percent_br(perc_meta, 1)} da meta.",
            color=PRIMARY if perc_meta >= frac_hist else WARNING,
            tooltip="Faturamento realizado até o último slot de 15 minutos.",
        )

    with c3:
        kpi_card(
            "Projeção de fechamento",
            fmt_currency_br(projecao),
            "Baseada na curva intradia histórica e no padrão do mês.",
            color=WARNING if projecao < meta_dia else PRIMARY,
            tooltip="Calculada projetando o faturamento atual pela fração histórica vendida até esse horário.",
        )

    with c4:
        gap_label = "Acima da meta" if gap >= 0 else "Abaixo da meta"
        gap_color = PRIMARY if gap >= 0 else DANGER
        kpi_card(
            "Gap projetado vs meta",
            fmt_currency_br(gap),
            f"{gap_label}.",
            color=gap_color,
            tooltip="Diferença entre a projeção de fechamento e a meta consolidada do dia.",
        )

    st.markdown("---")

    # === RITMOS & COMPARATIVOS ===
    st.subheader("📈 Ritmo do dia", divider="gray")

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        kpi_card(
            "Total D-1 (dia inteiro)",
            fmt_currency_br(total_d1),
            "Fechamento total de ontem.",
            color=PRIMARY,
            tooltip="Fechamento consolidado do dia anterior (D-1).",
        )

    with c6:
        kpi_card(
            "Total D-7 (dia inteiro)",
            fmt_currency_br(total_d7),
            "Fechamento do mesmo dia da semana passada.",
            color=PRIMARY,
            tooltip="Fechamento consolidado de D-7 (mesmo dia da semana anterior).",
        )

    with c7:
        kpi_card(
            "Dia já percorrido",
            fmt_percent_br(frac_hist, 1),
            "Fraçao média do dia que costuma estar vendida nesse horário.",
            color=WARNING,
            tooltip="Percentual médio do dia já realizado, segundo a curva intradia histórica.",
        )

    with c8:
        ritmo_comb = (ritmo_d1 + ritmo_d7 + ritmo_med) / 3 if all(
            v is not None for v in [ritmo_d1, ritmo_d7, ritmo_med]
        ) else 0
        texto_ritmo = (
            f"vs D-1: {fmt_number_br(ritmo_d1, 2)}x • "
            f"vs D-7: {fmt_number_br(ritmo_d7, 2)}x • "
            f"vs média do mês: {fmt_number_br(ritmo_med, 2)}x"
        )
        cor_ritmo = PRIMARY if ritmo_comb >= 1.0 else WARNING
        kpi_card(
            "Ritmo combinado",
            f"{fmt_number_br(ritmo_comb, 2)}x",
            texto_ritmo,
            color=cor_ritmo,
            tooltip=(
                "Média simples dos ritmos vs D-1, D-7 e média do mês. "
                "Acima de 1,00x indica aceleração; abaixo, perda de tração."
            ),
        )

    # Explicação
    with st.expander("🧠 Como interpretar os ritmos", expanded=False):
        st.markdown(
            f"""
            - **Ritmo vs D-1 ({fmt_number_br(ritmo_d1,2)}x)** → quanto o acumulado de hoje está maior ou menor que o acumulado de ontem no mesmo horário.  
            - **Ritmo vs D-7 ({fmt_number_br(ritmo_d7,2)}x)** → comparação com o mesmo dia da semana passada.  
            - **Ritmo vs média do mês ({fmt_number_br(ritmo_med,2)}x)** → comparação com o comportamento médio do mês para este horário.  

            Em geral:
            - **acima de 1,00x** → estamos acelerados em relação à referência.  
            - **abaixo de 1,00x** → estamos perdendo tração vs a referência.  
            """
        )

    # === ANÁLISE EXECUTIVA ===
    st.subheader("📝 Análise executiva da projeção", divider="gray")

    frac_txt = fmt_percent_br(frac_hist, 2)
    st.markdown(
        f"""
        ### Como a projeção é construída

        A projeção de fechamento usa um modelo em três camadas:

        1. **Curva intradia histórica**  
           - Para cada slot de 15 minutos, medimos que fração do faturamento diário costuma estar realizada ao longo do mês.  
           - No horário atual, o padrão histórico indica que cerca de **{frac_txt}** do dia já deveria estar vendido.

        2. **Base matemática da projeção**  
           - Consideramos a venda acumulada de hoje até o último slot: **{fmt_currency_br(venda_atual)}**.  
           - Dividimos esse valor pela fração histórica do horário (*venda_atual / frac_hist*).  
           - Isso gera uma projeção de fechamento em torno de **{fmt_currency_br(projecao)}** para o dia.

        3. **Camada de consistência por ritmo**  
           - Em paralelo, monitoramos os ritmos:  
             - **vs D-1:** {fmt_number_br(ritmo_d1,2)}x  
             - **vs D-7:** {fmt_number_br(ritmo_d7,2)}x  
             - **vs média do mês:** {fmt_number_br(ritmo_med,2)}x  
           - Ritmos acima de 1,00x sugerem aceleração; abaixo de 1,00x indicam perda de tração.  
           - Eles funcionam como uma *checagem de consistência*: se o dia foge muito do padrão, isso aparece imediatamente nesses índices.

        **Conclusão executiva**  
        - Projetamos o fechamento em **{fmt_currency_br(projecao)}**, o que implica um gap de **{fmt_currency_br(gap)}**
          em relação à meta de **{fmt_currency_br(meta_dia)}**.  
        """
    )


# =========================================================
# PAINEL 2 – CURVAS & RITMO
# =========================================================
def painel_curvas_ritmo(grid: pd.DataFrame, resumo: dict):
    st.subheader("📊 Curvas de venda (DDT)", divider="gray")

    fig_curvas = px.line(
        grid,
        x="SLOT",
        y=["valor_hoje", "valor_d1", "valor_d7", "valor_media_mes"],
        labels={"value": "Valor (R$)", "SLOT": "Horário", "variable": "Curva"},
    )
    fig_curvas.update_layout(
        legend_title="Curva",
        margin=dict(l=20, r=20, t=40, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#EEEEEE"},
    )
    st.plotly_chart(fig_curvas, use_container_width=True)

    st.subheader("📈 Ritmos ao longo do dia", divider="gray")

    projecao = float(resumo["projecao_dia"])
    grid2 = grid.copy()
    grid2["perc_dia_realizado"] = (
        grid2["acum_hoje"] / projecao if projecao > 0 else 0
    )

    df_ritmo = pd.DataFrame(
        {
            "SLOT": grid2["SLOT"],
            "Ritmo vs D-1": grid2["ritmo_vs_d1"],
            "Ritmo vs D-7": grid2["ritmo_vs_d7"],
            "Ritmo vs média do mês": grid2["ritmo_vs_media"],
            "% do dia realizado (Hoje)": grid2["perc_dia_realizado"],
        }
    )

    fig_ritmo = px.line(
        df_ritmo,
        x="SLOT",
        y=[
            "Ritmo vs D-1",
            "Ritmo vs D-7",
            "Ritmo vs média do mês",
            "% do dia realizado (Hoje)",
        ],
        labels={"value": "Índice", "SLOT": "Horário", "variable": "Métrica"},
    )
    fig_ritmo.update_layout(
        legend_title="Comparação",
        margin=dict(l=20, r=20, t=40, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#EEEEEE"},
    )
    st.plotly_chart(fig_ritmo, use_container_width=True)

    st.caption(
        "- As três primeiras linhas são ritmos (x vezes a referência).  \n"
        "- A linha “% do dia realizado (Hoje)” mostra o avanço do dia projetado (acumulado atual / projeção)."
    )

    # Gauges de ritmo
    st.subheader("🧭 Saúde do dia – gauges de ritmo", divider="gray")
    ritmo_d1 = float(resumo["ritmo_vs_d1"])
    ritmo_d7 = float(resumo["ritmo_vs_d7"])
    ritmo_med = float(resumo["ritmo_vs_media"])

    g1, g2, g3 = st.columns(3)
    with g1:
        gauge_ritmo(
            "Ritmo vs D-1",
            ritmo_d1,
            "1,00x = em linha com o acumulado de ontem para o mesmo horário.",
        )
    with g2:
        gauge_ritmo(
            "Ritmo vs D-7",
            ritmo_d7,
            "1,00x = em linha com o mesmo dia da semana passada.",
        )
    with g3:
        gauge_ritmo(
            "Ritmo vs média do mês",
            ritmo_med,
            "1,00x = comportamento igual à média do mês nesse horário.",
        )

    st.subheader("🔥 Mapa de calor – intensidade por horário", divider="gray")

    df_heat = pd.DataFrame(
        {
            "SLOT": grid["SLOT"],
            "Hoje": grid["valor_hoje"],
            "D-1": grid["valor_d1"],
            "D-7": grid["valor_d7"],
            "Média do mês": grid["valor_media_mes"],
        }
    )
    df_melt = df_heat.melt(id_vars="SLOT", var_name="Dia", value_name="Valor")
    heat_matrix = df_melt.pivot(index="Dia", columns="SLOT", values="Valor")

    fig_heat = px.imshow(
        heat_matrix,
        color_continuous_scale="Viridis",
        aspect="auto",
        labels={"color": "Vendas (R$)"},
    )
    fig_heat.update_layout(
        margin=dict(l=40, r=40, t=40, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#EEEEEE"},
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    with st.expander("🧾 Tabela completa (slot a slot)", expanded=False):
        st.dataframe(grid, use_container_width=True)


# =========================================================
# PAINEL 3 – SIMULAÇÃO DE META
# =========================================================
def painel_simulacao_meta(resumo: dict):
    st.subheader("🎯 Simulação de meta e gap", divider="gray")

    meta_atual   = float(resumo["meta_dia"])
    projecao     = float(resumo["projecao_dia"])
    venda_atual  = float(resumo["venda_atual_ate_slot"])

    st.write(
        "Use o controle abaixo para testar diferentes metas e ver o novo gap projetado."
    )

    nova_meta = st.slider(
        "Meta simulada (R$)",
        min_value=int(meta_atual * 0.5),
        max_value=int(meta_atual * 1.5),
        value=int(meta_atual),
        step=50000,
        format="%d",
    )

    gap_sim = projecao - nova_meta
    perc_cobertura = projecao / nova_meta if nova_meta > 0 else 0

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card(
            "Meta atual (oficial)",
            fmt_currency_br(meta_atual),
            "Meta consolidada carregada do arquivo de metas.",
            color=PRIMARY,
        )
    with c2:
        kpi_card(
            "Meta simulada",
            fmt_currency_br(nova_meta),
            "Valor usado para calcular o gap projetado.",
            color=WARNING,
        )
    with c3:
        cor_gap = PRIMARY if gap_sim >= 0 else DANGER
        kpi_card(
            "Gap simulado vs projeção",
            fmt_currency_br(gap_sim),
            f"Cobertura estimada de {fmt_percent_br(perc_cobertura,1)} da meta simulada.",
            color=cor_gap,
        )

    st.markdown(
        f"""
        - Com a meta simulada em **{fmt_currency_br(nova_meta)}**, a projeção de **{fmt_currency_br(projecao)}**
          gera um gap de **{fmt_currency_br(gap_sim)}**.  
        - A venda atual é **{fmt_currency_br(venda_atual)}**, o que já cobre
          **{fmt_percent_br(venda_atual / nova_meta,1)}** da meta simulada.  
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

    inject_global_css()

    user_name = st.session_state.get("user_name", st.session_state.get("user", ""))

    # Banner topo pós-login
    st.markdown(
        """
        <div class="top-banner" style="
            padding:14px 20px;
            border-radius:14px;
            background:linear-gradient(90deg,#00E676,#00B0FF);
            display:flex;
            align-items:center;
            justify-content:space-between;
            margin-bottom:16px;
        ">
            <div>
                <div style="font-size:1.2rem;font-weight:700;color:#001B20;">
                    Painel Executivo – FSJ Black Friday (Site + App)
                </div>
                <div style="font-size:0.85rem;color:#012A30;margin-top:4px;">
                    Monitor de projeção diária, ritmo intradia e comparativos com D-1, D-7 e média do mês.
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

    grid, resumo = load_grid_and_resumo(GRID_PATH, RESUMO_PATH)

    aba1, aba2, aba3 = st.tabs(["Visão Geral", "Curvas & Ritmo", "Simulação de Meta"])

    with aba1:
        painel_visao_geral(grid, resumo, user_name)

    with aba2:
        painel_curvas_ritmo(grid, resumo)

    with aba3:
        painel_simulacao_meta(resumo)


if __name__ == "__main__":
    main()
