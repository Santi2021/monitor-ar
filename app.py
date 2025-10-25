import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json

# Configuración de la página
st.set_page_config(
    page_title="Monitor AR",
    page_icon="🇦🇷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos personalizados
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    </style>
""", unsafe_allow_html=True)

# ==================== FUNCIONES AUXILIARES ====================

def fetch_bcra_data(endpoint="PrincipalesVariables"):
    """
    Consulta la API del BCRA v4.
    
    Args:
        endpoint (str): Endpoint a consultar (default: PrincipalesVariables)
    
    Returns:
        dict: Respuesta JSON de la API o None si hay error
    """
    base_url = "https://api.bcra.gob.ar/estadisticas/v4"
    
    try:
        # Si el usuario ingresó la URL completa, extraer solo el endpoint
        if endpoint.startswith("http"):
            endpoint = endpoint.split("/")[-1]
        
        url = f"{base_url}/{endpoint}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        return response.json()
    
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error al consultar BCRA: {str(e)}")
        return None
    except json.JSONDecodeError:
        st.error("❌ Error: La respuesta no es un JSON válido")
        return None

def fetch_ckan_data(action, params=None):
    """
    Consulta la API de datos.gob.ar (CKAN).
    
    Args:
        action (str): Acción CKAN (ej: package_search, datastore_search)
        params (dict): Parámetros adicionales para la consulta
    
    Returns:
        dict: Respuesta JSON de la API o None si hay error
    """
    base_url = "https://datos.gob.ar/api/3/action"
    
    try:
        url = f"{base_url}/{action}"
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get("success"):
            st.error(f"❌ Error en la respuesta de CKAN: {data.get('error', 'Desconocido')}")
            return None
        
        return data.get("result")
    
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error al consultar datos.gob.ar: {str(e)}")
        return None
    except json.JSONDecodeError:
        st.error("❌ Error: La respuesta no es un JSON válido")
        return None

def process_bcra_data(data):
    """
    Procesa los datos del BCRA y los convierte en DataFrame.
    
    Args:
        data (dict): Datos JSON del BCRA
    
    Returns:
        pd.DataFrame: DataFrame procesado o None
    """
    try:
        # Detectar estructura de PrincipalesVariables
        if "results" in data:
            df = pd.DataFrame(data["results"])
        elif isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            # Si es un dict con una sola clave que contiene lista
            for key, value in data.items():
                if isinstance(value, list):
                    df = pd.DataFrame(value)
                    break
            else:
                df = pd.DataFrame([data])
        else:
            return None
        
        # Intentar detectar y convertir fechas
        date_columns = ['fecha', 'date', 'd']
        for col in df.columns:
            if col.lower() in date_columns or 'fecha' in col.lower():
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                except:
                    pass
        
        return df
    
    except Exception as e:
        st.error(f"❌ Error al procesar datos del BCRA: {str(e)}")
        return None

def process_ckan_data(data):
    """
    Procesa los datos de CKAN y los convierte en DataFrame.
    
    Args:
        data (dict): Datos JSON de CKAN
    
    Returns:
        pd.DataFrame: DataFrame procesado o None
    """
    try:
        # Estructura típica de datastore_search
        if "records" in data:
            df = pd.DataFrame(data["records"])
        # Estructura de package_search
        elif "results" in data and isinstance(data["results"], list):
            df = pd.DataFrame(data["results"])
        elif isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            # Intentar extraer datos de estructuras anidadas
            for key in ['data', 'datos', 'items']:
                if key in data and isinstance(data[key], list):
                    df = pd.DataFrame(data[key])
                    break
            else:
                df = pd.DataFrame([data])
        else:
            return None
        
        return df
    
    except Exception as e:
        st.error(f"❌ Error al procesar datos de CKAN: {str(e)}")
        return None

def detect_and_plot_timeseries(df):
    """
    Detecta si el DataFrame contiene una serie temporal y genera un gráfico.
    
    Args:
        df (pd.DataFrame): DataFrame a analizar
    
    Returns:
        plotly.graph_objects.Figure: Gráfico o None
    """
    try:
        # Buscar columnas de fecha
        date_col = None
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                date_col = col
                break
            # Intentar detectar fechas por nombre
            if any(keyword in col.lower() for keyword in ['fecha', 'date', 'time', 'periodo']):
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    if df[col].notna().sum() > 0:
                        date_col = col
                        break
                except:
                    pass
        
        if date_col is None:
            return None
        
        # Buscar columnas numéricas
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if len(numeric_cols) == 0:
            return None
        
        # Ordenar por fecha
        df_sorted = df.sort_values(by=date_col)
        
        # Crear gráfico
        fig = go.Figure()
        
        # Agregar hasta 5 series numéricas
        for col in numeric_cols[:5]:
            fig.add_trace(go.Scatter(
                x=df_sorted[date_col],
                y=df_sorted[col],
                mode='lines+markers',
                name=col,
                hovertemplate='<b>%{fullData.name}</b><br>Fecha: %{x}<br>Valor: %{y:.2f}<extra></extra>'
            ))
        
        fig.update_layout(
            title="📈 Serie Temporal Detectada",
            xaxis_title="Fecha",
            yaxis_title="Valor",
            hovermode='x unified',
            template='plotly_white',
            height=500
        )
        
        return fig
    
    except Exception as e:
        st.warning(f"⚠️ No se pudo generar el gráfico: {str(e)}")
        return None

# ==================== INTERFAZ PRINCIPAL ====================

def main():
    # Header
    st.markdown('<h1 class="main-header">🇦🇷 Monitor AR</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("📊 Navegación")
        page = st.radio(
            "Seleccione una sección:",
            ["🏠 Inicio", "💰 Datos Económicos"]
        )
        
        st.markdown("---")
        st.markdown("### ℹ️ Acerca de")
        st.info("""
        **Monitor AR** es una aplicación para visualizar 
        datos económicos de Argentina desde fuentes oficiales.
        
        **Fuentes:**
        - BCRA (Banco Central)
        - Datos.gob.ar
        """)
    
    # ==================== PÁGINA DE INICIO ====================
    if page == "🏠 Inicio":
        st.header("🏠 Bienvenido a Monitor AR")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 🎯 Características
            
            - ✅ Consulta de APIs públicas argentinas
            - 📊 Visualización automática de datos
            - 📈 Gráficos interactivos de series temporales
            - 🔍 Exploración de datasets
            - 💾 Exportación de datos
            """)
        
        with col2:
            st.markdown("""
            ### 🚀 Cómo usar
            
            1. Navega a **Datos Económicos** en el menú lateral
            2. Selecciona una fuente de datos
            3. Ingresa el endpoint o palabra clave
            4. Haz clic en **Consultar**
            5. Explora los resultados
            """)
        
        st.markdown("---")
        
        st.success("👈 Comienza seleccionando **Datos Económicos** en el menú lateral")
    
    # ==================== PÁGINA DE DATOS ECONÓMICOS ====================
    elif page == "💰 Datos Económicos":
        st.header("💰 Consulta de Datos Económicos")
        
        # Selector de fuente
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fuente = st.selectbox(
                "📡 Seleccione la fuente de datos:",
                ["BCRA v4 - Banco Central", "Datos.gob.ar - CKAN"],
                help="Elija la API desde la cual desea consultar datos"
            )
        
        with col2:
            st.markdown("### ")
            show_help = st.checkbox("❓ Ayuda", value=False)
        
        # Mostrar ayuda según la fuente
        if show_help:
            if "BCRA" in fuente:
                with st.expander("ℹ️ Ayuda - BCRA API", expanded=True):
                    st.markdown("""
                    **Ejemplos de endpoints:**
                    - `PrincipalesVariables` - Variables principales
                    - `DatosVariable/1` - Datos de una variable específica (ID=1)
                    - `VariablesDisponibles` - Lista de todas las variables
                    
                    **URL base:** `https://api.bcra.gob.ar/estadisticas/v4/`
                    
                    Puede ingresar solo el endpoint o la URL completa.
                    """)
            else:
                with st.expander("ℹ️ Ayuda - Datos.gob.ar CKAN", expanded=True):
                    st.markdown("""
                    **Ejemplos de consultas:**
                    
                    **Búsqueda de datasets:**
                    - Acción: `package_search`
                    - Palabra clave: `inflacion`, `precios`, `empleo`
                    
                    **Consulta de datos:**
                    - Acción: `datastore_search`
                    - Resource ID: (obtener de la búsqueda previa)
                    
                    **URL base:** `https://datos.gob.ar/api/3/action/`
                    """)
        
        st.markdown("---")
        
        # Formulario de consulta
        if "BCRA" in fuente:
            st.subheader("🏦 Configuración BCRA")
            
            endpoint = st.text_input(
                "Endpoint:",
                value="PrincipalesVariables",
                help="Ingrese el endpoint a consultar (ej: PrincipalesVariables, VariablesDisponibles)"
            )
            
            if st.button("🔍 Consultar", type="primary", use_container_width=True):
                with st.spinner("Consultando BCRA..."):
                    data = fetch_bcra_data(endpoint)
                    
                    if data:
                        st.session_state['last_data'] = data
                        st.session_state['data_source'] = 'BCRA'
                        st.success("✅ Datos obtenidos correctamente")
        
        else:  # Datos.gob.ar
            st.subheader("🏛️ Configuración Datos.gob.ar")
            
            col1, col2 = st.columns(2)
            
            with col1:
                action = st.selectbox(
                    "Acción CKAN:",
                    ["package_search", "datastore_search", "package_show", "resource_show"],
                    help="Seleccione la acción a realizar en la API de CKAN"
                )
            
            with col2:
                keyword = st.text_input(
                    "Parámetro (q, id, resource_id):",
                    help="Ingrese la palabra clave o ID según la acción"
                )
            
            # Parámetros adicionales opcionales
            with st.expander("⚙️ Parámetros adicionales (opcional)"):
                col1, col2 = st.columns(2)
                with col1:
                    limit = st.number_input("Límite de resultados:", min_value=1, max_value=1000, value=10)
                with col2:
                    offset = st.number_input("Offset:", min_value=0, value=0)
            
            if st.button("🔍 Consultar", type="primary", use_container_width=True):
                params = {}
                
                # Configurar parámetros según la acción
                if action == "package_search":
                    params["q"] = keyword if keyword else "*"
                    params["rows"] = limit
                    params["start"] = offset
                elif action == "datastore_search":
                    if keyword:
                        params["resource_id"] = keyword
                        params["limit"] = limit
                        params["offset"] = offset
                    else:
                        st.error("❌ Para datastore_search debe ingresar un resource_id")
                        st.stop()
                elif action in ["package_show", "resource_show"]:
                    if keyword:
                        params["id"] = keyword
                    else:
                        st.error(f"❌ Para {action} debe ingresar un ID")
                        st.stop()
                
                with st.spinner("Consultando datos.gob.ar..."):
                    data = fetch_ckan_data(action, params)
                    
                    if data:
                        st.session_state['last_data'] = data
                        st.session_state['data_source'] = 'CKAN'
                        st.success("✅ Datos obtenidos correctamente")
        
        # ==================== VISUALIZACIÓN DE RESULTADOS ====================
        
        if 'last_data' in st.session_state and st.session_state['last_data']:
            st.markdown("---")
            st.header("📊 Resultados")
            
            data = st.session_state['last_data']
            source = st.session_state.get('data_source', 'Desconocido')
            
            # Tabs para organizar la información
            tab1, tab2, tab3 = st.tabs(["📄 JSON", "📋 Tabla", "📈 Gráfico"])
            
            # TAB 1: JSON
            with tab1:
                with st.expander("🔍 Ver JSON completo", expanded=False):
                    st.json(data)
                
                # Información sobre la estructura
                st.info(f"**Fuente:** {source} | **Claves principales:** {', '.join(list(data.keys())[:5])}")
            
            # TAB 2: Tabla
            with tab2:
                if source == 'BCRA':
                    df = process_bcra_data(data)
                else:
                    df = process_ckan_data(data)
                
                if df is not None and not df.empty:
                    st.success(f"✅ Tabla generada: {len(df)} registros × {len(df.columns)} columnas")
                    
                    # Filtros
                    with st.expander("🔧 Opciones de visualización"):
                        col1, col2 = st.columns(2)
                        with col1:
                            rows_to_show = st.slider("Filas a mostrar:", 5, min(100, len(df)), min(20, len(df)))
                        with col2:
                            if len(df.columns) > 10:
                                columns_to_show = st.multiselect(
                                    "Columnas a mostrar:",
                                    df.columns.tolist(),
                                    default=df.columns[:10].tolist()
                                )
                            else:
                                columns_to_show = df.columns.tolist()
                    
                    # Mostrar dataframe
                    if columns_to_show:
                        st.dataframe(
                            df[columns_to_show].head(rows_to_show),
                            use_container_width=True,
                            height=400
                        )
                    else:
                        st.dataframe(df.head(rows_to_show), use_container_width=True, height=400)
                    
                    # Descarga
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Descargar CSV",
                        data=csv,
                        file_name=f"monitor_ar_{source.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                    
                    # Guardar en session state para el gráfico
                    st.session_state['last_df'] = df
                else:
                    st.warning("⚠️ No se pudo generar una tabla con los datos obtenidos")
            
            # TAB 3: Gráfico
            with tab3:
                if 'last_df' in st.session_state:
                    df = st.session_state['last_df']
                    
                    fig = detect_and_plot_timeseries(df)
                    
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                        
                        st.success("✅ Serie temporal detectada y graficada automáticamente")
                    else:
                        st.info("ℹ️ No se detectó una serie temporal en los datos")
                        st.markdown("**Requisitos para graficar automáticamente:**")
                        st.markdown("- Debe existir una columna de fecha")
                        st.markdown("- Debe existir al menos una columna numérica")
                        
                        # Opción de gráfico manual
                        if not df.empty:
                            st.markdown("---")
                            st.subheader("🎨 Crear gráfico personalizado")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                x_col = st.selectbox("Eje X:", df.columns.tolist())
                            with col2:
                                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                                if numeric_cols:
                                    y_col = st.selectbox("Eje Y:", numeric_cols)
                                else:
                                    st.warning("No hay columnas numéricas disponibles")
                                    y_col = None
                            
                            if y_col and st.button("Generar gráfico"):
                                fig = px.line(df, x=x_col, y=y_col, title=f"{y_col} vs {x_col}")
                                st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("ℹ️ Primero consulte datos en la pestaña 'Tabla'")

if __name__ == "__main__":
    main()
