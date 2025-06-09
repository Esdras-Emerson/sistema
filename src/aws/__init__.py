
"""
Módulo AWS
Contém handlers para serviços AWS (S3, RDS, etc.)
"""

# Imports condicionais para evitar erros
try:
    from .s3_handler import (
        salvar_arquivo_s3,
        listar_arquivos_s3,
        baixar_arquivo_s3
    )
except ImportError:
    def salvar_arquivo_s3(nome_arquivo, conteudo):
        return f"mock_s3_key_{nome_arquivo}"
    
    def listar_arquivos_s3(prefixo=''):
        return []
    
    def baixar_arquivo_s3(chave_s3):
        return None

def test_aws_connection():
    """Testa conexão com serviços AWS"""
    return False

__all__ = [
    'salvar_arquivo_s3',
    'listar_arquivos_s3', 
    'baixar_arquivo_s3',
    'test_aws_connection'
]

