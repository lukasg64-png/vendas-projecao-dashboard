import streamlit as st
import pandas as pd

st.set_page_config(page_title="📈 Projeção de Vendas – Site + App", layout="wide")

st.title("📈 Projeção de Vendas – Site + App")

# ============================================================
# 1 — CARREGAR OS ARQUIVOS GERADOS PELO COLAB
# ============================================================

try:
    df_grid = pd.read_csv("data/saida_grid.csv")
    df_resumo = pd.read_csv("data/saida_resumo.csv")
except Exception as e:
    st.error(f"Erro ao carregar arquivos: {e}")
    st.stop()

# ============================================================
# 2 — MOSTRAR O RESUMO (1 LINHA)
# ============================================================

st.subheader("📌 Resumo do Dia")

# Mostrar bonito em caixa JSON
resumo_dict = df_resumo.iloc[0].to_dict()
st.json(resumo_dict)

# ============================================================
# 3 — GRÁFICO DDT
# ============================================================

st.subheader("📊 Curva DDT — Valor por Slot")

df_plot = df_grid.set_index("SLOT")[["valor_hoje", "valor_d1", "valor_d7", "valor_media_mes"]]

st.line_chart(df_plot)

# ============================================================
# 4 — TABELA COMPLETA DDT
# ============================================================

st.subheader("🧮 Tabela Completa — DDT Slot a Slot")
st.dataframe(df_grid, use_container_width=True)

# ============================================================
# 5 — DOWNLOAD DOS ARQUIVOS (opcional)
# ============================================================

st.subheader("⬇️ Baixar Arquivos Processados")

st.download_button("Download grid (DDT)", df_grid.to_csv(index=False), "saida_grid.csv")
st.download_button("Download resumo", df_resumo.to_csv(index=False), "saida_resumo.csv")
