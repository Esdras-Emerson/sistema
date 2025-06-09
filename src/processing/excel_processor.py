import streamlit as st
import pandas as pd
from io import BytesIO

def obter_valor_celula(df, linha, coluna):
    """Obtém valor de uma célula específica do DataFrame"""
    try:
        if len(df) > linha and len(df.columns) > coluna:
            valor = df.iat[linha, coluna]
            if pd.notna(valor):
                return str(valor).strip() if valor != '' else None
        return None
    except Exception:
        return None

def ler_dados_excel(arquivo):
    """Lê dados específicos de um arquivo Excel - versão simplificada SEM campos problemáticos"""
    try:
        if hasattr(arquivo, 'read'):
            arquivo.seek(0)
            arquivo_bytes = BytesIO(arquivo.read())
        else:
            arquivo_bytes = arquivo
            
        df = pd.read_excel(arquivo_bytes, sheet_name=0, header=None, engine='openpyxl')
        
        # Mapeamento das células - APENAS CAMPOS SEGUROS
        dados = {
            'concessionaria': obter_valor_celula(df, 1, 1),
            'rodovia': obter_valor_celula(df, 4, 1),
            'obra': obter_valor_celula(df, 6, 1),
            'sentido': obter_valor_celula(df, 4, 5),
            'km': obter_valor_celula(df, 6, 5),
            'ic': obter_valor_celula(df, 10, 1),
            'uir': obter_valor_celula(df, 10, 3),
            'uie': obter_valor_celula(df, 10, 5),
            'data_inspecao': obter_valor_celula(df, 1, 13),
            'ano_inspecao': obter_valor_celula(df, 0, 1),
            'codigo': obter_valor_celula(df, 0, 13),
            'codigo_artesp': obter_valor_celula(df, 2, 13),
            'tipo_pav': obter_valor_celula(df, 4, 8),
            'estrutural': obter_valor_celula(df, 52, 8),
            'funcional': obter_valor_celula(df, 52, 10),
            'durabilidade': obter_valor_celula(df, 52, 12),
            # REMOVIDOS: reparos, reformas, tipo_junta, tipo_AA, terapias
        }
        
        # Processar data_inspecao
        if dados['data_inspecao'] and pd.notna(dados['data_inspecao']):
            try:
                dados['data_inspecao'] = pd.to_datetime(dados['data_inspecao']).date()
            except:
                dados['data_inspecao'] = None
        
        # Processar ano_inspecao
        if dados['ano_inspecao']:
            try:
                dados['ano_inspecao'] = int(float(dados['ano_inspecao']))
            except:
                dados['ano_inspecao'] = None
        
        return dados
    except Exception as e:
        st.error(f"Erro ao processar arquivo: {str(e)}")
        return None

def validar_arquivo_excel(arquivo):
    """Valida se o arquivo Excel tem o formato esperado"""
    try:
        dados = ler_dados_excel(arquivo)
        if dados and dados.get('concessionaria'):
            return True
        return False
    except:
        return False

def processar_multiplos_arquivos(arquivos):
    """Processa múltiplos arquivos Excel"""
    dados_processados = []
    
    for arquivo in arquivos:
        dados = ler_dados_excel(arquivo)
        if dados:
            dados_processados.append(dados)
    
    return dados_processados
