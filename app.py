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

# CSS geral
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
        font-size: 1.5rem;
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
#                 LOGIN (data/logins.csv)
# ======================================================
def autenticar_usuario(usuario: str, senha: str):
    try:
        df_users = pd.read_csv("data/logins.csv")
    except Exception:
        return None

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
                st.error("Usuário ou senha inválidos. Verifique o arquivo `data/logins.csv`.")
            else:
                st.session_state["auth"] = True
                st.session_state["nome_usuario"] = nome
                st.rerun()

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

# meta-alvo intradia pra "estar em dia" com a meta
venda_esperada_horario = meta_dia * frac_hist if not pd.isna(meta_dia) and not pd.isna(frac_hist) else np.nan
indice_adherencia_meta = venda_atual / venda_esperada_horario if venda_esperada_horario and venda_esperada_horario != 0 else np.nan

# ======================================================
#                 HEADER DO PAINEL (logado)
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
#                 FUNÇÕES DE UI
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
#     PREPARO DE DADOS PARA GRÁFICOS E FAIXAS HORÁRIAS
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

# 4) Faixas horárias (0–6, 6–12, 12–20, 20–24)
grid_faixas = grid.copy()
grid_faixas["HORA"] = grid_faixas["SLOT"].str.slice(0, 2).astype(int)

def rotulo_faixa(hora: int) -> str:
    if 0 <= hora < 6:
        return "Madrugada (00h–06h)"
    elif 6 <= hora < 12:
        return "Manhã (06h–12h)"
    elif 12 <= hora < 20:
        return "Prime Time (12h–20h)"
    else:
        return "Late Night (20h–24h)"

grid_faixas["FAIXA"] = grid_faixas["HORA"].apply(rotulo_faixa)

# sumarizar por faixa
faixas_resumo = (
    grid_faixas
    .groupby("FAIXA")
    .agg({
        "valor_hoje": "sum",
        "valor_d1": "sum",
        "valor_d7": "sum",
        "valor_media_mes": "sum"
    })
    .reset_index()
)

# ======================================================
#                 ABAS PRINCIPAIS
# ======================================================
tab_dash, tab_sim, tab_faixas, tab_sobre = st.tabs(
    ["📊 Dashboard Executivo", "🎯 Simulações de Meta", "⏱️ Análise por Faixa Horária", "ℹ️ Sobre o Modelo"]
)

# ======================================================
#                 ABA 1 – DASHBOARD EXECUTIVO
# ======================================================
with tab_dash:
    st.markdown('<div class="section-title">🎯 Visão Geral do Dia</div>', unsafe_allow_html=True)

    # Linha 1 – visão macro
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
            sub="Projeção - meta do dia.",
            tooltip="Se positivo, tendência de superar a meta; se negativo, tendência de fechar abaixo."
        )

    # Linha 2 – comparativos
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
        seta_d1 = "🔺" if ritmo_d1 >= 1.05 else ("🔻" if ritmo_d1 <= 0.95 else "➖")
        kpi_card(
            "Ritmo vs D-1",
            f"<span style='color:{cor_ritmo_d1};'>{fmt_num_br(ritmo_d1, 2)}x {seta_d1}</span>",
            sub="> 1,00x = acima de ontem.",
            tooltip="Compara a venda acumulada de hoje com a de ontem no mesmo horário."
        )
    with row2[3]:
        cor_ritmo_d7 = PRIMARY if ritmo_d7 >= 1 else DANGER
        seta_d7 = "🔺" if ritmo_d7 >= 1.05 else ("🔻" if ritmo_d7 <= 0.95 else "➖")
        kpi_card(
            "Ritmo vs D-7",
            f"<span style='color:{cor_ritmo_d7};'>{fmt_num_br(ritmo_d7, 2)}x {seta_d7}</span>",
            sub="> 1,00x = acima da semana passada.",
            tooltip="Compara a venda de hoje com a do mesmo dia da semana anterior."
        )

    # Linha 3 – aderência de meta e ritmo médio
    row3 = st.columns(4)
    with row3[0]:
        cor_ritmo_med = PRIMARY if ritmo_media >= 1 else DANGER
        seta_med = "🔺" if ritmo_media >= 1.05 else ("🔻" if ritmo_media <= 0.95 else "➖")
        kpi_card(
            "Ritmo vs média do mês",
            f"<span style='color:{cor_ritmo_med};'>{fmt_num_br(ritmo_media, 2)}x {seta_med}</span>",
            sub="> 1,00x = acima da média intradia.",
            tooltip="Indica se o dia está acima ou abaixo do comportamento médio do mês."
        )
    with row3[1]:
        kpi_card(
            "Dia já percorrido (curva hist.)",
            f"<span style='color:{WARNING};'>{fmt_percent(frac_hist, 2)}</span>",
            sub="Fatia média do dia já realizada nesse horário.",
            tooltip="Percentual médio do faturamento diário que, historicamente, já aconteceu até este slot."
        )
    with row3[2]:
        kpi_card(
            "Venda esperada neste horário",
            f"<span>{fmt_moeda(venda_esperada_horario)}</span>",
            sub="Para estar em linha com a meta.",
            tooltip="Quanto deveríamos ter vendido até agora para estar 'on track' com a meta do dia."
        )
    with row3[3]:
        cor_idx = PRIMARY if indice_adherencia_meta >= 1 else DANGER
        seta_idx = "🔺" if indice_adherencia_meta >= 1.05 else ("🔻" if indice_adherencia_meta <= 0.95 else "➖")
        kpi_card(
            "Aderência à meta no horário",
            f"<span style='color:{cor_idx};'>{fmt_num_br(indice_adherencia_meta, 2)}x {seta_idx}</span>",
            sub="> 1,00x = acima do necessário.",
            tooltip="1,00x = exatamente em linha com o necessário para bater a meta; abaixo disso, dia atrasado."
        )

    # Insights
    st.markdown('<div class="section-title">🧠 Insights Estratégicos</div>', unsafe_allow_html=True)
    insights_html = f"""
    <div class="insights-box">
    <ul>
        <li>{exp_ritmo}</li>
        <li>{exp_d1}</li>
        <li>{exp_d7}</li>
        <li>Ritmos acima de <b>1,00x</b> indicam aceleração versus o comparativo; abaixo de <b>1,00x</b> apontam perda de tração.</li>
        <li>A aderência à meta no horário mostra se o dia está adiantado ou atrasado em relação ao que seria esperado para bater a meta.</li>
    </ul>
    </div>
    """
    st.markdown(insights_html, unsafe_allow_html=True)

    # Gráfico curvas por slot
    st.markdown('<div class="section-title">📊 Curvas de venda por slot (15 min)</div>', unsafe_allow_html=True)
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

    # Gráfico acumulado
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

    # Heatmap de ritmo vs média por slot
    st.markdown('<div class="section-title">🔥 Mapa de calor de ritmo vs média</div>', unsafe_allow_html=True)
    heat_df = grid.copy()
    heat_df["Ritmo vs média"] = heat_df["ritmo_vs_media"]
    fig_hm = px.imshow(
        [heat_df["Ritmo vs média"].values],
        labels=dict(x="Slot", color="Ritmo vs média"),
        x=heat_df["SLOT"],
        aspect="auto",
        color_continuous_scale="RdYlGn"
    )
    fig_hm.add_hline(y=0, line_color="#000000", opacity=0)  # só pra não bugar eixo
    fig_hm.update_yaxes(showticklabels=False)
    fig_hm.update_layout(
        height=140,
        template="plotly_dark",
        margin=dict(l=10, r=10, t=30, b=10),
        coloraxis_colorbar=dict(title="Ritmo")
    )
    st.plotly_chart(fig_hm, use_container_width=True)

    # Tabela
    st.markdown('<div class="section-title">🧮 Tabela detalhada – DDT slot a slot</div>', unsafe_allow_html=True)
    st.dataframe(grid, use_container_width=True)


# ======================================================
#           ABA 2 – SIMULAÇÕES DE META
# ======================================================
with tab_sim:
    st.markdown('<div class="section-title">🎯 Simulação de meta</div>', unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 2])

    with col_left:
        meta_atual = meta_dia
        meta_sim = st.number_input(
            "Nova meta simulada (R$)",
            min_value=0.0,
            value=float(meta_atual),
            step=50000.0,
            format="%.2f"
        )
        gap_sim = projecao - meta_sim
        venda_esp_sim = meta_sim * frac_hist if frac_hist and frac_hist > 0 else np.nan
        idx_meta_sim = venda_atual / venda_esp_sim if venda_esp_sim and venda_esp_sim != 0 else np.nan

        st.markdown("### Resultado da simulação")
        kpi_card(
            "Meta simulada",
            f"<span style='color:{PRIMARY};'>{fmt_moeda(meta_sim)}</span>",
            sub="Valor hipotético para teste de cenário.",
        )
        kpi_card(
            "Novo gap projetado",
            f"<span style='color:{PRIMARY if gap_sim >= 0 else DANGER};'>{fmt_moeda(gap_sim)}</span>",
            sub="Projeção - meta simulada.",
            tooltip="Se positivo: tendência de superar a meta simulada; se negativo: tendência de ficar abaixo."
        )
        cor_idx_sim = PRIMARY if idx_meta_sim >= 1 else DANGER
        seta_idx_sim = "🔺" if idx_meta_sim >= 1.05 else ("🔻" if idx_meta_sim <= 0.95 else "➖")
        kpi_card(
            "Aderência à meta simulada",
            f"<span style='color:{cor_idx_sim};'>{fmt_num_br(idx_meta_sim,2)}x {seta_idx_sim}</span>",
            sub="> 1,00x = acima do necessário.",
            tooltip="Compara o que já vendemos com o que deveríamos ter vendido até agora para bater a meta simulada."
        )

    with col_right:
        st.markdown("#### Comparativo de cenários")
        df_sim = pd.DataFrame({
            "Cenário": ["Meta atual", "Meta simulada"],
            "Meta (R$)": [meta_dia, meta_sim],
            "Projeção (R$)": [projecao, projecao],
        })
        df_sim["Gap (R$)"] = df_sim["Projeção (R$)"] - df_sim["Meta (R$)"]

        df_sim_fmt = df_sim.copy()
        df_sim_fmt["Meta (R$)"] = df_sim["Meta (R$)"].apply(fmt_moeda)
        df_sim_fmt["Projeção (R$)"] = df_sim["Projeção (R$)"].apply(fmt_moeda)
        df_sim_fmt["Gap (R$)"] = df_sim["Gap (R$)"].apply(fmt_moeda)
        st.table(df_sim_fmt)

        fig_sim = px.bar(
            df_sim,
            x="Cenário",
            y=["Meta (R$)", "Projeção (R$)"],
            barmode="group",
        )
        fig_sim.update_layout(
            height=320,
            template="plotly_dark",
            margin=dict(l=10, r=10, t=30, b=10),
            legend_title_text="",
        )
        st.plotly_chart(fig_sim, use_container_width=True)


# ======================================================
#        ABA 3 – ANÁLISE POR FAIXA HORÁRIA
# ======================================================
with tab_faixas:
    st.markdown('<div class="section-title">⏱️ Análise por faixa horária</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="insights-box">
        As faixas abaixo permitem enxergar onde o dia está “ganhando” ou “perdendo” em relação ao histórico:<br><br>
        • <b>Madrugada (00h–06h)</b><br>
        • <b>Manhã (06h–12h)</b><br>
        • <b>Prime Time (12h–20h)</b><br>
        • <b>Late Night (20h–24h)</b>
        </div>
        """,
        unsafe_allow_html=True,
    )

    faixa_selecionada = st.selectbox(
        "Selecione a faixa horária",
        faixas_resumo["FAIXA"].tolist()
    )

    df_faixa = grid_faixas[grid_faixas["FAIXA"] == faixa_selecionada].copy()

    total_faixa_hoje = df_faixa["valor_hoje"].sum()
    total_faixa_d1   = df_faixa["valor_d1"].sum()
    total_faixa_d7   = df_faixa["valor_d7"].sum()
    total_faixa_med  = df_faixa["valor_media_mes"].sum()

    col_fx1, col_fx2, col_fx3, col_fx4 = st.columns(4)
    with col_fx1:
        kpi_card("Venda hoje na faixa", fmt_moeda(total_faixa_hoje), sub=faixa_selecionada)
    with col_fx2:
        kpi_card("D-1 na faixa", fmt_moeda(total_faixa_d1), sub="mesmo intervalo")
    with col_fx3:
        kpi_card("D-7 na faixa", fmt_moeda(total_faixa_d7), sub="mesmo intervalo")
    with col_fx4:
        kpi_card("Média mês na faixa", fmt_moeda(total_faixa_med), sub="média histórica")

    # Mini curva desta faixa
    curvas_faixa = df_faixa.rename(columns=rename_map)
    curvas_faixa_long = curvas_faixa.melt(
        id_vars=["SLOT"],
        value_vars=list(rename_map.values()),
        var_name="Série",
        value_name="Valor"
    )

    st.markdown("#### Curva intradia da faixa selecionada")
    fig_fx = px.line(
        curvas_faixa_long,
        x="SLOT",
        y="Valor",
        color="Série",
    )
    fig_fx.update_layout(
        height=320,
        template="plotly_dark",
        margin=dict(l=10, r=10, t=30, b=10),
        legend_title_text="",
    )
    st.plotly_chart(fig_fx, use_container_width=True)

    st.markdown("#### Detalhe slot a slot da faixa")
    st.dataframe(
        df_faixa[["SLOT", "valor_hoje", "valor_d1", "valor_d7", "valor_media_mes"]],
        use_container_width=True
    )


# ======================================================
#        ABA 4 – SOBRE O MODELO
# ======================================================
with tab_sobre:
    st.markdown('<div class="section-title">ℹ️ Sobre o modelo de projeção</div>', unsafe_allow_html=True)

    explicacao_modelo_html = f"""
    <div class="insights-box" style="background-color:#050b12;border-color:#1a2a3a;">

    <b>1. Curva intradia histórica</b><br>
    • Para cada slot de 15 minutos, medimos qual fração média do faturamento diário costuma ser concluída ao longo do mês.<br>
    • No horário atual, o padrão histórico indica que cerca de <b>{fmt_percent(frac_hist, 2)}</b> do dia já deveria estar vendido.

    <br><br>

    <b>2. Base matemática de projeção</b><br>
    • Consideramos a venda acumulada até o último slot: <b>{fmt_moeda(venda_atual)}</b>.<br>
    • Dividimos essa venda pela fração histórica do horário, o que gera uma projeção-base de fechamento.<br>
    • Essa base resulta em aproximadamente <b>{fmt_moeda(projecao)}</b> para o dia.

    <br><br>

    <b>3. Camada de consistência por ritmo</b><br>
    • Em paralelo, acompanhamos os ritmos intradia:<br>
    &nbsp;&nbsp;• Ritmo vs D-1: <b>{fmt_num_br(ritmo_d1,2)}x</b><br>
    &nbsp;&nbsp;• Ritmo vs D-7: <b>{fmt_num_br(ritmo_d7,2)}x</b><br>
    &nbsp;&nbsp;• Ritmo vs média do mês: <b>{fmt_num_br(ritmo_media,2)}x</b><br>
    • Ritmos acima de <b>1,00x</b> sugerem aceleração; abaixo disso, perda de tração.<br>
    • Esses indicadores funcionam como checagem de consistência do comportamento do dia.

    <br><br>

    <b>4. Meta e aderência intradia</b><br>
    • A meta do dia é de <b>{fmt_moeda(meta_dia)}</b>.<br>
    • Com base na curva intradia, a venda esperada para o horário atual seria <b>{fmt_moeda(venda_esperada_horario)}</b>.<br>
    • A aderência à meta no horário é de <b>{fmt_num_br(indice_adherencia_meta,2)}x</b>, mostrando se estamos adiantados ou atrasados em relação ao alvo.

    <br><br>

    <b>Conclusão executiva</b><br>
    Combinando curva histórica, venda atual, meta e consistência de ritmo, o fechamento projetado é de
    <b>{fmt_moeda(projecao)}</b>.<br>
    Isso representa um gap de
    <b style="color:{PRIMARY if gap_proj >= 0 else DANGER};">{fmt_moeda(gap_proj)}</b>
    em relação à meta consolidada de <b>{fmt_moeda(meta_dia)}</b>.

    </div>
    """
    st.markdown(explicacao_modelo_html, unsafe_allow_html=True)

    st.markdown("### 🧾 Glossário rápido")
    st.markdown(
        """
        - **Meta do dia**: objetivo financeiro consolidado para Site + App.<br>
        - **Venda atual**: faturamento acumulado até o último slot processado na base.<br>
        - **Projeção de fechamento**: estimativa do faturamento total do dia, caso o ritmo atual se mantenha.<br>
        - **Ritmo vs D-1 / D-7 / mês**: quantas vezes o dia de hoje está melhor ou pior do que o comparativo.<br>
        - **Fração histórica do dia**: percentual médio do faturamento diário que, historicamente, já aconteceu até o horário atual.<br>
        - **Aderência à meta no horário**: relação entre a venda atual e a venda que seria esperada nesse horário para bater a meta.
        """,
        unsafe_allow_html=True,
    )
