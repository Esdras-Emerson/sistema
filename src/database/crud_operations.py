import streamlit as st
import pandas as pd
import datetime
from utils.config import get_db_engine
from src.database.models import get_fichas_table, create_tables, verificar_tabela_existe, verificar_duplicata_existe
from sqlalchemy import text

def inserir_dados_banco(dados_lista):
    """Insere dados no banco com verificação de duplicatas"""
    try:
        if not verificar_tabela_existe():
            if not create_tables():
                return False
        
        engine = get_db_engine()
        fichas_table = get_fichas_table()
        
        dados_inseridos = []
        dados_duplicados = []
        
        for dados in dados_lista:
            dados['data_upload'] = datetime.date.today()
            
            if verificar_duplicata_existe(dados):
                dados_duplicados.append(dados)
                st.warning(f"⚠️ Ficha duplicada ignorada: {dados.get('codigo', 'sem código')}")
            else:
                dados_inseridos.append(dados)
        
        if dados_inseridos:
            with engine.begin() as conn:
                for dados in dados_inseridos:
                    try:
                        stmt = fichas_table.insert().values(**dados)
                        conn.execute(stmt)
                    except Exception as e:
                        if "duplicate key" in str(e) or "UNIQUE constraint" in str(e):
                            st.warning(f"⚠️ Duplicata detectada pelo banco: {dados.get('codigo', 'sem código')}")
                        else:
                            raise e
            
            st.success(f"✅ {len(dados_inseridos)} ficha(s) inserida(s) com sucesso!")
        
        if dados_duplicados:
            st.info(f"ℹ️ {len(dados_duplicados)} ficha(s) duplicada(s) foram ignoradas")
        
        return len(dados_inseridos) > 0
        
    except Exception as e:
        st.error(f"Erro ao inserir no banco: {str(e)}")
        return False

def obter_todos_registros():
    """Obtém todos os registros do banco"""
    try:
        if not verificar_tabela_existe():
            if not create_tables():
                return pd.DataFrame()
        
        engine = get_db_engine()
        if engine is None:
            return pd.DataFrame()
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM fichas_inspecao"))
            count = result.scalar()
            
            if count == 0:
                st.info("Tabela vazia. Faça upload de arquivos para popular os dados.")
                return pd.DataFrame()
            
            df = pd.read_sql(text("SELECT * FROM fichas_inspecao ORDER BY data_upload DESC"), conn)
            return df
            
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return pd.DataFrame()

def obter_registro_por_id(registro_id):
    """Obtém um registro específico por ID"""
    try:
        engine = get_db_engine()
        if engine is None:
            st.error("Conexão com banco não disponível")
            return None

        with engine.connect() as conn:
            query = text("SELECT * FROM fichas_inspecao WHERE id = :id")
            df = pd.read_sql(query, conn, params={"id": registro_id})

            if not df.empty:
                return df.iloc[0].to_dict()
            return None

    except Exception as e:
        st.error(f"Erro ao obter registro: {str(e)}")
        return None

def atualizar_registro(registro_id, dados):
    """Atualiza um registro específico"""
    try:
        engine = get_db_engine()
        fichas_table = get_fichas_table()
        
        # Verificar se a atualização não criará duplicata
        if dados.get('codigo'):
            with engine.connect() as conn:
                query = text("""
                    SELECT COUNT(*) FROM fichas_inspecao 
                    WHERE codigo = :codigo AND id != :id
                """)
                result = conn.execute(query, {'codigo': dados['codigo'], 'id': registro_id})
                if result.scalar() > 0:
                    st.error("❌ Já existe outra ficha com este código")
                    return False
        
        with engine.begin() as conn:
            stmt = fichas_table.update().where(fichas_table.c.id == registro_id).values(**dados)
            result = conn.execute(stmt)
            
            if result.rowcount > 0:
                st.success("✅ Registro atualizado com sucesso!")
                return True
            else:
                st.warning("⚠️ Nenhum registro foi atualizado")
                return False
                
    except Exception as e:
        st.error(f"Erro ao atualizar: {str(e)}")
        return False

def deletar_registro(registro_id):
    """Deleta um registro específico"""
    try:
        engine = get_db_engine()
        fichas_table = get_fichas_table()
        
        with engine.begin() as conn:
            stmt = fichas_table.delete().where(fichas_table.c.id == registro_id)
            result = conn.execute(stmt)
            
            if result.rowcount > 0:
                st.success("✅ Registro deletado com sucesso!")
                return True
            else:
                st.warning("⚠️ Nenhum registro foi deletado")
                return False
                
    except Exception as e:
        st.error(f"Erro ao deletar: {str(e)}")
        return False

def criar_novo_registro(dados):
    """Cria um novo registro com verificação de duplicata"""
    if verificar_duplicata_existe(dados):
        st.error("❌ Já existe uma ficha com estes dados")
        return False
    
    dados['data_upload'] = datetime.date.today()
    return inserir_dados_banco([dados])

def testar_conexao_banco():
    """Testa a conexão com o banco de dados"""
    try:
        engine = get_db_engine()
        if engine:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                st.success("✅ Conexão com banco estabelecida com sucesso!")
                return True
        else:
            st.error("❌ Engine do banco não disponível")
            return False
    except Exception as e:
        st.error(f"❌ Erro na conexão: {str(e)}")
        return False
