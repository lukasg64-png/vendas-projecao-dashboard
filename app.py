import streamlit as st
import pandas as pd
from pathlib import Path

# ======================================================
#            CONFIGURAÇÃO GERAL DO APP
# ======================================================

st.set_page_config(
    page_title="📈 FSJ Black Friday 2026 – Projeção de Vendas",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Paleta de cores do tema
PRIMARY = "#00C853"   # Verde FSJ
DANGER  = "#FF1744"   # Vermelho alerta
WARNING = "#FFD600"   # Amarelo atenção
CARD_BG = "#151515"   # Fundo dos cards
BG_DARK = "#0B0B0B"

# CSS para deixar o visual mais “Black Friday FSJ”
st.markdown(
    f"""
    <style>
        .stApp {{
            background-color: {BG_DARK};
            color: #FFFFFF;
        }}
        .big-title {{
            font-size: 34px !important;
            font-weight: 800 !important;
            color: #FFFFFF;
        }}
        .subtitle {{
            font-size: 16px !important;
            color: #CCCCCC;
        }}
        .logo-box {{
            background: linear-gradient(90deg, #00C853 0%, #1DE9B6 50%, #000000 100%);
            padding: 14px 24px;
            border-radius: 12px;
            margin-bottom: 10px;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ======================================================
#                  LOGIN VIA CSV
# ======================================================

@st.cache_data
def load_users(path: str = "data/usuarios.csv") -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        # fallback: um usuário padrão se o CSV não existir
        return pd.DataFrame(
            [{"usuario": "farmacias_sao_joao", "senha": "blackfriday2025", "nome": "Admin", "perfil": "admin"}]
        )
    df = pd.read_csv(p)
    # normalizar nomes de colunas
    df.columns = [c.strip().lower() for c in df.columns]
    return df


def autenticar_usuario(usuario: str, senha: str, users_df: pd.DataFrame):
    """Retorna a linha do usuário se login estiver correto, senão None."""
    if not usuario or not senha:
        return None
    mask = (users_df["usuario"] == usuario) & (users_df["senha"] == senha)
    if mask.any():
        return users_df[mask].iloc[0]
    return None


def tela_login():
    users_df = load_users()

    st.markdown("<div class='logo-box'><span class='big-title'>FSJ Black Friday 2026</span><br><span class='subtitle'>Painel de Projeção de Vendas – Site + App</span></div>", unsafe_allow_html=True)
    st.markdown("### 🔐 Acesso Restrito")

    col_login, col_info = st.columns([1, 1.2])

    with col_login:
        usuario = st.text_input("Usuário", key="login_user")
        senha   = st.text_input("Senha", type="password", key="login_pwd")

        if st.button("Entrar", type="primary", use_container_width=True):
            user_row = autenticar_usuario(usuario, senha, users_df)
            if user_row is not None:
                st.session_state["auth"] = True
                st.session_state["user_name"] = user_row.get("nome", usuario)
                st.session_state["user_profile"] = user_row.get("perfil", "user")
                st.experimental_rerun()
            else:
                st.error("Usuário ou senha inválidos. Verifique e tente novamente.")

    with col_info:
        st.markdown(
            """
            **FSJ Black Friday 2026 – Painel Executivo**

            - Controle diário de **meta x venda x projeção**
            - Comparação com **D-1** e **D-7** (mesmo horário)
            - Curva intradia baseada no comportamento histórico
            - Indicadores em tempo real para decisões táticas

            > Para adicionar ou alterar usuários, basta editar o arquivo `data/usuarios.csv`
            > com as colunas `usuario`, `senha`, `nome` (e opcionalmente `perfil`).
            """
        )


# Estado de autenticação
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    tela_login()
    st.stop()

# ======================================================
#          CARREGAR ARQUIVOS GERADOS NO COLAB
# ======================================================

@st.cache_data
def load_resumo(path: str = "data/saida_resumo.csv") -> pd.Series:
    df = pd.read_csv(path)
    if df.empty:
        raise ValueError("Arquivo saída_resumo.csv está vazio.")
    row = df.iloc[0]
    row.index = [c.strip() for c in row.index]
    return row


@st.cache_data
def load_grid(path: str = "data/saida_grid.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    return df


def get_first(row: pd.Series, keys, default=None):
    """Pega o primeiro campo existente em `keys`."""
    if isinstance(keys, str):
        keys = [keys]
    for k in keys:
        if k in row.index:
            return row[k]
    return default


# Carrega dados
try:
    resumo_row = load_resumo()
    grid = load_grid()
except Exception as e:
    st.error(f"Erro ao carregar arquivos de saída: {e}")
    st.stop()

# ======================================================
#        EXTRAIR MÉTRICAS DO RESUMO (COM ROBUSTEZ)
# ======================================================

data_ref = get_first(resumo_row, ["data_referencia", "data"], "")
meta_dia = float(get_first(resumo_row, ["meta_dia", "MetaDia", "meta_total", "Meta_TOTAL"], 0.0))

venda_atual = float(
    get_first(resumo_row, ["venda_atual_ate_slot", "venda_atual", "VendaAtual"], 0.0)
)

projecao = float(
    get_first(resumo_row, ["projecao_dia", "projecao", "ProjecaoDia"], venda_atual)
)

gap = get_first(resumo_row, ["desvio_projecao", "gap"], None)
if gap is None:
    gap = projecao - meta_dia
gap = float(gap)

percent_hist = float(
    get_first(resumo_row, ["percentual_dia_hist", "frac_hist"], 0.0)
)

total_d1  = float(get_first(resumo_row, ["total_d1"], 0.0))
meta_d1   = float(get_first(resumo_row, ["meta_d1"], meta_dia))
desvio_d1 = float(get_first(resumo_row, ["desvio_d1"], total_d1 - meta_d1))

total_d7  = float(get_first(resumo_row, ["total_d7"], 0.0))
meta_d7   = float(get_first(resumo_row, ["meta_d7"], meta_dia))
desvio_d7 = float(get_first(resumo_row, ["desvio_d7"], total_d7 - meta_d7))

ritmo_vs_d1    = float(get_first(resumo_row, ["ritmo_vs_d1"], 0.0))
ritmo_vs_d7    = float(get_first(resumo_row, ["ritmo_vs_d7"], 0.0))
ritmo_vs_media = float(get_first(resumo_row, ["ritmo_vs_media"], 0.0))

exp_ritmo = get_first(resumo_row, "explicacao_ritmo", "")
exp_d1    = get_first(resumo_row, "explicacao_d1", "")
exp_d7    = get_first(resumo_row, "explicacao_d7", "")

# ======================================================
#                    CABEÇALHO
# ======================================================

st.markdown(
    "<div class='logo-box'><span class='big-title'>📈 FSJ Black Friday 2026 – Projeção de Vendas (Site + App)</span><br>"
    f"<span class='subtitle'>Usuário: {st.session_state.get('user_name', 'N/A')} • Data de referência: {data_ref}</span></div>",
    unsafe_allow_html=True,
)

st.sidebar.markdown("## ⚙️ Opções")
st.sidebar.write("Arquivos usados:")
st.sidebar.code("data/saida_resumo.csv\ndata/saida_grid.csv\ndata/usuarios.csv")
if st.sidebar.button("Sair da sessão"):
    st.session_state["auth"] = False
    st.experimental_rerun()

# ======================================================
#                 FUNÇÃO DE CARD KPI
# ======================================================

def kpi(title: str, value: str, color: str, help_text: str | None = None):
    tooltip = f"title='{help_text}'" if help_text else ""
    st.markdown(
        f"""
        <div style="background:{CARD_BG}; padding:18px; border-radius:14px;
                    text-align:center; border:1px solid #333; box-shadow:0 0 12px rgba(0,0,0,0.6);">
            <div style="font-size:14px; color:#CCCCCC; margin-bottom:6px;" {tooltip}>{title}</div>
            <div style="font-size:26px; font-weight:700; color:{color};">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ======================================================
#                     KPIs PRINCIPAIS
# ======================================================

st.markdown("### 🎯 Visão Geral do Dia")

row1 = st.columns(4)
with row1[0]:
    kpi("Meta do Dia", f"R$ {meta_dia:,.0f}", PRIMARY)
with row1[1]:
    kpi("Venda Atual", f"R$ {venda_atual:,.0f}", PRIMARY)
with row1[2]:
    cor_proj = PRIMARY if projecao >= meta_dia else DANGER
    kpi("Projeção de Fechamento", f"R$ {projecao:,.0f}", cor_proj)
with row1[3]:
    cor_gap = PRIMARY if gap >= 0 else DANGER
    kpi("Gap Projetado vs Meta", f"R$ {gap:,.0f}", cor_gap)

row2 = st.columns(4)
with row2[0]:
    kpi("Total D-1 (dia inteiro)", f"R$ {total_d1:,.0f}", "#FFFFFF")
with row2[1]:
    kpi("Desvio D-1 vs Meta", f"R$ {desvio_d1:,.0f}", PRIMARY if desvio_d1 >= 0 else DANGER)
with row2[2]:
    kpi("Total D-7 (dia inteiro)", f"R$ {total_d7:,.0f}", "#FFFFFF")
with row2[3]:
    kpi("Desvio D-7 vs Meta", f"R$ {desvio_d7:,.0f}", PRIMARY if desvio_d7 >= 0 else DANGER)

row3 = st.columns(3)
with row3[0]:
    kpi("Ritmo vs D-1", f"{ritmo_vs_d1:,.2f}x", PRIMARY if ritmo_vs_d1 >= 1 else DANGER)
with row3[1]:
    kpi("Ritmo vs D-7", f"{ritmo_vs_d7:,.2f}x", PRIMARY if ritmo_vs_d7 >= 1 else DANGER)
with row3[2]:
    kpi("Dia já percorrido (histórico)", f"{percent_hist*100:,.1f}%", WARNING)

# ======================================================
#                  INSIGHTS EXECUTIVOS
# ======================================================

st.markdown("### 🧠 Insights Estratégicos")

if not exp_ritmo:
    exp_ritmo = (
        f"Até agora vendemos aproximadamente **R$ {venda_atual:,.0f}**, o que representa "
        f"**{percent_hist*100:,.1f}%** da curva intradia histórica."
    )
if not exp_d1:
    exp_d1 = (
        f"No dia anterior (D-1) o dia fechou em **R$ {total_d1:,.0f}** "
        f"frente a uma meta de **R$ {meta_d1:,.0f}** (**{desvio_d1:,.0f}** de desvio)."
    )
if not exp_d7:
    exp_d7 = (
        f"Há uma semana (D-7), o dia fechou em **R$ {total_d7:,.0f}** "
        f"frente à meta de **R$ {meta_d7:,.0f}** (**{desvio_d7:,.0f}** de desvio)."
    )

st.info(
    f"""
- {exp_ritmo}
- {exp_d1}
- {exp_d7}
- Ritmo atual vs D-1: **{ritmo_vs_d1:,.2f}x** • Ritmo atual vs D-7: **{ritmo_vs_d7:,.2f}x**  
- Se o ritmo atual se mantiver, projetamos **R$ {projecao:,.0f}** no fechamento.
"""
)

# ======================================================
#                  CURVAS E HISTÓRICO DDT
# ======================================================

st.markdown("### 📊 Curva Intradia – DDT por Slot (15 em 15 minutos)")

# garantir que SLOT é string ordenável
if "SLOT" in grid.columns:
    grid = grid.sort_values("SLOT")
    grid = grid.set_index("SLOT")

col_curva1, col_curva2 = st.columns(2)

# Curva de valor por slot
with col_curva1:
    st.markdown("#### 💵 Venda por Slot (Hoje x D-1 x D-7 x Média Mês)")
    cols_valor = [c for c in ["valor_hoje", "valor_d1", "valor_d7", "valor_media_mes"] if c in grid.columns]
    if cols_valor:
        st.line_chart(grid[cols_valor])
    else:
        st.warning("Colunas de valor por slot não encontradas em `saida_grid.csv`.")

# Curva acumulada
with col_curva2:
    st.markdown("#### 📈 Curva Acumulada (Hoje x D-1 x D-7 x Média Mês)")
    cols_acum = [c for c in ["acum_hoje", "acum_d1", "acum_d7", "acum_media_mes"] if c in grid.columns]
    if cols_acum:
        st.line_chart(grid[cols_acum])
    else:
        st.warning("Colunas acumuladas não encontradas em `saida_grid.csv`.")

# ======================================================
#                TABELA DETALHADA / EXPORT
# ======================================================

st.markdown("### 🧮 Tabela Detalhada – Slot a Slot")

st.dataframe(grid.reset_index(), use_container_width=True)

st.download_button(
    "⬇️ Baixar tabela completa (CSV)",
    data=grid.reset_index().to_csv(index=False).encode("utf-8"),
    file_name="fsj_black_friday_ddt_completo.csv",
    mime="text/csv",
)
