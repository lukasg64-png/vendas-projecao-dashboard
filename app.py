import streamlit as st
import pandas as pd
from pathlib import Path

# tentar carregar plotly sem quebrar o app
try:
    import plotly.express as px
except Exception:  # se não tiver plotly, os gráficos viram opcionais
    px = None

# ======================================================
#                CONFIGURAÇÃO GERAL
# ======================================================

st.set_page_config(
    page_title="FSJ Black Friday 2026 – Projeção de Vendas",
    layout="wide",
    initial_sidebar_state="collapsed",
)

PRIMARY = "#00E676"
DANGER = "#FF1744"
WARNING = "#FFC400"
CARD_BG = "#141414"

DATA_DIR = Path("data")


# ======================================================
#                  FUNÇÕES AUXILIARES
# ======================================================

def fmt_num_br(valor: float, casas: int = 0):
    if pd.isna(valor):
        return "-"
    fmt = f"{valor:,.{casas}f}"
    return fmt.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_moeda(valor: float):
    if pd.isna(valor):
        return "-"
    return f"R$ {fmt_num_br(valor, 0)}"


def fmt_percent(frac: float, casas: int = 1):
    if pd.isna(frac):
        return "-"
    return f"{fmt_num_br(frac * 100, casas)}%"


def carregar_usuarios():
    path = DATA_DIR / "usuarios.csv"
    # sep=None + engine="python" tenta adivinhar se é ; ou ,
    df = pd.read_csv(path, sep=None, engine="python")
    # padronizar nomes em minúsculo
    df.columns = [c.strip().lower() for c in df.columns]
    return df


def carregar_resumo():
    path = DATA_DIR / "saida_resumo.csv"
    df = pd.read_csv(path)

    row = df.iloc[0].copy()

    cols_float = [
        "meta_dia", "venda_atual_ate_slot", "percentual_dia_hist",
        "projecao_dia", "desvio_projecao",
        "total_d1", "meta_d1", "desvio_d1",
        "total_d7", "meta_d7", "desvio_d7",
        "ritmo_vs_d1", "ritmo_vs_d7", "ritmo_vs_media",
    ]
    for c in cols_float:
        if c in row.index:
            row[c] = pd.to_numeric(row[c], errors="coerce")

    return row


def carregar_grid():
    path = DATA_DIR / "saida_grid.csv"
    df = pd.read_csv(path)

    num_cols = [
        "valor_hoje", "valor_d1", "valor_d7", "valor_media_mes",
        "frac_hist", "acum_hoje", "acum_d1", "acum_d7", "acum_media_mes",
        "ritmo_vs_d1", "ritmo_vs_d7", "ritmo_vs_media",
    ]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    return df


def kpi_html(titulo: str, valor: str, tooltip: str, cor_valor: str = PRIMARY):
    return f"""
    <div title="{tooltip}"
         style="
            background: rgba(255,255,255,0.03);
            padding: 14px 16px;
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.07);
            box-shadow: 0 6px 16px rgba(0,0,0,0.45);
            backdrop-filter: blur(6px);
         ">
        <div style="font-size:0.80rem;color:#CCCCCC;margin-bottom:4px;">
            {titulo}
        </div>
        <div style="font-size:1.6rem;font-weight:700;color:{cor_valor};">
            {valor}
        </div>
        <div style="font-size:0.70rem;color:#888888;margin-top:2px;">
            Passe o mouse para ver a explicação.
        </div>
    </div>
    """


def header(resumo, usuario_nome: str):
    try:
        data_ref = pd.to_datetime(resumo["data_referencia"]).date()
        data_str = data_ref.strftime("%d/%m/%Y")
    except Exception:
        data_str = "–"

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(90deg,#00C853,#00E5FF);
            padding: 10px 18px;
            border-radius: 0 0 18px 18px;
            display:flex;
            justify-content:space-between;
            align-items:center;
        ">
            <div>
                <div style="font-size:0.85rem;color:#E0FFE8;">
                    Usuário: <b>{usuario_nome}</b> • Data de referência: <b>{data_str}</b>
                </div>
                <div style="font-size:1.2rem;font-weight:700;color:#FFFFFF;margin-top:2px;">
                    📈 FSJ Black Friday 2026 – Projeção de Vendas (Site + App)
                </div>
            </div>
            <div style="
                font-size:0.75rem;
                background:rgba(0,0,0,0.18);
                padding:6px 10px;
                border-radius:999px;
                color:#F5F5F5;
            ">
                Feito por: <b>Planejamento e Dados E-Commerce</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ======================================================
#                     LOGIN
# ======================================================

def login_screen():
    st.markdown(
        """
        <div style="text-align:center;margin-top:40px;margin-bottom:20px;">
            <div style="font-size:1.6rem;font-weight:700;margin-bottom:6px;">
                🔐 FSJ – Painel de Projeção de Vendas
            </div>
            <div style="font-size:0.95rem;color:#AAAAAA;">
                Acesse com seu usuário cadastrado em <b>Planejamento & Dados E-Commerce</b>.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    usuarios_df = carregar_usuarios()

    with st.form("login_form"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar")

    if entrar:
        # garantir que as colunas existem
        cols = [c.lower() for c in usuarios_df.columns]
        if not {"usuario", "senha"}.issubset(set(cols)):
            st.error("Arquivo usuarios.csv não está no formato esperado (usuario, senha, nome).")
            return

        # padronizar colunas
        usuarios_df.columns = cols

        linha = usuarios_df[
            (usuarios_df["usuario"] == usuario) &
            (usuarios_df["senha"] == senha)
        ]

        if linha.empty:
            st.error("Usuário ou senha inválidos.")
        else:
            nome = linha.iloc[0]["nome"] if "nome" in linha.columns else usuario
            st.session_state["auth"] = True
            st.session_state["usuario_nome"] = nome
            st.rerun()


# ======================================================
#                     PÁGINA PRINCIPAL
# ======================================================

def main():
    resumo = carregar_resumo()
    grid = carregar_grid()

    usuario_nome = st.session_state.get("usuario_nome", "Usuário")

    header(resumo, usuario_nome)
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### 🎯 Visão Geral do Dia")

    col1, col2, col3, col4 = st.columns(4)

    meta_dia = resumo.get("meta_dia", 0.0)
    venda_atual = resumo.get("venda_atual_ate_slot", 0.0)
    projecao = resumo.get("projecao_dia", 0.0)
    gap_proj = resumo.get("desvio_projecao", 0.0)

    total_d1 = resumo.get("total_d1", 0.0)
    total_d7 = resumo.get("total_d7", 0.0)
    ritmo_d1 = resumo.get("ritmo_vs_d1", 0.0)
    ritmo_d7 = resumo.get("ritmo_vs_d7", 0.0)
    frac_hist = resumo.get("percentual_dia_hist", 0.0)
    ritmo_media = resumo.get("ritmo_vs_media", 0.0)

    # linha 1
    with col1:
        st.markdown(
            kpi_html(
                "Meta do dia",
                fmt_moeda(meta_dia),
                "Meta consolidada de vendas (Site + App) definida pelo planejamento para o dia.",
                PRIMARY,
            ),
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            kpi_html(
                "Venda atual (até o último slot)",
                fmt_moeda(venda_atual),
                "Soma das vendas registradas até o slot de 15 minutos mais recente.",
                PRIMARY if venda_atual > 0 else "#CCCCCC",
            ),
            unsafe_allow_html=True,
        )

    with col3:
        cor_proj = PRIMARY if projecao >= meta_dia else DANGER
        st.markdown(
            kpi_html(
                "Projeção de fechamento",
                fmt_moeda(projecao),
                (
                    "Projeção construída a partir da venda acumulada, dividida "
                    "pelo percentual médio do mês correspondente ao horário, "
                    "com uma checagem pelos ritmos vs D-1, D-7 e média do mês."
                ),
                cor_proj,
            ),
            unsafe_allow_html=True,
        )

    with col4:
        cor_gap = PRIMARY if gap_proj >= 0 else DANGER
        st.markdown(
            kpi_html(
                "Gap projetado vs meta",
                fmt_moeda(gap_proj),
                "Diferença entre a projeção de fechamento e a meta do dia. "
                "Valor negativo indica tendência de ficar abaixo da meta.",
                cor_gap,
            ),
            unsafe_allow_html=True,
        )

    # linha 2
    col5, col6, col7, col8 = st.columns(4)

    with col5:
        st.markdown(
            kpi_html(
                "Total D-1 (dia inteiro)",
                fmt_moeda(total_d1),
                "Venda total consolidada do dia anterior (D-1).",
                PRIMARY,
            ),
            unsafe_allow_html=True,
        )

    with col6:
        st.markdown(
            kpi_html(
                "Total D-7 (dia inteiro)",
                fmt_moeda(total_d7),
                "Venda total consolidada do mesmo dia da semana passada (D-7).",
                PRIMARY,
            ),
            unsafe_allow_html=True,
        )

    with col7:
        st.markdown(
            kpi_html(
                "Ritmo vs D-1",
                f"{fmt_num_br(ritmo_d1, 2)}x",
                "Ritmo acumulado de hoje dividido pelo acumulado de D-1 no mesmo horário.",
                PRIMARY if ritmo_d1 >= 1 else DANGER,
            ),
            unsafe_allow_html=True,
        )

    with col8:
        st.markdown(
            kpi_html(
                "Ritmo vs D-7",
                f"{fmt_num_br(ritmo_d7, 2)}x",
                "Ritmo acumulado de hoje dividido pelo acumulado de D-7 no mesmo horário.",
                PRIMARY if ritmo_d7 >= 1 else DANGER,
            ),
            unsafe_allow_html=True,
        )

    # linha 3
    col9, col10 = st.columns(2)

    with col9:
        st.markdown(
            kpi_html(
                "Dia já percorrido (curva histórica)",
                fmt_percent(frac_hist, 1),
                "Percentual médio do mês que já deveria ter sido vendido até este slot.",
                WARNING,
            ),
            unsafe_allow_html=True,
        )

    with col10:
        st.markdown(
            kpi_html(
                "Ritmo vs média do mês",
                f"{fmt_num_br(ritmo_media, 2)}x",
                "Compara a venda acumulada de hoje com a média do mês no mesmo horário.",
                PRIMARY if ritmo_media >= 1 else DANGER,
            ),
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ---------------------- INSIGHTS -----------------

    st.markdown("### 🧠 Insights Estratégicos")

    exp_r = resumo.get("explicacao_ritmo", "")
    exp_d1 = resumo.get("explicacao_d1", "")
    exp_d7 = resumo.get("explicacao_d7", "")

    st.markdown(
        f"""
        <div style="
            background:{CARD_BG};
            padding:18px 20px;
            border-radius:14px;
            border:1px solid rgba(255,255,255,0.08);
        ">
            <ul style="padding-left:18px;margin:0;font-size:0.9rem;color:#EEEEEE;">
                <li>{exp_r}</li>
                <li>{exp_d1}</li>
                <li>{exp_d7}</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ------------------ EXPLICAÇÃO DO MODELO -------------

    st.markdown("#### ⚙️ Como a projeção é calculada?")

    explicacao_modelo = f"""
    A projeção de fechamento é construída em três camadas:

    1. **Curva intradia histórica**  
       • Calculamos, para cada slot de 15 minutos, qual fração do dia já foi vendida ao longo do mês.  
       • No horário atual, essa fração média é de **{fmt_percent(frac_hist, 2)}**.

    2. **Base de projeção**  
       • Consideramos a venda acumulada de hoje (**{fmt_moeda(venda_atual)}**).  
       • Dividimos pela fração histórica do horário atual, obtendo um fechamento esperado.

    3. **Camada de ritmo e consistência**  
       • Monitoramos os ritmos vs D-1 (**{fmt_num_br(ritmo_d1,2)}x**), vs D-7 (**{fmt_num_br(ritmo_d7,2)}x**) e vs média do mês (**{fmt_num_br(ritmo_media,2)}x**).  
       • Esses indicadores funcionam como checagem de consistência: se o comportamento do dia estiver muito fora do padrão, isso aparece imediatamente nos ritmos.

    O resultado final é a projeção exibida em **“Projeção de fechamento”**, hoje em **{fmt_moeda(projecao)}**, com gap projetado de **{fmt_moeda(gap_proj)}** em relação à meta.
    """

    st.markdown(explicacao_modelo)

    st.markdown("---")
    st.markdown("### 📊 Curvas de Vendas | DDT Slot a Slot")

    if px is None:
        st.warning("Plotly não está instalado. Adicione `plotly` ao requirements.txt para ver os gráficos.")
    else:
        tab1, tab2 = st.tabs(["Curva por slot", "Acumulado por slot"])

        with tab1:
            fig = px.line(
                grid,
                x="SLOT",
                y=["valor_hoje", "valor_d1", "valor_d7", "valor_media_mes"],
                labels={"value": "Vendas (R$)", "SLOT": "Horário", "variable": "Série"},
            )
            fig.update_layout(template="plotly_dark", height=420)
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            fig2 = px.line(
                grid,
                x="SLOT",
                y=["acum_hoje", "acum_d1", "acum_d7", "acum_media_mes"],
                labels={"value": "Vendas Acumuladas (R$)", "SLOT": "Horário", "variable": "Série"},
            )
            fig2.update_layout(template="plotly_dark", height=420)
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("### 🧮 Tabela detalhada – DDT Slot a Slot")

    df_show = grid.copy()

    for col in ["valor_hoje", "valor_d1", "valor_d7", "valor_media_mes",
                "acum_hoje", "acum_d1", "acum_d7", "acum_media_mes"]:
        if col in df_show.columns:
            df_show[col] = df_show[col].apply(fmt_moeda)

    if "frac_hist" in df_show.columns:
        df_show["frac_hist"] = df_show["frac_hist"].apply(lambda x: fmt_percent(x, 2))
    for col in ["ritmo_vs_d1", "ritmo_vs_d7", "ritmo_vs_media"]:
        if col in df_show.columns:
            df_show[col] = df_show[col].apply(lambda x: f"{fmt_num_br(x,2)}x")

    st.dataframe(df_show, use_container_width=True, height=420)


# ======================================================
#                 CONTROLE DE FLUXO
# ======================================================

if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    login_screen()
else:
    main()
