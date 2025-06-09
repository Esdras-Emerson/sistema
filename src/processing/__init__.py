
"""
Módulo de processamento
Contém funções para processamento de arquivos Excel e dados
"""

try:
    from .excel_processor import (
        ler_dados_excel,
        validar_arquivo_excel,
        processar_multiplos_arquivos,
        obter_valor_celula
    )
except ImportError:
    # Definir funções vazias se o módulo não puder ser importado
    def ler_dados_excel(arquivo):
        return None
    
    def validar_arquivo_excel(arquivo):
        return False
    
    def processar_multiplos_arquivos(arquivos):
        return []
    
    def obter_valor_celula(df, linha, coluna):
        return None

# Configurações de processamento
FORMATOS_SUPORTADOS = ['.xls', '.xlsx']
CELULAS_OBRIGATORIAS = [
    'concessionaria', 'rodovia', 'obra', 'sentido', 'km',
    'estrutural', 'funcional', 'durabilidade'
]

def get_formatos_suportados():
    """Retorna lista de formatos de arquivo suportados"""
    return FORMATOS_SUPORTADOS

def get_celulas_obrigatorias():
    """Retorna lista de células obrigatórias"""
    return CELULAS_OBRIGATORIAS

__all__ = [
    'ler_dados_excel',
    'validar_arquivo_excel',
    'processar_multiplos_arquivos',
    'obter_valor_celula',
    'get_formatos_suportados',
    'get_celulas_obrigatorias',
    'FORMATOS_SUPORTADOS',
    'CELULAS_OBRIGATORIAS'
]

