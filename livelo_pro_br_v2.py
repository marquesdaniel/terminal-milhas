import streamlit as st
import pandas as pd
import os
import requests
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("🏦 LIVEL0 - PRO Brasil")

ARQUIVO = "precos_milhas.csv"

# ==========================
# FORMATAÇÃO BR
# ==========================

def br_number(valor, casas=2):
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ==========================
# DÓLAR AUTOMÁTICO
# ==========================

@st.cache_data(ttl=1800)
def obter_dolar():
    try:
        hoje = datetime.now().strftime("%m-%d-%Y")
        url = f"https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoDolarDia(dataCotacao=@dataCotacao)?@dataCotacao='{hoje}'&$top=1&$format=json"
        response = requests.get(url)
        data = response.json()
        return float(data["value"][0]["cotacaoVenda"])
    except:
        return None

dolar = obter_dolar()

# ==========================
# CARREGAR CSV
# ==========================

def carregar_precos():
    if not os.path.exists(ARQUIVO):
        df_inicial = pd.DataFrame({
            "Compradora": ["MaxMilhas", "HotMilhas", "BankMilhas"],
            "Programa": ["Smiles", "Latam", "Azul"],
            "Preco": [25.0, 24.0, 23.5]
        })
        df_inicial.to_csv(ARQUIVO, index=False)
        return df_inicial
    return pd.read_csv(ARQUIVO)

df_precos = carregar_precos()

# ==========================
# ABAS
# ==========================

aba1, aba2, aba3, aba4 = st.tabs([
    "💳 Compra Direta",
    "💳 Cartão",
    "📋 Tabela CSV",
    "📊 Estratégia"
])

# =====================================================
# ABA 1 - COMPRA DIRETA
# =====================================================

with aba1:

    gasto_compra = st.number_input("Valor compra (R$)", 0.0, 500000.0, 10000.0)
    preco_livelo = st.number_input("Preço 1000 Livelo (R$)", 25.0, 45.0, 35.0)
    bonus_compra = st.slider("Bônus Compra (%)", 0, 200, 0)/100

    pontos_base = (gasto_compra / preco_livelo) * 1000 if preco_livelo > 0 else 0
    pontos_compra_final = pontos_base * (1 + bonus_compra)

    st.metric("Pontos Finais Compra", br_number(pontos_compra_final,0))

# =====================================================
# ABA 2 - CARTÃO
# =====================================================

with aba2:

    if dolar:
        st.success(f"Dólar PTAX: R$ {br_number(dolar)}")
    else:
        dolar = st.number_input("Dólar manual", 4.0, 7.0, 5.0)

    gasto_cartao = st.number_input("Gasto cartão (R$)", 0.0, 500000.0, 10000.0)
    pontos_por_dolar = st.number_input("Pontos por dólar", 1.0, 5.0, 1.0)

    pontos_cartao = (gasto_cartao / dolar) * pontos_por_dolar if dolar else 0

    st.metric("Pontos Gerados Cartão", br_number(pontos_cartao,0))

# =====================================================
# ABA 3 - TABELA CSV
# =====================================================

with aba3:

    st.warning("Tabela NÃO atualiza automaticamente.")

    df_editado = st.data_editor(df_precos, num_rows="dynamic", use_container_width=True)

    if st.button("💾 Salvar"):
        df_editado.to_csv(ARQUIVO, index=False)
        st.success("Tabela salva.")

# =====================================================
# ABA 4 - ESTRATÉGIA
# =====================================================
with aba4:

    st.header("📊 Estratégia Consolidada")

    pontos_totais = pontos_compra_final + pontos_cartao
    st.metric("Total Pontos", br_number(pontos_totais,0))

    programa = st.selectbox("Programa", df_precos["Programa"].unique())

    df_prog = df_precos[df_precos["Programa"] == programa]

    bonus_transferencia = st.slider("Bônus Transferência (%)", 50, 120, 80)/100

    milhas_totais = pontos_totais * (1 + bonus_transferencia)

    resultados = []

    for _, row in df_prog.iterrows():
        preco = row["Preco"]
        receita = (milhas_totais/1000) * preco
        lucro = receita - gasto_compra
        roi = lucro / gasto_compra if gasto_compra > 0 else 0

        resultados.append({
            "Compradora": row["Compradora"],
            "Preço Milheiro": preco,
            "Receita": receita,
            "Lucro": lucro,
            "ROI": roi
        })

    df_result = pd.DataFrame(resultados)
    df_result = df_result.sort_values("Lucro", ascending=False)

    st.subheader("📊 Ranking Completo das Compradoras")

    df_exibicao = df_result.copy()
    df_exibicao["Preço Milheiro"] = df_exibicao["Preço Milheiro"].apply(lambda x: f"R$ {br_number(x)}")
    df_exibicao["Receita"] = df_exibicao["Receita"].apply(lambda x: f"R$ {br_number(x)}")
    df_exibicao["Lucro"] = df_exibicao["Lucro"].apply(lambda x: f"R$ {br_number(x)}")
    df_exibicao["ROI"] = df_exibicao["ROI"].apply(lambda x: f"{br_number(x*100)}%")

    st.dataframe(df_exibicao, use_container_width=True)

    melhor = df_result.iloc[0]

    # ==========================
    # BREAK-EVEN
    # ==========================

    if milhas_totais > 0:
        preco_break_even = gasto_compra / (milhas_totais/1000)
    else:
        preco_break_even = 0

    st.subheader("📈 Break-even")

    st.metric("Preço mínimo do milheiro para não ter prejuízo",
              f"R$ {br_number(preco_break_even)}")

    # ==========================
    # MARGEM MÍNIMA
    # ==========================

    margem_alvo = st.slider("Margem mínima desejada (%)", 0, 30, 5)/100

    status = ""

    if melhor["ROI"] >= margem_alvo:
        status = "🟢 OPERAÇÃO APROVADA"
        st.success(status)
    elif melhor["ROI"] > 0:
        status = "🟡 ROI positivo, mas abaixo da margem alvo"
        st.warning(status)
    else:
        status = "🔴 OPERAÇÃO REPROVADA"
        st.error(status)

    st.subheader("🏆 Melhor Opção")

    st.metric("Compradora", melhor["Compradora"])
    st.metric("Lucro", f"R$ {br_number(melhor['Lucro'])}")
    st.metric("ROI", f"{br_number(melhor['ROI']*100)}%")

    # ==========================
    # SENSIBILIDADE
    # ==========================

    st.subheader("📉 Sensibilidade ROI vs Preço Milheiro")

    precos = np.linspace(preco_break_even*0.8, preco_break_even*1.4, 30)
    rois = []

    for p in precos:
        receita_s = (milhas_totais/1000) * p
        lucro_s = receita_s - gasto_compra
        roi_s = lucro_s / gasto_compra if gasto_compra > 0 else 0
        rois.append(roi_s)

    fig, ax = plt.subplots(figsize=(4,3))
    ax.plot(precos, rois)
    ax.axhline(margem_alvo, linestyle="--")
    ax.set_xlabel("Preço Milheiro")
    ax.set_ylabel("ROI")
    st.pyplot(fig)
