#!/usr/bin/env python3
"""
Script de prueba para validar conectividad con APIs
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from utils.api_helpers import obtener_tasas_bcra, obtener_emae
import pandas as pd

print("🧪 Iniciando pruebas de conectividad...")
print("=" * 60)

# Test BCRA
print("\n1️⃣ Probando API BCRA v3.0...")
print("-" * 60)
tasas = obtener_tasas_bcra()

for nombre, df in tasas.items():
    if not df.empty:
        print(f"✅ {nombre.upper()}: {len(df)} registros obtenidos")
        print(f"   Último valor: {df.iloc[-1]['valor']:.2f} ({df.iloc[-1]['fecha'].strftime('%Y-%m-%d')})")
    else:
        print(f"❌ {nombre.upper()}: Sin datos")

# Test EMAE
print("\n2️⃣ Probando EMAE (Datos.gob)...")
print("-" * 60)
df_emae = obtener_emae()

if not df_emae.empty:
    print(f"✅ EMAE: {len(df_emae)} registros obtenidos")
    print(f"   Último valor: {df_emae.iloc[-1]['valor']:.2f} ({df_emae.iloc[-1]['fecha'].strftime('%Y-%m-%d')})")
else:
    print(f"❌ EMAE: Sin datos")

print("\n" + "=" * 60)
print("✅ Pruebas finalizadas")
