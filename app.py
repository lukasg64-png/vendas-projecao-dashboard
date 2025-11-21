import streamlit as st
import pandas as pd
from pathlib import Path
import locale

# ======================================================
#            CONFIGURAÇÃO GERAL DO APP
# ======================================================

st.set_page_config(
    page_title="📈 FSJ Black Friday 2026 – Projeção de Vendas",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Tenta usar locale PT-BR para formatação
try:
    locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")
except:
    # Se não tiver no servidor, vamos usar fallback manual
    pass

PRIMARY = "#00C853"   # Verde FSJ
DANGER  = "#FF1744"   # Vermelho alerta
WARNING = "#FFD600"   # Amarelo atenção
CARD_BG = "#151515"   # Fundo dos cards
BG_DARK = "#050505"   # Fundo geral

def money_br(valor, com_centavos=True):
    """Formata número no padrão brasileiro: 1.234.567,89."""
    try:
        if com_centavos:
            return locale.format_string("%.2f", float(valor), grouping=True)
        else:
            return locale.format_string("%.0f", float(valor), grouping=True)
    except:
        # Fallback caso locale não funcione
        if com_centavos:
            s = f"{float(valor):,.2f}"
        else:
            s = f"{float(valor):,.0f}"
        s = s.replace(",", "X").replace(".", ",").replace("X", ".")
        return s

# CSS visual
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
            font-size: 15px !important;
            color: #CCCCCC;
        }}
        .logo-box {{
            background: linear-gradient(90deg, #00C853 0%, #1DE9B6 50%, #000000 100%);
            padding: 14px 24px;
            border-radius: 12px;
            margin-bottom: 18px;
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
            [{"usuario": "farmacias_sao_joao",
              "senha": "blackfriday2026",
              "nome": "Admin",
              "perfil": "admin"}]
        )
    df = pd.read_csv(p)
    df.columns = [c.strip().lower() for c in df.columns]
    # garantir colunas mínimas
    if "usuario" not in df.columns or "senha" not in df.columns:
        raise ValueError("Arquivo usuarios.csv precisa ter colunas 'usuario' e 'senha'.")
    return df

def autenticar_usuario(usuario: str, senha: str, users_df: pd.DataFrame):
    if not usuario or not senha:
        return None
    mask = (users_df["usuario"] == usuario) & (users_df["senha"] == senha)
    if mask.any():
        return users_df[mask].iloc[0]
    return None

def tela_login():
    users_df = load_users()

    st.markdown(
        "<div class='logo-box'>"
        "<span class='big-title'>FSJ Black Friday 2026</span><br>"
        "<span class='subtitle'>Painel de Projeção de Vendas – Site + App</span>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown("### 🔐 Acesso Restrito")

    col_login, col_info = st.columns([1, 1.2])

    with col_login:
        usuario = st.text_input("Usuário")
        senha   = st.text_input("Senha", type="password")

        if st.button("Entrar", type="primary", use_container_width=True):
            user_row = autenticar_usuario(usuario, senha, users_df)
            if user_row is not None:
                st.session_state["auth"] = True
                st.session_state["user_name"] = user_row.get("nome", usuario)
                st.session_state["user_profile"] = user_row.get("perfil", "user")
                st.experimental_rerun()
            else:
                st.error("Usuário ou senha inválidos.")

    with col_info:
        st.markdown(
            """
            **FSJ Black Friday 2026 – Painel Executivo**

            - Monitoramento de **meta x venda x projeção** em tempo quase real  
            - Comparativos com **D-1** e **D-7** por mesmo horário  
            - Curva intradia baseada no histórico do mês  
            - Indicadores de ritmo para decisões táticas durante o dia  

            > Para incluir/alterar acessos, edite o arquivo `data/usuarios.csv`
            > com as colunas `usuario`, `senha`, `nome` (e opcionalmente `perfil`).
            """
        )

    st.markdown(
        "<p style='text-align:center; color:#888; margin-top:40px;'>"
        "Feito por: <b>Planejamento e Dados – E-commerce FSJ</b>"
        "</p>",
        unsafe_allow_html=True,
    )

# estado de autenticação
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
        raise ValueError("Arquivo saida_resumo.csv está vazio.")
    row = df.iloc[0]
    row.index = [c.strip() for c in row.index]
    return row

@st.cache_data
def load_grid(path: str = "data/saida_grid.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    return df

resumo_row = load_resumo()
grid = load_grid()

# ======================================================
#      EXTRAIR MÉTRICAS DO RESUMO (COLUNAS JÁ CONHECIDAS)
# ======================================================

data_ref             = resumo_row["data_referencia"]
meta_dia             = float(resumo_row["meta_dia"])
venda_atual          = float(resumo_row["venda_atual_ate_slot"])
percent_hist         = float(resumo_row["percentual_dia_hist"])
projecao             = float(resumo_row["projecao_dia"])
gap                  = float(resumo_row["desvio_projecao"])
total_d1             = float(resumo_row["total_d1"])
meta_d1              = float(resumo_row["meta_d1"])
desvio_d1            = float(resumo_row["desvio_d1"])
total_d7             = float(resumo_row["total_d7"])
meta_d7              = float(resumo_row["meta_d7"])
desvio_d7            = float(resumo_row["desvio_d7"])
ritmo_vs_d1          = float(resumo_row["ritmo_vs_d1"])
ritmo_vs_d7          = float(resumo_row["ritmo_vs_d7"])
ritmo_vs_media       = float(resumo_row["ritmo_vs_media"])
exp_ritmo            = resumo_row["explicacao_ritmo"]
exp_d1               = resumo_row["explicacao_d1"]
exp_d7               = resumo_row["explicacao_d7"]

# ======================================================
#                    CABEÇALHO
# ======================================================

st.markdown(
    "<div class='logo-box'>"
    "<span class='big-title'>📈 FSJ Black Friday 2026 – Projeção de Vendas (Site + App)</span><br>"
    f"<span class='subtitle'>Usuário: {st.session_state.get('user_name', 'N/A')} • Data de referência: {data_ref}</span>"
    "</div>",
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

def kpi(title: str, value: str, color: str):
    st.markdown(
        f"""
        <div style="
            background:{CARD_BG};
            padding:18px;
            border-radius:14px;
            text-align:center;
            border:1px solid #333;
            box-shadow:0 0 12px rgba(0,0,0,0.7);">
            <div style="font-size:14px; color:#CCCCCC; margin-bottom:6px;">{title}</div>
            <div style="font-size:26px; font-weight:700; color:{color};">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ======================================================
#                     KPIs PRINCIPAIS
# ======================================================

st.markdown("### 🎯 Visão Geral do Dia")

c1, c2, c3, c4 = st.columns(4)
with c1:
    kpi("Meta do Dia", f"R$ {money_br(meta_dia, com_centavos=False)}", PRIMARY)
with c2:
    kpi("Venda Atual", f"R$ {money_br(venda_atual, com_centavos=False)}", PRIMARY)
with c3:
    cor_proj = PRIMARY if projecao >= meta_dia else DANGER
    kpi("Projeção de Fechamento", f"R$ {money_br(projecao, com_centavos=False)}", cor_proj)
with c4:
    cor_gap = PRIMARY if gap >= 0 else DANGER
    kpi("Gap Projetado vs Meta", f"R$ {money_br(gap, com_centavos=False)}", cor_gap)

c5, c6, c7, c8 = st.columns(4)
with c5:
    kpi("Total D-1 (dia inteiro)", f"R$ {money_br(total_d1, com_centavos=False)}", "#FFFFFF")
with c6:
    kpi("Desvio D-1 vs Meta", f"R$ {money_br(desvio_d1, com_centavos=False)}",
        PRIMARY if desvio_d1 >= 0 else DANGER)
with c7:
    kpi("Total D-7 (dia inteiro)", f"R$ {money_br(total_d7, com_centavos=False)}", "#FFFFFF")
with c8:
    kpi("Desvio D-7 vs Meta", f"R$ {money_br(desvio_d7, com_centavos=False)}",
        PRIMARY if desvio_d7 >= 0 else DANGER)

c9, c10, c11 = st.columns(3)
with c9:
    kpi("Ritmo vs D-1", f"{ritmo_vs_d1:,.2f}x",
        PRIMARY if ritmo_vs_d1 >= 1 else DANGER)
with c10:
    kpi("Ritmo vs D-7", f"{ritmo_vs_d7:,.2f}x",
        PRIMARY if ritmo_vs_d7 >= 1 else DANGER)
with c11:
    kpi("Dia já percorrido (curva hist.)", f"{percent_hist*100:,.1f}%", WARNING)

# ======================================================
#                  INSIGHTS EXECUTIVOS
# ======================================================

st.markdown("### 🧠 Insights Estratégicos")

st.info(
    f"""
- {exp_ritmo}  
- {exp_d1}  
- {exp_d7}  
- Ritmo atual vs D-1: **{ritmo_vs_d1:,.2f}x** • Ritmo atual vs D-7: **{ritmo_vs_d7:,.2f}x**  
- Se o ritmo atual se mantiver, o fechamento projetado é de **R$ {money_br(projecao, com_centavos=False)}**.
"""
)

# Caixa explicando a metodologia
with st.expander("📘 Como funciona a projeção?"):
    st.markdown(
        """
        **Metodologia do modelo de projeção FSJ Black Friday 2026**

        1. **Curva intradia histórica**  
           - Cada dia é dividido em slots de 15 minutos.  
           - Para cada slot, calculamos quanto ele representa do total do dia.  
           - A média desses percentuais gera a curva intradia histórica (*percentual_dia_hist / frac_hist*).

        2. **Ritmo atual**  
           - A venda acumulada até o último slot do dia é comparada com:  
             - o mesmo horário de **ontem (D-1)**  
             - o mesmo horário de **D-7**  
             - a curva média do mês.  
           - Isso gera indicadores de ritmo (ex.: 1,20x o ritmo de D-1).

        3. **Projeção de fechamento**  
           - Se já percorremos, por exemplo, 30% da curva intradia histórica,  
             então a venda atual deveria representar ~30% do total esperado.  
           - Fórmula básica:  
             **projeção_dia ≈ venda_atual / percentual_dia_hist**

        4. **Desvios e metas**  
           - Gap projetado = projeção_dia – meta_dia.  
           - Também comparamos o fechamento real de D-1 e D-7 contra suas metas.  

        Essa abordagem permite enxergar não só o quanto já vendemos,
        mas principalmente **a força do dia** e a **tendência de fechamento**
        em tempo quase real.
        """
    )

# ======================================================
#                  CURVAS E HISTÓRICO DDT
# ======================================================

st.markdown("### 📊 Curva Intradia – DDT por Slot (15 em 15 minutos)")

if "SLOT" in grid.columns:
    grid = grid.sort_values("SLOT").set_index("SLOT")

col_curva1, col_curva2 = st.columns(2)

with col_curva1:
    st.markdown("#### 💵 Venda por Slot (Hoje x D-1 x D-7 x Média Mês)")
    cols_valor = [c for c in ["valor_hoje", "valor_d1", "valor_d7", "valor_media_mes"] if c in grid.columns]
    if cols_valor:
        st.line_chart(grid[cols_valor])
    else:
        st.warning("Colunas de valor por slot não encontradas em saida_grid.csv.")

with col_curva2:
    st.markdown("#### 📈 Curva Acumulada (Hoje x D-1 x D-7 x Média Mês)")
    cols_acum = [c for c in ["acum_hoje", "acum_d1", "acum_d7", "acum_media_mes"] if c in grid.columns]
    if cols_acum:
        st.line_chart(grid[cols_acum])
    else:
        st.warning("Colunas acumuladas não encontradas em saida_grid.csv.")

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
