# src/ui/__init__.py
"""
Módulo de interface do usuário
Contém todas as interfaces Streamlit do sistema
"""

# Configurações da UI
UI_CONFIG = {
    'page_title': 'Sistema de Fichas de Inspeção',
    'page_icon': '🔧',
    'layout': 'wide',
    'initial_sidebar_state': 'expanded'
}

def get_ui_config():
    """Retorna configurações padrão da UI"""
    return UI_CONFIG

def setup_page_config():
    """Configura a página Streamlit com configurações padrão"""
    import streamlit as st
    st.set_page_config(**UI_CONFIG)

# Imports condicionais para evitar erros
try:
    from .upload_interface import upload_interface
except ImportError:
    upload_interface = None

try:
    from .visualization_interface import visualizacao_interface
except ImportError:
    visualizacao_interface = None

try:
    from .crud_interface import crud_interface
except ImportError:
    crud_interface = None

__all__ = [
    'upload_interface',
    'visualizacao_interface', 
    'crud_interface',
    'get_ui_config',
    'setup_page_config',
    'UI_CONFIG'
]
