import streamlit as st
import pandas as pd
import datetime
from src.database.crud_operations import (
    obter_todos_registros, 
    obter_registro_por_id,
    atualizar_registro,
    deletar_registro,
    criar_novo_registro
)
from src.database.models import obter_opcoes_classificacao

def crud_interface():
    st.header('🛠️ CRUD - Gerenciar Dados')
    
    operacao = st.selectbox(
        "Selecione a operação:",
        ["Visualizar", "Criar", "Atualizar", "Deletar"]
    )
    
    if operacao == "Visualizar":
        crud_read()
    elif operacao == "Criar":
        crud_create()
    elif operacao == "Atualizar":
        crud_update()
    elif operacao == "Deletar":
        crud_delete()

def crud_read():
    st.subheader("👀 Visualizar Registros")
    
    df = obter_todos_registros()
    
    if not df.empty:
        # Filtros para busca
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            concessionarias = ["Todas"] + list(df['concessionaria'].dropna().unique())
            concessionaria_filter = st.selectbox("Filtrar por Concessionária:", concessionarias)
        
        with col2:
            anos = ["Todos"] + list(sorted(df['ano_inspecao'].dropna().unique()))
            ano_filter = st.selectbox("Filtrar por Ano:", anos)
        
        with col3:
            rodovias = ["Todas"] + list(df['rodovia'].dropna().unique())
            rodovia_filter = st.selectbox("Filtrar por Rodovia:", rodovias)
        
        with col4:
            orgaos = ["Todos"] + list(df['orgao_regulador'].dropna().unique()) if 'orgao_regulador' in df.columns else ["Todos"]
            orgao_filter = st.selectbox("Filtrar por Órgão:", orgaos)
        
        # Aplicar filtros
        df_filtrado = df.copy()
        if concessionaria_filter != "Todas":
            df_filtrado = df_filtrado[df_filtrado['concessionaria'] == concessionaria_filter]
        if ano_filter != "Todos":
            df_filtrado = df_filtrado[df_filtrado['ano_inspecao'] == ano_filter]
        if rodovia_filter != "Todas":
            df_filtrado = df_filtrado[df_filtrado['rodovia'] == rodovia_filter]
        if orgao_filter != "Todos" and 'orgao_regulador' in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado['orgao_regulador'] == orgao_filter]
        
        st.dataframe(df_filtrado, use_container_width=True)
        
        # Downloads - CORRIGIDO PARA XLSX
        if not df_filtrado.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Download CSV
                csv = df_filtrado.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"fichas_inspecao_{datetime.date.today()}.csv",
                    mime="text/csv"
                )
            
            with col2:
                # Download XLSX - NOVO
                from io import BytesIO
                
                # Criar arquivo Excel em memória
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_filtrado.to_excel(writer, index=False, sheet_name='Fichas_Inspecao')
                
                # Obter dados do arquivo
                excel_data = output.getvalue()
                
                st.download_button(
                    label="📊 Download XLSX",
                    data=excel_data,
                    file_name=f"fichas_inspecao_{datetime.date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        # Estatísticas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total de Fichas", len(df_filtrado))
        with col2:
            st.metric("Concessionárias", df_filtrado['concessionaria'].nunique())
        with col3:
            st.metric("Rodovias", df_filtrado['rodovia'].nunique())
        with col4:
            st.metric("Anos", df_filtrado['ano_inspecao'].nunique())
    else:
        st.info("Nenhum registro encontrado")


def crud_create():
    st.subheader("➕ Criar Novo Registro")
    
    with st.form("criar_registro"):
        col1, col2 = st.columns(2)
        
        with col1:
            concessionaria = st.text_input("Concessionária*", help="Campo obrigatório")
            rodovia = st.text_input("Rodovia*", help="Campo obrigatório")
            obra = st.text_input("Obra")
            sentido = st.text_input("Sentido")
            km = st.text_input("KM*", help="Campo obrigatório")
            ic = st.text_input("IC")
            uir = st.text_input("UIR")
            uie = st.text_input("UIE")
            
            # NOVO: Seleção do órgão regulador
            orgao_regulador = st.selectbox("Órgão Regulador*", ["ARTESP", "ANTT"], help="Campo obrigatório")
        
        with col2:
            data_inspecao = st.date_input("Data de Inspeção*", help="Campo obrigatório")
            ano_inspecao = st.number_input("Ano de Inspeção*", min_value=2000, max_value=2030, value=2024, help="Campo obrigatório")
            codigo = st.text_input("Código*", help="Campo obrigatório - deve ser único")
            codigo_artesp = st.text_input("Código ARTESP")
            tipo_pav = st.text_input("Tipo de Pavimento")
            
            # Classificações baseadas no órgão selecionado
            opcoes_classificacao = obter_opcoes_classificacao(orgao_regulador)
            opcoes_com_vazio = [""] + opcoes_classificacao
            
            estrutural = st.selectbox("Estrutural*", opcoes_com_vazio, help="Campo obrigatório")
            funcional = st.selectbox("Funcional*", opcoes_com_vazio, help="Campo obrigatório")
            durabilidade = st.selectbox("Durabilidade*", opcoes_com_vazio, help="Campo obrigatório")
        
        submitted = st.form_submit_button("✅ Criar Registro", type="primary")
        
        if submitted:
            # Validar campos obrigatórios
            campos_obrigatorios = {
                'concessionaria': concessionaria,
                'rodovia': rodovia,
                'km': km,
                'data_inspecao': data_inspecao,
                'ano_inspecao': ano_inspecao,
                'codigo': codigo,
                'orgao_regulador': orgao_regulador,
                'estrutural': estrutural,
                'funcional': funcional,
                'durabilidade': durabilidade
            }
            
            campos_vazios = [nome for nome, valor in campos_obrigatorios.items() if not valor]
            
            if campos_vazios:
                st.error(f"❌ Campos obrigatórios não preenchidos: {', '.join(campos_vazios)}")
            else:
                dados = {
                    'concessionaria': concessionaria,
                    'rodovia': rodovia,
                    'obra': obra,
                    'sentido': sentido,
                    'km': km,
                    'ic': ic,
                    'uir': uir,
                    'uie': uie,
                    'data_inspecao': data_inspecao,
                    'ano_inspecao': int(ano_inspecao),
                    'codigo': codigo,
                    'codigo_artesp': codigo_artesp,
                    'tipo_pav': tipo_pav,
                    'orgao_regulador': orgao_regulador,
                    'estrutural': estrutural,
                    'funcional': funcional,
                    'durabilidade': durabilidade,
                    'arquivo_s3': f"manual_{codigo}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                }
                
                if criar_novo_registro(dados):
                    st.success("✅ Registro criado com sucesso!")
                    st.rerun()

def crud_update():
    st.subheader("✏️ Atualizar Registro")
    
    df = obter_todos_registros()
    
    if not df.empty:
        # Seleção do registro
        registro_opcoes = [f"ID {row['id']} - {row['codigo']} - {row['concessionaria']}" for _, row in df.iterrows()]
        registro_selecionado = st.selectbox("Selecione o registro para atualizar:", registro_opcoes)
        
        if registro_selecionado:
            registro_id = int(registro_selecionado.split(" - ")[0].replace("ID ", ""))
            registro_atual = obter_registro_por_id(registro_id)
            
            if registro_atual:
                with st.form("atualizar_registro"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        concessionaria = st.text_input("Concessionária", value=registro_atual.get('concessionaria', ''))
                        rodovia = st.text_input("Rodovia", value=registro_atual.get('rodovia', ''))
                        obra = st.text_input("Obra", value=registro_atual.get('obra', ''))
                        km = st.text_input("KM", value=registro_atual.get('km', ''))
                        
                        # Órgão regulador
                        orgao_atual = registro_atual.get('orgao_regulador', 'ARTESP')
                        orgao_regulador = st.selectbox("Órgão Regulador", ["ARTESP", "ANTT"], 
                                                     index=0 if orgao_atual == 'ARTESP' else 1)
                    
                    with col2:
                        # Classificações baseadas no órgão
                        opcoes_classificacao = obter_opcoes_classificacao(orgao_regulador)
                        
                        estrutural_atual = registro_atual.get('estrutural', '')
                        estrutural_index = opcoes_classificacao.index(estrutural_atual) if estrutural_atual in opcoes_classificacao else 0
                        estrutural = st.selectbox("Estrutural", opcoes_classificacao, index=estrutural_index)
                        
                        funcional_atual = registro_atual.get('funcional', '')
                        funcional_index = opcoes_classificacao.index(funcional_atual) if funcional_atual in opcoes_classificacao else 0
                        funcional = st.selectbox("Funcional", opcoes_classificacao, index=funcional_index)
                        
                        durabilidade_atual = registro_atual.get('durabilidade', '')
                        durabilidade_index = opcoes_classificacao.index(durabilidade_atual) if durabilidade_atual in opcoes_classificacao else 0
                        durabilidade = st.selectbox("Durabilidade", opcoes_classificacao, index=durabilidade_index)
                        
                        ano_inspecao = st.number_input("Ano de Inspeção", value=int(registro_atual.get('ano_inspecao', 2024)))
                    
                    submitted = st.form_submit_button("🔄 Atualizar Registro", type="primary")
                    
                    if submitted:
                        dados_atualizados = {
                            'concessionaria': concessionaria,
                            'rodovia': rodovia,
                            'obra': obra,
                            'km': km,
                            'orgao_regulador': orgao_regulador,
                            'estrutural': estrutural,
                            'funcional': funcional,
                            'durabilidade': durabilidade,
                            'ano_inspecao': ano_inspecao
                        }
                        
                        if atualizar_registro(registro_id, dados_atualizados):
                            st.rerun()
    else:
        st.info("Nenhum registro encontrado para atualizar")

def crud_delete():
    st.subheader("🗑️ Deletar Registro")
    
    df = obter_todos_registros()
    
    if not df.empty:
        # Seleção do registro
        registro_opcoes = [f"ID {row['id']} - {row['codigo']} - {row['concessionaria']}" for _, row in df.iterrows()]
        registro_selecionado = st.selectbox("Selecione o registro para deletar:", registro_opcoes)
        
        if registro_selecionado:
            registro_id = int(registro_selecionado.split(" - ")[0].replace("ID ", ""))
            registro = obter_registro_por_id(registro_id)
            
            if registro:
                st.write("**Registro selecionado:**")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Código:** {registro.get('codigo', 'N/A')}")
                    st.write(f"**Concessionária:** {registro.get('concessionaria', 'N/A')}")
                    st.write(f"**Rodovia:** {registro.get('rodovia', 'N/A')}")
                with col2:
                    st.write(f"**Ano:** {registro.get('ano_inspecao', 'N/A')}")
                    st.write(f"**Órgão:** {registro.get('orgao_regulador', 'N/A')}")
                    st.write(f"**Estrutural:** {registro.get('estrutural', 'N/A')}")
                
                st.warning("⚠️ Esta ação não pode ser desfeita!")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🗑️ Confirmar Exclusão", type="secondary"):
                        if deletar_registro(registro_id):
                            st.rerun()
                with col2:
                    if st.button("❌ Cancelar"):
                        st.rerun()
    else:
        st.info("Nenhum registro encontrado para deletar")

