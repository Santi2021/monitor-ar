"""
Monitor AR - MVP Sprint 1
Aplicación Streamlit para interactuar con Claude AI (Anthropic)

Repositorio: https://github.com/Santi2021/monitor-ar
"""

import streamlit as st
from anthropic import Anthropic, APIError, APIConnectionError
import sys

# ============================================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================================

st.set_page_config(
    page_title="Monitor AR",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

@st.cache_resource
def inicializar_cliente():
    """
    Inicializa el cliente de Anthropic usando la API key desde Streamlit Secrets.
    Se cachea para evitar reinicializaciones innecesarias.
    
    Returns:
        Anthropic: Cliente inicializado o None si hay error
    """
    try:
        api_key = st.secrets["ANTHROPIC_API_KEY"]
        return Anthropic(api_key=api_key)
    except KeyError:
        st.error("❌ Error: No se encontró ANTHROPIC_API_KEY en los secrets de Streamlit.")
        st.info("💡 Configura tu API key en `.streamlit/secrets.toml` (local) o en Streamlit Cloud (Settings > Secrets)")
        return None
    except Exception as e:
        st.error(f"❌ Error inesperado al inicializar cliente: {str(e)}")
        return None


def consultar_claude(cliente, pregunta, modelo="claude-3-5-sonnet-20241022"):
    """
    Envía una pregunta a Claude y obtiene la respuesta.
    
    Args:
        cliente (Anthropic): Cliente de Anthropic inicializado
        pregunta (str): Pregunta del usuario
        modelo (str): Modelo de Claude a utilizar
        
    Returns:
        tuple: (respuesta_texto, error_mensaje)
    """
    try:
        # Enviar mensaje a Claude
        response = cliente.messages.create(
            model=modelo,
            max_tokens=1024,
            messages=[
                {"role": "user", "content": pregunta}
            ]
        )
        
        # Extraer el texto de la respuesta
        respuesta = response.content[0].text
        return respuesta, None
        
    except APIConnectionError:
        return None, "❌ Error de conexión. Verifica tu conexión a internet e intenta nuevamente."
    
    except APIError as e:
        if "authentication" in str(e).lower() or "api_key" in str(e).lower():
            return None, "❌ Error de autenticación. Verifica que tu ANTHROPIC_API_KEY sea válida."
        else:
            return None, f"❌ Error de API: {str(e)}"
    
    except Exception as e:
        return None, f"❌ Error inesperado: {str(e)}"


# ============================================================================
# INTERFAZ PRINCIPAL
# ============================================================================

def main():
    """
    Función principal que construye la interfaz de la aplicación.
    """
    
    # Header
    st.title("🤖 Monitor AR")
    st.markdown("### Asistente impulsado por Claude AI")
    st.markdown("---")
    
    # Inicializar cliente de Anthropic
    cliente = inicializar_cliente()
    
    # Si no hay cliente válido, detener ejecución
    if cliente is None:
        st.stop()
    
    # Instrucciones para el usuario
    st.markdown("""
    **¿Cómo usar esta aplicación?**
    1. Escribe tu pregunta en el campo de texto
    2. Presiona el botón "Enviar a Claude"
    3. Espera la respuesta del asistente
    """)
    
    st.markdown("---")
    
    # Campo de entrada de texto
    pregunta = st.text_area(
        "💬 Escribe tu pregunta:",
        height=150,
        placeholder="Ejemplo: ¿Cuál es la capital de Argentina?",
        help="Escribe cualquier pregunta que quieras hacerle a Claude"
    )
    
    # Botón de envío
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        enviar = st.button("🚀 Enviar a Claude", type="primary", use_container_width=True)
    
    # Procesamiento al presionar el botón
    if enviar:
        # Validar que haya texto
        if not pregunta or pregunta.strip() == "":
            st.warning("⚠️ Por favor, escribe una pregunta antes de enviar.")
        else:
            # Mostrar spinner mientras se procesa
            with st.spinner("🤔 Claude está pensando..."):
                respuesta, error = consultar_claude(cliente, pregunta.strip())
            
            # Mostrar resultado
            if error:
                st.error(error)
            else:
                st.success("✅ Respuesta recibida:")
                st.markdown("---")
                # Mostrar respuesta en un contenedor especial
                with st.container():
                    st.markdown("**Respuesta de Claude:**")
                    st.write(respuesta)
                st.markdown("---")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray; font-size: 0.8em;'>
            Monitor AR v1.0 - MVP Sprint 1 | Powered by Claude (Anthropic)
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":
    main()
