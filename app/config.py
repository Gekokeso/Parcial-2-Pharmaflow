import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuración base de la aplicación"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret')
    
    # MySQL
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3307))
    MYSQL_USER = os.getenv('MYSQL_USER', 'pharmaflow_user')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'pharmaflow_pass')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'pharmaflow')
    
    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@"
        f"{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # MongoDB
    MONGODB_URI = os.getenv(
        'MONGODB_URI',
        'mongodb://admin:adminpass123@localhost:27017/pharmaflow?authSource=admin'
    )
    MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'pharmaflow')
    
    # Redis
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', 'redispass123')
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    
    # Neo4j
    NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
    NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'neo4jpass123')
    
    # Session
    SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', 3600))
    MAX_LOGIN_ATTEMPTS = int(os.getenv('MAX_LOGIN_ATTEMPTS', 5))


class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Configuración para testing"""
    DEBUG = True
    TESTING = True


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}