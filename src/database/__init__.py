"""
Módulo de banco de dados
Contém modelos e operações CRUD para o sistema de fichas
"""

try:
    from .models import (
        fichas_table,
        create_tables,
        get_fichas_table,
        metadata,
        verificar_tabela_existe
    )
except ImportError:
    fichas_table = None
    create_tables = lambda: False
    get_fichas_table = lambda: None
    metadata = None
    verificar_tabela_existe = lambda: False

try:
    from .crud_operations import (
        inserir_dados_banco,
        obter_todos_registros,
        atualizar_registro,
        deletar_registro,
        criar_novo_registro,
        obter_registro_por_id,
        testar_conexao_banco
    )
except ImportError:
    # Funções vazias se não conseguir importar
    inserir_dados_banco = lambda x: False
    obter_todos_registros = lambda: []
    atualizar_registro = lambda x, y: False
    deletar_registro = lambda x: False
    criar_novo_registro = lambda x: False
    obter_registro_por_id = lambda x: None
    testar_conexao_banco = lambda: False

def init_database():
    """Inicializa o banco de dados criando as tabelas necessárias"""
    try:
        return create_tables()
    except Exception as e:
        print(f"Erro ao inicializar banco: {e}")
        return False

__all__ = [
    'fichas_table',
    'create_tables',
    'get_fichas_table',
    'metadata',
    'verificar_tabela_existe',
    'inserir_dados_banco',
    'obter_todos_registros',
    'atualizar_registro',
    'deletar_registro',
    'criar_novo_registro',
    'obter_registro_por_id',
    'testar_conexao_banco',
    'init_database'
]
