cat > monitor-ar/pages/dashboard_macro.py << 'EOF'
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from pathlib import Path

# Agregar path para imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.api_helpers import obtener_tasas_bcra, obtener_emae

# ============================================
# CONFIGURACIÓN DE PÁGINA
# ============================================

st.set_page_config(
    page_title="Dashboard Macro | Monitor AR",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# ESTILOS PERSONALIZADOS (BLOOMBERG STYLE)
# ============================================

st.markdown("""
<style>
    /* Fondo oscuro estilo terminal */
    .stApp {
        background-color: #0e1117;
    }
    
    /* Títulos */
    h1, h2, h3 {
        color: #00d4ff !important;
        font-family: 'Courier New', monospace;
    }
    
    /* Métricas */
    [data-testid="stMetricValue"] {
        color: #00ff88;
        font-size: 28px;
        font-weight: bold;
    }
    
    /* Contenedores */
    .stContainer {
        background-color: #1a1d29;
        border: 1px solid #2d3748;
        border-radius: 8px;
        padding: 20px;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0a0c10;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #6c757d;
        font-size: 12px;
        padding: 20px;
        margin-top: 50px;
        border-top: 1px solid #2d3748;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# SIDEBAR
# ============================================

with st.sidebar:
    st.markdown("### 📊 Dashboard Macroeconómico")
    st.markdown("---")
    
    st.markdown("#### Fuentes de Datos")
    st.markdown("- 🏦 BCRA API v3.0")
    st.markdown("- 📈 Datos.gob Argentina")
    st.markdown("---")
    
    if st.button("🔄 Actualizar Datos", use_container_width=True):
        st.rerun()

# ============================================
# HEADER
# ============================================

st.title("📊 Dashboard Macroeconómico Argentino")
st.markdown("### Monitor en tiempo real de indicadores clave")
st.markdown("---")

# ============================================
# SECCIÓN 1: TASAS DE INTERÉS (BCRA)
# ============================================

st.subheader("💰 Tasas de Interés — BCRA")

with st.spinner("Cargando datos del BCRA..."):
    tasas_data = obtener_tasas_bcra()

# Crear gráfico de tasas
if any(not df.empty for df in tasas_data.values()):
    fig_tasas = go.Figure()
    
    # TPM
    if not tasas_data['tpm'].empty:
        df_tpm = tasas_data['tpm'].tail(90)  # Últimos 90 días
        fig_tasas.add_trace(go.Scatter(
            x=df_tpm['fecha'],
            y=df_tpm['valor'],
            name='Tasa de Política Monetaria',
            line=dict(color='#00d4ff', width=3)
        ))
    
    # BADLAR
    if not tasas_data['badlar'].empty:
        df_badlar = tasas_data['badlar'].tail(90)
        fig_tasas.add_trace(go.Scatter(
            x=df_badlar['fecha'],
            y=df_badlar['valor'],
            name='BADLAR Privados',
            line=dict(color='#00ff88', width=2)
        ))
    
    # PF USD
    if not tasas_data['pf_usd'].empty:
        df_pf = tasas_data['pf_usd'].tail(90)
        fig_tasas.add_trace(go.Scatter(
            x=df_pf['fecha'],
            y=df_pf['valor'],
            name='Plazo Fijo USD',
            line=dict(color='#ff6b6b', width=2)
        ))
    
    # Layout
    fig_tasas.update_layout(
        template='plotly_dark',
        paper_bgcolor='#0e1117',
        plot_bgcolor='#1a1d29',
        height=450,
        hovermode='x unified',
        xaxis=dict(title='Fecha', gridcolor='#2d3748'),
        yaxis=dict(title='TNA %', gridcolor='#2d3748'),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig_tasas, use_container_width=True)
    
    # Métricas actuales
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if not tasas_data['tpm'].empty:
            ultimo_tpm = tasas_data['tpm'].iloc[-1]['valor']
            st.metric("TPM Actual", f"{ultimo_tpm:.2f}%")
    
    with col2:
        if not tasas_data['badlar'].empty:
            ultimo_badlar = tasas_data['badlar'].iloc[-1]['valor']
            st.metric("BADLAR", f"{ultimo_badlar:.2f}%")
    
    with col3:
        if not tasas_data['pf_usd'].empty:
            ultimo_pf = tasas_data['pf_usd'].iloc[-1]['valor']
            st.metric("PF USD", f"{ultimo_pf:.2f}%")

else:
    st.warning("⚠️ No se pudieron cargar las tasas del BCRA en este momento.")

st.markdown("---")

# ============================================
# SECCIÓN 2: EMAE (ACTIVIDAD ECONÓMICA)
# ============================================

st.subheader("📈 Estimador Mensual de Actividad Económica (EMAE)")

with st.spinner("Cargando datos del EMAE..."):
    df_emae = obtener_emae()

if not df_emae.empty:
    # Últimos 24 meses
    df_emae_reciente = df_emae.tail(24)
    
    fig_emae = go.Figure()
    
    fig_emae.add_trace(go.Scatter(
        x=df_emae_reciente['fecha'],
        y=df_emae_reciente['valor'],
        mode='lines+markers',
        name='EMAE Desestacionalizado',
        line=dict(color='#00d4ff', width=3),
        marker=dict(size=6)
    ))
    
    # Layout
    fig_emae.update_layout(
        template='plotly_dark',
        paper_bgcolor='#0e1117',
        plot_bgcolor='#1a1d29',
        height=450,
        hovermode='x unified',
        xaxis=dict(title='Fecha', gridcolor='#2d3748'),
        yaxis=dict(title='Índice Base 2004=100', gridcolor='#2d3748')
    )
    
    st.plotly_chart(fig_emae, use_container_width=True)
    
    # Métrica actual
    col1, col2, col3 = st.columns(3)
    
    with col1:
        valor_actual = df_emae_reciente.iloc[-1]['valor']
        st.metric("EMAE Actual", f"{valor_actual:.2f}")
    
    with col2:
        if len(df_emae_reciente) >= 2:
            valor_anterior = df_emae_reciente.iloc[-2]['valor']
            variacion = ((valor_actual / valor_anterior - 1) * 100)
            st.metric("Variación Mensual", f"{variacion:+.2f}%")
    
    with col3:
        if len(df_emae_reciente) >= 13:
            valor_anio_anterior = df_emae_reciente.iloc[-13]['valor']
            variacion_anual = ((valor_actual / valor_anio_anterior - 1) * 100)
            st.metric("Variación Interanual", f"{variacion_anual:+.2f}%")

else:
    st.warning("⚠️ No se pudieron cargar los datos del EMAE en este momento.")

# ============================================
# FOOTER
# ============================================

st.markdown("---")
st.markdown("""
<div class="footer">
    <strong>Monitor AR v2.0</strong> | Dashboard Macroeconómico Argentino<br>
    Datos provistos por <strong>BCRA</strong> y <strong>Datos.gob Argentina</strong> | Actualización automática<br>
    Desarrollado con <strong>Streamlit + Plotly</strong>
</div>
""", unsafe_allow_html=True)
EOF
