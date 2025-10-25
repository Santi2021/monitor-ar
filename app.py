import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import urllib3
from anthropic import Anthropic

# Desactivar warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
# CONFIGURACIÓN DE SERIES (CURADURÍA)
# ============================================================================
CONFIG_SERIES = [
    {
        "source": "BCRA",
        "name": "Reservas Internacionales",
        "id_or_resource": "1",  # ID real de Reservas en API BCRA v4
        "endpoint_url": "https://api.bcra.gob.ar/estadisticas/v4.0/DatosVariable",
        "params": {},
        "date_field": "fecha",
        "value_field": "valor",
        "freq": "diaria",
        "unit": "USD millones",
        "notes": "Reservas Internacionales del BCRA en millones de dólares"
    },
    {
        "source": "CKAN",
        "name": "IPC Nivel General - Variación Mensual",
        "id_or_resource": "145c52ee-11f3-4194-a84e-7db3e88a53c1",  # Resource ID real de IPC
        "endpoint_url": "https://datos.gob.ar/api/3/action/datastore_search",
        "params": {"limit": 500},
        "date_field": "indice_tiempo",
        "value_field": "ipc_ng_variacion_mensual",
        "freq": "mensual",
        "unit": "%",
        "notes": "Variación mensual del IPC Nivel General (INDEC)"
    }
]

# ============================================================================
# ESTILOS CSS (BLOOMBERG-INSPIRED)
# ============================================================================
def apply_custom_styles():
    st.markdown("""
    <style>
    /* Importar fuente */
    @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600;700&display=swap');
    
    /* Variables de color */
    :root {
        --bg-main: #1E1E1E;
        --bg-card: #2A2A2A;
        --text-primary: #E8E8E8;
        --text-secondary: #A0A0A0;
        --accent: #0077FF;
        --border: #333333;
        --success: #00CC66;
        --error: #FF3333;
    }
    
    /* Fondo principal */
    .stApp {
        background-color: var(--bg-main);
        font-family: 'Segoe UI', Arial, sans-serif;
        color: var(--text-primary);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: var(--bg-main);
        border-right: 1px solid var(--border);
    }
    
    [data-testid="stSidebar"] .css-1d391kg {
        color: var(--text-secondary);
    }
    
    /* Títulos */
    h1, h2, h3 {
        color: var(--text-primary) !important;
        font-weight: 700;
    }
    
    h1 {
        font-size: 26px !important;
    }
    
    h2 {
        font-size: 22px !important;
    }
    
    h3 {
        font-size: 18px !important;
    }
    
    /* Tarjetas */
    .card {
        background-color: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 4px;
        padding: 20px;
        margin: 10px 0;
        transition: all 0.3s ease;
    }
    
    .card:hover {
        border-color: var(--accent);
        box-shadow: 0 0 10px rgba(0, 119, 255, 0.3);
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 3px;
        font-size: 12px;
        font-weight: 600;
        margin: 0 5px;
    }
    
    .badge-bcra {
        background-color: var(--accent);
        color: white;
    }
    
    .badge-ckan {
        background-color: var(--success);
        color: white;
    }
    
    .badge-pendiente {
        background-color: #FF9500;
        color: white;
    }
    
    /* Botones */
    .stButton>button {
        background-color: var(--accent);
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #005BB5;
        box-shadow: 0 2px 8px rgba(0, 119, 255, 0.4);
    }
    
    /* Métricas */
    [data-testid="stMetricValue"] {
        color: var(--accent) !important;
        font-size: 28px !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
        font-size: 14px !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 4px;
        color: var(--text-primary) !important;
    }
    
    /* Texto */
    p, span, div {
        color: var(--text-primary);
    }
    
    /* Tablas */
    .dataframe {
        color: var(--text-primary) !important;
        background-color: var(--bg-card) !important;
    }
    
    /* Header custom */
    .main-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 0;
        border-bottom: 2px solid var(--accent);
        margin-bottom: 30px;
    }
    
    .main-header h1 {
        margin: 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .version {
        color: var(--text-secondary);
        font-size: 14px;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-color: var(--accent) !important;
    }
    
    /* Warnings y errores */
    .stAlert {
        background-color: var(--bg-card);
        border-left: 4px solid var(--accent);
        color: var(--text-primary);
    }
    
    /* Download button */
    .download-btn {
        background-color: var(--success) !important;
    }
    
    .download-btn:hover {
        background-color: #00994D !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# UTILIDADES DE RED
# ============================================================================

def fetch_bcra_series(id_serie, n=1000):
    """
    Obtiene serie de BCRA API v4.0
    """
    try:
        url = f"https://api.bcra.gob.ar/estadisticas/v4.0/DatosVariable/{id_serie}/{n}"
        response = requests.get(url, timeout=15, verify=False)
        response.raise_for_status()
        data = response.json()
        
        if 'results' in data:
            df = pd.DataFrame(data['results'])
            return df, None
        else:
            return None, "Formato de respuesta inesperado"
    except requests.exceptions.SSLError:
        return None, "Error SSL - BCRA API (común en ambientes locales)"
    except requests.exceptions.Timeout:
        return None, "Timeout - API BCRA no responde"
    except Exception as e:
        return None, f"Error: {str(e)}"

def fetch_ckan_series(resource_id, limit=500):
    """
    Obtiene serie de datos.gob.ar (CKAN)
    """
    try:
        url = "https://datos.gob.ar/api/3/action/datastore_search"
        params = {
            "resource_id": resource_id,
            "limit": limit
        }
        response = requests.get(url, params=params, timeout=15, verify=False)
        response.raise_for_status()
        data = response.json()
        
        if data.get('success') and 'result' in data:
            records = data['result']['records']
            df = pd.DataFrame(records)
            return df, None
        else:
            return None, "Formato de respuesta inesperado"
    except Exception as e:
        return None, f"Error: {str(e)}"

def detect_timeseries(df, date_field=None, value_field=None):
    """
    Detecta y normaliza serie temporal
    """
    if df is None or df.empty:
        return None
    
    # Usar campos explícitos si están definidos
    if date_field and value_field:
        if date_field in df.columns and value_field in df.columns:
            try:
                df_clean = df[[date_field, value_field]].copy()
                df_clean[date_field] = pd.to_datetime(df_clean[date_field], errors='coerce')
                df_clean = df_clean.dropna()
                df_clean = df_clean.sort_values(date_field)
                df_clean.columns = ['fecha', 'valor']
                df_clean['valor'] = pd.to_numeric(df_clean['valor'], errors='coerce')
                return df_clean
            except:
                pass
    
    # Heurística fallback
    date_cols = [col for col in df.columns if 'fecha' in col.lower() or 'date' in col.lower() or 'tiempo' in col.lower()]
    value_cols = [col for col in df.columns if 'valor' in col.lower() or 'value' in col.lower() or 'variacion' in col.lower()]
    
    if date_cols and value_cols:
        try:
            df_clean = df[[date_cols[0], value_cols[0]]].copy()
            df_clean.columns = ['fecha', 'valor']
            df_clean['fecha'] = pd.to_datetime(df_clean['fecha'], errors='coerce')
            df_clean['valor'] = pd.to_numeric(df_clean['valor'], errors='coerce')
            df_clean = df_clean.dropna()
            df_clean = df_clean.sort_values('fecha')
            return df_clean
        except:
            pass
    
    return None

# ============================================================================
# COMPONENTES UI
# ============================================================================

def render_header():
    """Header principal estilo Bloomberg"""
    st.markdown("""
    <div class="main-header">
        <h1>🚀 MONITOR AR</h1>
        <span class="version">v1.0</span>
    </div>
    """, unsafe_allow_html=True)

def render_serie_card(serie_config, index):
    """Renderiza tarjeta individual de serie"""
    
    # Verificar si la serie está completa
    is_pending = not serie_config.get('id_or_resource') or not serie_config.get('name')
    
    st.markdown(f"""
    <div class="card">
        <h3>{serie_config.get('name', 'Sin nombre')}
            <span class="badge badge-{serie_config.get('source', '').lower()}">{serie_config.get('source', 'N/A')}</span>
            {'<span class="badge badge-pendiente">PENDIENTE</span>' if is_pending else ''}
        </h3>
        <p style="color: var(--text-secondary); font-size: 14px;">{serie_config.get('notes', '')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if is_pending:
        st.warning("⚠️ Configuración incompleta - pendiente de carga")
        return
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("🔄 Actualizar", key=f"refresh_{index}"):
            st.rerun()
    
    # Fetch data
    with st.spinner("Cargando datos..."):
        if serie_config['source'] == 'BCRA':
            df_raw, error = fetch_bcra_series(serie_config['id_or_resource'])
        elif serie_config['source'] == 'CKAN':
            df_raw, error = fetch_ckan_series(serie_config['id_or_resource'], 
                                             serie_config.get('params', {}).get('limit', 500))
        else:
            df_raw, error = None, "Fuente no soportada"
        
        if error:
            st.warning(f"⚠️ {error}")
            return
        
        if df_raw is None or df_raw.empty:
            st.warning("⚠️ No se obtuvieron datos")
            return
        
        # Detectar serie temporal
        df_ts = detect_timeseries(df_raw, 
                                  serie_config.get('date_field'), 
                                  serie_config.get('value_field'))
        
        if df_ts is None or df_ts.empty:
            st.warning("⚠️ No se pudo procesar como serie temporal")
            with st.expander("📄 Ver datos crudos"):
                st.dataframe(df_raw.head(20))
            return
        
        # Mostrar métricas
        ultimo_valor = df_ts['valor'].iloc[-1]
        ultima_fecha = df_ts['fecha'].iloc[-1]
        
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Último valor", f"{ultimo_valor:.2f} {serie_config.get('unit', '')}")
        with col_m2:
            st.metric("Fecha", ultima_fecha.strftime("%Y-%m-%d"))
        with col_m3:
            st.metric("Registros", len(df_ts))
        
        # Tabs: Gráfico / Tabla
        tab1, tab2 = st.tabs(["📈 Gráfico", "📊 Tabla"])
        
        with tab1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_ts['fecha'],
                y=df_ts['valor'],
                mode='lines',
                name=serie_config['name'],
                line=dict(color='#0077FF', width=2)
            ))
            
            fig.update_layout(
                plot_bgcolor='#1E1E1E',
                paper_bgcolor='#1E1E1E',
                font=dict(color='#E8E8E8'),
                xaxis=dict(
                    gridcolor='#333333',
                    showgrid=True
                ),
                yaxis=dict(
                    gridcolor='#333333',
                    showgrid=True,
                    title=serie_config.get('unit', '')
                ),
                hovermode='x unified',
                margin=dict(l=40, r=40, t=40, b=40)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.dataframe(df_ts.tail(50), use_container_width=True)
            
            # Botón de descarga
            csv = df_ts.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Exportar CSV",
                data=csv,
                file_name=f"{serie_config['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key=f"download_{index}"
            )
        
        # Expander con JSON crudo
        with st.expander("🔍 Ver JSON crudo (primeros 5 registros)"):
            st.json(df_raw.head(5).to_dict(orient='records'))

# ============================================================================
# PÁGINAS
# ============================================================================

def page_inicio():
    """Página de inicio"""
    render_header()
    
    st.markdown("""
    ## Bienvenido a Monitor AR
    
    **Monitor AR** es tu panel de control para seguimiento de variables macroeconómicas argentinas.
    
    ### 📊 Funcionalidades
    
    - **Dashboard Macro**: Series curadas de BCRA e INDEC
    - **Mercado**: Visualización de activos vía TradingView
    - **Asistente IA**: Análisis y consultas con Claude
    
    ### 🚀 Comenzar
    
    Selecciona una sección en el menú lateral para explorar los datos.
    
    ---
    
    *Datos actualizados desde fuentes oficiales: BCRA API v4.0 y datos.gob.ar*
    """)

def page_dashboard():
    """Dashboard de series macroeconómicas"""
    render_header()
    
    st.title("📊 Dashboard Macro")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**{len(CONFIG_SERIES)}** series configuradas")
    with col2:
        if st.button("🔄 Actualizar todas"):
            st.rerun()
    
    st.markdown("---")
    
    # Renderizar cada serie
    for idx, serie in enumerate(CONFIG_SERIES):
        render_serie_card(serie, idx)
        st.markdown("<br>", unsafe_allow_html=True)

def page_mercado():
    """Página de mercado con TradingView"""
    render_header()
    
    st.title("📈 Mercado")
    
    st.markdown("""
    Visualización de activos financieros en tiempo real mediante TradingView.
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        ticker = st.text_input("Símbolo (ticker)", value="SPX", help="Ejemplos: SPX, GLD, BTCUSD, GGAL.BA")
    
    with col2:
        interval = st.selectbox("Intervalo", ["D", "W", "M", "60", "15"], index=0)
    
    # Embed de TradingView
    tradingview_html = f"""
    <!-- TradingView Widget BEGIN -->
    <div class="tradingview-widget-container" style="height:600px;width:100%">
      <div id="tradingview_chart" style="height:calc(100% - 32px);width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
      {{
        "width": "100%",
        "height": 568,
        "symbol": "{ticker}",
        "interval": "{interval}",
        "timezone": "America/Argentina/Buenos_Aires",
        "theme": "dark",
        "style": "1",
        "locale": "es",
        "toolbar_bg": "#1E1E1E",
        "enable_publishing": false,
        "backgroundColor": "#1E1E1E",
        "gridColor": "#333333",
        "hide_top_toolbar": false,
        "hide_legend": false,
        "save_image": true,
        "container_id": "tradingview_chart"
      }}
      );
      </script>
    </div>
    <!-- TradingView Widget END -->
    """
    
    st.components.v1.html(tradingview_html, height=600)
    
    st.markdown("---")
    st.markdown("""
    **Tickers populares:**
    - **SPX**: S&P 500
    - **GLD**: Oro
    - **BTCUSD**: Bitcoin
    - **GGAL.BA**: Grupo Financiero Galicia (BYMA)
    - **YPFD.BA**: YPF (BYMA)
    - **DXY**: Índice Dólar
    """)

def page_asistente():
    """Asistente IA con Claude"""
    render_header()
    
    st.title("🤖 Asistente IA")
    
    st.markdown("""
    Realiza consultas sobre las series cargadas o análisis macroeconómico general.
    """)
    
    # API Key
    api_key = st.text_input("API Key de Anthropic", type="password", 
                            help="Ingresa tu API key de Claude")
    
    if not api_key:
        st.info("👆 Ingresa tu API key de Anthropic para comenzar")
        return
    
    # Inicializar historial
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Mostrar historial
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Input del usuario
    if prompt := st.chat_input("Escribe tu consulta..."):
        # Agregar mensaje del usuario
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Contexto con series configuradas
        context = "Series disponibles:\n"
        for s in CONFIG_SERIES:
            context += f"- {s['name']} ({s['source']}, {s['freq']}, {s['unit']})\n"
        
        # Llamar a Claude
        try:
            client = Anthropic(api_key=api_key)
            
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                
                with client.messages.stream(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=2000,
                    messages=[
                        {"role": "system", "content": f"Eres un asistente experto en macroeconomía argentina. {context}"},
                        *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                    ]
                ) as stream:
                    for text in stream.text_stream:
                        full_response += text
                        message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        
        except Exception as e:
            st.error(f"Error al conectar con Claude: {str(e)}")

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    st.set_page_config(
        page_title="Monitor AR",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Aplicar estilos
    apply_custom_styles()
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 🚀 MONITOR AR")
        st.markdown("---")
        
        page = st.radio(
            "Navegación",
            ["🏠 Inicio", "📊 Dashboard Macro", "📈 Mercado", "🤖 Asistente"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: var(--text-secondary); font-size: 12px;">
            <p>Monitor AR v1.0</p>
            <p>Datos de BCRA y datos.gob.ar</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Router
    if page == "🏠 Inicio":
        page_inicio()
    elif page == "📊 Dashboard Macro":
        page_dashboard()
    elif page == "📈 Mercado":
        page_mercado()
    elif page == "🤖 Asistente":
        page_asistente()

if __name__ == "__main__":
    main()
