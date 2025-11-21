def montar_projecao(df_slots, meta_dia, data_ref=None):
    df = df_slots.copy()

    # ----------------------------------------------
    # 1. Data de referência e D-1 / D-7
    # ----------------------------------------------
    if data_ref is None:
        data_ref = df["DATA"].max()

    data_ref = pd.to_datetime(data_ref).date()
    data_d1  = data_ref - timedelta(days=1)
    data_d7  = data_ref - timedelta(days=7)

    # ----------------------------------------------
    # 2. Curva por dia (DDT)
    # ----------------------------------------------
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

    # ----------------------------------------------
    # 3. Curva média do mês
    # ----------------------------------------------
    datas_ts = pd.to_datetime(df["DATA"])
    mes = data_ref.month
    ano = data_ref.year

    base_mes = df[
        (datas_ts.dt.month == mes) &
        (datas_ts.dt.year  == ano)
    ]

    curva_media = (
        base_mes.groupby("SLOT")["VALOR_TOTAL_15M"]
                .mean()
                .reset_index()
                .sort_values("SLOT")
    )

    # ----------------------------------------------
    # 4. Grid base de HOJE
    # ----------------------------------------------
    grid = curva_hoje[["SLOT"]].copy()

    grid = grid.merge(
        curva_hoje.rename(columns={"VALOR_TOTAL_15M": "valor_hoje"}),
        on="SLOT",
        how="left"
    )
    grid = grid.merge(
        curva_d1.rename(columns={"VALOR_TOTAL_15M": "valor_d1"}),
        on="SLOT",
        how="left"
    )
    grid = grid.merge(
        curva_d7.rename(columns={"VALOR_TOTAL_15M": "valor_d7"}),
        on="SLOT",
        how="left"
    )
    grid = grid.merge(
        curva_media.rename(columns={"VALOR_TOTAL_15M": "valor_media_mes"}),
        on="SLOT",
        how="left"
    )

    grid = grid.fillna(0.0)

    # ----------------------------------------------
    # 5. Acumulados
    # ----------------------------------------------
    grid["acum_hoje"]      = grid["valor_hoje"].cumsum()
    grid["acum_d1"]        = grid["valor_d1"].cumsum()
    grid["acum_d7"]        = grid["valor_d7"].cumsum()
    grid["acum_media_mes"] = grid["valor_media_mes"].cumsum()

    # Fração histórica (curva intradia do mês)
    max_media = grid["acum_media_mes"].max()
    if max_media > 0:
        grid["frac_hist"] = grid["acum_media_mes"] / max_media
    else:
        grid["frac_hist"] = 0.0

    # ----------------------------------------------
    # 6. Ritmo e projeção
    # ----------------------------------------------
    ultimo_idx   = grid.index.max()
    venda_atual  = float(grid.loc[ultimo_idx, "acum_hoje"])
    acum_d1_ult  = float(grid.loc[ultimo_idx, "acum_d1"])
    acum_d7_ult  = float(grid.loc[ultimo_idx, "acum_d7"])
    acum_med_ult = float(grid.loc[ultimo_idx, "acum_media_mes"])
    frac_hist_atual = float(grid.loc[ultimo_idx, "frac_hist"])

    ritmo_d1    = venda_atual / acum_d1_ult  if acum_d1_ult  > 0 else 0.0
    ritmo_d7    = venda_atual / acum_d7_ult  if acum_d7_ult  > 0 else 0.0
    ritmo_media = venda_atual / acum_med_ult if acum_med_ult > 0 else 0.0

    # Se temos fração histórica > 0, projeta por ela
    if frac_hist_atual > 0:
        projecao = venda_atual / frac_hist_atual
    else:
        projecao = venda_atual

    # Totais do dia anterior e D-7 (até o último slot)
    total_d1 = float(grid["acum_d1"].max())
    total_d7 = float(grid["acum_d7"].max())

    # ----------------------------------------------
    # 7. Dicionário RESUMO no padrão esperado pelo front
    # ----------------------------------------------
    resumo = {
        "data": str(data_ref),

        "meta_dia": float(meta_dia),
        "venda_atual": float(venda_atual),

        "projecao": float(projecao),
        "gap": float(projecao - meta_dia),

        "ritmo_d1": float(ritmo_d1),
        "ritmo_d7": float(ritmo_d7),
        "ritmo_media": float(ritmo_media),

        "total_d1": float(total_d1),
        "total_d7": float(total_d7),

        "frac_hist": float(frac_hist_atual),
    }

    return grid, resumo
