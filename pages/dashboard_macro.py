import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from utils.api_helpers import obtener_tasas_bcra, obtener_emae

st.set_page_config(
    page_title="Monitor AR - Dashboard Macro",
    page_icon="📊",
    layout="wide"
)

# Estilo oscuro tipo terminal Bloomberg
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #00ff41;
    }
    h1, h2, h3 {
        color: #00ff41;
        font-family: 'Courier New', monospace;
    }
    .metric-card {
        background-color: #1a1d23;
        border-left: 3px solid #00ff41;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .cache-badge {
        background-color: #ff9800;
        color: #000;
        padding: 2px 8px;
        border-radius: 3px;
        font-size: 12px;
        font-weight: bold;
        margin-left: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 Monitor AR - Dashboard Macroeconómico")
st.markdown("---")

# Obtener datos
with st.spinner("Cargando datos de tasas BCRA..."):
    tasas_bcra = obtener_tasas_bcra()

with st.spinner("Cargando datos de EMAE..."):
    emae_data = obtener_emae()

# === SECCIÓN: TASAS BCRA ===
st.header("💰 Tasas de Interés (BCRA)")

col1, col2, col3 = st.columns(3)

# TPM
with col1:
    tpm_info = tasas_bcra.get('TPM', {})
    df_tpm = tpm_info.get('data')
    cache_tpm = tpm_info.get('desde_cache', False)
    
    titulo_tpm = "Tasa de Política Monetaria (TPM)"
    if cache_tpm:
        titulo_tpm += ' <span class="cache-badge">CACHE</span>'
    
    st.markdown(f"### {titulo_tpm}", unsafe_allow_html=True)
    
    if df_tpm is not None and not df_tpm.empty:
        ultimo_valor = df_tpm.iloc[-1]['valor']
        ultima_fecha = df_tpm.iloc[-1]['fecha'].strftime('%Y-%m-%d')
        
        st.metric(
            label=f"Última tasa ({ultima_fecha})",
            value=f"{ultimo_valor:.2f}%"
        )
        
        fig_tpm = go.Figure()
        fig_tpm.add_trace(go.Scatter(
            x=df_tpm['fecha'],
            y=df_tpm['valor'],
            mode='lines',
            name='TPM',
            line=dict(color='#00ff41', width=2)
        ))
        fig_tpm.update_layout(
            template='plotly_dark',
            height=300,
            margin=dict(l=0, r=0, t=30, b=0),
            showlegend=False,
            paper_bgcolor='#0e1117',
            plot_bgcolor='#1a1d23'
        )
        st.plotly_chart(fig_tpm, use_container_width=True)
    else:
        st.warning("⚠️ No hay datos disponibles para TPM")

# BADLAR
with col2:
    badlar_info = tasas_bcra.get('BADLAR', {})
    df_badlar = badlar_info.get('data')
    cache_badlar = badlar_info.get('desde_cache', False)
    
    titulo_badlar = "BADLAR"
    if cache_badlar:
        titulo_badlar += ' <span class="cache-badge">CACHE</span>'
    
    st.markdown(f"### {titulo_badlar}", unsafe_allow_html=True)
    
    if df_badlar is not None and not df_badlar.empty:
        ultimo_valor = df_badlar.iloc[-1]['valor']
        ultima_fecha = df_badlar.iloc[-1]['fecha'].strftime('%Y-%m-%d')
        
        st.metric(
            label=f"Última tasa ({ultima_fecha})",
            value=f"{ultimo_valor:.2f}%"
        )
        
        fig_badlar = go.Figure()
        fig_badlar.add_trace(go.Scatter(
            x=df_badlar['fecha'],
            y=df_badlar['valor'],
            mode='lines',
            name='BADLAR',
            line=dict(color='#ffa500', width=2)
        ))
        fig_badlar.update_layout(
            template='plotly_dark',
            height=300,
            margin=dict(l=0, r=0, t=30, b=0),
            showlegend=False,
            paper_bgcolor='#0e1117',
            plot_bgcolor='#1a1d23'
        )
        st.plotly_chart(fig_badlar, use_container_width=True)
    else:
        st.warning("⚠️ No hay datos disponibles para BADLAR")

# Plazo Fijo USD
with col3:
    pf_usd_info = tasas_bcra.get('PF_USD', {})
    df_pf_usd = pf_usd_info.get('data')
    cache_pf_usd = pf_usd_info.get('desde_cache', False)
    
    titulo_pf = "Plazo Fijo USD"
    if cache_pf_usd:
        titulo_pf += ' <span class="cache-badge">CACHE</span>'
    
    st.markdown(f"### {titulo_pf}", unsafe_allow_html=True)
    
    if df_pf_usd is not None and not df_pf_usd.empty:
        ultimo_valor = df_pf_usd.iloc[-1]['valor']
        ultima_fecha = df_pf_usd.iloc[-1]['fecha'].strftime('%Y-%m-%d')
        
        st.metric(
            label=f"Última tasa ({ultima_fecha})",
            value=f"{ultimo_valor:.2f}%"
        )
        
        fig_pf = go.Figure()
        fig_pf.add_trace(go.Scatter(
            x=df_pf_usd['fecha'],
            y=df_pf_usd['valor'],
            mode='lines',
            name='PF USD',
            line=dict(color='#00bfff', width=2)
        ))
        fig_pf.update_layout(
            template='plotly_dark',
            height=300,
            margin=dict(l=0, r=0, t=30, b=0),
            showlegend=False,
            paper_bgcolor='#0e1117',
            plot_bgcolor='#1a1d23'
        )
        st.plotly_chart(fig_pf, use_container_width=True)
    else:
        st.warning("⚠️ No hay datos disponibles para Plazo Fijo USD")

st.markdown("---")

# === SECCIÓN: EMAE ===
st.header("📈 Actividad Económica (EMAE)")

df_emae = emae_data.get('data')
cache_emae = emae_data.get('desde_cache', False)

titulo_emae = "Estimador Mensual de Actividad Económica"
if cache_emae:
    titulo_emae += ' <span class="cache-badge">CACHE</span>'

st.markdown(f"### {titulo_emae}", unsafe_allow_html=True)

if df_emae is not None and not df_emae.empty:
    ultimo_valor = df_emae.iloc[-1]['valor']
    ultima_fecha = df_emae.iloc[-1]['fecha'].strftime('%Y-%m-%d')
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.metric(
            label=f"Último valor ({ultima_fecha})",
            value=f"{ultimo_valor:.2f}"
        )
        st.caption(f"Base 2004 = 100")
        st.caption(f"Total de observaciones: {len(df_emae)}")
    
    with col2:
        fig_emae = go.Figure()
        fig_emae.add_trace(go.Scatter(
            x=df_emae['fecha'],
            y=df_emae['valor'],
            mode='lines',
            name='EMAE',
            line=dict(color='#00ff41', width=2),
            fill='tozeroy',
            fillcolor='rgba(0, 255, 65, 0.1)'
        ))
        fig_emae.update_layout(
            template='plotly_dark',
            height=400,
            margin=dict(l=0, r=0, t=30, b=0),
            showlegend=False,
            paper_bgcolor='#0e1117',
            plot_bgcolor='#1a1d23',
            yaxis_title="Índice (base 2004=100)"
        )
        st.plotly_chart(fig_emae, use_container_width=True)
else:
    st.warning("⚠️ No hay datos disponibles para EMAE. Verifique su conexión o intente más tarde.")

# Footer
st.markdown("---")
st.caption("🔄 Los datos se actualizan automáticamente desde fuentes oficiales (BCRA, datos.gob.ar)")
if any([cache_tpm, cache_badlar, cache_pf_usd, cache_emae]):
    st.caption("⚠️ Algunos datos provienen de caché local debido a problemas de conectividad")
