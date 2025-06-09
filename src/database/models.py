from sqlalchemy import Table, Column, Integer, String, MetaData, Date, inspect, text, UniqueConstraint
from utils.config import get_db_engine
import streamlit as st

metadata = MetaData()

# Classificações por órgão
CLASSIFICACOES_ARTESP = ['C0', 'C1', 'C2', 'B2', 'B3', 'B4', 'A4', 'A5']
CLASSIFICACOES_ANTT = ['0', '1', '2', '3', '4', '5']

def obter_opcoes_classificacao(tipo_orgao):
    """Retorna as opções de classificação baseadas no órgão"""
    if tipo_orgao.lower() == 'artesp':
        return CLASSIFICACOES_ARTESP
    elif tipo_orgao.lower() == 'antt':
        return CLASSIFICACOES_ANTT
    else:
        return CLASSIFICACOES_ARTESP  # Padrão ARTESP

# Tabela com restrições únicas
fichas_table = Table('fichas_inspecao', metadata,
                    Column('id', Integer, primary_key=True, autoincrement=True),
                    Column('concessionaria', String(255)),
                    Column('rodovia', String(255)),
                    Column('obra', String(255)),
                    Column('sentido', String(100)),
                    Column('km', String(100)),
                    Column('ic', String(255)),
                    Column('uir', String(255)),
                    Column('uie', String(255)),
                    Column('data_inspecao', Date),
                    Column('ano_inspecao', Integer),
                    Column('codigo', String(255)),
                    Column('codigo_artesp', String(255)),
                    Column('tipo_pav', String(500)),
                    Column('orgao_regulador', String(50)),  # NOVO: ARTESP ou ANTT
                    Column('estrutural', String(10)),
                    Column('funcional', String(10)),
                    Column('durabilidade', String(10)),
                    Column('arquivo_s3', String(500)),
                    Column('data_upload', Date),
                    
                    # Restrições únicas
                    UniqueConstraint('codigo', 'data_inspecao', name='uq_ficha_codigo_data'),
                    UniqueConstraint('arquivo_s3', name='uq_arquivo_s3'),
                    UniqueConstraint('concessionaria', 'rodovia', 'km', 'ano_inspecao', name='uq_ficha_completa')
)

def verificar_duplicata_existe(dados):
    """Verifica se já existe uma ficha com os mesmos dados"""
    try:
        engine = get_db_engine()
        if engine is None:
            return False
        
        with engine.connect() as conn:
            # Verificar por código e data de inspeção
            if dados.get('codigo') and dados.get('data_inspecao'):
                query = text("""
                    SELECT COUNT(*) FROM fichas_inspecao 
                    WHERE codigo = :codigo AND data_inspecao = :data_inspecao
                """)
                result = conn.execute(query, {
                    'codigo': dados['codigo'],
                    'data_inspecao': dados['data_inspecao']
                })
                if result.scalar() > 0:
                    return True
            
            # Verificar por arquivo S3
            if dados.get('arquivo_s3'):
                query = text("""
                    SELECT COUNT(*) FROM fichas_inspecao 
                    WHERE arquivo_s3 = :arquivo_s3
                """)
                result = conn.execute(query, {'arquivo_s3': dados['arquivo_s3']})
                if result.scalar() > 0:
                    return True
        
        return False
        
    except Exception as e:
        st.error(f"Erro ao verificar duplicata: {str(e)}")
        return False

def verificar_tabela_existe():
    """Verifica se a tabela fichas_inspecao existe"""
    try:
        engine = get_db_engine()
        if engine is None:
            return False
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        return 'fichas_inspecao' in tables
    except Exception as e:
        st.error(f"Erro ao verificar tabela: {str(e)}")
        return False

def create_tables():
    """Cria as tabelas no banco de dados se não existirem"""
    try:
        engine = get_db_engine()
        if engine is None:
            st.error("Engine do banco não disponível")
            return False
        
        metadata.create_all(engine)
        st.success("✅ Tabela fichas_inspecao criada com sucesso!")
        return True
    except Exception as e:
        st.error(f"Erro ao criar tabelas: {str(e)}")
        return False

def get_fichas_table():
    """Retorna a tabela de fichas"""
    return fichas_table
