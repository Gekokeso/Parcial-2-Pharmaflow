import os
from app import create_app

# Determinar el entorno
config_name = os.getenv('FLASK_ENV', 'development')

# Crear la aplicación
app = create_app(config_name)

if __name__ == '__main__':
    # Configuración para desarrollo
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )