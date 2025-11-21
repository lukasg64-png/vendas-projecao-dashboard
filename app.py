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
    # Fallback se o arquivo não existir
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


def fmt_currency_br(x: float, decimals: int = 0) -> str:
    if x is None:
        return "-"
    try:
        if np.isnan(x):
            return "-"
    except Exception:
        pass
    fmt = f"{x:,.{decimals}f}"
    fmt = fmt.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {fmt}"


def fmt_percent_br(x: float, decimals: int = 2) -> str:
    if x is None:
        return "-"
    try:
        if np.isnan(x):
            return "-"
    except Exception:
        pass
    pct = x * 100
    fmt = f"{pct:,.{decimals}f}"
    fmt = fmt.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{fmt}%"


def kpi_card(
    title: str,
    value: str,
    subtitle: str = "",
    color: str = PRIMARY,
    tooltip: str | None = None,
):
    info_html = ""
    if tooltip:
        info_html = (
            f"<span style='margin-left:6px; cursor:help;' title='{tooltip}'>ℹ️</span>"
        )

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
# TELA DE LOGIN
# =========================================================
def login_screen(df_logins: pd.DataFrame):
    # Barra superior compacta
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

    # Container central do login
    login_col = st.columns([1, 1, 1])[1]
    with login_col:
        st.markdown(
            """
            <div style="font-size:1.05rem;font-weight:600;margin-bottom:8px;">
                🔐 Acesse o painel
            </div>
            """,
            unsafe_allow_html=True,
        )

        username = st.text_input("Usuário", key="login_user")
        password = st.text_input("Senha", type="password", key="login_pwd")

        if st.button("Entrar", type="primary", use_container_width=True):
            ok, nome = authenticate(username.strip(), password.strip(), df_logins)
            if ok:
                st.session_state["auth"] = True
                st.session_state["user"] = username.strip()
                st.session_state["user_name"] = nome
                st.rerun()
            else:
                st.error(
                    "Usuário ou senha inválidos. Confira os dados ou fale com o time de Dados."
                )

        st.caption("Dica: usuários são carregados do arquivo `data/logins.csv`.")


# =========================================================
# CARREGAR DADOS PRINCIPAIS
# =========================================================
@st.cache_data
def load_grid_and_resumo(grid_path: Path, resumo_path: Path):
    grid = pd.read_csv(grid_path)
    resumo_df = pd.read_csv(resumo_path)
    resumo = resumo_df.iloc[0].to_dict()
    return grid, resumo


# =========================================================
# VISÃO GERAL (TAB 1)
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

    perc_meta_real = venda_atual / meta_dia if meta_dia > 0 else 0.0

    st.markdown(
        f"""
        <div style="margin-bottom:10px;font-size:0.9rem;color:#BBBBBB;">
            Usuário: <b>{user_name}</b> • Data de referência: <b>{data_ref.strftime('%d/%m/%Y')}</b> • Canal: Site + App
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- KPIs linha 1 ---
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
        kpi_card(
            "Venda atual",
            fmt_currency_br(venda_atual),
            f"Equivalente a {fmt_percent_br(perc_meta_real, 1)} da meta.",
            color=PRIMARY if perc_meta_real >= frac_hist else WARNING,
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

    gap_label = "Acima da meta" if gap >= 0 else "Abaixo da meta"
    gap_color = PRIMARY if gap >= 0 else DANGER
    with c4:
        kpi_card(
            "Gap projetado vs meta",
            fmt_currency_br(gap),
            f"{gap_label}.",
            color=gap_color,
            tooltip="Diferença entre a projeção de fechamento e a meta consolidada do dia.",
        )

    st.markdown("---")

    # --- Ritmos & totais ---
    st.subheader("📈 Ritmo do dia", divider="gray")

    c5, c6, c7, c8 = st.columns(4)

    with c5:
        kpi_card(
            "Total D-1 (dia inteiro)",
            fmt_currency_br(total_d1),
            "Faturamento total de ontem.",
            color=PRIMARY,
            tooltip="Fechamento consolidado do dia anterior (D-1).",
        )

    with c6:
        kpi_card(
            "Total D-7 (dia inteiro)",
            fmt_currency_br(total_d7),
            "Fechamento do mesmo dia da semana passada.",
            color=PRIMARY,
            tooltip="Fechamento consolidado de D-7 (mesmo dia da semana, semana anterior).",
        )

    with c7:
        kpi_card(
            "Dia já percorrido (histórico)",
            fmt_percent_br(frac_hist, 1),
            "Fraçao média do dia que costuma estar vendida nesse horário.",
            color=WARNING,
            tooltip="Percentual médio do dia já realizado, segundo a curva intradia histórica.",
        )

    with c8:
        texto_ritmo = (
            f"vs D-1: {ritmo_d1:.2f}x • "
            f"vs D-7: {ritmo_d7:.2f}x • "
            f"vs média do mês: {ritmo_med:.2f}x"
        )
        kpi_card(
            "Ritmo combinado",
            "",
            texto_ritmo,
            color=PRIMARY if ritmo_d1 >= 1 and ritmo_d7 >= 1 else WARNING,
            tooltip="Ritmos de venda comparando o acumulado de hoje com D-1, D-7 e média do mês.",
        )

    # --- Como interpretar o ritmo ---
    with st.expander("🧠 Como interpretar os ritmos", expanded=False):
        st.markdown(
            f"""
            - **Ritmo vs D-1 ({ritmo_d1:.2f}x)** → quanto o acumulado de hoje está maior ou menor que o acumulado de ontem no mesmo horário.  
            - **Ritmo vs D-7 ({ritmo_d7:.2f}x)** → comparação com o mesmo dia da semana passada.  
            - **Ritmo vs média do mês ({ritmo_med:.2f}x)** → comparação com o comportamento médio do mês para este horário.  

            Em geral:
            - **acima de 1,00x** → estamos acelerados em relação à referência.  
            - **abaixo de 1,00x** → estamos perdendo tração vs a referência.  
            """
        )

    # --- Análise executiva de projeção ---
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
           - Dividimos esse valor pela fração histórica do horário: `venda_atual / frac_hist`.  
           - Isso gera uma projeção de fechamento em torno de **{fmt_currency_br(projecao)}** para o dia.

        3. **Camada de consistência por ritmo**  
           - Em paralelo, monitoramos os ritmos:  
             - **vs D-1:** {ritmo_d1:.2f}x  
             - **vs D-7:** {ritmo_d7:.2f}x  
             - **vs média do mês:** {ritmo_med:.2f}x  
           - Ritmos acima de 1,00x sugerem aceleração; abaixo de 1,00x indicam perda de tração.  
           - Eles funcionam como uma *checagem de consistência*: se o dia foge muito do padrão, isso aparece imediatamente nesses índices.

        **Conclusão executiva**  
        - Projetamos o fechamento em **{fmt_currency_br(projecao)}**, o que implica um gap de **{fmt_currency_br(gap)}** em relação à meta de **{fmt_currency_br(meta_dia)}**.  
        """
    )


# =========================================================
# CURVAS & RITMO (TAB 2)
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
    )
    st.plotly_chart(fig_curvas, use_container_width=True)

    st.subheader("📈 Ritmos ao longo do dia", divider="gray")

    projecao = float(resumo["projecao_dia"])
    grid = grid.copy()

    if projecao > 0:
        grid["perc_dia_realizado"] = grid["acum_hoje"] / projecao
    else:
        grid["perc_dia_realizado"] = 0.0

    df_ritmo = pd.DataFrame(
        {
            "SLOT": grid["SLOT"],
            "Ritmo vs D-1": grid["ritmo_vs_d1"],
            "Ritmo vs D-7": grid["ritmo_vs_d7"],
            "Ritmo vs média do mês": grid["ritmo_vs_media"],
            "% do dia realizado": grid["perc_dia_realizado"],
        }
    )

    fig_ritmo = px.line(
        df_ritmo,
        x="SLOT",
        y=[
            "Ritmo vs D-1",
            "Ritmo vs D-7",
            "Ritmo vs média do mês",
            "% do dia realizado",
        ],
        labels={"value": "Índice", "SLOT": "Horário", "variable": "Métrica"},
    )
    fig_ritmo.update_layout(
        legend_title="Comparação",
        margin=dict(l=20, r=20, t=40, b=40),
    )
    st.plotly_chart(fig_ritmo, use_container_width=True)

    st.caption(
        """
        - As três primeiras linhas são ritmos (x vezes a referência).  
        - A linha “% do dia realizado” mostra o avanço do dia projetado (acumulado atual / projeção).
        """
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
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    with st.expander("🧾 Tabela completa (slot a slot)", expanded=False):
        st.dataframe(grid, use_container_width=True)


# =========================================================
# SIMULAÇÃO DE META (TAB 3)
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
    perc_real = venda_atual / nova_meta if nova_meta > 0 else 0

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
          **{fmt_percent_br(perc_real,1)}** da meta simulada.
        """
    )


# =========================================================
# MAIN
# =========================================================
def main():
    df_logins = load_logins(LOGINS_PATH)

    if "auth" not in st.session_state:
        st.session_state["auth"] = False

    # Se não autenticado, mostra tela de login
    if not st.session_state["auth"]:
        login_screen(df_logins)
        return

    # Usuário autenticado → carrega dados do painel
    user_name = st.session_state.get("user_name", st.session_state.get("user", ""))

    # Barra superior do painel
    st.markdown(
        """
        <div style="
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

    # Carregar dados
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
