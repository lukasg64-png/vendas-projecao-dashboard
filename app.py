import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ============================================================
# CONFIG GERAL DO APP
# ============================================================

st.set_page_config(
    page_title="FSJ Black Friday 2026 – Projeção de Vendas",
    layout="wide",
    initial_sidebar_state="collapsed"
)

PRIMARY = "#00E676"   # verde neon
DANGER  = "#FF1744"   # vermelho
WARNING = "#FFD600"   # amarelo
CARD_BG = "#111111"
BG_GRAD = "linear-gradient(90deg, #00E676 0%, #00BFA5 40%, #000000 100%)"

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def format_brl(x):
    """Formata número como moeda brasileira: 1.550.000"""
    try:
        x = float(x)
    except (TypeError, ValueError):
        return "-"
    return ("R$ " + f"{x:,.0f}").replace(",", "X").replace(".", ",").replace("X", ".")


def format_pct(x, decimals=1):
    """Formata percentual com vírgula."""
    try:
        x = float(x) * 100
    except (TypeError, ValueError):
        return "-"
    return f"{x:,.{decimals}f}%".replace(",", "X").replace(".", ",").replace("X", ".")


def kpi_card(title, value, subtitle=None, color=PRIMARY):
    """Desenha um card de KPI bonitão."""
    subtitle_html = f"<div style='font-size:13px; color:#AAAAAA; margin-top:4px;'>{subtitle}</div>" if subtitle else ""
    st.markdown(
        f"""
        <div style="
            background:{CARD_BG};
            padding:18px 20px;
            border-radius:16px;
            border:1px solid #222;
            box-shadow:0 10px 30px rgba(0,0,0,0.5);
            text-align:left;
        ">
            <div style="font-size:13px; color:#BBBBBB; text-transform:uppercase; letter-spacing:1px;">
                {title}
            </div>
            <div style="font-size:28px; font-weight:700; color:{color}; margin-top:6px;">
                {value}
            </div>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True
    )


def load_usuarios(path="data/usuarios.csv"):
    df = pd.read_csv(path)
    cols = {c.lower(): c for c in df.columns}

    col_user = cols.get("usuario") or list(df.columns)[0]
    col_pass = cols.get("senha")   or list(df.columns)[1]
    col_name = cols.get("nome")

    return df, col_user, col_pass, col_name


def autenticar(usuario, senha, df_users, col_user, col_pass):
    match = df_users[
        (df_users[col_user].astype(str) == str(usuario)) &
        (df_users[col_pass].astype(str) == str(senha))
    ]
    return match.iloc[0] if not match.empty else None


# ============================================================
# CSS GLOBAL
# ============================================================

st.markdown(
    f"""
    <style>
        .stApp {{
            background: radial-gradient(circle at top left, #1B1B1B 0, #000000 60%);
            color: #FFFFFF;
            font-family: "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }}
        .block-container {{
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }}
        .css-18e3th9, .css-1d391kg {{
            padding-top: 0;
        }}
        /* Esconde footer padrão do Streamlit */
        footer {{visibility: hidden;}}
    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# LOGIN
# ============================================================

if "auth" not in st.session_state:
    st.session_state["auth"] = False
    st.session_state["user_name"] = None

df_users, COL_USER, COL_PASS, COL_NAME = load_usuarios()

def login_screen():
    st.markdown(
        f"""
        <div style="
            height:100vh;
            display:flex;
            align-items:center;
            justify-content:center;
            flex-direction:column;
            background:{BG_GRAD};
        ">
            <div style="
                background:rgba(0,0,0,0.75);
                padding:32px 40px;
                border-radius:18px;
                box-shadow:0 20px 40px rgba(0,0,0,0.7);
                max-width:420px;
                width:100%;
                text-align:center;
            ">
                <div style="font-size:38px; margin-bottom:10px;">📊 FSJ Black Friday 2026</div>
                <div style="font-size:16px; color:#BBBBBB; margin-bottom:18px;">
                    Projeção de Vendas – Site + App
                </div>
                <div style="font-size:12px; color:#888888; margin-bottom:20px;">
                    Feito por: <b>Planejamento e Dados E-Commerce</b>
                </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form", clear_on_submit=False):
        user = st.text_input("Usuário")
        pwd  = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar")

    if entrar:
        row = autenticar(user, pwd, df_users, COL_USER, COL_PASS)
        if row is not None:
            st.session_state["auth"] = True
            st.session_state["user_name"] = (
                str(row[COL_NAME]) if COL_NAME and pd.notna(row[COL_NAME]) else str(row[COL_USER])
            )
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha inválidos.")

    st.markdown("</div></div>", unsafe_allow_html=True)


if not st.session_state["auth"]:
    login_screen()
    st.stop()

# ============================================================
# CARREGAR BASES (saídas do Colab)
# ============================================================

@st.cache_data
def load_dados():
    df_resumo = pd.read_csv("data/saida_resumo.csv")
    df_grid   = pd.read_csv("data/saida_grid.csv")

    # Garante colunas esperadas no resumo (assumimos 1 linha só)
    resumo_row = df_resumo.iloc[0].to_dict()

    # Converte datas se existir
    if "data" in resumo_row:
        try:
            resumo_row["data"] = pd.to_datetime(resumo_row["data"]).date()
        except Exception:
            pass

    # Força float nas métricas numéricas
    for col in [
        "meta_dia", "venda_atual", "projecao", "gap",
        "ritmo_d1", "ritmo_d7", "ritmo_media",
        "total_d1", "total_d7", "frac_hist"
    ]:
        if col in resumo_row:
            try:
                resumo_row[col] = float(resumo_row[col])
            except Exception:
                resumo_row[col] = None

    # Garante que SLOT é string
    if "SLOT" in df_grid.columns:
        df_grid["SLOT"] = df_grid["SLOT"].astype(str)

    return resumo_row, df_grid

resumo, df_grid = load_dados()

data_ref = resumo.get("data", None)
data_ref_str = (
    data_ref.strftime("%d/%m/%Y")
    if isinstance(data_ref, datetime) or hasattr(data_ref, "strftime")
    else str(data_ref)
)

# ============================================================
# HEADER EXECUTIVO
# ============================================================

st.markdown(
    f"""
    <div style="
        background:{BG_GRAD};
        border-radius:18px;
        padding:20px 26px;
        margin-bottom:22px;
        box-shadow:0 18px 40px rgba(0,0,0,0.7);
        position:relative;
    ">
        <div style="font-size:30px; font-weight:700;">
            📈 FSJ Black Friday 2026 – Projeção de Vendas (Site + App)
        </div>
        <div style="margin-top:6px; font-size:13px; color:#E0FFE9;">
            Usuário: <b>{st.session_state["user_name"]}</b>
            • Data de referência: <b>{data_ref_str}</b>
        </div>
        <div style="position:absolute; right:24px; top:22px; font-size:11px; color:#111; 
                    background:rgba(255,255,255,0.85); padding:4px 10px; border-radius:999px;">
            Feito por: Planejamento e Dados E-Commerce
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <h3 style="margin-top:0; margin-bottom:12px;">🎯 Visão Geral do Dia</h3>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# KPIs PRINCIPAIS
# ============================================================

meta_dia     = resumo.get("meta_dia")
venda_atual  = resumo.get("venda_atual")
projecao     = resumo.get("projecao")
gap          = resumo.get("gap")
total_d1     = resumo.get("total_d1")
total_d7     = resumo.get("total_d7")
frac_hist    = resumo.get("frac_hist")
ritmo_d1     = resumo.get("ritmo_d1")
ritmo_d7     = resumo.get("ritmo_d7")
ritmo_media  = resumo.get("ritmo_media")

# Primeira linha de KPIs
c1, c2, c3, c4 = st.columns(4)
with c1:
    kpi_card("Meta do Dia", format_brl(meta_dia), color=PRIMARY)
with c2:
    kpi_card("Venda Atual", format_brl(venda_atual), color=PRIMARY)
with c3:
    cor_proj = PRIMARY if (projecao or 0) >= (meta_dia or 0) else WARNING
    kpi_card("Projeção de Fechamento", format_brl(projecao), color=cor_proj)
with c4:
    cor_gap = PRIMARY if (gap or 0) >= 0 else DANGER
    kpi_card("Gap Projetado vs Meta", format_brl(gap), color=cor_gap)

# Segunda linha: D-1 / D-7 / dia percorrido
c5, c6, c7, c8 = st.columns(4)
with c5:
    kpi_card("Total D-1 (dia inteiro)", format_brl(total_d1), subtitle="Ontem", color="#FFFFFF")
with c6:
    kpi_card("Total D-7 (dia inteiro)", format_brl(total_d7), subtitle="Semana passada", color="#FFFFFF")
with c7:
    kpi_card("Ritmo vs D-1", f"{ritmo_d1:.2f}x" if ritmo_d1 is not None else "-", color=PRIMARY if (ritmo_d1 or 0) >= 1 else DANGER)
with c8:
    kpi_card("Dia já percorrido (curva hist.)",
             format_pct(frac_hist or 0, decimals=1),
             color=WARNING)

# ============================================================
# INSIGHTS EXECUTIVOS
# ============================================================

st.markdown("### 🧠 Insights Estratégicos")

texto_insights = f"""
- Até agora vendemos **{format_brl(venda_atual)}**, o que representa **{format_pct(frac_hist or 0)}** da curva intradia histórica para este dia.  
- A projeção de fechamento é **{format_brl(projecao)}**, contra uma meta de **{format_brl(meta_dia)}**, indicando um **gap de {format_brl(gap)}**.  
- Ontem (D-1) fechamos em **{format_brl(total_d1)}** e há 7 dias (D-7) em **{format_brl(total_d7)}**.  
- O ritmo atual está em **{f"{ritmo_d1:.2f}x" if ritmo_d1 is not None else "-"}** de D-1 e **{f"{ritmo_d7:.2f}x" if ritmo_d7 is not None else "-"}** de D-7, com relação à média do mês em **{f"{ritmo_media:.2f}x" if ritmo_media is not None else "-"}**.  
"""

st.info(texto_insights)

# ============================================================
# GRÁFICOS – CURVAS E ANÁLISES
# ============================================================

st.markdown("### 📊 Curvas Intradia – Hoje vs D-1 vs D-7 vs Média")

if {"SLOT", "valor_hoje"}.issubset(df_grid.columns):
    plot_df = df_grid.copy()

    # Tabelar long para plotly
    cols_curvas = []
    for col, label in [
        ("valor_hoje", "Hoje"),
        ("valor_d1", "D-1"),
        ("valor_d7", "D-7"),
        ("valor_media_mes", "Média mês"),
    ]:
        if col in plot_df.columns:
            tmp = plot_df[["SLOT", col]].rename(columns={col: "valor"})
            tmp["Série"] = label
            cols_curvas.append(tmp)

    if cols_curvas:
        long_df = pd.concat(cols_curvas, ignore_index=True)
        fig = px.line(
            long_df,
            x="SLOT",
            y="valor",
            color="Série",
            markers=True,
            template="plotly_dark",
        )
        fig.update_layout(
            height=380,
            xaxis_title="Horário (SLOT)",
            yaxis_title="Valor em 15 min",
            margin=dict(l=10, r=10, t=40, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Não encontrei as colunas necessárias em `saida_grid.csv` para montar as curvas.")

# ============================================================
# ANÁLISE POR HORA (AGREGAÇÃO)
# ============================================================

st.markdown("### ⏱️ Vendas por Hora – Hoje vs D-1 vs D-7")

if "SLOT" in df_grid.columns and "valor_hoje" in df_grid.columns:
    df_hora = df_grid.copy()
    df_hora["HORA"] = df_hora["SLOT"].str.slice(0, 2)

    agg_cols = []
    for col, label in [
        ("valor_hoje", "Hoje"),
        ("valor_d1", "D-1"),
        ("valor_d7", "D-7"),
    ]:
        if col in df_hora.columns:
            tmp = df_hora.groupby("HORA")[col].sum().reset_index()
            tmp["Série"] = label
            tmp = tmp.rename(columns={col: "valor"})
            agg_cols.append(tmp)

    if agg_cols:
        long_h = pd.concat(agg_cols, ignore_index=True)
        fig_bar = px.bar(
            long_h,
            x="HORA",
            y="valor",
            color="Série",
            barmode="group",
            template="plotly_dark",
        )
        fig_bar.update_layout(
            height=360,
            xaxis_title="Hora",
            yaxis_title="Total por hora",
            margin=dict(l=10, r=10, t=40, b=10),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

# ============================================================
# TABELA DETALHADA COM “CALOR”
# ============================================================

st.markdown("### 🧮 Tabela Slot a Slot (Detalhe Operacional)")

if not df_grid.empty:
    df_show = df_grid.copy()

    # Formata algumas colunas numéricas principais
    for col in ["valor_hoje", "valor_d1", "valor_d7", "valor_media_mes",
                "acum_hoje", "acum_d1", "acum_d7", "acum_media_mes"]:
        if col in df_show.columns:
            df_show[col] = df_show[col].apply(lambda x: format_brl(x)[3:] if pd.notna(x) else "-")

    if "frac_hist" in df_show.columns:
        df_show["frac_hist"] = df_grid["frac_hist"].apply(lambda x: format_pct(x, 1))

    st.dataframe(df_show, use_container_width=True, height=420)
else:
    st.warning("Tabela de slots vazia.")

# ============================================================
# METODOLOGIA
# ============================================================

with st.expander("📐 Entenda a Metodologia de Projeção", expanded=False):
    st.markdown(
        """
        **Como este painel projeta o fechamento do dia?**

        1. A base intradia foi agregada em janelas de **15 minutos (SLOT)** para o Site + App.  
        2. Para cada dia histórico do mês, calcula-se a curva acumulada de vendas ao longo do dia.  
        3. A partir dessas curvas, obtemos a **curva intradia média**, que indica qual fração do dia
           já costuma ter sido vendida em cada horário.  
        4. No dia atual, olhamos o **acumulado de vendas até o último SLOT disponível** e dividimos
           pela fração histórica correspondente a esse mesmo horário.  
        5. Esse cálculo gera a **projeção de fechamento**, que é comparada com a **meta do dia**,
           com o **resultado de ontem (D-1)** e com o **resultado da semana anterior (D-7)**.  
        6. Os indicadores de **ritmo (x vezes D-1, D-7, média do mês)** ajudam a entender se o dia está
           acelerando ou desacelerando em relação aos padrões recentes.

        Essa abordagem combina visão executiva com leitura estatística da curva intradia,
        permitindo decisões rápidas durante a operação da **Black Friday FSJ 2026**.
        """
    )

# ============================================================
# RODAPÉ
# ============================================================

st.markdown(
    """
    <div style="text-align:right; font-size:11px; color:#777; margin-top:30px;">
        FSJ Black Friday 2026 • Painel de Projeção • Planejamento e Dados E-Commerce
    </div>
    """,
    unsafe_allow_html=True,
)
