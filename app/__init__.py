from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from pymongo import MongoClient
from neo4j import GraphDatabase
import redis

from app.config import config
from app.models.mysql_models import db

# Instancias globales
mongo_client = None
mongo_db = None
redis_client = None
neo4j_driver = None
jwt = JWTManager()


# Manejadores de errores JWT
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'error': 'Token expirado'}), 401


@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'error': 'Token inválido'}), 422


@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({'error': 'Token no proporcionado'}), 401


def create_app(config_name='development'):
    """Factory para crear la aplicación Flask"""
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Inicializar extensiones
    CORS(app)
    jwt.init_app(app)
    
    # Inicializar MySQL (SQLAlchemy)
    db.init_app(app)
    
    # Inicializar MongoDB
    global mongo_client, mongo_db
    mongo_client = MongoClient(app.config['MONGODB_URI'])
    mongo_db = mongo_client[app.config['MONGODB_DATABASE']]
    
    # Inicializar Redis
    global redis_client
    redis_client = redis.Redis(
        host=app.config['REDIS_HOST'],
        port=app.config['REDIS_PORT'],
        password=app.config['REDIS_PASSWORD'],
        db=app.config['REDIS_DB'],
        decode_responses=True
    )
    
    # Inicializar Neo4j
    global neo4j_driver
    neo4j_driver = GraphDatabase.driver(
        app.config['NEO4J_URI'],
        auth=(app.config['NEO4J_USER'], app.config['NEO4J_PASSWORD'])
    )
    
    # Registrar Blueprints
    from app.routes import auth, inventario, ensayos, interacciones
    
    app.register_blueprint(auth.bp)
    app.register_blueprint(inventario.bp)
    app.register_blueprint(ensayos.bp)
    app.register_blueprint(interacciones.bp)
    
    # Crear tablas si no existen
    with app.app_context():
        db.create_all()
    
    # Ruta de prueba
    @app.route('/health')
    def health():
        return {
            'status': 'ok',
            'mysql': 'connected',
            'mongodb': 'connected',
            'redis': 'connected',
            'neo4j': 'connected'
        }
    
    return app


def get_mongo_db():
    """Obtener instancia de MongoDB"""
    return mongo_db


def get_redis_client():
    """Obtener instancia de Redis"""
    return redis_client


def get_neo4j_driver():
    """Obtener instancia de Neo4j"""
    return neo4j_driver