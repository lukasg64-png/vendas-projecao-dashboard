import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="📈 Projeção de Vendas – Site + App", layout="wide")

# ===========================================================
# FUNÇÕES AUXILIARES
# ===========================================================

def meta_do_dia(metas_df, data_ref):
    dia = pd.to_datetime(data_ref).day
    row = metas_df[metas_df["dia"] == dia]
    return float(row["total"].values[0]) if not row.empty else 0.0


def montar_projecao(df_slots, meta_dia, data_ref=None):
    df = df_slots.copy()

    if data_ref is None:
        data_ref = df["DATA"].max()
    data_ref = pd.to_datetime(data_ref).date()

    data_d1 = data_ref - timedelta(days=1)
    data_d7 = data_ref - timedelta(days=7)

    # Curva DDT
    def curva(data_alvo):
        cur = df[df["DATA"] == data_alvo]
        if cur.empty:
            return pd.DataFrame({"SLOT": [], "VALOR_TOTAL_15M": []})
        return (
            cur.groupby("SLOT")["VALOR_TOTAL_15M"]
            .sum()
            .reset_index()
            .sort_values("SLOT")
        )

    curva_hoje = curva(data_ref)
    curva_d1   = curva(data_d1)
    curva_d7   = curva(data_d7)

    # Média do mês
    mes = pd.to_datetime(data_ref).month
    ano = pd.to_datetime(data_ref).year
    base_mes = df[(pd.to_datetime(df["DATA"]).dt.month == mes) &
                  (pd.to_datetime(df["DATA"]).dt.year == ano)]

    curva_media = (
        base_mes.groupby("SLOT")["VALOR_TOTAL_15M"]
        .mean()
        .reset_index()
        .sort_values("SLOT")
    )

    # Construir grid
    grid = curva_hoje[["SLOT"]].copy()
    grid = grid.merge(curva_hoje.rename(columns={"VALOR_TOTAL_15M":"valor_hoje"}), on="SLOT")
    grid = grid.merge(curva_d1.rename(columns={"VALOR_TOTAL_15M":"valor_d1"}), on="SLOT", how="left")
    grid = grid.merge(curva_d7.rename(columns={"VALOR_TOTAL_15M":"valor_d7"}), on="SLOT", how="left")
    grid = grid.merge(curva_media.rename(columns={"VALOR_TOTAL_15M":"valor_media_mes"}), on="SLOT", how="left")

    grid = grid.fillna(0)

    # Acumulados
    grid["acum_hoje"]       = grid["valor_hoje"].cumsum()
    grid["acum_d1"]         = grid["valor_d1"].cumsum()
    grid["acum_d7"]         = grid["valor_d7"].cumsum()
    grid["acum_media_mes"]  = grid["valor_media_mes"].cumsum()

    grid["frac_hist"] = grid["acum_media_mes"] / grid["acum_media_mes"].max()

    # Ritmos
    def safe(a, b): return a / b if b != 0 else 0
    ultimo = grid.index.max()

    ritmo_d1    = safe(grid.loc[ultimo,"acum_hoje"], grid.loc[ultimo,"acum_d1"])
    ritmo_d7    = safe(grid.loc[ultimo,"acum_hoje"], grid.loc[ultimo,"acum_d7"])
    ritmo_media = safe(grid.loc[ultimo,"acum_hoje"], grid.loc[ultimo,"acum_media_mes"])

    frac_hist_atual = grid.loc[ultimo, "frac_hist"]
    venda_atual     = grid.loc[ultimo, "acum_hoje"]

    if frac_hist_atual > 0:
        projecao = venda_atual / frac_hist_atual
    else:
        projecao = 0

    total_d1 = grid["acum_d1"].max()
    total_d7 = grid["acum_d7"].max()

    resumo = {
        "data_referencia": str(data_ref),
        "meta_dia": meta_dia,
        "venda_atual_ate_slot": venda_atual,
        "percentual_dia_hist": frac_hist_atual,
        "tipo_percentual_base": "intradia_hist",
        "projecao_dia": projecao,
        "desvio_projecao": projecao - meta_dia,
        "total_d1": total_d1,
        "meta_d1": meta_dia,
        "desvio_d1": total_d1 - meta_dia,
        "total_d7": total_d7,
        "meta_d7": meta_dia,
        "desvio_d7": total_d7 - meta_dia,
        "ritmo_vs_d1": ritmo_d1,
        "ritmo_vs_d7": ritmo_d7,
        "ritmo_vs_media": ritmo_media,
        "explicacao_ritmo": f"Até agora vendemos {venda_atual:,.0f}, equivalente a {frac_hist_atual*100:.2f}% da curva intradia histórica.",
        "explicacao_d1": f"Ontem fechamos em {total_d1:,.0f} vs meta {meta_dia:,.0f} ({total_d1-meta_dia:,.0f} de desvio).",
        "explicacao_d7": f"Há 7 dias fechamos em {total_d7:,.0f} vs meta {meta_dia:,.0f} ({total_d7-meta_dia:,.0f} de desvio).",
    }

    return grid, resumo

# ===========================================================
# INTERFACE STREAMLIT
# ===========================================================

st.title("📈 Projeção de Vendas – Site + App")

# --- Carregar arquivos ---
df = pd.read_csv("data/ultima_base.csv")
# --- Carregar metas (compatível com sua planilha real) ---
metas = pd.read_excel("data/metas_novembro.xlsx")

# Padronizar nomes
metas = metas.rename(columns={
    "Dia": "dia",
    "App": "app",
    "Site": "site",
    "site + APP": "total"
})

# Garantir tipos corretos
metas["dia"] = metas["dia"].astype(int)
metas["total"] = metas["total"].astype(float)


df["DATA"] = pd.to_datetime(df["DATA"]).dt.date

st.sidebar.header("Configurações")

data_forcada = st.sidebar.date_input("Forçar data de referência (opcional)", value=None)

data_ref = data_forcada if data_forcada else df["DATA"].max()
meta_dia = meta_do_dia(metas, data_ref)

# Executar projeção
grid, resumo = montar_projecao(df, meta_dia, data_ref)

# --- RESUMO ---
st.subheader("📌 Resumo do Dia")
st.json(resumo)

# --- GRÁFICO ---
st.subheader("📊 Curva DDT — Valor por Slot")
st.line_chart(
    grid.set_index("SLOT")[["valor_hoje", "valor_d1", "valor_d7", "valor_media_mes"]]
)

# --- TABELA COMPLETA ---
st.subheader("🧮 Tabela Completa — DDT Slot a Slot")
st.dataframe(grid, use_container_width=True)
