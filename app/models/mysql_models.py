from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import validates
import bcrypt

db = SQLAlchemy()


class Usuario(db.Model):
    """Modelo de Usuario para autenticación y autorización"""
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.Enum('gerente', 'farmaceutico', 'investigador'), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    transacciones = db.relationship('Transaccion', backref='usuario', lazy=True)
    
    def set_password(self, password):
        """Hashea y guarda la contraseña"""
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'), 
            bcrypt.gensalt()
        ).decode('utf-8')
    
    def check_password(self, password):
        """Verifica la contraseña"""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'rol': self.rol,
            'activo': self.activo,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }


class Proveedor(db.Model):
    """Modelo de Proveedor"""
    __tablename__ = 'proveedores'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    contacto = db.Column(db.String(100))
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(100))
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    lotes = db.relationship('Lote', backref='proveedor', lazy=True)


class Producto(db.Model):
    """Modelo de Producto/Medicamento"""
    __tablename__ = 'productos'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo_barras = db.Column(db.String(50), unique=True, nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    principio_activo = db.Column(db.String(100))
    tipo_medicamento = db.Column(
        db.Enum('generico', 'patentado', 'controlado'),
        nullable=False
    )
    precio_base = db.Column(db.Numeric(10, 2), nullable=False)
    temperatura_almacenamiento = db.Column(db.Numeric(3, 1))
    requiere_refrigeracion = db.Column(db.Boolean, default=False)
    activo = db.Column(db.Boolean, default=True)
    
    # Relaciones
    lotes = db.relationship('Lote', backref='producto', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'codigo_barras': self.codigo_barras,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'principio_activo': self.principio_activo,
            'tipo_medicamento': self.tipo_medicamento,
            'precio_base': float(self.precio_base),
            'temperatura_almacenamiento': float(self.temperatura_almacenamiento) if self.temperatura_almacenamiento else None,
            'requiere_refrigeracion': self.requiere_refrigeracion,
            'activo': self.activo
        }


class Lote(db.Model):
    """Modelo de Lote con control de concurrencia optimista"""
    __tablename__ = 'lotes'
    
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    numero_lote = db.Column(db.String(50), unique=True, nullable=False)
    cantidad_inicial = db.Column(db.Integer, nullable=False)
    cantidad_actual = db.Column(db.Integer, nullable=False)
    fecha_fabricacion = db.Column(db.Date, nullable=False)
    fecha_caducidad = db.Column(db.Date, nullable=False)
    precio_compra = db.Column(db.Numeric(10, 2), nullable=False)
    precio_venta = db.Column(db.Numeric(10, 2), nullable=False)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'))
    ubicacion_almacen = db.Column(db.String(100))
    version = db.Column(db.Integer, default=0, nullable=False)  # Control de concurrencia
    
    # Relaciones
    transacciones = db.relationship('Transaccion', backref='lote', lazy=True)
    
    @validates('cantidad_actual')
    def validate_cantidad(self, key, value):
        """Valida que la cantidad no sea negativa"""
        if value < 0:
            raise ValueError("La cantidad no puede ser negativa")
        return value
    
    def to_dict(self):
        return {
            'id': self.id,
            'producto_id': self.producto_id,
            'numero_lote': self.numero_lote,
            'cantidad_inicial': self.cantidad_inicial,
            'cantidad_actual': self.cantidad_actual,
            'fecha_fabricacion': self.fecha_fabricacion.isoformat() if self.fecha_fabricacion else None,
            'fecha_caducidad': self.fecha_caducidad.isoformat() if self.fecha_caducidad else None,
            'precio_compra': float(self.precio_compra),
            'precio_venta': float(self.precio_venta),
            'proveedor_id': self.proveedor_id,
            'ubicacion_almacen': self.ubicacion_almacen,
            'version': self.version,
            'producto': self.producto.to_dict() if self.producto else None
        }


class Transaccion(db.Model):
    """Modelo de Transacción de inventario"""
    __tablename__ = 'transacciones'
    
    id = db.Column(db.Integer, primary_key=True)
    lote_id = db.Column(db.Integer, db.ForeignKey('lotes.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    tipo_transaccion = db.Column(
        db.Enum('entrada', 'salida', 'ajuste'),
        nullable=False
    )
    cantidad = db.Column(db.Integer, nullable=False)
    fecha_transaccion = db.Column(db.DateTime, default=datetime.utcnow)
    motivo = db.Column(db.String(200))
    referencia = db.Column(db.String(100))
    
    def to_dict(self):
        return {
            'id': self.id,
            'lote_id': self.lote_id,
            'usuario_id': self.usuario_id,
            'tipo_transaccion': self.tipo_transaccion,
            'cantidad': self.cantidad,
            'fecha_transaccion': self.fecha_transaccion.isoformat() if self.fecha_transaccion else None,
            'motivo': self.motivo,
            'referencia': self.referencia
        }


class InteraccionMedicamentosa(db.Model):
    """Modelo de Interacciones entre medicamentos"""
    __tablename__ = 'interacciones_medicamentosas'
    
    id = db.Column(db.Integer, primary_key=True)
    medicamento_a_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    medicamento_b_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    tipo_interaccion = db.Column(
        db.Enum('leve', 'moderada', 'grave'),
        nullable=False
    )
    descripcion = db.Column(db.Text)
    recomendaciones = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    medicamento_a = db.relationship('Producto', foreign_keys=[medicamento_a_id])
    medicamento_b = db.relationship('Producto', foreign_keys=[medicamento_b_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'medicamento_a': self.medicamento_a.nombre if self.medicamento_a else None,
            'medicamento_b': self.medicamento_b.nombre if self.medicamento_b else None,
            'tipo_interaccion': self.tipo_interaccion,
            'descripcion': self.descripcion,
            'recomendaciones': self.recomendaciones
        }