import streamlit as st
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def inicializar_sistema():
    """Inicializa o sistema criando tabelas necessárias"""
    try:
        from src.database.models import create_tables
        return create_tables()
    except Exception as e:
        st.error(f"Erro na inicialização: {str(e)}")
        return False

def main():
    st.set_page_config(page_title="Sistema de Fichas de Inspeção", layout="wide")
    
    st.title('🔧 Sistema de Gestão de Fichas de Inspeção')
    
    # Inicializar sistema na primeira execução
    if 'sistema_inicializado' not in st.session_state:
        with st.spinner('Inicializando sistema...'):
            if inicializar_sistema():
                st.session_state.sistema_inicializado = True
                st.success("✅ Sistema inicializado com sucesso!")
            else:
                st.warning("⚠️ Sistema funcionando em modo limitado")
                st.session_state.sistema_inicializado = True
    
    # Navegação - ADICIONADA NOVA OPÇÃO
    st.sidebar.title("Navegação")
    opcao = st.sidebar.selectbox(
        "Escolha uma opção:",
        ["Upload de Arquivos", "Visualização de Dados", "CRUD - Gerenciar Dados", "Converse Comigo"]
    )
    
    # Importações condicionais
    if opcao == "Upload de Arquivos":
        try:
            from src.ui.upload_interface import upload_interface
            upload_interface()
        except ImportError as e:
            st.error(f"Módulo não encontrado: {e}")
            st.info("Funcionalidade em desenvolvimento")
    
    elif opcao == "Visualização de Dados":
        try:
            from src.ui.visualization_interface import visualizacao_interface
            visualizacao_interface()
        except ImportError as e:
            st.error(f"Módulo não encontrado: {e}")
            st.info("Funcionalidade em desenvolvimento")
    
    elif opcao == "CRUD - Gerenciar Dados":
        try:
            from src.ui.crud_interface import crud_interface
            crud_interface()
        except ImportError as e:
            st.error(f"Módulo não encontrado: {e}")
            st.info("Funcionalidade em desenvolvimento")
    
    elif opcao == "Converse Comigo":  # NOVA SEÇÃO
        try:
            from src.ui.chat_interface import chat_interface
            chat_interface()
        except ImportError as e:
            st.error(f"Módulo não encontrado: {e}")
            st.info("Instale as dependências: pip install langchain langchain-openai langchain-community faiss-cpu")

if __name__ == "__main__":
    main()

