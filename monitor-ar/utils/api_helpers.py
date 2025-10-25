cat > monitor-ar/utils/api_helpers.py << 'EOF'
import requests
import pandas as pd
import streamlit as st
from datetime import datetime
import urllib3

# Deshabilitar warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================
# 1️⃣ MÓDULO BCRA v3.0
# ============================================

def obtener_serie_bcra(id_variable: int, nombre_serie: str) -> pd.DataFrame:
    """
    Obtiene serie monetaria desde BCRA API v3.0
    
    Args:
        id_variable: ID de la serie (ej: 160, 145, 132)
        nombre_serie: Nombre descriptivo para logs
    
    Returns:
        DataFrame con columnas ['fecha', 'valor']
    """
    url = f"https://api.bcra.gob.ar/estadisticas/v3.0/Monetarias/{id_variable}"
    
    try:
        response = requests.get(url, verify=False, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if 'results' not in data:
            st.warning(f"⚠️ No se pudo obtener la serie monetaria del BCRA: {nombre_serie}")
            return pd.DataFrame()
        
        df = pd.DataFrame(data['results'])
        
        # Normalizar columnas
        if 'fecha' in df.columns and 'valor' in df.columns:
            df['fecha'] = pd.to_datetime(df['fecha'])
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
            return df[['fecha', 'valor']].dropna()
        else:
            st.warning(f"⚠️ Estructura inesperada en respuesta del BCRA para {nombre_serie}")
            return pd.DataFrame()
            
    except requests.exceptions.Timeout:
        st.warning(f"⚠️ Timeout al conectar con BCRA para {nombre_serie}")
        return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        st.warning(f"⚠️ No se pudo obtener la serie monetaria del BCRA: {nombre_serie}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"⚠️ Error inesperado al procesar {nombre_serie}: {str(e)}")
        return pd.DataFrame()


def obtener_tasas_bcra() -> dict:
    """
    Obtiene las 3 tasas principales del BCRA
    
    Returns:
        dict con keys: 'tpm', 'badlar', 'pf_usd'
    """
    tasas = {
        'tpm': obtener_serie_bcra(160, "Tasa de Política Monetaria"),
        'badlar': obtener_serie_bcra(145, "BADLAR Privados"),
        'pf_usd': obtener_serie_bcra(132, "PF USD Total")
    }
    
    return tasas


# ============================================
# 2️⃣ MÓDULO DATOS.GOB (EMAE)
# ============================================

def obtener_emae_api() -> pd.DataFrame:
    """
    Intenta obtener EMAE desde API Series
    
    Returns:
        DataFrame con columnas ['fecha', 'valor'] o vacío si falla
    """
    url = "https://apis.datos.gob.ar/series/api/series?ids=emae_desestacionalizada"
    
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        
        data = response.json()
        
        if 'data' in data and len(data['data']) > 0:
            df = pd.DataFrame(data['data'], columns=['fecha', 'valor'])
            df['fecha'] = pd.to_datetime(df['fecha'])
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
            
            st.success("✅ Datos EMAE cargados correctamente desde la API.")
            return df.dropna()
        else:
            return pd.DataFrame()
            
    except Exception as e:
        return pd.DataFrame()


def obtener_emae_csv_fallback() -> pd.DataFrame:
    """
    Fallback: descarga EMAE desde CSV
    
    Returns:
        DataFrame con columnas ['fecha', 'valor']
    """
    url = "https://infra.datos.gob.ar/catalog/sspm/dataset/143/distribution/143.3/download/emae-valores-anuales-indice-base-2004-mensual.csv"
    
    try:
        df = pd.read_csv(url)
        
        # Detectar columna de fecha (primera columna usualmente)
        fecha_col = df.columns[0]
        
        # Buscar columna que contenga "desestacionalizada"
        valor_col = None
        for col in df.columns:
            if 'desestacionalizada' in col.lower():
                valor_col = col
                break
        
        if valor_col is None:
            # Si no encuentra, usar segunda columna
            valor_col = df.columns[1]
        
        df_clean = df[[fecha_col, valor_col]].copy()
        df_clean.columns = ['fecha', 'valor']
        
        df_clean['fecha'] = pd.to_datetime(df_clean['fecha'], errors='coerce')
        df_clean['valor'] = pd.to_numeric(df_clean['valor'], errors='coerce')
        
        st.info("📊 Datos cargados desde fuente alternativa (CSV).")
        return df_clean.dropna()
        
    except Exception as e:
        st.warning("⚠️ No se pudo obtener el EMAE.")
        return pd.DataFrame()


def obtener_emae() -> pd.DataFrame:
    """
    Obtiene EMAE con sistema de fallback automático
    
    Returns:
        DataFrame con columnas ['fecha', 'valor']
    """
    # Intento 1: API
    df = obtener_emae_api()
    
    if not df.empty:
        return df
    
    # Intento 2: CSV Fallback
    df = obtener_emae_csv_fallback()
    
    return df
EOF
