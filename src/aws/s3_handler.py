import streamlit as st
import datetime
import boto3
from botocore.exceptions import ClientError
from utils.config import get_s3_client, get_s3_bucket

def verificar_arquivo_existe_s3(nome_arquivo):
    """Verifica se um arquivo já existe no S3"""
    try:
        s3_client = get_s3_client()
        bucket = get_s3_bucket()
        
        if not s3_client or not bucket:
            return False
        
        try:
            s3_client.head_object(Bucket=bucket, Key=nome_arquivo)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                raise e
        
    except Exception as e:
        st.error(f"Erro ao verificar arquivo no S3: {str(e)}")
        return False

def salvar_arquivo_s3(nome_arquivo, conteudo):
    """Salva arquivo no S3 com timestamp"""
    try:
        s3_client = get_s3_client()
        bucket = get_s3_bucket()
        
        if not s3_client or not bucket:
            st.warning("S3 não configurado")
            return None
        
        data_upload = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        chave_s3 = f'fichas_inspecao/{data_upload}_{nome_arquivo}'
        
        if hasattr(conteudo, 'read'):
            conteudo.seek(0)
            s3_client.put_object(Bucket=bucket, Key=chave_s3, Body=conteudo.read())
        else:
            s3_client.put_object(Bucket=bucket, Key=chave_s3, Body=conteudo)
        
        st.success(f"📁 Arquivo salvo no S3: {chave_s3}")
        return chave_s3
        
    except Exception as e:
        st.error(f"Erro ao salvar no S3: {str(e)}")
        return None

def salvar_pdf_sem_duplicata(nome_arquivo, conteudo, pasta="relatorios_pdf"):
    """Salva PDF no S3 evitando duplicatas por nome"""
    try:
        s3_client = get_s3_client()
        bucket = get_s3_bucket()
        
        if not s3_client or not bucket:
            st.warning("S3 não configurado")
            return None
        
        chave_s3 = f'{pasta}/{nome_arquivo}'
        
        # Verificar se arquivo já existe
        if verificar_arquivo_existe_s3(chave_s3):
            st.info(f"📄 PDF {nome_arquivo} já existe no S3, reutilizando...")
            return chave_s3
        
        # Se não existe, salvar
        if hasattr(conteudo, 'read'):
            conteudo.seek(0)
            file_content = conteudo.read()
        else:
            file_content = conteudo
        
        s3_client.put_object(
            Bucket=bucket, 
            Key=chave_s3, 
            Body=file_content,
            ContentType='application/pdf'
        )
        
        st.success(f"📄 Novo PDF salvo: {chave_s3}")
        return chave_s3
        
    except Exception as e:
        st.error(f"Erro ao salvar PDF no S3: {str(e)}")
        return None

def listar_arquivos_s3(prefixo=''):
    """Lista arquivos no S3 com prefixo específico"""
    try:
        s3_client = get_s3_client()
        bucket = get_s3_bucket()
        
        if not s3_client or not bucket:
            return []
        
        # Usar list_objects_v2 com paginação
        response = s3_client.list_objects_v2(
            Bucket=bucket, 
            Prefix=prefixo,
            MaxKeys=1000
        )
        
        arquivos = []
        if 'Contents' in response:
            for obj in response['Contents']:
                # Filtrar apenas arquivos (não pastas vazias)
                if obj['Size'] > 0:
                    arquivos.append(obj['Key'])
        
        # Verificar se há mais páginas
        while response.get('IsTruncated', False):
            response = s3_client.list_objects_v2(
                Bucket=bucket,
                Prefix=prefixo,
                ContinuationToken=response['NextContinuationToken'],
                MaxKeys=1000
            )
            if 'Contents' in response:
                for obj in response['Contents']:
                    if obj['Size'] > 0:
                        arquivos.append(obj['Key'])
        
        return arquivos
        
    except Exception as e:
        st.error(f"Erro ao listar arquivos S3: {str(e)}")
        return []

def baixar_arquivo_s3(chave_s3):
    """Baixa arquivo do S3"""
    try:
        s3_client = get_s3_client()
        bucket = get_s3_bucket()
        
        if not s3_client or not bucket:
            return None
        
        response = s3_client.get_object(Bucket=bucket, Key=chave_s3)
        return response['Body'].read()
        
    except Exception as e:
        st.error(f"Erro ao baixar arquivo S3: {str(e)}")
        return None

def deletar_arquivo_s3(chave_s3):
    """Deleta arquivo do S3"""
    try:
        s3_client = get_s3_client()
        bucket = get_s3_bucket()
        
        if not s3_client or not bucket:
            return False
        
        s3_client.delete_object(Bucket=bucket, Key=chave_s3)
        st.success(f"🗑️ Arquivo deletado do S3: {chave_s3}")
        return True
        
    except Exception as e:
        st.error(f"Erro ao deletar arquivo S3: {str(e)}")
        return False

def obter_info_arquivo_s3(chave_s3):
    """Obtém informações de um arquivo no S3"""
    try:
        s3_client = get_s3_client()
        bucket = get_s3_bucket()
        
        if not s3_client or not bucket:
            return None
        
        response = s3_client.head_object(Bucket=bucket, Key=chave_s3)
        
        return {
            'tamanho': response['ContentLength'],
            'ultima_modificacao': response['LastModified'],
            'content_type': response.get('ContentType', 'unknown'),
            'etag': response['ETag']
        }
        
    except Exception as e:
        st.error(f"Erro ao obter info do arquivo S3: {str(e)}")
        return None

def testar_conexao_s3():
    """Testa a conexão com o S3"""
    try:
        s3_client = get_s3_client()
        bucket = get_s3_bucket()
        
        if not s3_client or not bucket:
            st.error("❌ S3 não configurado")
            return False
        
        # Tentar listar objetos do bucket
        response = s3_client.list_objects_v2(Bucket=bucket, MaxKeys=1)
        st.success("✅ Conexão com S3 estabelecida com sucesso!")
        return True
        
    except Exception as e:
        st.error(f"❌ Erro na conexão S3: {str(e)}")
        return False

