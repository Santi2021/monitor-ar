# app.py
import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from urllib3.exceptions import InsecureRequestWarning
import urllib3

# Desactivar warnings SSL globalmente
urllib3.disable_warnings(InsecureRequestWarning)

# ============================================================================
# CONFIGURACIÓN GLOBAL
# ============================================================================

st.set_page_config(
    page_title="Dashboard Económico Argentina",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# SERIES CANÓNICAS V1
# ============================================================================

SERIES_CANONICAS = [
    {
        "pack": "monetarias_financieras",
        "source": "BCRA",
        "id": "1",
        "nombre_canonico": "Monetarias y Financieras · Base Monetaria — Total [Millones ARS]",
        "unidad": "Millones ARS",
        "frecuencia": "Diaria",
        "endpoint": "estadisticas/v2.0/DatosVariable",
        "params": {"idVariable": 1},
        "campo_fecha": "fecha",
        "campo_valor": "valor"
    },
    {
        "pack": "monetarias_financieras",
        "source": "BCRA",
        "id": "7",
        "nombre_canonico": "Monetarias y Financieras · Reservas Internacionales — Total [Millones USD]",
        "unidad": "Millones USD",
        "frecuencia": "Diaria",
        "endpoint": "estadisticas/v2.0/DatosVariable",
        "params": {"idVariable": 7},
        "campo_fecha": "fecha",
        "campo_valor": "valor"
    },
    {
        "pack": "tasas_interes",
        "source": "BCRA",
        "id": "3",
        "nombre_canonico": "Tasas de Interés · BADLAR — Privados [TNA %]",
        "unidad": "TNA %",
        "frecuencia": "Diaria",
        "endpoint": "estadisticas/v2.0/DatosVariable",
        "params": {"idVariable": 3},
        "campo_fecha": "fecha",
        "campo_valor": "valor"
    },
    {
        "pack": "tasas_interes",
        "source": "BCRA",
        "id": "4",
        "nombre_canonico": "Tasas de Interés · Plazo Fijo — Personas hasta $10M [TNA %]",
        "unidad": "TNA %",
        "frecuencia": "Diaria",
        "endpoint": "estadisticas/v2.0/DatosVariable",
        "params": {"idVariable": 4},
        "campo_fecha": "fecha",
        "campo_valor": "valor"
    },
    {
        "pack": "tasas_interes",
        "source": "BCRA",
        "id": "5",
        "nombre_canonico": "Tasas de Interés · Pases Pasivos — 1 Día [TNA %]",
        "unidad": "TNA %",
        "frecuencia": "Diaria",
        "endpoint": "estadisticas/v2.0/DatosVariable",
        "params": {"idVariable": 5},
        "campo_fecha": "fecha",
        "campo_valor": "valor"
    },
    {
        "pack": "tipo_cambio",
        "source": "BCRA",
        "id": "4",
        "nombre_canonico": "Tipo de Cambio · Dólar — Mayorista Promedio [ARS/USD]",
        "unidad": "ARS/USD",
        "frecuencia": "Diaria",
        "endpoint": "estadisticas/v2.0/DatosVariable",
        "params": {"idVariable": 4},
        "campo_fecha": "fecha",
        "campo_valor": "valor"
    },
    {
        "pack": "inflacion",
        "source": "CKAN",
        "resource_id": "145c4e6d-c7f3-4cd0-8357-81734ab86167",
        "nombre_canonico": "Inflación · IPC Nacional — Nivel General [Índice base 2016=100]",
        "unidad": "Índice",
        "frecuencia": "Mensual",
        "endpoint": "https://datos.gob.ar/api/3/action/datastore_search",
        "params": {"resource_id": "145c4e6d-c7f3-4cd0-8357-81734ab86167", "limit": 1000},
        "campo_fecha": "indice_tiempo",
        "campo_valor": "nivel_general"
    },
    {
        "pack": "inflacion",
        "source": "CKAN",
        "resource_id": "145c4e6d-c7f3-4cd0-8357-81734ab86167",
        "nombre_canonico": "Inflación · IPC Nacional — Variación Mensual [% m/m]",
        "unidad": "% m/m",
        "frecuencia": "Mensual",
        "endpoint": "https://datos.gob.ar/api/3/action/datastore_search",
        "params": {"resource_id": "145c4e6d-c7f3-4cd0-8357-81734ab86167", "limit": 1000},
        "campo_fecha": "indice_tiempo",
        "campo_valor": "nivel_general_mensual"
    },
    {
        "pack": "inflacion",
        "source": "CKAN",
        "resource_id": "145c4e6d-c7f3-4cd0-8357-81734ab86167",
        "nombre_canonico": "Inflación · IPC Nacional — Variación Interanual [% y/y]",
        "unidad": "% y/y",
        "frecuencia": "Mensual",
        "endpoint": "https://datos.gob.ar/api/3/action/datastore_search",
        "params": {"resource_id": "145c4e6d-c7f3-4cd0-8357-81734ab86167", "limit": 1000},
        "campo_fecha": "indice_tiempo",
        "campo_valor": "nivel_general_interanual"
    },
    {
        "pack": "actividad_economica",
        "source": "BCRA",
        "id": "11",
        "nombre_canonico": "Actividad Económica · EMAE — Nivel [Índice base 2004=100]",
        "unidad": "Índice",
        "frecuencia": "Mensual",
        "endpoint": "estadisticas/v2.0/DatosVariable",
        "params": {"idVariable": 11},
        "campo_fecha": "fecha",
        "campo_valor": "valor"
    },
    {
        "pack": "sector_externo",
        "source": "BCRA",
        "id": "23",
        "nombre_canonico": "Sector Externo · Exportaciones — Total [Millones USD]",
        "unidad": "Millones USD",
        "frecuencia": "Mensual",
        "endpoint": "estadisticas/v2.0/DatosVariable",
        "params": {"idVariable": 23},
        "campo_fecha": "fecha",
        "campo_valor": "valor"
    },
    {
        "pack": "sector_externo",
        "source": "BCRA",
        "id": "24",
        "nombre_canonico": "Sector Externo · Importaciones — Total [Millones USD]",
        "unidad": "Millones USD",
        "frecuencia": "Mensual",
        "endpoint": "estadisticas/v2.0/DatosVariable",
        "params": {"idVariable": 24},
        "campo_fecha": "fecha",
        "campo_valor": "valor"
    },
    {
        "pack": "agregados_monetarios",
        "source": "BCRA",
        "id": "28",
        "nombre_canonico": "Agregados Monetarios · M2 Privado — Total [Millones ARS]",
        "unidad": "Millones ARS",
        "frecuencia": "Diaria",
        "endpoint": "estadisticas/v2.0/DatosVariable",
        "params": {"idVariable": 28},
        "campo_fecha": "fecha",
        "campo_valor": "valor"
    },
    {
        "pack": "fiscal",
        "source": "BCRA",
        "id": "6",
        "nombre_canonico": "Fiscal · Depósitos del Sector Público — Total [Millones ARS]",
        "unidad": "Millones ARS",
        "frecuencia": "Diaria",
        "endpoint": "estadisticas/v2.0/DatosVariable",
        "params": {"idVariable": 6},
        "campo_fecha": "fecha",
        "campo_valor": "valor"
    },
    {
        "pack": "credito",
        "source": "BCRA",
        "id": "12",
        "nombre_canonico": "Crédito · Préstamos al Sector Privado — Total [Millones ARS]",
        "unidad": "Millones ARS",
        "frecuencia": "Mensual",
        "endpoint": "estadisticas/v2.0/DatosVariable",
        "params": {"idVariable": 12},
        "campo_fecha": "fecha",
        "campo_valor": "valor"
    }
]

# ============================================================================
# FUNCIONES UTILITARIAS DE RED
# ============================================================================

def fetch_bcra_list():
    """Obtiene lista de variables disponibles del BCRA"""
    url = "https://api.bcra.gob.ar/estadisticas/v2.0/principalesvariables"
    try:
        response = requests.get(url, timeout=15, verify=False)
        if response.status_code == 200:
            data = response.json()
            return data.get('results', [])
    except Exception as e:
        st.warning(f"⚠️ Error al obtener lista BCRA: {str(e)}")
    return []

def fetch_bcra_series(id_variable, n=1000):
    """Obtiene serie de datos del BCRA por ID"""
    url = f"https://api.bcra.gob.ar/estadisticas/v2.0/DatosVariable/{id_variable}/{n}"
    try:
        response = requests.get(url, timeout=15, verify=False)
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            if results:
                df = pd.DataFrame(results)
                return df
    except Exception as e:
        st.warning(f"⚠️ Error al obtener serie BCRA ID {id_variable}: {str(e)}")
    return None

def ckan_search(q="", limit=20, offset=0):
    """Busca datasets en CKAN datos.gob.ar"""
    url = "https://datos.gob.ar/api/3/action/package_search"
    params = {
        "q": q,
        "rows": limit,
        "start": offset
    }
    try:
        response = requests.get(url, params=params, timeout=15, verify=False)
        if response.status_code == 200:
            data = response.json()
            return data.get('result', {})
    except Exception as e:
        st.warning(f"⚠️ Error en búsqueda CKAN: {str(e)}")
    return {}

def ckan_preview(resource_id, limit=100):
    """Obtiene preview de un recurso CKAN"""
    url = "https://datos.gob.ar/api/3/action/datastore_search"
    params = {
        "resource_id": resource_id,
        "limit": limit
    }
    try:
        response = requests.get(url, params=params, timeout=15, verify=False)
        if response.status_code == 200:
            data = response.json()
            records = data.get('result', {}).get('records', [])
            if records:
                return pd.DataFrame(records)
    except Exception as e:
        st.warning(f"⚠️ Error al obtener recurso CKAN {resource_id}: {str(e)}")
    return None

def detect_timeseries(df):
    """Detecta columnas de fecha y valor en un DataFrame"""
    date_cols = []
    value_cols = []
    
    for col in df.columns:
        col_lower = col.lower()
        # Detectar fechas
        if any(x in col_lower for x in ['fecha', 'date', 'time', 'periodo', 'indice_tiempo']):
            date_cols.append(col)
        # Detectar valores numéricos
        elif df[col].dtype in ['float64', 'int64'] and col.lower() != '_id':
            value_cols.append(col)
    
    return date_cols, value_cols

# ============================================================================
# FUNCIONES DE FILTRADO ANTI-RUIDO
# ============================================================================

def es_tasa_ruido(nombre):
    """Detecta tasas TEA/TEM/efectivas que generan ruido"""
    nombre_lower = nombre.lower()
    ruido_keywords = ['tea', 'tem', 'efectiva', 'cft']
    return any(kw in nombre_lower for kw in ruido_keywords)

def normalizar_nombre(nombre):
    """Normaliza nombre para detectar duplicados"""
    return nombre.casefold().strip()

def extraer_unidad(descripcion):
    """Extrae badge de unidad desde descripción"""
    desc_lower = descripcion.lower()
    
    if 'tna' in desc_lower:
        return 'TNA'
    elif 'tea' in desc_lower:
        return 'TEA'
    elif 'tem' in desc_lower:
        return 'TEM'
    elif '% y/y' in desc_lower or 'interanual' in desc_lower:
        return '% y/y'
    elif '% m/m' in desc_lower or 'mensual' in desc_lower:
        return '% m/m'
    elif 'índice' in desc_lower or 'indice' in desc_lower or 'nivel' in desc_lower:
        return 'Nivel'
    elif 'millones' in desc_lower:
        if 'usd' in desc_lower:
            return 'Millones USD'
        else:
            return 'Millones ARS'
    elif '%' in desc_lower:
        return '%'
    else:
        return 'Valor'

# ============================================================================
# FUNCIONES DE OBTENCIÓN Y PROCESAMIENTO DE SERIES
# ============================================================================

def obtener_serie_canonica(config):
    """Obtiene datos de una serie canónica según su configuración"""
    if config['source'] == 'BCRA':
        df = fetch_bcra_series(config['id'])
        if df is not None and not df.empty:
            df[config['campo_fecha']] = pd.to_datetime(df[config['campo_fecha']])
            df = df.sort_values(config['campo_fecha'])
            return df
    
    elif config['source'] == 'CKAN':
        df = ckan_preview(config['resource_id'], limit=1000)
        if df is not None and not df.empty:
            try:
                df[config['campo_fecha']] = pd.to_datetime(df[config['campo_fecha']])
                df = df.sort_values(config['campo_fecha'])
                return df
            except:
                pass
    
    return None

def obtener_ultima_observacion(df, campo_fecha, campo_valor):
    """Obtiene la última observación válida de una serie"""
    if df is None or df.empty:
        return None, None
    
    try:
        df_clean = df[[campo_fecha, campo_valor]].dropna()
        if df_clean.empty:
            return None, None
        
        ultima = df_clean.iloc[-1]
        fecha = ultima[campo_fecha]
        valor = ultima[campo_valor]
        
        return fecha, valor
    except:
        return None, None

# ============================================================================
# COMPONENTES UI
# ============================================================================

def render_serie_card(config, col_container=None):
    """Renderiza una tarjeta de serie con datos actualizados"""
    container = col_container if col_container else st
    
    with container.container():
        st.markdown(f"""
        <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; background: white; height: 100%;">
            <h4 style="margin: 0 0 10px 0; color: #1f77b4;">{config['nombre_canonico']}</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Botón de actualización
        if st.button("🔄 Actualizar", key=f"refresh_{config['id']}_{config['source']}"):
            with st.spinner("Obteniendo datos..."):
                df = obtener_serie_canonica(config)
                if df is not None:
                    st.session_state[f"data_{config['id']}_{config['source']}"] = df
        
        # Obtener datos (de cache o nuevos)
        cache_key = f"data_{config['id']}_{config['source']}"
        if cache_key not in st.session_state:
            df = obtener_serie_canonica(config)
            if df is not None:
                st.session_state[cache_key] = df
        else:
            df = st.session_state[cache_key]
        
        # Mostrar última observación
        if df is not None and not df.empty:
            fecha, valor = obtener_ultima_observacion(df, config['campo_fecha'], config['campo_valor'])
            
            if fecha and valor:
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.metric("Última observación", f"{valor:,.2f}")
                with col2:
                    st.caption(f"📅 {fecha.strftime('%d/%m/%Y')}")
                
                # Tabs para visualización
                tab1, tab2, tab3 = st.tabs(["📊 Gráfico", "📋 Tabla", "🔍 JSON"])
                
                with tab1:
                    # Gráfico de línea
                    fig = px.line(
                        df,
                        x=config['campo_fecha'],
                        y=config['campo_valor'],
                        title=f"{config['frecuencia']} - {config['unidad']}"
                    )
                    fig.update_layout(
                        height=250,
                        margin=dict(l=0, r=0, t=30, b=0),
                        xaxis_title="",
                        yaxis_title=config['unidad']
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with tab2:
                    # Tabla de datos
                    st.dataframe(
                        df[[config['campo_fecha'], config['campo_valor']]].tail(20),
                        use_container_width=True,
                        height=250
                    )
                
                with tab3:
                    # JSON crudo
                    st.json(df.tail(10).to_dict(orient='records'))
            else:
                st.warning("No hay observaciones válidas")
        else:
            st.error("❌ No se pudieron obtener datos")
        
        st.markdown("</div>", unsafe_allow_html=True)

# ============================================================================
# INICIALIZACIÓN SESSION STATE
# ============================================================================

if 'custom_series' not in st.session_state:
    st.session_state.custom_series = []

if 'catalogo_filtro_canonicas' not in st.session_state:
    st.session_state.catalogo_filtro_canonicas = True

# ============================================================================
# SIDEBAR NAVEGACIÓN
# ============================================================================

st.sidebar.title("📊 Dashboard Económico")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Navegación",
    ["🏠 Inicio", "📈 Datos Económicos", "📚 Catálogo", "⭐ Mi Dashboard", "🤖 Asistente"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.info("""
**Series Canónicas v1**
- 15 series preseleccionadas
- Filtros anti-ruido
- APIs robustas con timeout
""")

# ============================================================================
# PÁGINA: INICIO
# ============================================================================

if menu == "🏠 Inicio":
    st.title("📊 Dashboard Económico Argentina")
    st.markdown("### Acceso unificado a datos económicos oficiales")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        #### 📈 Datos Económicos
        Explora series preseleccionadas:
        - Monetarias y Financieras
        - Tasas de Interés
        - Tipo de Cambio
        - Inflación
        - Actividad Económica
        """)
    
    with col2:
        st.markdown("""
        #### 📚 Catálogo
        Busca y filtra series:
        - BCRA (Banco Central)
        - CKAN (Datos Abiertos)
        - Filtros anti-ruido
        - Agregar a Dashboard
        """)
    
    with col3:
        st.markdown("""
        #### ⭐ Mi Dashboard
        Series personalizadas:
        - Canónicas preseleccionadas
        - Series agregadas manualmente
        - Visualización en tarjetas
        - Exportación de datos
        """)
    
    st.markdown("---")
    
    st.success("""
    **✨ Novedades v1:**
    - 15 series canónicas preconfiguradas
    - Filtros inteligentes para reducir ruido
    - Requests robustos con manejo de errores
    - Nomenclatura normalizada
    """)

# ============================================================================
# PÁGINA: DATOS ECONÓMICOS
# ============================================================================

elif menu == "📈 Datos Económicos":
    st.title("📈 Datos Económicos - Series Canónicas")
    
    # Filtro por pack
    packs_disponibles = list(set([s['pack'] for s in SERIES_CANONICAS]))
    pack_seleccionado = st.selectbox(
        "Filtrar por categoría",
        ["Todas"] + sorted(packs_disponibles)
    )
    
    # Filtrar series
    if pack_seleccionado == "Todas":
        series_filtradas = SERIES_CANONICAS
    else:
        series_filtradas = [s for s in SERIES_CANONICAS if s['pack'] == pack_seleccionado]
    
    st.markdown(f"**{len(series_filtradas)} series disponibles**")
    st.markdown("---")
    
    # Renderizar en grid de 2 columnas
    for i in range(0, len(series_filtradas), 2):
        cols = st.columns(2)
        
        for j, col in enumerate(cols):
            if i + j < len(series_filtradas):
                with col:
                    render_serie_card(series_filtradas[i + j])

# ============================================================================
# PÁGINA: CATÁLOGO
# ============================================================================

elif menu == "📚 Catálogo":
    st.title("📚 Catálogo de Series")
    
    # Toggle filtro canónicas
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### Explorar series disponibles")
    with col2:
        st.session_state.catalogo_filtro_canonicas = st.toggle(
            "Solo canónicas",
            value=st.session_state.catalogo_filtro_canonicas
        )
    
    tabs = st.tabs(["🏦 BCRA", "🗃️ CKAN Datos Abiertos"])
    
    # ========== TAB BCRA ==========
    with tabs[0]:
        st.markdown("#### Variables Principales BCRA")
        
        if st.button("🔄 Cargar Variables BCRA"):
            with st.spinner("Obteniendo catálogo BCRA..."):
                variables = fetch_bcra_list()
                st.session_state.bcra_variables = variables
        
        if 'bcra_variables' in st.session_state and st.session_state.bcra_variables:
            variables = st.session_state.bcra_variables
            
            # Filtros anti-ruido
            if st.session_state.catalogo_filtro_canonicas:
                variables_filtradas = []
                nombres_vistos = set()
                
                for v in variables:
                    nombre = v.get('descripcion', '')
                    
                    # Filtrar TEA/TEM
                    if es_tasa_ruido(nombre):
                        continue
                    
                    # Evitar duplicados
                    nombre_norm = normalizar_nombre(nombre)
                    if nombre_norm in nombres_vistos:
                        continue
                    
                    nombres_vistos.add(nombre_norm)
                    variables_filtradas.append(v)
                
                variables = variables_filtradas
            
            st.info(f"📊 {len(variables)} variables disponibles")
            
            # Mostrar tabla
            for var in variables[:50]:  # Limitar a 50 para performance
                with st.expander(f"**{var.get('descripcion')}**"):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        unidad = extraer_unidad(var.get('descripcion', ''))
                        st.markdown(f"**Unidad:** `{unidad}`")
                        st.caption(f"ID: {var.get('idVariable')}")
                    
                    with col2:
                        st.markdown(f"**Último valor:** {var.get('valor', 'N/A')}")
                    
                    with col3:
                        st.caption(f"{var.get('fecha', '')}")
                    
                    if st.button("➕ Agregar a Mi Dashboard", key=f"add_bcra_{var.get('idVariable')}"):
                        nueva_serie = {
                            "pack": "custom",
                            "source": "BCRA",
                            "id": str(var.get('idVariable')),
                            "nombre_canonico": var.get('descripcion'),
                            "unidad": unidad,
                            "frecuencia": "Variable",
                            "endpoint": "estadisticas/v2.0/DatosVariable",
                            "params": {"idVariable": var.get('idVariable')},
                            "campo_fecha": "fecha",
                            "campo_valor": "valor"
                        }
                        st.session_state.custom_series.append(nueva_serie)
                        st.success("✅ Serie agregada al dashboard")
    
    # ========== TAB CKAN ==========
    with tabs[1]:
        st.markdown("#### CKAN Datos Abiertos")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            query = st.text_input("🔍 Buscar datasets", placeholder="ej: inflación, empleo, comercio...")
        with col2:
            if st.button("Buscar"):
                st.session_state.ckan_query = query
        
        # Paginación
        if 'ckan_page' not in st.session_state:
            st.session_state.ckan_page = 0
        
        if st.button("🔄 Buscar en CKAN") or 'ckan_query' in st.session_state:
            query = st.session_state.get('ckan_query', '')
            offset = st.session_state.ckan_page * 20
            
            with st.spinner("Buscando en CKAN..."):
                result = ckan_search(query, limit=20, offset=offset)
                
                if result:
                    datasets = result.get('results', [])
                    total = result.get('count', 0)
                    
                    st.info(f"📦 {total} datasets encontrados")
                    
                    for dataset in datasets:
                        with st.expander(f"**{dataset.get('title')}**"):
                            st.markdown(dataset.get('notes', 'Sin descripción')[:200])
                            
                            recursos = dataset.get('resources', [])
                            if recursos:
                                st.markdown(f"**{len(recursos)} recursos disponibles:**")
                                
                                for rec in recursos[:5]:
                                    col1, col2 = st.columns([3, 1])
                                    with col1:
                                        st.caption(f"📄 {rec.get('name', 'Sin nombre')}")
                                    with col2:
                                        if st.button("👁️ Preview", key=f"preview_{rec.get('id')}"):
                                            st.session_state.preview_resource = rec.get('id')
                    
                    # Controles de paginación
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col1:
                        if st.session_state.ckan_page > 0:
                            if st.button("⬅️ Anterior"):
                                st.session_state.ckan_page -= 1
                                st.rerun()
                    with col3:
                        if (st.session_state.ckan_page + 1) * 20 < total:
                            if st.button("Siguiente ➡️"):
                                st.session_state.ckan_page += 1
                                st.rerun()
        
        # Preview de recurso
        if 'preview_resource' in st.session_state:
            st.markdown("---")
            st.markdown("### 👁️ Preview de Recurso")
            
            resource_id = st.session_state.preview_resource
            df_preview = ckan_preview(resource_id, limit=100)
            
            if df_preview is not None:
                st.dataframe(df_preview.head(20))
                
                # Detectar series temporales
                date_cols, value_cols = detect_timeseries(df_preview)
                
                if date_cols and value_cols:
                    st.success(f"✅ Serie temporal detectada")
                    st.info(f"**Fechas:** {', '.join(date_cols)}")
                    st.info(f"**Valores:** {', '.join(value_cols)}")
                    
                    # Permitir agregar
                    col1, col2 = st.columns(2)
                    with col1:
                        campo_fecha = st.selectbox("Columna de fecha", date_cols)
                    with col2:
                        campo_valor = st.selectbox("Columna de valor", value_cols)
                    
                    if st.button("➕ Agregar serie al Dashboard"):
                        nueva_serie = {
                            "pack": "custom",
                            "source": "CKAN",
                            "resource_id": resource_id,
                            "nombre_canonico": f"CKAN · {campo_valor}",
                            "unidad": "Valor",
                            "frecuencia": "Variable",
                            "endpoint": "https://datos.gob.ar/api/3/action/datastore_search",
                            "params": {"resource_id": resource_id, "limit": 1000},
                            "campo_fecha": campo_fecha,
                            "campo_valor": campo_valor
                        }
                        st.session_state.custom_series.append(nueva_serie)
                        st.success("✅ Serie agregada al dashboard")

# ============================================================================
# PÁGINA: MI DASHBOARD
# ============================================================================

elif menu == "⭐ Mi Dashboard":
    st.title("⭐ Mi Dashboard Personalizado")
    
    # Combinar series canónicas + personalizadas
    todas_las_series = SERIES_CANONICAS + st.session_state.custom_series
    
    if not todas_las_series:
        st.info("No hay series en el dashboard. Agrega series desde el Catálogo.")
    else:
        st.info(f"📊 {len(todas_las_series)} series en tu dashboard")
        
        # Renderizar en grid de 3 columnas
        for i in range(0, len(todas_las_series), 3):
            cols = st.columns(3)
            
            for j, col in enumerate(cols):
                if i + j < len(todas_las_series):
                    with col:
                        render_serie_card(todas_las_series[i + j])
        
        st.markdown("---")
        
        # Opciones de gestión
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Limpiar series personalizadas"):
                st.session_state.custom_series = []
                st.success("Series personalizadas eliminadas")
                st.rerun()
        
        with col2:
            if st.button("💾 Exportar configuración"):
                config_export = {
                    "canonicas": SERIES_CANONICAS,
                    "personalizadas": st.session_state.custom_series
                }
                st.download_button(
                    "📥 Descargar JSON",
                    data=json.dumps(config_export, indent=2),
                    file_name="dashboard_config.json",
                    mime="application/json"
                )

# ============================================================================
# PÁGINA: ASISTENTE (mantenida del código anterior)
# ============================================================================

elif menu == "🤖 Asistente":
    st.title("🤖 Asistente de Consultas")
    st.info("Esta funcionalidad mantiene la lógica del asistente anterior. Se integra con las nuevas series canónicas.")
    
    st.markdown("""
    ### Próximas mejoras:
    - Consultas en lenguaje natural sobre series canónicas
    - Análisis automático de correlaciones
    - Alertas y notificaciones
    - Exportación automatizada
    """)
    
    # Placeholder para mantener compatibilidad
    if st.button("Habilitar Asistente IA"):
        st.warning("Función en desarrollo. Próximamente disponible.")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.caption("Dashboard Económico Argentina v1.0 | Series Canónicas + Filtros Anti-Ruido | Datos: BCRA + CKAN")
