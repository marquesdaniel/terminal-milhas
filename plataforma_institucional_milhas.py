import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
from sklearn.linear_model import LinearRegression
import datetime

# ==========================
# BANCO DE DADOS
# ==========================

engine = create_engine("sqlite:///milhas.db")

def inicializar_db():
    with engine.connect() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS operacoes (
            data TEXT,
            programa TEXT,
            bonus REAL,
            preco REAL,
            roi REAL,
            bloqueio INTEGER
        )
        """)

inicializar_db()

# ==========================
# MACHINE LEARNING DINÂMICO
# ==========================

def treinar_modelo():
    df = pd.read_sql("SELECT * FROM operacoes", engine)

    if len(df) < 10:
        return None

    X = df[["bonus","preco"]]
    y = df["roi"]

    model = LinearRegression()
    model.fit(X,y)
    return model

modelo = treinar_modelo()

# ==========================
# INTERFACE
# ==========================

st.set_page_config(layout="wide")
st.title("🏦 Plataforma Institucional Multi-Programa")

programas = ["Smiles","Latam","Azul"]

col1,col2,col3 = st.columns(3)

with col1:
    programa = st.selectbox("Programa",programas)

with col2:
    bonus = st.slider("Bônus (%)",50,120,80)/100

with col3:
    preco = st.slider("Preço por 1000",25,50,35)

vol = st.slider("Volatilidade (%)",5,30,15)/100
capital = st.number_input("Capital Inicial",10000)

# ==========================
# VALUATION
# ==========================

if modelo:
    roi_estimado = modelo.predict([[bonus,preco]])[0]
else:
    roi_estimado = 0.08 + 0.4*bonus - 0.02*preco - 0.3*vol

resultados = np.random.normal(roi_estimado,vol,5000)

prob = np.mean(resultados>0.05)
var95 = np.percentile(resultados,5)
sharpe = roi_estimado/vol

score = min(100,max(0,(roi_estimado*50)+(prob*30)+(sharpe*20)))

st.subheader("📊 Métricas Institucionais")

m1,m2,m3,m4 = st.columns(4)
m1.metric("ROI Esperado",f"{roi_estimado*100:.2f}%")
m2.metric("Prob ROI>5%",f"{prob*100:.2f}%")
m3.metric("Sharpe",f"{sharpe:.2f}")
m4.metric("Score",f"{score:.1f}")

# ==========================
# RANKING MULTI-PROGRAMA
# ==========================

st.subheader("🏆 Ranking Simultâneo")

ranking = []

for prog in programas:
    roi_prog = 0.08 + 0.4*bonus - 0.02*preco - 0.3*vol
    score_prog = min(100,max(0,(roi_prog*50)+(prob*30)+(sharpe*20)))
    ranking.append([prog,roi_prog,score_prog])

df_rank = pd.DataFrame(ranking,columns=["Programa","ROI","Score"])
st.dataframe(df_rank.sort_values("Score",ascending=False))

# ==========================
# HISTOGRAMA
# ==========================

fig,ax = plt.subplots()
ax.hist(resultados,bins=40)
st.pyplot(fig)

# ==========================
# REGISTRAR OPERAÇÃO REAL
# ==========================

st.subheader("💾 Registrar Operação Real")

bonus_real = st.number_input("Bônus Real (%)",80)
preco_real = st.number_input("Preço Real",35)
roi_real = st.number_input("ROI Real (%)",8)
bloqueio = st.selectbox("Bloqueio?",[0,1])

if st.button("Registrar"):
    df_novo = pd.DataFrame([{
        "data":datetime.datetime.now().isoformat(),
        "programa":programa,
        "bonus":bonus_real/100,
        "preco":preco_real,
        "roi":roi_real/100,
        "bloqueio":bloqueio
    }])

    df_novo.to_sql("operacoes",engine,if_exists="append",index=False)
    st.success("Operação registrada.")
