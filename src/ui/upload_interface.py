import streamlit as st
import pandas as pd
import datetime
from src.processing.excel_processor import ler_dados_excel
from src.aws.s3_handler import salvar_arquivo_s3
from src.database.crud_operations import inserir_dados_banco, testar_conexao_banco

def upload_interface():
    st.header('📁 Upload de Arquivos')
    
    # Testar conexão com banco primeiro
    if st.button('🔍 Testar Conexão com Banco'):
        testar_conexao_banco()
    
    st.divider()
    
    # SEÇÃO 1: Upload de Fichas Excel
    st.subheader("📊 Insira suas fichas rotineiras em formato do Excel (XLS e XLSX)")
    st.info("💡 Faça upload das planilhas de fichas de inspeção rotineiras")
    
    uploaded_excel_files = st.file_uploader(
        'Escolha os arquivos Excel das fichas rotineiras',
        type=['xls', 'xlsx'],
        accept_multiple_files=True,
        help="Selecione um ou mais arquivos Excel com as fichas de inspeção",
        key="excel_uploader"
    )
    
    if uploaded_excel_files:
        st.success(f"✅ {len(uploaded_excel_files)} arquivo(s) Excel selecionado(s)")
        
        # Mostrar lista de arquivos selecionados
        with st.expander("📋 Arquivos Excel selecionados"):
            for arquivo in uploaded_excel_files:
                st.write(f"• {arquivo.name} ({arquivo.size} bytes)")
        
        if st.button('🚀 Processar Fichas Excel', type="primary", key="process_excel"):
            processar_arquivos_excel(uploaded_excel_files)
    
    st.divider()
    
    # SEÇÃO 2: Upload de PDFs
    st.subheader("📄 Insira o relatório 2 da sua inspeção especial no formato PDF")
    st.info("💡 Faça upload dos relatórios de inspeção especial em formato PDF")
    
    uploaded_pdf_files = st.file_uploader(
        'Escolha os arquivos PDF dos relatórios de inspeção especial',
        type=['pdf'],
        accept_multiple_files=True,
        help="Selecione um ou mais arquivos PDF com os relatórios de inspeção especial",
        key="pdf_uploader"
    )
    
    if uploaded_pdf_files:
        st.success(f"✅ {len(uploaded_pdf_files)} arquivo(s) PDF selecionado(s)")
        
        # Mostrar lista de arquivos PDF selecionados
        with st.expander("📋 Arquivos PDF selecionados"):
            for arquivo in uploaded_pdf_files:
                st.write(f"• {arquivo.name} ({arquivo.size} bytes)")
        
        if st.button('📄 Processar Relatórios PDF', type="secondary", key="process_pdf"):
            processar_arquivos_pdf(uploaded_pdf_files)
    
    st.divider()
    
    # SEÇÃO 3: Estatísticas e Informações
    mostrar_estatisticas_upload()

def processar_arquivos_excel(uploaded_files):
    """Processa arquivos Excel das fichas rotineiras"""
    st.subheader("🔄 Processando Fichas Excel")
    
    progress_bar = st.progress(0)
    dados_processados = []
    
    for i, arquivo in enumerate(uploaded_files):
        st.write(f"📄 Processando ficha: {arquivo.name}")
        
        try:
            # Ler dados do Excel
            dados = ler_dados_excel(arquivo)
            
            if dados:
                st.write(f"✅ Dados extraídos de {arquivo.name}")
                
                # Salvar no S3 na pasta específica para fichas
                try:
                    chave_s3 = salvar_arquivo_s3(f"fichas_excel/{arquivo.name}", arquivo)
                    if chave_s3:
                        dados['arquivo_s3'] = chave_s3
                        st.write(f"📁 Ficha salva no S3: {chave_s3}")
                    else:
                        dados['arquivo_s3'] = f"local_fichas_{arquivo.name}"
                        st.warning("S3 não configurado, usando referência local")
                except Exception as e:
                    st.warning(f"Erro no S3: {str(e)}")
                    dados['arquivo_s3'] = f"local_fichas_{arquivo.name}"
                
                dados_processados.append(dados)
            else:
                st.error(f"❌ Falha ao extrair dados de {arquivo.name}")
                
        except Exception as e:
            st.error(f"❌ Erro ao processar {arquivo.name}: {str(e)}")
        
        progress_bar.progress((i + 1) / len(uploaded_files))
    
    # Inserir fichas no banco
    if dados_processados:
        st.write(f"📊 Total de {len(dados_processados)} ficha(s) processada(s)")
        
        # Mostrar preview tabular das fichas
        st.subheader("📋 Preview das Fichas Processadas")
        df_preview = pd.DataFrame(dados_processados)
        st.dataframe(df_preview, use_container_width=True)
        
        st.write("🔄 Inserindo fichas no banco de dados...")
        
        # Tentar inserir no banco
        sucesso = inserir_dados_banco(dados_processados)
        
        if sucesso:
            st.success(f"✅ {len(dados_processados)} ficha(s) inserida(s) no banco com sucesso!")
        else:
            st.error("❌ Falha ao inserir fichas no banco")
            
            # Salvar dados localmente como backup
            df_backup = pd.DataFrame(dados_processados)
            csv_backup = df_backup.to_csv(index=False)
            st.download_button(
                label="📥 Download das fichas (backup)",
                data=csv_backup,
                file_name=f"backup_fichas_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    else:
        st.warning("⚠️ Nenhuma ficha foi processada com sucesso")

def processar_arquivos_pdf(uploaded_files):
    """Processa arquivos PDF dos relatórios de inspeção especial - CORRIGIDO"""
    st.subheader("📄 Processando Relatórios PDF")
    
    progress_bar = st.progress(0)
    pdfs_processados = []
    
    for i, arquivo in enumerate(uploaded_files):
        st.write(f"📄 Processando relatório: {arquivo.name}")
        
        try:
            # Verificar se o arquivo não está vazio
            arquivo.seek(0)  # Voltar ao início
            file_size = len(arquivo.read())
            arquivo.seek(0)  # Voltar ao início novamente
            
            if file_size == 0:
                st.error(f"❌ Arquivo {arquivo.name} está vazio")
                continue
            
            st.info(f"📊 Tamanho do arquivo: {file_size} bytes")
            
            # Salvar PDF no S3 na pasta específica para relatórios
            from src.aws.s3_handler import salvar_pdf_sem_duplicata
            chave_s3 = salvar_pdf_sem_duplicata(arquivo.name, arquivo, "relatorios_pdf")
            
            if chave_s3:
                st.success(f"✅ {arquivo.name} salvo no S3")
                st.write(f"📁 Localização: {chave_s3}")
                
                # Tentar processar o PDF para extrair texto
                try:
                    texto_extraido = processar_pdf_para_texto(arquivo)
                    if texto_extraido:
                        st.success(f"📖 Texto extraído com sucesso ({len(texto_extraido)} caracteres)")
                        
                        # Mostrar preview do texto
                        with st.expander(f"👁️ Preview do texto de {arquivo.name}"):
                            st.text_area("Texto extraído:", texto_extraido[:1000] + "..." if len(texto_extraido) > 1000 else texto_extraido, height=200)
                    else:
                        st.warning(f"⚠️ Não foi possível extrair texto de {arquivo.name}")
                        
                except Exception as e:
                    st.warning(f"⚠️ Erro ao extrair texto: {str(e)}")
                
                pdfs_processados.append({
                    'nome': arquivo.name,
                    'tamanho': file_size,
                    'chave_s3': chave_s3,
                    'data_upload': datetime.datetime.now(),
                    'tipo': 'relatorio_inspecao_especial',
                    'status': 'processado'
                })
                
            else:
                st.error(f"❌ Erro ao salvar {arquivo.name}")
                
        except Exception as e:
            st.error(f"❌ Erro ao processar {arquivo.name}: {str(e)}")
        
        progress_bar.progress((i + 1) / len(uploaded_files))
    
    # Mostrar resumo dos PDFs processados
    if pdfs_processados:
        st.success(f"🎉 {len(pdfs_processados)} relatório(s) PDF processado(s) com sucesso!")
        
        # Mostrar tabela de PDFs processados
        st.subheader("📋 Relatórios PDF Processados")
        df_pdfs = pd.DataFrame(pdfs_processados)
        st.dataframe(df_pdfs, use_container_width=True)
        
        st.info("💡 Os relatórios PDF estão disponíveis para consulta no chat inteligente (seção 'Converse Comigo')")
        
    else:
        st.warning("⚠️ Nenhum relatório PDF foi processado com sucesso")

def processar_pdf_para_texto_docling(arquivo):
    """Extrai texto de PDF usando Docling - versão avançada"""
    import tempfile
    import os
    
    try:
        # Salvar arquivo temporariamente
        arquivo.seek(0)
        conteudo_bytes = arquivo.read()
        arquivo.seek(0)
        
        if len(conteudo_bytes) == 0:
            st.error("❌ Arquivo PDF está vazio")
            return None
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(conteudo_bytes)
            tmp_file_path = tmp_file.name
        
        # Usar Docling para extração
        try:
            from docling.document_converter import DocumentConverter
            
            converter = DocumentConverter()
            result = converter.convert(tmp_file_path)
            
            # Extrair texto estruturado
            texto_extraido = result.document.export_to_markdown()
            
            if texto_extraido.strip():
                st.success(f"✅ Texto extraído com Docling: {len(texto_extraido)} caracteres")
                
                # Mostrar preview estruturado
                with st.expander(f"📖 Preview estruturado de {arquivo.name}"):
                    st.markdown(texto_extraido[:2000] + "..." if len(texto_extraido) > 2000 else texto_extraido)
                
                return texto_extraido
            
        except ImportError:
            st.warning("Docling não disponível, usando método alternativo...")
            return processar_pdf_metodo_alternativo(tmp_file_path)
        except Exception as e:
            st.warning(f"Docling falhou: {str(e)}, tentando método alternativo...")
            return processar_pdf_metodo_alternativo(tmp_file_path)
        
    except Exception as e:
        st.error(f"Erro geral: {str(e)}")
        return None
    finally:
        try:
            if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
        except:
            pass

def processar_pdf_metodo_alternativo(tmp_file_path):
    """Método alternativo caso Docling falhe"""
    try:
        import PyMuPDF as fitz
        doc = fitz.open(tmp_file_path)
        
        texto_extraido = ""
        for page_num in range(min(10, len(doc))):
            page = doc[page_num]
            texto_extraido += f"\n=== PÁGINA {page_num + 1} ===\n"
            texto_extraido += page.get_text() + "\n"
        
        doc.close()
        return texto_extraido
        
    except Exception as e:
        st.error(f"Método alternativo falhou: {str(e)}")
        return None

        
    except Exception as e:
        st.error(f"Erro geral no processamento de PDF: {str(e)}")
        return None
    finally:
        # Limpar arquivo temporário
        try:
            if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
        except:
            pass

def mostrar_estatisticas_upload():
    """Mostra estatísticas dos uploads"""
    st.subheader("📊 Informações do Sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **📊 Fichas Excel:**
        - Dados estruturados das inspeções
        - Armazenados no banco de dados
        - Disponíveis para visualização e análise
        - Formatos aceitos: .xls, .xlsx
        """)
    
    with col2:
        st.info("""
        **📄 Relatórios PDF:**
        - Documentos de inspeção especial
        - Armazenados no S3
        - Disponíveis para consulta via chat
        - Formato aceito: .pdf
        """)
    
    # Verificar dados existentes
    try:
        from src.database.crud_operations import obter_todos_registros
        df = obter_todos_registros()
        
        if not df.empty:
            st.success(f"✅ {len(df)} fichas já cadastradas no sistema")
        else:
            st.info("ℹ️ Nenhuma ficha cadastrada ainda")
            
    except Exception as e:
        st.warning("⚠️ Não foi possível verificar fichas existentes")
    
    # Verificar PDFs no S3
    try:
        from src.aws.s3_handler import listar_arquivos_s3
        pdfs_fichas = listar_arquivos_s3("fichas_excel/")
        pdfs_relatorios = listar_arquivos_s3("relatorios_pdf/")
        
        if pdfs_fichas or pdfs_relatorios:
            st.success(f"✅ {len(pdfs_fichas)} fichas Excel e {len(pdfs_relatorios)} relatórios PDF no S3")
        else:
            st.info("ℹ️ Nenhum arquivo no S3 ainda")
            
    except Exception as e:
        st.warning("⚠️ Não foi possível verificar arquivos no S3")




