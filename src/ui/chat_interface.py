import streamlit as st
import pandas as pd
import boto3
from io import BytesIO
from pathlib import Path
import tempfile
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores.faiss import FAISS
from langchain_openai.chat_models import ChatOpenAI 
from langchain.chains import RetrievalQA
from langchain.schema import Document
from src.database.crud_operations import obter_todos_registros
from src.aws.s3_handler import listar_arquivos_s3, baixar_arquivo_s3
from utils.config import get_s3_client, get_s3_bucket

def chat_interface():
    st.header('💬 Converse Comigo - Chat Inteligente Completo')
    
    # Verificar se OpenAI API key está configurada
    openai_api_key = st.secrets.get("OPENAI_API_KEY", "")
    if not openai_api_key:
        st.error("❌ Chave da API OpenAI não configurada. Adicione OPENAI_API_KEY no secrets.toml")
        return
    
    # Configurar OpenAI API key
    os.environ["OPENAI_API_KEY"] = openai_api_key
    
    # Seção de status dos dados
    mostrar_status_dados()
    
    # Botões de controle
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Recarregar Dados"):
            recarregar_todos_dados()
    
    with col2:
        if st.button("📊 Verificar Bucket S3"):
            verificar_arquivos_s3()
    
    with col3:
        if st.button("🗑️ Limpar Chat"):
            limpar_chat()
    
    # Inicializar chat se necessário
    if "chat_chain_completo" not in st.session_state:
        with st.spinner("🔄 Inicializando chat completo..."):
            if criar_chat_completo():
                st.success("✅ Chat completo inicializado!")
            else:
                st.error("❌ Erro ao inicializar chat")
                return
    
    # Interface do chat
    st.subheader("💭 Chat Inteligente - Fichas Excel + PDFs + Banco")
    st.info("💡 Faça perguntas sobre fichas, relatórios PDF e dados do sistema")
    
    # Área de histórico de mensagens
    if "chat_history_completo" not in st.session_state:
        st.session_state.chat_history_completo = []
    
    # Container para mensagens
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.chat_history_completo:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                if message["role"] == "assistant" and "sources" in message:
                    with st.expander("📄 Fontes consultadas"):
                        for source in message["sources"]:
                            st.write(f"• {source}")
    
    # Input do usuário
    user_input = st.chat_input("Digite sua pergunta sobre fichas, PDFs ou dados...")
    
    if user_input:
        # Adicionar mensagem do usuário
        st.session_state.chat_history_completo.append({"role": "user", "content": user_input})
        
        with st.chat_message("user"):
            st.write(user_input)
        
        # Processar resposta
        with st.chat_message("assistant"):
            with st.spinner("🤔 Consultando todos os dados..."):
                try:
                    response = st.session_state.chat_chain_completo({"query": user_input})
                    answer = response["result"]
                    sources = [doc.metadata.get("source", "Desconhecido") for doc in response.get("source_documents", [])]
                    
                    st.write(answer)
                    
                    if sources:
                        with st.expander("📄 Fontes consultadas"):
                            for source in set(sources):
                                st.write(f"• {source}")
                    
                    # Adicionar resposta ao histórico
                    st.session_state.chat_history_completo.append({
                        "role": "assistant", 
                        "content": answer,
                        "sources": list(set(sources))
                    })
                    
                except Exception as e:
                    st.error(f"Erro ao processar pergunta: {str(e)}")

def mostrar_status_dados():
    """Mostra status de todos os dados disponíveis - versão corrigida"""
    st.subheader("📊 Status dos Dados Disponíveis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Fichas no banco
        try:
            df = obter_todos_registros()
            if not df.empty:
                st.success(f"✅ {len(df)} fichas no banco")
                
                # Mostrar detalhes das fichas
                with st.expander("📋 Detalhes das fichas"):
                    concessionarias = df['concessionaria'].value_counts()
                    for conc, count in concessionarias.items():
                        st.write(f"• {conc}: {count} fichas")
            else:
                st.warning("⚠️ Nenhuma ficha no banco")
        except Exception as e:
            st.error(f"❌ Erro ao acessar banco: {str(e)}")
    
    with col2:
        # PDFs no S3
        try:
            # Tentar diferentes prefixos
            prefixos_pdf = ["relatorios_pdf/", "pdfs/", ""]
            pdfs_encontrados = []
            
            for prefixo in prefixos_pdf:
                pdfs = listar_arquivos_s3(prefixo)
                pdfs_pdf = [p for p in pdfs if p.lower().endswith('.pdf')]
                pdfs_encontrados.extend(pdfs_pdf)
            
            # Remover duplicatas
            pdfs_encontrados = list(set(pdfs_encontrados))
            
            if pdfs_encontrados:
                st.success(f"✅ {len(pdfs_encontrados)} PDFs no S3")
                with st.expander("📄 PDFs encontrados"):
                    for pdf in pdfs_encontrados:
                        st.write(f"• {pdf.split('/')[-1]}")
            else:
                st.warning("⚠️ Nenhum PDF no S3")
                
                # Debug: listar todos os arquivos
                todos_arquivos = listar_arquivos_s3("")
                if todos_arquivos:
                    st.info(f"Debug: {len(todos_arquivos)} arquivos total no S3")
                    with st.expander("🔍 Todos os arquivos no S3"):
                        for arquivo in todos_arquivos[:10]:  # Mostrar apenas 10
                            st.write(f"• {arquivo}")
                        if len(todos_arquivos) > 10:
                            st.write(f"... e mais {len(todos_arquivos) - 10} arquivos")
                            
        except Exception as e:
            st.error(f"❌ Erro ao acessar PDFs S3: {str(e)}")
    
    with col3:
        # Excels no S3
        try:
            # Tentar diferentes prefixos
            prefixos_excel = ["fichas_excel/", "excel/", ""]
            excels_encontrados = []
            
            for prefixo in prefixos_excel:
                excels = listar_arquivos_s3(prefixo)
                excels_excel = [e for e in excels if e.lower().endswith(('.xls', '.xlsx'))]
                excels_encontrados.extend(excels_excel)
            
            # Remover duplicatas
            excels_encontrados = list(set(excels_encontrados))
            
            if excels_encontrados:
                st.success(f"✅ {len(excels_encontrados)} Excels no S3")
                with st.expander("📊 Excels encontrados"):
                    for excel in excels_encontrados:
                        st.write(f"• {excel.split('/')[-1]}")
            else:
                st.warning("⚠️ Nenhum Excel no S3")
                
        except Exception as e:
            st.error(f"❌ Erro ao acessar Excels S3: {str(e)}")


def importar_dados_fichas_banco():
    """Importa dados das fichas do banco de dados - versão corrigida"""
    documentos = []
    
    try:
        df = obter_todos_registros()
        
        if not df.empty:
            st.info(f"📊 Carregando {len(df)} fichas do banco...")
            
            # Verificar se todas as colunas existem
            colunas_esperadas = ['id', 'concessionaria', 'rodovia', 'obra', 'sentido', 'km', 
                               'codigo', 'codigo_artesp', 'data_inspecao', 'ano_inspecao',
                               'orgao_regulador', 'tipo_pav', 'estrutural', 'funcional', 
                               'durabilidade', 'ic', 'uir', 'uie', 'data_upload', 'arquivo_s3']
            
            colunas_existentes = df.columns.tolist()
            st.info(f"🔍 Colunas disponíveis: {len(colunas_existentes)}")
            
            for index, row in df.iterrows():
                try:
                    texto_ficha = f"""
                    FICHA DE INSPEÇÃO - BANCO DE DADOS #{index + 1}
                    
                    ID: {row.get('id', 'N/A')}
                    Concessionária: {row.get('concessionaria', 'N/A')}
                    Rodovia: {row.get('rodovia', 'N/A')}
                    Obra: {row.get('obra', 'N/A')}
                    Sentido: {row.get('sentido', 'N/A')}
                    KM: {row.get('km', 'N/A')}
                    Código: {row.get('codigo', 'N/A')}
                    Código ARTESP: {row.get('codigo_artesp', 'N/A')}
                    
                    Data de Inspeção: {row.get('data_inspecao', 'N/A')}
                    Ano de Inspeção: {row.get('ano_inspecao', 'N/A')}
                    
                    Órgão Regulador: {row.get('orgao_regulador', 'N/A')}
                    Tipo de Pavimento: {row.get('tipo_pav', 'N/A')}
                    
                    CLASSIFICAÇÕES:
                    Estrutural: {row.get('estrutural', 'N/A')}
                    Funcional: {row.get('funcional', 'N/A')}
                    Durabilidade: {row.get('durabilidade', 'N/A')}
                    
                    IC: {row.get('ic', 'N/A')}
                    UIR: {row.get('uir', 'N/A')}
                    UIE: {row.get('uie', 'N/A')}
                    
                    Data de Upload: {row.get('data_upload', 'N/A')}
                    Arquivo S3: {row.get('arquivo_s3', 'N/A')}
                    """
                    
                    doc = Document(
                        page_content=texto_ficha,
                        metadata={
                            "source": f"Ficha_Banco_{row.get('codigo', f'ID_{row.get('id', index)}')}",
                            "tipo": "ficha_banco",
                            "concessionaria": str(row.get('concessionaria', '')),
                            "rodovia": str(row.get('rodovia', '')),
                            "ano": str(row.get('ano_inspecao', '')),
                            "doc_id": len(documentos),
                            "ficha_id": row.get('id', index)
                        }
                    )
                    documentos.append(doc)
                    
                except Exception as e:
                    st.warning(f"Erro ao processar ficha {index}: {str(e)}")
                    continue
            
            st.success(f"✅ {len(documentos)} fichas processadas para o chat")
        
        return documentos
        
    except Exception as e:
        st.error(f"Erro ao importar fichas do banco: {str(e)}")
        return []


def importar_pdfs_s3():
    """Importa e processa PDFs do S3"""
    documentos = []
    
    try:
        pdfs_s3 = listar_arquivos_s3("relatorios_pdf/")
        
        if pdfs_s3:
            st.info(f"📁 Processando {len(pdfs_s3)} PDFs do S3...")
            
            for arquivo in pdfs_s3[:10]:  # Limitar para performance
                try:
                    conteudo_pdf = baixar_arquivo_s3(arquivo)
                    
                    if conteudo_pdf:
                        # Processar PDF
                        texto_extraido = processar_pdf_bytes(conteudo_pdf, arquivo)
                        
                        if texto_extraido:
                            doc = Document(
                                page_content=texto_extraido,
                                metadata={
                                    "source": arquivo.split('/')[-1],
                                    "tipo": "pdf_s3",
                                    "arquivo_s3": arquivo,
                                    "doc_id": len(documentos)
                                }
                            )
                            documentos.append(doc)
                            st.success(f"✅ PDF processado: {arquivo.split('/')[-1]}")
                        
                except Exception as e:
                    st.warning(f"Erro ao processar PDF {arquivo}: {str(e)}")
        
        return documentos
        
    except Exception as e:
        st.warning(f"Erro ao acessar PDFs no S3: {str(e)}")
        return []

def importar_excels_s3():
    """Importa e processa arquivos Excel do S3"""
    documentos = []
    
    try:
        excels_s3 = listar_arquivos_s3("fichas_excel/")
        
        if excels_s3:
            st.info(f"📊 Processando {len(excels_s3)} Excels do S3...")
            
            for arquivo in excels_s3:
                try:
                    conteudo_excel = baixar_arquivo_s3(arquivo)
                    
                    if conteudo_excel:
                        # Processar Excel
                        dados_excel = processar_excel_bytes(conteudo_excel, arquivo)
                        
                        if dados_excel:
                            texto_excel = f"""
                            ARQUIVO EXCEL - {arquivo.split('/')[-1]}
                            
                            Concessionária: {dados_excel.get('concessionaria', 'N/A')}
                            Rodovia: {dados_excel.get('rodovia', 'N/A')}
                            Obra: {dados_excel.get('obra', 'N/A')}
                            Sentido: {dados_excel.get('sentido', 'N/A')}
                            KM: {dados_excel.get('km', 'N/A')}
                            Código: {dados_excel.get('codigo', 'N/A')}
                            
                            Data de Inspeção: {dados_excel.get('data_inspecao', 'N/A')}
                            Ano de Inspeção: {dados_excel.get('ano_inspecao', 'N/A')}
                            
                            Classificações:
                            Estrutural: {dados_excel.get('estrutural', 'N/A')}
                            Funcional: {dados_excel.get('funcional', 'N/A')}
                            Durabilidade: {dados_excel.get('durabilidade', 'N/A')}
                            
                            Arquivo S3: {arquivo}
                            """
                            
                            doc = Document(
                                page_content=texto_excel,
                                metadata={
                                    "source": arquivo.split('/')[-1],
                                    "tipo": "excel_s3",
                                    "arquivo_s3": arquivo,
                                    "doc_id": len(documentos)
                                }
                            )
                            documentos.append(doc)
                            st.success(f"✅ Excel processado: {arquivo.split('/')[-1]}")
                        
                except Exception as e:
                    st.warning(f"Erro ao processar Excel {arquivo}: {str(e)}")
        
        return documentos
        
    except Exception as e:
        st.warning(f"Erro ao acessar Excels no S3: {str(e)}")
        return []

def processar_pdf_bytes(conteudo_bytes, nome_arquivo):
    """Processa bytes de PDF e extrai texto"""
    import tempfile
    import os
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(conteudo_bytes)
            tmp_file_path = tmp_file.name
        
        texto_extraido = ""
        
        # Tentar com PyMuPDF
        try:
            import fitz
            doc = fitz.open(tmp_file_path)
            
            for page_num in range(min(5, len(doc))):  # Primeiras 5 páginas
                page = doc[page_num]
                page_text = page.get_text()
                if page_text.strip():
                    texto_extraido += f"\n=== PÁGINA {page_num + 1} ===\n"
                    texto_extraido += page_text[:1000] + "\n"  # Limitar tamanho
            
            doc.close()
            
        except Exception as e:
            st.warning(f"Erro ao processar PDF {nome_arquivo}: {str(e)}")
        
        # Limpar arquivo temporário
        try:
            os.unlink(tmp_file_path)
        except:
            pass
        
        return texto_extraido if texto_extraido.strip() else f"Conteúdo do PDF {nome_arquivo}"
        
    except Exception as e:
        st.error(f"Erro geral ao processar PDF: {str(e)}")
        return None

def processar_excel_bytes(conteudo_bytes, nome_arquivo):
    """Processa bytes de Excel e extrai dados"""
    try:
        from src.processing.excel_processor import ler_dados_excel
        from io import BytesIO
        
        # Criar objeto file-like
        excel_file = BytesIO(conteudo_bytes)
        excel_file.name = nome_arquivo
        
        # Processar Excel
        dados = ler_dados_excel(excel_file)
        return dados
        
    except Exception as e:
        st.warning(f"Erro ao processar Excel {nome_arquivo}: {str(e)}")
        return None

def criar_chat_completo():
    """Cria chat completo com todos os dados"""
    try:
        # Importar todos os tipos de documentos
        docs_banco = importar_dados_fichas_banco()
        docs_pdfs = importar_pdfs_s3()
        docs_excels = importar_excels_s3()
        
        # Combinar todos os documentos
        todos_documentos = docs_banco + docs_pdfs + docs_excels
        
        if not todos_documentos:
            st.error("Nenhum documento encontrado")
            return False
        
        st.info(f"📚 Total de documentos: {len(todos_documentos)}")
        st.info(f"   - Fichas do banco: {len(docs_banco)}")
        st.info(f"   - PDFs do S3: {len(docs_pdfs)}")
        st.info(f"   - Excels do S3: {len(docs_excels)}")
        
        # Dividir documentos
        documentos = split_documentos(todos_documentos)
        
        # Criar vector store
        vector_store = criar_vector_store(documentos)
        
        if not vector_store:
            return False
        
        # Configurar chat
        chat = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.1
        )
        
        # Configurar retriever
        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 8}  # Mais documentos para consulta
        )
        
        # Criar chain
        chat_chain = RetrievalQA.from_chain_type(
            llm=chat,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True
        )
        
        st.session_state["chat_chain_completo"] = chat_chain
        return True
        
    except Exception as e:
        st.error(f"Erro ao criar chat completo: {str(e)}")
        return False

def split_documentos(documentos):
    """Divide documentos em chunks"""
    if not documentos:
        return []
    
    recur_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    
    documentos_split = recur_splitter.split_documents(documentos)
    
    for i, doc in enumerate(documentos_split):
        doc.metadata["chunk_id"] = i
    
    return documentos_split

def criar_vector_store(documentos):
    """Cria vector store"""
    if not documentos:
        return None
    
    try:
        embedding_model = OpenAIEmbeddings()
        vector_store = FAISS.from_documents(
            documents=documentos,
            embedding=embedding_model
        )
        return vector_store
    except Exception as e:
        st.error(f"Erro ao criar vector store: {str(e)}")
        return None

def verificar_arquivos_s3():
    """Verifica arquivos no S3"""
    st.subheader("📁 Arquivos no S3")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**PDFs:**")
        pdfs = listar_arquivos_s3("relatorios_pdf/")
        for pdf in pdfs:
            st.write(f"• {pdf.split('/')[-1]}")
    
    with col2:
        st.write("**Excels:**")
        excels = listar_arquivos_s3("fichas_excel/")
        for excel in excels:
            st.write(f"• {excel.split('/')[-1]}")

def recarregar_todos_dados():
    """Recarrega todos os dados"""
    if "chat_chain_completo" in st.session_state:
        del st.session_state.chat_chain_completo
    st.success("🔄 Dados recarregados! Chat será reinicializado.")
    st.rerun()

def limpar_chat():
    """Limpa histórico do chat"""
    st.session_state.chat_history_completo = []
    st.success("🗑️ Chat limpo!")
    st.rerun()

