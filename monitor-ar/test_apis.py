import sys
from datetime import datetime
from api_helpers from utils.api_helpers import obtener_tasas_bcra, obtener_emae


def imprimir_separador():
    print("\n" + "="*70 + "\n")

def test_tasas_bcra():
    """Prueba la obtención de tasas del BCRA con manejo de caché."""
    print("🧪 TEST: Tasas BCRA")
    print("-" * 70)
    
    try:
        tasas = obtener_tasas_bcra()
        
        for nombre, info in tasas.items():
            df = info.get('data')
            desde_cache = info.get('desde_cache', False)
            
            print(f"\n📊 Serie: {nombre}")
            
            if df is not None and not df.empty:
                print(f"   ✅ Registros: {len(df)}")
                print(f"   📅 Rango: {df['fecha'].min()} → {df['fecha'].max()}")
                print(f"   💾 Origen: {'CACHÉ LOCAL' if desde_cache else 'API ONLINE'}")
                print(f"   📈 Último valor: {df.iloc[-1]['valor']:.2f} ({df.iloc[-1]['fecha'].strftime('%Y-%m-%d')})")
                
                if desde_cache:
                    print(f"   ⚠️  Usando datos guardados localmente")
            else:
                print(f"   ❌ Sin datos disponibles (ni online ni caché)")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR en test de tasas BCRA: {e}")
        return False

def test_emae():
    """Prueba la obtención de EMAE con manejo de caché."""
    print("🧪 TEST: EMAE")
    print("-" * 70)
    
    try:
        emae_info = obtener_emae()
        df = emae_info.get('data')
        desde_cache = emae_info.get('desde_cache', False)
        
        print(f"\n📊 Serie: EMAE (Estimador Mensual de Actividad Económica)")
        
        if df is not None and not df.empty:
            print(f"   ✅ Registros: {len(df)}")
            print(f"   📅 Rango: {df['fecha'].min()} → {df['fecha'].max()}")
            print(f"   💾 Origen: {'CACHÉ LOCAL' if desde_cache else 'API ONLINE'}")
            print(f"   📈 Último valor: {df.iloc[-1]['valor']:.2f} ({df.iloc[-1]['fecha'].strftime('%Y-%m-%d')})")
            
            if desde_cache:
                print(f"   ⚠️  Usando datos guardados localmente")
        else:
            print(f"   ❌ Sin datos disponibles (ni online ni caché)")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR en test de EMAE: {e}")
        return False

def main():
    print("\n" + "🚀 MONITOR AR - TEST DE APIs CON SISTEMA DE CACHÉ ".center(70, "="))
    print(f"⏰ Hora de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    imprimir_separador()
    
    # Test BCRA
    exito_bcra = test_tasas_bcra()
    
    imprimir_separador()
    
    # Test EMAE
    exito_emae = test_emae()
    
    imprimir_separador()
    
    # Resumen
    print("📋 RESUMEN DE PRUEBAS")
    print("-" * 70)
    print(f"   BCRA Tasas: {'✅ OK' if exito_bcra else '❌ FALLÓ'}")
    print(f"   EMAE:       {'✅ OK' if exito_emae else '❌ FALLÓ'}")
    
    if exito_bcra and exito_emae:
        print("\n✅ Todas las pruebas completadas exitosamente")
        print("💡 El sistema está usando caché cuando las APIs no responden")
        return 0
    else:
        print("\n⚠️  Algunas pruebas fallaron - revisar logs arriba")
        return 1

if __name__ == "__main__":
    sys.exit(main())
