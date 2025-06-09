import streamlit as st
from sqlalchemy import text

@st.cache_resource
def get_db_engine():
    """Retorna engine do banco de dados com correção para SQLAlchemy 2.x"""
    try:
        from sqlalchemy import create_engine
        
        # Verificar se as credenciais estão disponíveis
        database_url = st.secrets.get("DATABASE_URL", "")
        
        if database_url:
            st.info(f"🔗 Usando DATABASE_URL para conexão")
            engine = create_engine(
                database_url,
                connect_args={"sslmode": "require"},
                echo=False
            )
        else:
            # Construir URL a partir de componentes
            DB_USER = st.secrets.get("DB_USER", "")
            DB_PASSWORD = st.secrets.get("DB_PASSWORD", "")
            DB_HOST = st.secrets.get("DB_HOST", "")
            DB_PORT = st.secrets.get("DB_PORT", "5432")
            DB_NAME = st.secrets.get("DB_NAME", "")
            
            if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_NAME]):
                st.error("❌ Credenciais do banco incompletas")
                return None
            
            connection_string = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
            st.info(f"🔗 Conectando ao banco: {DB_HOST}:{DB_PORT}/{DB_NAME}")
            
            engine = create_engine(
                connection_string,
                connect_args={"sslmode": "require"},
                echo=False
            )
        
        # Testar conexão usando text() - CORREÇÃO PRINCIPAL
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            st.success("✅ Conexão com banco estabelecida")
        
        return engine
    
    except ImportError:
        st.error("❌ SQLAlchemy não instalado")
        return None
    except Exception as e:
        st.error(f"❌ Erro ao conectar ao banco: {str(e)}")
        return None

def get_s3_client():
    """Retorna cliente S3 ou None se não configurado"""
    try:
        import boto3
        AWS_ACCESS_KEY_ID = st.secrets.get("AWS_ACCESS_KEY_ID", "")
        AWS_SECRET_ACCESS_KEY = st.secrets.get("AWS_SECRET_ACCESS_KEY", "")
        AWS_REGION = st.secrets.get("AWS_REGION", "us-east-1")
        
        if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
            return boto3.client('s3',
                               aws_access_key_id=AWS_ACCESS_KEY_ID,
                               aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                               region_name=AWS_REGION)
        return None
    except:
        return None

def get_s3_bucket():
    """Retorna nome do bucket S3"""
    return st.secrets.get("AWS_S3_BUCKET", "")
