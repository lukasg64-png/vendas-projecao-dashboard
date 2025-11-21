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

PRIMARY = "#00E676"
DANGER  = "#FF1744"
WARNING = "#FFD54F"
CARD_BG = "#111111"

# =========================================================
# HELPERS
# =========================================================
def fmt_currency_br(x, decimals=0):
    try:
        if x is None or np.isnan(x):
            return "-"
    except:
        pass
    s = f"{x:,.{decimals}f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"

def fmt_percent_br(x, decimals=1):
    try:
        if x is None or np.isnan(x):
            return "-"
    except:
        pass
    pct = x * 100
    s = f"{pct:,.{decimals}f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{s}%"

def load_logins(path: Path):
    if not path.exists():
        return pd.DataFrame([
            {"usuario": "farmacias_sao_joao", "senha": "blackfriday2025", "nome": "Time E-commerce"}
        ])
    df = pd.read_csv(path, dtype=str).fillna("")
    return df

def authenticate(username, password, df_logins):
    row = df_logins[
        (df_logins["usuario"] == username) &
        (df_logins["senha"] == password)
    ]
    if not row.empty:
        return True, row["nome"].iloc[0]
    return False, None

def kpi_card(title, value, subtitle="", color=PRIMARY, tooltip=None):
    info = ""
    if tooltip:
        info = f"<span style='margin-left:6px; cursor:help;' title='{tooltip}'>ℹ️</span>"

    html = f"""
    <div style='background:{CARD_BG};padding:18px 20px;border-radius:12px;
        border:1px solid #333;box-shadow:0 0 10px rgba(0,0,0,0.4);'>
        <div style='font-size:0.8rem;color:#BBBBBB;display:flex;justify-content:space-between;'>
            <span>{title}</span>{info}
        </div>
        <div style='font-size:1.7rem;font-weight:700;margin-top:4px;color:{color};'>
            {value}
        </div>
        <div style='font-size:0.75rem;color:#888888;margin-top:6px;'>
            {subtitle}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# =========================================================
# LOGIN
# =========================================================
def login_screen(df_logins):
    st.markdown(
        """
        <div style="
            padding:14px 18px;border-radius:14px;
            background:linear-gradient(90deg,#00E676,#00B0FF);
            display:flex;align-items:center;justify-content:space-between;
            margin-bottom:12px;">
            <div>
                <div style="font-size:1.2rem;font-weight:700;color:#001B20;">
                    FSJ Black Friday – Painel de Projeção
                </div>
                <div style="font-size:0.9rem;color:#012A30;margin-top:4px;">
                    Bem-vindo, São João! <b>Tem Black na São João? Tem Black na São João! 🔥</b>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col = st.columns([1, 1, 1])[1]

    with col:
        st.markdown("### 🔐 Acesse o painel")

        user = st.text_input("Usuário")
        pwd  = st.text_input("Senha", type="password")

        if st.button("Entrar", type="primary", use_container_width=True):
            ok, nome = authenticate(user.strip(), pwd.strip(), df_logins)
            if ok:
                st.session_state["auth"] = True
                st.session_state["user_name"] = nome
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")

        st.caption("Logins carregados de `data/logins.csv`.")


# =========================================================
# CARREGAR DADOS
# =========================================================
@st.cache_data
def load_grid_and_resumo(grid_path, resumo_path):
    grid = pd.read_csv(grid_path)
    resumo_df = pd.read_csv(resumo_path)
    resumo = resumo_df.iloc[0].to_dict()
    return grid, resumo


# =========================================================
# VISÃO GERAL
# =========================================================
def painel_visao_geral(grid, resumo, user_name):

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

    perc_meta_real = venda_atual / meta_dia if meta_dia else 0

    st.markdown(
        f"""
        <div style="margin-bottom:10px;font-size:0.9rem;color:#BBBBBB;">
            Usuário: <b>{user_name}</b> • Data de referência: <b>{data_ref.strftime('%d/%m/%Y')}</b>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        kpi_card("Meta do dia", fmt_currency_br(meta_dia),
                 "Meta consolidada Site + App.")

    with c2:
        kpi_card(
            "Venda atual",
            fmt_currency_br(venda_atual),
            f"{fmt_percent_br(perc_meta_real)} da meta.",
            color=PRIMARY if perc_meta_real >= frac_hist else WARNING,
        )

    with c3:
        kpi_card(
            "Projeção de fechamento",
            fmt_currency_br(projecao),
            "Baseada na curva intradia histórica.",
            color=PRIMARY if projecao >= meta_dia else WARNING,
        )

    gap_color = PRIMARY if gap >= 0 else DANGER
    gap_label = "Acima da meta" if gap >= 0 else "Abaixo da meta"

    with c4:
        kpi_card(
            "Gap projetado",
            fmt_currency_br(gap),
            gap_label,
            color=gap_color,
        )

    st.markdown("---")

    st.subheader("📈 Ritmo do dia", divider="gray")

    c5, c6, c7, c8 = st.columns(4)

    with c5:
        kpi_card("Total D-1", fmt_currency_br(total_d1), "Ontem.")

    with c6:
        kpi_card("Total D-7", fmt_currency_br(total_d7), "Semana passada.")

    with c7:
        kpi_card("Dia já percorrido", fmt_percent_br(frac_hist), "Histórico intradia.")

    with c8:
        ritmo_combinado = (ritmo_d1 + ritmo_d7 + ritmo_med) / 3
        texto = (
            f"vs D-1: {ritmo_d1:.2f}x • "
            f"vs D-7: {ritmo_d7:.2f}x • "
            f"vs média: {ritmo_med:.2f}x"
        )
        kpi_card(
            "Ritmo combinado",
            f"{ritmo_combinado:.2f}x",
            texto,
            color=PRIMARY if ritmo_combinado >= 1 else WARNING,
        )

    # ANALISE EXECUTIVA
    st.subheader("📝 Análise executiva da projeção", divider="gray")

    st.markdown(
        f"""
        A projeção é construída em três camadas:

        **1. Curva intradia histórica**  
        - No horário atual, o dia costuma estar em **{fmt_percent_br(frac_hist)}**.

        **2. Base matemática da projeção**  
        - Faturamento acumulado: **{fmt_currency_br(venda_atual)}**  
        - Projeção: **{fmt_currency_br(projecao)}**

        **3. Ritmos de consistência**  
        - D-1: {ritmo_d1:.2f}x  
        - D-7: {ritmo_d7:.2f}x  
        - Média: {ritmo_med:.2f}x

        **Conclusão:** Gap projetado de **{fmt_currency_br(gap)}**
        """
    )


# =========================================================
# CURVAS & RITMO
# =========================================================
def painel_curvas_ritmo(grid, resumo):
    st.subheader("📊 Curvas de venda", divider="gray")

    fig = px.line(
        grid,
        x="SLOT",
        y=["valor_hoje", "valor_d1", "valor_d7", "valor_media_mes"],
        labels={"value": "R$"}
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📈 Ritmos ao longo do dia", divider="gray")

    projecao = float(resumo["projecao_dia"])
    grid["perc_realizado"] = grid["acum_hoje"] / projecao if projecao > 0 else 0

    df = pd.DataFrame({
        "SLOT": grid["SLOT"],
        "Ritmo vs D-1": grid["ritmo_vs_d1"],
        "Ritmo vs D-7": grid["ritmo_vs_d7"],
        "Ritmo vs média": grid["ritmo_vs_media"],
        "% realizado": grid["perc_realizado"],
    })

    fig2 = px.line(df, x="SLOT", y=df.columns[1:])
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("🔥 Heatmap de intensidade", divider="gray")

    melt = grid.melt(id_vars="SLOT",
                     value_vars=["valor_hoje","valor_d1","valor_d7","valor_media_mes"],
                     var_name="Dia", value_name="Valor")

    matrix = melt.pivot(index="Dia", columns="SLOT", values="Valor")

    fig3 = px.imshow(matrix, color_continuous_scale="Viridis")
    st.plotly_chart(fig3, use_container_width=True)


# =========================================================
# SIMULACAO DE META
# =========================================================
def painel_simulacao_meta(resumo):
    st.subheader("🎯 Simulação de meta", divider="gray")

    meta = float(resumo["meta_dia"])
    proj = float(resumo["projecao_dia"])
    venda = float(resumo["venda_atual_ate_slot"])

    nova_meta = st.slider(
        "Nova meta (R$)", int(meta*0.5), int(meta*1.5), int(meta), step=25000
    )

    gap = proj - nova_meta
    perc_proj = proj / nova_meta if nova_meta else 0
    perc_real = venda / nova_meta if nova_meta else 0

    c1, c2, c3 = st.columns(3)

    with c1:
        kpi_card("Meta atual", fmt_currency_br(meta))
    with c2:
        kpi_card("Meta simulada", fmt_currency_br(nova_meta), color=WARNING)
    with c3:
        kpi_card(
            "Gap simulado",
            fmt_currency_br(gap),
            f"Cobertura: {fmt_percent_br(perc_proj)}",
            color=PRIMARY if gap >= 0 else DANGER,
        )

    st.write(
        f"A venda atual cobre {fmt_percent_br(perc_real)} da meta simulada."
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

    # HEADER
    st.markdown(
        """
        <div style="
            padding:14px 20px;border-radius:14px;
            background:linear-gradient(90deg,#00E676,#00B0FF);
            display:flex;align-items:center;justify-content:space-between;
            margin-bottom:16px;">
            <div>
                <div style="font-size:1.2rem;font-weight:700;color:#001B20;">
                    Painel Executivo – FSJ Black Friday
                </div>
                <div style="font-size:0.85rem;color:#012A30;">
                    Monitor de projeção, curva intradia e ritmo.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    grid, resumo = load_grid_and_resumo(GRID_PATH, RESUMO_PATH)

    aba1, aba2, aba3 = st.tabs(["Visão Geral", "Curvas & Ritmo", "Simulação"])

    with aba1:
        painel_visao_geral(grid, resumo, st.session_state["user_name"])

    with aba2:
        painel_curvas_ritmo(grid, resumo)

    with aba3:
        painel_simulacao_meta(resumo)


if __name__ == "__main__":
    main()
