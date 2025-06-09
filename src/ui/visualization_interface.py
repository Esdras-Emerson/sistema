
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def visualizacao_interface():
    st.header('📊 Visualização de Dados')
    
    # Tentar carregar dados do banco
    try:
        from src.database.crud_operations import obter_todos_registros
        df = obter_todos_registros()
        
        if df.empty:
            st.warning("⚠️ Nenhum dado encontrado no banco de dados")
            st.info("Faça upload de alguns arquivos primeiro na seção 'Upload de Arquivos'")
            return
        
        # Filtros - CORRIGIDO PARA INCLUIR DURABILIDADE
        col1, col2, col3, col4 = st.columns(4)  # Mudança: 4 colunas em vez de 3
        
        with col1:
            anos_disponiveis = sorted(df['ano_inspecao'].dropna().unique())
            if len(anos_disponiveis) > 0:
                anos_selecionados = st.multiselect(
                    "Selecione os anos:",
                    anos_disponiveis,
                    default=anos_disponiveis
                )
            else:
                anos_selecionados = []
        
        with col2:
            estrutural_options = df['estrutural'].dropna().unique()
            estrutural_filter = st.multiselect(
                "Classificação Estrutural:",
                estrutural_options,
                default=estrutural_options
            )
        
        with col3:
            funcional_options = df['funcional'].dropna().unique()
            funcional_filter = st.multiselect(
                "Classificação Funcional:",
                funcional_options,
                default=funcional_options
            )
        
        with col4:  # NOVA COLUNA PARA DURABILIDADE
            durabilidade_options = df['durabilidade'].dropna().unique()
            durabilidade_filter = st.multiselect(
                "Classificação Durabilidade:",
                durabilidade_options,
                default=durabilidade_options
            )
        
        # Aplicar filtros - INCLUINDO DURABILIDADE
        df_filtrado = df.copy()
        if anos_selecionados:
            df_filtrado = df_filtrado[df_filtrado['ano_inspecao'].isin(anos_selecionados)]
        if estrutural_filter:
            df_filtrado = df_filtrado[df_filtrado['estrutural'].isin(estrutural_filter)]
        if funcional_filter:
            df_filtrado = df_filtrado[df_filtrado['funcional'].isin(funcional_filter)]
        if durabilidade_filter:  # NOVO FILTRO
            df_filtrado = df_filtrado[df_filtrado['durabilidade'].isin(durabilidade_filter)]
        
        if df_filtrado.empty:
            st.warning("Nenhum dado encontrado com os filtros aplicados")
            return
        
        # Gráfico principal - Quantidade de fichas por ano
        st.subheader("📈 Quantidade de Fichas por Ano")
        
        quantidade_por_ano = df_filtrado.groupby('ano_inspecao').size().reset_index(name='quantidade')
        
        if not quantidade_por_ano.empty:
            fig = px.bar(
                quantidade_por_ano,
                x='ano_inspecao',
                y='quantidade',
                title='Distribuição de Fichas por Ano de Inspeção',
                labels={'ano_inspecao': 'Ano de Inspeção', 'quantidade': 'Quantidade de Fichas'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Gráficos de classificações - TODOS OS TRÊS
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("🏗️ Classificação Estrutural")
            estrutural_count = df_filtrado['estrutural'].value_counts()
            if not estrutural_count.empty:
                fig_estrutural = px.pie(
                    values=estrutural_count.values,
                    names=estrutural_count.index,
                    title="Distribuição - Estrutural"
                )
                st.plotly_chart(fig_estrutural, use_container_width=True)
            else:
                st.info("Sem dados para exibir")
        
        with col2:
            st.subheader("⚙️ Classificação Funcional")
            funcional_count = df_filtrado['funcional'].value_counts()
            if not funcional_count.empty:
                fig_funcional = px.pie(
                    values=funcional_count.values,
                    names=funcional_count.index,
                    title="Distribuição - Funcional"
                )
                st.plotly_chart(fig_funcional, use_container_width=True)
            else:
                st.info("Sem dados para exibir")
        
        with col3:
            st.subheader("🔧 Classificação Durabilidade")
            durabilidade_count = df_filtrado['durabilidade'].value_counts()
            if not durabilidade_count.empty:
                fig_durabilidade = px.pie(
                    values=durabilidade_count.values,
                    names=durabilidade_count.index,
                    title="Distribuição - Durabilidade"
                )
                st.plotly_chart(fig_durabilidade, use_container_width=True)
            else:
                st.info("Sem dados para exibir")
        
        # Gráfico comparativo das três classificações
        st.subheader("📊 Comparação das Classificações")
        
        # Criar DataFrame para comparação
        classificacoes_data = []
        for _, row in df_filtrado.iterrows():
            classificacoes_data.extend([
                {'Tipo': 'Estrutural', 'Classificação': row['estrutural'], 'Ficha': row['codigo']},
                {'Tipo': 'Funcional', 'Classificação': row['funcional'], 'Ficha': row['codigo']},
                {'Tipo': 'Durabilidade', 'Classificação': row['durabilidade'], 'Ficha': row['codigo']}
            ])
        
        if classificacoes_data:
            df_classificacoes = pd.DataFrame(classificacoes_data)
            
            # Gráfico de barras agrupadas
            fig_comparacao = px.histogram(
                df_classificacoes,
                x='Classificação',
                color='Tipo',
                barmode='group',
                title='Comparação entre Classificações',
                labels={'count': 'Quantidade de Fichas'}
            )
            st.plotly_chart(fig_comparacao, use_container_width=True)
        
        # Tabela de dados
        st.subheader("📋 Dados Detalhados")
        st.dataframe(df_filtrado, use_container_width=True)
        
        # Estatísticas resumidas
        st.subheader("📊 Estatísticas Resumidas")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Fichas", len(df_filtrado))
        with col2:
            st.metric("Concessionárias", df_filtrado['concessionaria'].nunique())
        with col3:
            st.metric("Rodovias", df_filtrado['rodovia'].nunique())
        with col4:
            anos_range = f"{df_filtrado['ano_inspecao'].min()}-{df_filtrado['ano_inspecao'].max()}" if len(df_filtrado) > 0 else "N/A"
            st.metric("Período", anos_range)
        
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        st.info("Funcionalidade de visualização temporariamente indisponível")
        
        # Mostrar interface básica mesmo com erro
        st.subheader("📈 Gráfico de Exemplo")
        
        # Dados de exemplo
        dados_exemplo = pd.DataFrame({
            'ano': [2020, 2021, 2022, 2023, 2024],
            'quantidade': [15, 23, 18, 31, 27]
        })
        
        fig_exemplo = px.bar(
            dados_exemplo,
            x='ano',
            y='quantidade',
            title='Exemplo - Distribuição de Fichas por Ano'
        )
        st.plotly_chart(fig_exemplo, use_container_width=True)
        
        st.info("Este é um exemplo. Conecte ao banco de dados para ver dados reais.")


