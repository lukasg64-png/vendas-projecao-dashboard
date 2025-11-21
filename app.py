import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# ======================================================
#                 CONFIGURAÇÃO BÁSICA
# ======================================================
st.set_page_config(
    page_title="FSJ Black Friday 2026 – Projeção de Vendas",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Paleta
PRIMARY = "#00C853"   # verde
DANGER  = "#FF1744"   # vermelho
WARNING = "#FFC400"   # amarelo
CARD_BG = "#111111"

# CSS geral (card, header, fonte, etc.)
st.markdown(
    f"""
    <style>
    body {{
        background-color: #000000;
        color: #FFFFFF;
        font-family: "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}

    .main .block-container {{
        padding-top: 0.8rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }}

    .fsj-header {{
        background: linear-gradient(90deg, #00C853 0%, #004D40 100%);
        padding: 0.7rem 1.2rem;
        border-radius: 0.8rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: #FFFFFF;
        margin-bottom: 1rem;
    }}

    .fsj-header-title {{
        font-size: 1.3rem;
        font-weight: 700;
    }}

    .fsj-header-sub {{
        font-size: 0.82rem;
        opacity: 0.9;
    }}

    .fsj-badge {{
        background-color: rgba(0,0,0,0.2);
        padding: 0.25rem 0.7rem;
        border-radius: 999px;
        font-size: 0.78rem;
        white-space: nowrap;
    }}

    .kpi-card {{
        background-color: {CARD_BG};
        border-radius: 0.8rem;
        padding: 0.9rem 1rem;
        border: 1px solid #222;
        height: 100%;
    }}

    .kpi-title {{
        font-size: 0.8rem;
        color: #CCCCCC;
        margin-bottom: 0.25rem;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }}

    .kpi-value {{
        font-size: 1.6rem;
        font-weight: 700;
        margin-bottom: 0.15rem;
    }}

    .kpi-sub {{
        font-size: 0.75rem;
        color: #999999;
    }}

    .kpi-tooltip {{
        font-size: 0.72rem;
        color: #AAAAAA;
        margin-top: 0.2rem;
    }}

    .insights-box {{
        background-color: #051018;
        border-radius: 0.8rem;
        padding: 0.9rem 1rem;
        border: 1px solid #102533;
        font-size: 0.9rem;
        line-height: 1.55;
    }}

    .section-title {{
        font-size: 1.05rem;
        font-weight: 700;
        margin-top: 0.8rem;
        margin-bottom: 0.4rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ======================================================
#                 FORMATADORES
# ======================================================
def fmt_num_br(valor: float, casas: int = 0) -> str:
    if pd.isna(valor):
        return "-"
    fmt = f"{valor:,.{casas}f}"
    # 1,234,567.89  ->  1.234.567,89
    fmt = fmt.replace(",", "X").replace(".", ",").replace("X", ".")
    return fmt

def fmt_moeda(valor: float, casas: int = 0) -> str:
    if pd.isna(valor):
        return "-"
    return f"R$ {fmt_num_br(valor, casas)}"

def fmt_percent(frac: float, casas: int = 1) -> str:
    if pd.isna(frac):
        return "-"
    return f"{fmt_num_br(frac * 100, casas)}%"

# ======================================================
#                 LOGIN (usuarios.csv)
# ======================================================
def autenticar_usuario(usuario: str, senha: str):
    try:
        df_users = pd.read_csv("data/usuarios.csv")
    except Exception:
        return None

    # esperados: usuario, senha, nome
    df_users.columns = [c.strip().lower() for c in df_users.columns]
    for col in ["usuario", "senha"]:
        if col not in df_users.columns:
            return None

    linha = df_users[
        (df_users["usuario"].astype(str) == str(usuario)) &
        (df_users["senha"].astype(str) == str(senha))
    ]

    if linha.empty:
        return None

    nome = linha.iloc[0]["nome"] if "nome" in df_users.columns else usuario
    return str(nome)

if "auth" not in st.session_state:
    st.session_state["auth"] = False
if "nome_usuario" not in st.session_state:
    st.session_state["nome_usuario"] = None

if not st.session_state["auth"]:
    st.markdown(
        """
        <div class="fsj-header">
            <div>
                <div class="fsj-header-title">📈 FSJ Black Friday 2026 – Projeção de Vendas (Site + App)</div>
                <div class="fsj-header-sub">Acesso restrito • Faça login para visualizar o painel executivo.</div>
            </div>
            <div class="fsj-badge">Feito por: Planejamento e Dados E-Commerce</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 🔐 Login")
    with st.form("login_form"):
        col_l, col_r = st.columns([1, 1])
        with col_l:
            user = st.text_input("Usuário")
        with col_r:
            pwd = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar")

        if entrar:
            nome = autenticar_usuario(user, pwd)
            if nome is None:
                st.error("Usuário ou senha inválidos. Verifique o arquivo `data/usuarios.csv`.")
            else:
                st.session_state["auth"] = True
                st.session_state["nome_usuario"] = nome

    if not st.session_state["auth"]:
        st.stop()

# ======================================================
#                 CARREGAR BASES (grid + resumo)
# ======================================================
try:
    grid = pd.read_csv("data/saida_grid.csv")
    resumo_df = pd.read_csv("data/saida_resumo.csv")
except Exception as e:
    st.error(f"Erro ao carregar arquivos `saida_grid.csv` ou `saida_resumo.csv`: {e}")
    st.stop()

if resumo_df.empty:
    st.error("Arquivo `saida_resumo.csv` está vazio.")
    st.stop()

r = resumo_df.iloc[0]

data_ref_str = str(r.get("data_referencia", ""))
try:
    data_ref = pd.to_datetime(data_ref_str).date()
except Exception:
    data_ref = data_ref_str

meta_dia     = float(r.get("meta_dia", np.nan))
venda_atual  = float(r.get("venda_atual_ate_slot", np.nan))
frac_hist    = float(r.get("percentual_dia_hist", np.nan))
projecao     = float(r.get("projecao_dia", np.nan))
gap_proj     = float(r.get("desvio_projecao", np.nan))
total_d1     = float(r.get("total_d1", np.nan))
total_d7     = float(r.get("total_d7", np.nan))
ritmo_d1     = float(r.get("ritmo_vs_d1", np.nan))
ritmo_d7     = float(r.get("ritmo_vs_d7", np.nan))
ritmo_media  = float(r.get("ritmo_vs_media", np.nan))

exp_ritmo = r.get("explicacao_ritmo", "")
exp_d1    = r.get("explicacao_d1", "")
exp_d7    = r.get("explicacao_d7", "")

# ======================================================
#                 HEADER DO PAINEL (já logado)
# ======================================================
st.markdown(
    f"""
    <div class="fsj-header">
        <div>
            <div class="fsj-header-title">📈 FSJ Black Friday 2026 – Projeção de Vendas (Site + App)</div>
            <div class="fsj-header-sub">
                Usuário: <b>{st.session_state['nome_usuario']}</b> • 
                Data de referência: <b>{data_ref}</b>
            </div>
        </div>
        <div class="fsj-badge">Feito por: Planejamento e Dados E-Commerce</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ======================================================
#                 FUNÇÃO PARA DESENHAR KPI
# ======================================================
def kpi_card(title: str, value_html: str, sub: str = "", tooltip: str = "", color_border: str = "#222222"):
    extra = f"border-color:{color_border};" if color_border else ""
    html = f"""
    <div class="kpi-card" style="{extra}">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value_html}</div>
        <div class="kpi-sub">{sub}</div>
        {f'<div class="kpi-tooltip">ℹ️ {tooltip}</div>' if tooltip else ''}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# ======================================================
#                 KPIs – VISÃO GERAL DO DIA
# ======================================================
st.markdown('<div class="section-title">🎯 Visão Geral do Dia</div>', unsafe_allow_html=True)

row1 = st.columns(4)
with row1[0]:
    kpi_card(
        "Meta do dia",
        f"<span style='color:{PRIMARY};'>{fmt_moeda(meta_dia)}</span>",
        sub="Meta consolidada Site + App",
        tooltip="Meta total do dia para os canais digitais."
    )
with row1[1]:
    kpi_card(
        "Venda atual",
        f"<span style='color:{PRIMARY if venda_atual >= 0 else DANGER};'>{fmt_moeda(venda_atual)}</span>",
        sub="Até o último slot processado.",
        tooltip="Venda acumulada até o horário mais recente da base."
    )
with row1[2]:
    kpi_card(
        "Projeção de fechamento",
        f"<span style='color:{PRIMARY if projecao >= meta_dia else DANGER};'>{fmt_moeda(projecao)}</span>",
        sub="Modelo intradia + consistência de ritmo.",
        tooltip="Estimativa de fechamento para o dia com base na curva histórica e venda atual."
    )
with row1[3]:
    kpi_card(
        "Gap projetado vs meta",
        f"<span style='color:{PRIMARY if gap_proj >= 0 else DANGER};'>{fmt_moeda(gap_proj)}</span>",
        sub="Posição relativa se mantivermos o ritmo atual.",
        tooltip="Diferença entre a projeção de fechamento e a meta do dia."
    )

row2 = st.columns(4)
with row2[0]:
    kpi_card(
        "Total D-1 (dia inteiro)",
        f"<span>{fmt_moeda(total_d1)}</span>",
        sub="Ontem (D-1).",
        tooltip=exp_d1 if isinstance(exp_d1, str) else ""
    )
with row2[1]:
    kpi_card(
        "Total D-7 (dia inteiro)",
        f"<span>{fmt_moeda(total_d7)}</span>",
        sub="Mesmo dia da semana passada (D-7).",
        tooltip=exp_d7 if isinstance(exp_d7, str) else ""
    )
with row2[2]:
    cor_ritmo_d1 = PRIMARY if ritmo_d1 >= 1 else DANGER
    kpi_card(
        "Ritmo vs D-1",
        f"<span style='color:{cor_ritmo_d1};'>{fmt_num_br(ritmo_d1, 2)}x</span>",
        sub="> 1,00x = acima de ontem.",
        tooltip="Compara a venda acumulada de hoje com a de ontem no mesmo horário."
    )
with row2[3]:
    cor_ritmo_d7 = PRIMARY if ritmo_d7 >= 1 else DANGER
    kpi_card(
        "Ritmo vs D-7",
        f"<span style='color:{cor_ritmo_d7};'>{fmt_num_br(ritmo_d7, 2)}x</span>",
        sub="> 1,00x = acima da semana passada.",
        tooltip="Compara a venda acumulada de hoje com a do mesmo dia da semana passada."
    )

row3 = st.columns(2)
with row3[0]:
    cor_ritmo_med = PRIMARY if ritmo_media >= 1 else DANGER
    kpi_card(
        "Ritmo vs média do mês",
        f"<span style='color:{cor_ritmo_med};'>{fmt_num_br(ritmo_media, 2)}x</span>",
        sub="> 1,00x = acima da média intradia.",
        tooltip="Indica se o dia está acima ou abaixo do comportamento médio do mês."
    )
with row3[1]:
    kpi_card(
        "Dia já percorrido (curva hist.)",
        f"<span style='color:{WARNING};'>{fmt_percent(frac_hist, 2)}</span>",
        sub="Fatia média do dia já realizada nesse horário.",
        tooltip="Mostra em que percentual do dia, em média, o canal costuma estar nesse slot."
    )

# ======================================================
#                 INSIGHTS E EXPLICAÇÕES
# ======================================================
st.markdown('<div class="section-title">🧠 Insights Estratégicos</div>', unsafe_allow_html=True)

insights_html = f"""
<div class="insights-box">
<ul>
    <li>{exp_ritmo}</li>
    <li>{exp_d1}</li>
    <li>{exp_d7}</li>
    <li>Ritmo &gt; <b>1,00x</b> indica dia mais forte que o comparativo; ritmo &lt; <b>1,00x</b> aponta atenção e necessidade de ação comercial.</li>
</ul>
</div>
"""
st.markdown(insights_html, unsafe_allow_html=True)

# ======================================================
#       COMO A PROJEÇÃO É CALCULADA (EXPLICADO)
# ======================================================
st.markdown('<div class="section-title">⚙️ Como a projeção é calculada?</div>', unsafe_allow_html=True)

explicacao_modelo_html = f"""
<div class="insights-box" style="background-color:#050b12;border-color:#1a2a3a;">
A projeção utiliza um modelo em três camadas para dar robustez ao número apresentado em <b>“Projeção de fechamento”</b>:

<br><br>

<b>1. Curva intradia histórica</b><br>
• Para cada slot de 15 minutos, medimos qual fração do faturamento diário costuma estar realizada ao longo do mês.<br>
• No horário atual, o padrão histórico indica que cerca de <b>{fmt_percent(frac_hist, 2)}</b> do dia já deveria estar vendido.

<br><br>

<b>2. Base matemática de projeção</b><br>
• Consideramos a venda acumulada de hoje até o último slot: <b>{fmt_moeda(venda_atual)}</b>.<br>
• Dividimos esse valor pela fração histórica do horário, obtendo uma projeção-base de fechamento.<br>
• Essa base resulta em aproximadamente <b>{fmt_moeda(projecao)}</b> para o dia.

<br><br>

<b>3. Camada de consistência por ritmo</b><br>
• Em paralelo, monitoramos os ritmos:<br>
&nbsp;&nbsp;• vs D-1: <b>{fmt_num_br(ritmo_d1,2)}x</b> &nbsp;&nbsp;• vs D-7: <b>{fmt_num_br(ritmo_d7,2)}x</b> &nbsp;&nbsp;• vs média do mês: <b>{fmt_num_br(ritmo_media,2)}x</b><br>
• Ritmos acima de <b>1,00x</b> sugerem aceleração; abaixo de <b>1,00x</b> indicam perda de tração.<br>
• Esses indicadores funcionam como “checagem de consistência” da projeção: se o dia foge muito do padrão, isso aparece imediatamente nos ritmos.

<br><br>

<b>Conclusão executiva</b><br>
Com esse conjunto de sinais, projetamos o fechamento em <b>{fmt_moeda(projecao)}</b>,<br>
o que representa um gap de <b style="color:{PRIMARY if gap_proj >= 0 else DANGER};">{fmt_moeda(gap_proj)}</b> em relação à meta consolidada de <b>{fmt_moeda(meta_dia)}</b>.
</div>
"""
st.markdown(explicacao_modelo_html, unsafe_allow_html=True)

# ======================================================
#                 PREPARAÇÃO DOS DADOS P/ GRÁFICOS
# ======================================================
# 1) Curvas de valor por slot
grid_curvas = grid.copy()
rename_map = {
    "valor_hoje": "Hoje",
    "valor_d1": "D-1",
    "valor_d7": "D-7",
    "valor_media_mes": "Média do mês"
}
grid_curvas = grid_curvas.rename(columns=rename_map)

curvas_long = grid_curvas.melt(
    id_vars="SLOT",
    value_vars=list(rename_map.values()),
    var_name="Série",
    value_name="Valor"
)

# 2) Acumulado vs histórico
acum_cols = {
    "acum_hoje": "Hoje acumulado",
    "acum_d1": "D-1 acumulado",
    "acum_d7": "D-7 acumulado",
    "acum_media_mes": "Média acumulada"
}
grid_acum = grid.rename(columns=acum_cols)

acum_long = grid_acum.melt(
    id_vars="SLOT",
    value_vars=list(acum_cols.values()),
    var_name="Série",
    value_name="Valor acumulado"
)

# 3) Ritmos por slot
ritmo_cols = {
    "ritmo_vs_d1": "Ritmo vs D-1",
    "ritmo_vs_d7": "Ritmo vs D-7",
    "ritmo_vs_media": "Ritmo vs média"
}
grid_ritmo = grid.rename(columns=ritmo_cols)

ritmo_long = grid_ritmo.melt(
    id_vars="SLOT",
    value_vars=list(ritmo_cols.values()),
    var_name="Série",
    value_name="Ritmo"
)

# ======================================================
#                 GRÁFICOS
# ======================================================
st.markdown('<div class="section-title">📊 Curvas de venda por slot</div>', unsafe_allow_html=True)

fig1 = px.line(
    curvas_long,
    x="SLOT",
    y="Valor",
    color="Série",
    markers=False,
)
fig1.update_layout(
    height=350,
    template="plotly_dark",
    margin=dict(l=10, r=10, t=30, b=10),
    legend_title_text="",
)
st.plotly_chart(fig1, use_container_width=True)

st.markdown('<div class="section-title">📈 Acumulado vs histórico</div>', unsafe_allow_html=True)

fig2 = px.line(
    acum_long,
    x="SLOT",
    y="Valor acumulado",
    color="Série",
)
fig2.add_hline(
    y=meta_dia,
    line_dash="dash",
    line_color=WARNING,
    annotation_text="Meta do dia",
    annotation_position="top left"
)
fig2.update_layout(
    height=350,
    template="plotly_dark",
    margin=dict(l=10, r=10, t=30, b=10),
    legend_title_text="",
)
st.plotly_chart(fig2, use_container_width=True)

st.markdown('<div class="section-title">📉 Ritmos por horário</div>', unsafe_allow_html=True)

fig3 = px.line(
    ritmo_long,
    x="SLOT",
    y="Ritmo",
    color="Série",
)
fig3.add_hline(y=1.0, line_dash="dash", line_color="#888888", annotation_text="1,00x (linha de equilíbrio)")
fig3.update_layout(
    height=320,
    template="plotly_dark",
    margin=dict(l=10, r=10, t=30, b=10),
    legend_title_text="",
)
st.plotly_chart(fig3, use_container_width=True)

# ======================================================
#                 TABELA DETALHADA
# ======================================================
st.markdown('<div class="section-title">🧮 Tabela detalhada – DDT slot a slot</div>', unsafe_allow_html=True)
st.dataframe(grid, use_container_width=True)
