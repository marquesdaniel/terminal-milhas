import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from scipy.stats import norm

# ==========================
# CONFIGURAÇÃO DA PÁGINA
# ==========================

st.set_page_config(page_title="Terminal Profissional Milhas",
                   layout="wide")

st.title("📊 Terminal Profissional de Valuation de Milhas")

# ==========================
# MODELO MACHINE LEARNING
# ==========================

@st.cache_resource
def treinar_modelo():
    np.random.seed(42)
    bonus = np.random.uniform(0.5,1.0,300)
    preco = np.random.uniform(30,45,300)
    vol = np.random.uniform(0.05,0.25,300)

    roi = 0.08 + 0.4*bonus - 0.02*preco - 0.3*vol + np.random.normal(0,0.02,300)

    X = np.column_stack((bonus,preco,vol))
    y = roi

    model = LinearRegression()
    model.fit(X,y)
    return model

modelo = treinar_modelo()

# ==========================
# SIDEBAR INPUTS
# ==========================

st.sidebar.header("⚙️ Parâmetros")

bonus = st.sidebar.slider("Bônus (%)",50,120,80)/100
preco = st.sidebar.slider("Preço por 1000 pontos",25,50,35)
vol = st.sidebar.slider("Volatilidade (%)",5,30,15)/100
capital = st.sidebar.number_input("Capital Inicial",value=10000)

# ==========================
# PREDIÇÃO
# ==========================

X_novo = np.array([[bonus,preco,vol]])
roi_estimado = modelo.predict(X_novo)[0]

resultados = np.random.normal(roi_estimado,vol,5000)

prob = np.mean(resultados>0.05)
var95 = np.percentile(resultados,5)
cvar95 = resultados[resultados<=var95].mean()
sharpe = roi_estimado/vol
score = min(100,max(0,(roi_estimado*50)+(prob*30)+(sharpe*20)))

preco_max = preco/(1+roi_estimado)
capital_12m = capital*(1+roi_estimado)**12

# ==========================
# DASHBOARD
# ==========================

col1,col2,col3 = st.columns(3)

col1.metric("ROI Esperado",f"{roi_estimado*100:.2f}%")
col2.metric("Prob ROI > 5%",f"{prob*100:.2f}%")
col3.metric("Sharpe Ratio",f"{sharpe:.2f}")

col4,col5,col6 = st.columns(3)

col4.metric("VaR 95%",f"{var95*100:.2f}%")
col5.metric("CVaR 95%",f"{cvar95*100:.2f}%")
col6.metric("Score",f"{score:.1f}/100")

st.subheader("📈 Distribuição Simulada de ROI")

fig, ax = plt.subplots()
ax.hist(resultados,bins=40)
st.pyplot(fig)

st.subheader("💰 Projeção de Capital (12 meses)")

meses = np.arange(1,13)
crescimento = capital*(1+roi_estimado)**meses

fig2, ax2 = plt.subplots()
ax2.plot(meses,crescimento)
ax2.set_xlabel("Meses")
ax2.set_ylabel("Capital")
st.pyplot(fig2)

st.subheader("📌 Preço Máximo Ideal")
st.write(f"Preço máximo ideal por 1000 pontos: **R$ {preco_max:.2f}**")

classificacao = (
    "🔥 EXCELENTE" if score>75 else
    "👍 BOA" if score>55 else
    "⚖️ NEUTRA" if score>40 else
    "❌ EVITAR"
)

st.subheader("📊 Classificação")
st.write(classificacao)
