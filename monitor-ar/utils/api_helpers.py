import os
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import warnings
from datetime import datetime

warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# Configuración de caché
CACHE_DIR = '.cache'
os.makedirs(CACHE_DIR, exist_ok=True)

def crear_sesion_con_reintentos():
    """Crea sesión requests con estrategia de reintentos."""
    sesion = requests.Session()
    reintentos = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adaptador = HTTPAdapter(max_retries=reintentos)
    sesion.mount("http://", adaptador)
    sesion.mount("https://", adaptador)
    return sesion

def leer_cache_csv(nombre_archivo):
    """Lee un archivo CSV desde el directorio de caché."""
    ruta = os.path.join(CACHE_DIR, nombre_archivo)
    if os.path.exists(ruta):
        try:
            df = pd.read_csv(ruta)
            return df
        except Exception as e:
            print(f"⚠️ Error leyendo caché {nombre_archivo}: {e}")
            return None
    return None

def escribir_cache_csv(df, nombre_archivo):
    """Escribe un DataFrame en caché como CSV."""
    if df is None or df.empty:
        return
    ruta = os.path.join(CACHE_DIR, nombre_archivo)
    try:
        df.to_csv(ruta, index=False)
        print(f"✅ Caché guardado: {nombre_archivo}")
    except Exception as e:
        print(f"⚠️ Error escribiendo caché {nombre_archivo}: {e}")

def obtener_tasas_bcra():
    """
    Obtiene tasas del BCRA v3 con fallback a caché.
    Retorna dict con 3 DataFrames: {'TPM': df, 'BADLAR': df, 'PF_USD': df}
    Cada DataFrame tiene columnas: fecha, valor
    También retorna flag 'desde_cache' para cada serie.
    """
    base_url = "https://api.bcra.gob.ar/estadisticascambiarias/v1.0"
    
    series = {
        'TPM': {'endpoint': '/datos/tpm', 'cache': 'bcra_tpm.csv'},
        'BADLAR': {'endpoint': '/datos/badlar', 'cache': 'bcra_badlar.csv'},
        'PF_USD': {'endpoint': '/datos/tasasPasivas', 'cache': 'bcra_pf_usd.csv'}
    }
    
    sesion = crear_sesion_con_reintentos()
    resultado = {}
    
    for nombre, config in series.items():
        url = base_url + config['endpoint']
        df = None
        desde_cache = False
        
        try:
            print(f"🔄 Consultando BCRA: {nombre}...")
            respuesta = sesion.get(url, timeout=10, verify=False)
            respuesta.raise_for_status()
            
            data = respuesta.json()
            
            if 'results' in data and data['results']:
                registros = data['results']
                df = pd.DataFrame(registros)
                
                # Normalizar columnas
                if 'fecha' in df.columns and 'valor' in df.columns:
                    df = df[['fecha', 'valor']].copy()
                    df['fecha'] = pd.to_datetime(df['fecha'])
                    df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
                    df = df.dropna()
                    df = df.sort_values('fecha')
                    
                    # Guardar en caché
                    escribir_cache_csv(df, config['cache'])
                    print(f"✅ {nombre}: {len(df)} registros obtenidos")
                else:
                    raise ValueError(f"Estructura inesperada en respuesta de {nombre}")
            else:
                raise ValueError(f"Sin resultados en API para {nombre}")
                
        except Exception as e:
            print(f"❌ Error obteniendo {nombre} desde API: {e}")
            print(f"🔄 Intentando leer desde caché...")
            df = leer_cache_csv(config['cache'])
            
            if df is not None and not df.empty:
                # Normalizar caché
                if 'fecha' in df.columns and 'valor' in df.columns:
                    df['fecha'] = pd.to_datetime(df['fecha'])
                    df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
                    df = df.dropna()
                    desde_cache = True
                    print(f"✅ {nombre}: {len(df)} registros desde caché")
                else:
                    df = None
        
        resultado[nombre] = {
            'data': df,
            'desde_cache': desde_cache
        }
    
    return resultado

def obtener_emae():
    """
    Obtiene EMAE desde datos.gob.ar con fallback a caché.
    Retorna dict: {'data': DataFrame, 'desde_cache': bool}
    DataFrame tiene columnas: fecha, valor
    """
    url = "https://apis.datos.gob.ar/series/api/series/?ids=143.3_NO_PR_2004_A_21&limit=5000&format=csv"
    cache_nombre = 'emae.csv'
    
    df = None
    desde_cache = False
    sesion = crear_sesion_con_reintentos()
    
    try:
        print(f"🔄 Consultando EMAE desde datos.gob.ar...")
        respuesta = sesion.get(url, timeout=15)
        respuesta.raise_for_status()
        
        from io import StringIO
        df = pd.read_csv(StringIO(respuesta.text))
        
        # Normalizar columnas (el CSV de datos.gob tiene formato específico)
        if 'indice_tiempo' in df.columns and '143.3_NO_PR_2004_A_21' in df.columns:
            df = df.rename(columns={
                'indice_tiempo': 'fecha',
                '143.3_NO_PR_2004_A_21': 'valor'
            })
            df = df[['fecha', 'valor']].copy()
            df['fecha'] = pd.to_datetime(df['fecha'])
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
            df = df.dropna()
            df = df.sort_values('fecha')
            
            escribir_cache_csv(df, cache_nombre)
            print(f"✅ EMAE: {len(df)} registros obtenidos")
        else:
            raise ValueError("Estructura inesperada en respuesta de EMAE")
            
    except Exception as e:
        print(f"❌ Error obteniendo EMAE desde API: {e}")
        print(f"🔄 Intentando leer desde caché...")
        df = leer_cache_csv(cache_nombre)
        
        if df is not None and not df.empty:
            # Normalizar caché
            if 'fecha' in df.columns and 'valor' in df.columns:
                df['fecha'] = pd.to_datetime(df['fecha'])
                df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
                df = df.dropna()
                desde_cache = True
                print(f"✅ EMAE: {len(df)} registros desde caché")
            else:
                df = None
    
    return {
        'data': df,
        'desde_cache': desde_cache
    }
