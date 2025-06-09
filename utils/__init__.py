"""
Módulo de utilitários
Contém configurações e funções auxiliares do sistema
"""

from .config import (
    get_s3_client,
    get_db_engine,
    get_s3_bucket,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_S3_BUCKET,
    AWS_REGION,
    DB_USER,
    DB_PASSWORD,
    DB_HOST,
    DB_PORT,
    DB_NAME
)

# Função para verificar configurações
def verificar_configuracoes():
    """Verifica se todas as configurações necessárias estão definidas"""
    import streamlit as st
    
    configs_necessarias = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY', 
        'AWS_S3_BUCKET',
        'DB_USER',
        'DB_PASSWORD',
        'DB_HOST',
        'DB_NAME'
    ]
    
    configs_faltando = []
    for config in configs_necessarias:
        if not st.secrets.get(config):
            configs_faltando.append(config)
    
    if configs_faltando:
        st.error(f"Configurações faltando: {', '.join(configs_faltando)}")
        return False
    
    return True

def init_system():
    """Inicializa o sistema completo"""
    from src.database import init_database
    from src.aws import test_aws_connection
    
    # Verificar configurações
    if not verificar_configuracoes():
        return False
    
    # Inicializar banco
    if not init_database():
        return False
    
    # Testar AWS
    if not test_aws_connection():
        return False
    
    return True

__all__ = [
    'get_s3_client',
    'get_db_engine', 
    'get_s3_bucket',
    'verificar_configuracoes',
    'init_system'
]
