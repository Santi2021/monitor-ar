# app.py - Monitor AR Dashboard Macroeconómico
# Sprint 2: Integración BCRA v3.0 + Datos.gob EMAE

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 CONFIGURACIÓN DE PÁGINA Y ESTILO BLOOMBERG
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Monitor AR | Dashboard Macro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados tipo Bloomberg Terminal
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;700&display=swap');
    
    /* Fondo principal oscuro */
    .stApp {
        background-color: #0a0a0a;
        color: #dddddd;
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #111111;
        border-right: 1px solid #2E8BFF;
    }
    
    [data-testid="stSidebar"] .css-1d391kg {
        color: #dddddd;
    }
    
    /* Títulos */
    h1, h2, h3 {
        font-family: 'JetBrains Mono', monospace;
        color: #2E8BFF;
        font-weight: 700;
        letter-spacing: 1px;
    }
    
    /* Cards personalizadas */
    .metric-card {
        background: linear-gradient(135deg, #1a1a1a 0%, #0d0d0d 100%);
        border: 1px solid #2E8BFF;
        border-radius: 8px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 12px rgba(46, 139, 255, 0.15);
    }
    
    .metric-title {
        font-size: 0.85rem;
        color: #888888;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 8px;
    }
    
    .metric-value {
        font-size: 2rem;
        color: #2E8BFF;
        font-weight: 700;
    }
    
    /* Textos informativos */
    .info-text {
        color: #999999;
        font-size: 0.8rem;
        font-style: italic;
        margin-top: 8px;
    }
    
    /* Alertas */
    .stAlert {
        background-color: #1a1a1a;
        border-left: 3px solid #ff6b6b;
        color: #dddddd;
    }
    
    /* Botones */
    .stButton>button {
        background-color: #2E8BFF;
        color: #0a0a0a;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        border: none;
        border-radius: 4px;
        padding: 10px 24px;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #1a6fd9;
        box-shadow: 0 0 20px rgba(46, 139, 255, 0.5);
    }
    
    /* Reducir márgenes por defecto de Streamlit */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# 🔌 MÓDULO: BCRA API v3.0
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_monetarias():
    """
    Obtiene series monetarias del BCRA v3.0
    IDs curados: Tasas de interés y política monetaria
    """
    BASE_URL = "https://api.bcra.gob.ar/estadisticas/v3.0"
    
    # Diccionario de series monetarias clave
    SERIES_MONETARIAS = {
        160: "Tasa de Política Monetaria (TNA %)",
        145: "BADLAR Privados (TNA %)",
        132: "Tasa LELIQ 28 días (%)"
    }
    
    resultados = {}
    fecha_fin = datetime.now().strftime('%Y-%m-%d')
    fecha_inicio = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    for id_serie, nombre in SERIES_MONETARIAS.items():
        try:
            url = f"{BASE_URL}/Datos/Monetarios/{id_serie}/{fecha_inicio}/{fecha_fin}"
            response = requests.get(url, verify=False, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    df = pd.DataFrame(data['results'])
                    df['fecha'] = pd.to_datetime(df['fecha'])
                    df = df.sort_values('fecha')
                    df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
                    
                    resultados[nombre] = df[['fecha', 'valor']].dropna()
                    
        except Exception as e:
            st.warning(f"⚠️ Error obteniendo {nombre}: {str(e)}")
            continue
    
    return resultados

# ═══════════════════════════════════════════════════════════════════════════════
# 🔌 MÓDULO: DATOS.GOB EMAE
# ═══════════════════════════════════════════════════════════════════════════════

def get_emae():
    """
    Obtiene EMAE desestacionalizado desde Datos.gob (API Series)
    Con fallback a CSV si la API falla
    """
    # ID oficial de EMAE desestacionalizado
    EMAE_ID = "11.3_VMATC_2004_M_36"
    API_URL = f"https://apis.datos.gob.ar/series/api/series/?ids={EMAE_ID}&format=json&limit=5000"
    
    try:
        # Intento 1: API Series de Datos.gob
        response = requests.get(API_URL, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data and len(data['data']) > 0:
                df = pd.DataFrame(data['data'], columns=['fecha', 'valor'])
                df['fecha'] = pd.to_datetime(df['fecha'])
                df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
                df = df.dropna().sort_values('fecha')
                
                return df
        
        # Intento 2: Fallback a CSV directo
        CSV_URL = "https://infra.datos.gob.ar/catalog/modernizacion/dataset/1/distribution/1.2/download/emae-valores-trimestrales-base-1993-100.csv"
        df = pd.read_csv(CSV_URL)
        
        # Buscar columna de EMAE desestacionalizado
        columnas_posibles = [col for col in df.columns if 'desestacionalizado' in col.lower()]
        
        if columnas_posibles:
            df_limpio = df[['indice_tiempo', columnas_posibles[0]]].copy()
            df_limpio.columns = ['fecha', 'valor']
            df_limpio['fecha'] = pd.to_datetime(df_limpio['fecha'])
            df_limpio['valor'] = pd.to_numeric(df_limpio['valor'], errors='coerce')
            
            return df_limpio.dropna().sort_values('fecha')
        
    except Exception as e:
        st.error(f"⚠️ No se pudo obtener EMAE: {str(e)}")
        return None
    
    return None

# ═══════════════════════════════════════════════════════════════════════════════
# 📊 FUNCIÓN: GRÁFICO PLOTLY ESTILO BLOOMBERG
# ═══════════════════════════════════════════════════════════════════════════════

def crear_grafico_bloomberg(df, titulo, y_label, color="#2E8BFF"):
    """
    Genera gráfico interactivo con estética Bloomberg Terminal
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['fecha'],
        y=df['valor'],
        mode='lines',
        line=dict(color=color, width=2),
        fill='tozeroy',
        fillcolor=f'rgba(46, 139, 255, 0.1)',
        hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Valor: %{y:.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        template="plotly_dark",
        title=dict(
            text=titulo,
            font=dict(size=18, color='#2E8BFF', family='JetBrains Mono'),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title="Fecha",
            gridcolor='#1a1a1a',
            showgrid=True
        ),
        yaxis=dict(
            title=y_label,
            gridcolor='#1a1a1a',
            showgrid=True
        ),
        plot_bgcolor='#0a0a0a',
        paper_bgcolor='#0a0a0a',
        font=dict(color='#dddddd', family='JetBrains Mono'),
        hovermode='x unified',
        margin=dict(l=60, r=40, t=80, b=60)
    )
    
    return fig

# ═══════════════════════════════════════════════════════════════════════════════
# 🧭 SIDEBAR NAVEGACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

st.sidebar.markdown("""
<div style='text-align: center; padding: 20px 0;'>
    <h1 style='color: #2E8BFF; margin: 0;'>📊</h1>
    <h2 style='color: #2E8BFF; margin: 0; font-size: 1.5rem;'>MONITOR AR</h2>
    <p style='color: #666; font-size: 0.75rem; margin-top: 5px;'>Dashboard Macroeconómico</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")

# Selector de sección
seccion = st.sidebar.radio(
    "NAVEGACIÓN",
    ["🏠 Inicio", "📊 Dashboard Macro", "💹 Mercado"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")

st.sidebar.markdown("""
<div style='padding: 15px; background-color: #1a1a1a; border-radius: 5px; border-left: 3px solid #2E8BFF;'>
    <p style='font-size: 0.7rem; color: #888; margin: 0;'>
        <b>Fuentes de datos:</b><br>
        • BCRA API v3.0<br>
        • Datos.gob Argentina<br>
        • Actualización en tiempo real
    </p>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# 🏠 SECCIÓN: INICIO
# ═══════════════════════════════════════════════════════════════════════════════

if seccion == "🏠 Inicio":
    
    st.markdown("<h1 style='text-align: center;'>🇦🇷 MONITOR AR</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888; font-size: 1.1rem;'>Dashboard Macroeconómico Profesional</p>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class='metric-card'>
            <div class='metric-title'>📈 Datos en Tiempo Real</div>
            <p style='color: #dddddd; font-size: 0.9rem;'>
                Integración directa con APIs oficiales del BCRA y Datos.gob Argentina
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='metric-card'>
            <div class='metric-title'>💼 Interfaz Profesional</div>
            <p style='color: #dddddd; font-size: 0.9rem;'>
                Diseño inspirado en terminales Bloomberg para análisis efectivo
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class='metric-card'>
            <div class='metric-title'>📊 Indicadores Clave</div>
            <p style='color: #dddddd; font-size: 0.9rem;'>
                Seguimiento de tasas, política monetaria y actividad económica
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    st.markdown("### 🎯 Características Principales")
    
    st.markdown("""
    <div style='background-color: #1a1a1a; padding: 20px; border-radius: 8px; border-left: 3px solid #2E8BFF;'>
        <ul style='color: #dddddd; font-size: 0.95rem;'>
            <li><b>Series Monetarias BCRA:</b> Tasas de política monetaria, BADLAR, LELIQ</li>
            <li><b>Indicadores de Actividad:</b> EMAE desestacionalizado</li>
            <li><b>Visualizaciones Interactivas:</b> Gráficos Plotly con zoom y tooltips</li>
            <li><b>Actualizaciones Automáticas:</b> Conexión directa con fuentes oficiales</li>
            <li><b>Diseño Responsivo:</b> Optimizado para desktop y mobile</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        if st.button("🚀 IR AL DASHBOARD", use_container_width=True):
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# 📊 SECCIÓN: DASHBOARD MACRO
# ═══════════════════════════════════════════════════════════════════════════════

elif seccion == "📊 Dashboard Macro":
    
    st.markdown("<h1>📊 Dashboard Macroeconómico</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #888;'>Indicadores clave de la economía argentina en tiempo real</p>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ─────────────────────────────────────────────────────────────────────────
    # SECCIÓN 1: TASAS MONETARIAS BCRA
    # ─────────────────────────────────────────────────────────────────────────
    
    st.markdown("### 🏦 Tasas de Interés y Política Monetaria")
    
    with st.spinner("📡 Conectando con BCRA API v3.0..."):
        series_bcra = fetch_monetarias()
    
    if series_bcra:
        # Mostrar último valor de cada tasa en tarjetas
        cols_tasas = st.columns(len(series_bcra))
        
        for idx, (nombre, df) in enumerate(series_bcra.items()):
            if not df.empty:
                ultimo_valor = df.iloc[-1]['valor']
                ultima_fecha = df.iloc[-1]['fecha'].strftime('%d/%m/%Y')
                
                with cols_tasas[idx]:
                    st.markdown(f"""
                    <div class='metric-card'>
                        <div class='metric-title'>{nombre.split('(')[0].strip()}</div>
                        <div class='metric-value'>{ultimo_valor:.2f}%</div>
                        <div class='info-text'>Actualizado: {ultima_fecha}</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Gráfico integrado de todas las tasas
        fig_tasas = go.Figure()
        
        colores = ['#2E8BFF', '#FF6B6B', '#4ECDC4']
        
        for idx, (nombre, df) in enumerate(series_bcra.items()):
            if not df.empty:
                fig_tasas.add_trace(go.Scatter(
                    x=df['fecha'],
                    y=df['valor'],
                    mode='lines',
                    name=nombre.split('(')[0].strip(),
                    line=dict(color=colores[idx % len(colores)], width=2),
                    hovertemplate='<b>%{x|%Y-%m-%d}</b><br>%{y:.2f}%<extra></extra>'
                ))
        
        fig_tasas.update_layout(
            template="plotly_dark",
            title=dict(
                text="Evolución de Tasas de Interés",
                font=dict(size=18, color='#2E8BFF', family='JetBrains Mono'),
                x=0.5,
                xanchor='center'
            ),
            xaxis=dict(title="Fecha", gridcolor='#1a1a1a', showgrid=True),
            yaxis=dict(title="Tasa (%)", gridcolor='#1a1a1a', showgrid=True),
            plot_bgcolor='#0a0a0a',
            paper_bgcolor='#0a0a0a',
            font=dict(color='#dddddd', family='JetBrains Mono'),
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            ),
            height=500,
            margin=dict(l=60, r=40, t=100, b=60)
        )
        
        st.plotly_chart(fig_tasas, use_container_width=True)
        
        st.markdown("""
        <div class='info-text' style='text-align: center;'>
            Fuente: Banco Central de la República Argentina (BCRA) - API v3.0 Estadísticas | 
            Las tasas se expresan en TNA (Tasa Nominal Anual)
        </div>
        """, unsafe_allow_html=True)
        
    else:
        st.error("⚠️ Series monetarias no disponibles en este momento. Verifique conectividad con BCRA.")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # ─────────────────────────────────────────────────────────────────────────
    # SECCIÓN 2: EMAE - ACTIVIDAD ECONÓMICA
    # ─────────────────────────────────────────────────────────────────────────
    
    st.markdown("### 📈 Estimador Mensual de Actividad Económica (EMAE)")
    
    with st.spinner("📡 Conectando con Datos.gob Argentina..."):
        df_emae = get_emae()
    
    if df_emae is not None and not df_emae.empty:
        
        # Tarjeta con último valor
        ultimo_emae = df_emae.iloc[-1]['valor']
        fecha_emae = df_emae.iloc[-1]['fecha'].strftime('%m/%Y')
        
        # Calcular variación interanual
        try:
            hace_12_meses = df_emae.iloc[-13]['valor']
            var_interanual = ((ultimo_emae - hace_12_meses) / hace_12_meses) * 100
            var_color = "#4ECDC4" if var_interanual >= 0 else "#FF6B6B"
            var_simbolo = "▲" if var_interanual >= 0 else "▼"
        except:
            var_interanual = None
            var_color = "#888"
            var_simbolo = "—"
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>Nivel EMAE (Base 2004=100)</div>
                <div class='metric-value'>{ultimo_emae:.2f}</div>
                <div class='info-text'>Período: {fecha_emae}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if var_interanual is not None:
                st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-title'>Variación Interanual</div>
                    <div class='metric-value' style='color: {var_color};'>{var_simbolo} {var_interanual:+.2f}%</div>
                    <div class='info-text'>vs mismo mes año anterior</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class='metric-card'>
                    <div class='metric-title'>Variación Interanual</div>
                    <div class='metric-value' style='color: #888;'>— N/D</div>
                    <div class='info-text'>Datos insuficientes</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Gráfico EMAE
        fig_emae = crear_grafico_bloomberg(
            df_emae,
            "Evolución del EMAE Desestacionalizado",
            "Índice (Base 2004=100)",
            "#2E8BFF"
        )
        
        fig_emae.update_layout(height=500)
        
        st.plotly_chart(fig_emae, use_container_width=True)
        
        st.markdown("""
        <div class='info-text' style='text-align: center;'>
            Fuente: INDEC vía Datos.gob Argentina | 
            Serie desestacionalizada Base 2004=100 | 
            Actualización mensual con rezago de ~30 días
        </div>
        """, unsafe_allow_html=True)
        
    else:
        st.error("⚠️ EMAE no disponible en este momento. Endpoint fuera de servicio o sin datos.")

# ═══════════════════════════════════════════════════════════════════════════════
# 💹 SECCIÓN: MERCADO (Placeholder)
# ═══════════════════════════════════════════════════════════════════════════════

elif seccion == "💹 Mercado":
    
    st.markdown("<h1>💹 Mercado Financiero</h1>", unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style='text-align: center; padding: 60px 20px; background-color: #1a1a1a; border-radius: 10px; border: 2px dashed #2E8BFF;'>
        <h2 style='color: #2E8BFF; margin-bottom: 20px;'>🚧 Sección en Desarrollo</h2>
        <p style='color: #888; font-size: 1.1rem;'>
            Esta funcionalidad estará disponible en el próximo sprint.<br><br>
            <b>Próximamente:</b><br>
            • Cotizaciones en tiempo real<br>
            • Bonos soberanos<br>
            • Tipo de cambio (oficial y MEP)<br>
            • Índices bursátiles
        </p>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# 🔚 FOOTER
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("<br><br>", unsafe_allow_html=True)

st.markdown("""
<div style='text-align: center; padding: 20px; color: #555; font-size: 0.75rem; border-top: 1px solid #222;'>
    Monitor AR v2.0 | Dashboard Macroeconómico Argentino<br>
    Datos provistos por BCRA y Datos.gob Argentina | Actualización automática<br>
    Desarrollado con Streamlit + Plotly
</div>
""", unsafe_allow_html=True)
