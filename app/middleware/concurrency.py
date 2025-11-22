from sqlalchemy.exc import SQLAlchemyError
from app.models.mysql_models import db, Lote, Transaccion


class ConcurrencyException(Exception):
    """Excepción para errores de concurrencia"""
    pass


class OptimisticLockManager:
    """
    Gestor de control de concurrencia optimista.
    
    Implementa el patrón de versionado para detectar conflictos
    cuando múltiples usuarios intentan modificar el mismo lote.
    """
    
    @staticmethod
    def actualizar_inventario_con_lock(lote_id, cantidad_cambio, usuario_id, 
                                       tipo_transaccion, motivo, referencia, version_esperada):
        """
        Actualiza el inventario con control de concurrencia optimista.
        
        Args:
            lote_id: ID del lote a modificar
            cantidad_cambio: Cantidad a agregar (positivo) o restar (negativo)
            usuario_id: ID del usuario que realiza la transacción
            tipo_transaccion: 'entrada', 'salida', o 'ajuste'
            motivo: Razón de la transacción
            referencia: Referencia externa (factura, orden, etc.)
            version_esperada: Versión que el usuario vio antes de modificar
            
        Returns:
            dict: Lote actualizado y transacción registrada
            
        Raises:
            ConcurrencyException: Si hay un conflicto de versión
            ValueError: Si la operación no es válida
        """
        try:
            # 1. Obtener el lote con lock FOR UPDATE
            lote = db.session.query(Lote).filter_by(id=lote_id).with_for_update().first()
            
            if not lote:
                raise ValueError(f"Lote {lote_id} no encontrado")
            
            # 2. VERIFICAR VERSIÓN (Control de Concurrencia Optimista)
            if lote.version != version_esperada:
                db.session.rollback()
                raise ConcurrencyException(
                    f"Conflicto de concurrencia detectado. "
                    f"El lote fue modificado por otro usuario. "
                    f"Versión esperada: {version_esperada}, "
                    f"Versión actual: {lote.version}. "
                    f"Por favor, recargue los datos e intente nuevamente."
                )
            
            # 3. Calcular nueva cantidad
            nueva_cantidad = lote.cantidad_actual + cantidad_cambio
            
            # 4. Validar que no quede negativo
            if nueva_cantidad < 0:
                db.session.rollback()
                raise ValueError(
                    f"Inventario insuficiente. "
                    f"Cantidad disponible: {lote.cantidad_actual}, "
                    f"Cantidad solicitada: {abs(cantidad_cambio)}"
                )
            
            # 5. Actualizar cantidad y VERSION
            lote.cantidad_actual = nueva_cantidad
            lote.version += 1  # Incrementar versión
            
            # 6. Registrar la transacción
            transaccion = Transaccion(
                lote_id=lote_id,
                usuario_id=usuario_id,
                tipo_transaccion=tipo_transaccion,
                cantidad=abs(cantidad_cambio),
                motivo=motivo,
                referencia=referencia
            )
            
            db.session.add(transaccion)
            db.session.commit()
            
            return {
                'success': True,
                'lote': lote.to_dict(),
                'transaccion': transaccion.to_dict(),
                'mensaje': 'Inventario actualizado correctamente'
            }
            
        except ConcurrencyException:
            raise
        except ValueError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Error de base de datos: {str(e)}")
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error inesperado: {str(e)}")
    
    
    @staticmethod
    def vender_producto(lote_id, cantidad, usuario_id, referencia_venta, version_esperada):
        """
        Procesa una venta de producto con control de concurrencia.
        
        Este es un método de conveniencia que llama a actualizar_inventario_con_lock
        con los parámetros apropiados para una venta.
        """
        return OptimisticLockManager.actualizar_inventario_con_lock(
            lote_id=lote_id,
            cantidad_cambio=-cantidad,  # Negativo porque es salida
            usuario_id=usuario_id,
            tipo_transaccion='salida',
            motivo='Venta de producto',
            referencia=referencia_venta,
            version_esperada=version_esperada
        )
    
    
    @staticmethod
    def agregar_inventario(lote_id, cantidad, usuario_id, referencia_compra, version_esperada):
        """
        Agrega inventario con control de concurrencia.
        """
        return OptimisticLockManager.actualizar_inventario_con_lock(
            lote_id=lote_id,
            cantidad_cambio=cantidad,  # Positivo porque es entrada
            usuario_id=usuario_id,
            tipo_transaccion='entrada',
            motivo='Compra/ingreso de producto',
            referencia=referencia_compra,
            version_esperada=version_esperada
        )


# Ejemplo de uso con manejo de reintentos
class TransactionRetryManager:
    """Gestor de reintentos automáticos para transacciones"""
    
    @staticmethod
    def ejecutar_con_reintentos(funcion, max_reintentos=3, *args, **kwargs):
        """
        Ejecuta una función con reintentos automáticos en caso de conflictos.
        
        Args:
            funcion: Función a ejecutar
            max_reintentos: Número máximo de reintentos
            *args, **kwargs: Argumentos para la función
            
        Returns:
            Resultado de la función
            
        Raises:
            ConcurrencyException: Si se exceden los reintentos
        """
        for intento in range(max_reintentos):
            try:
                return funcion(*args, **kwargs)
            except ConcurrencyException as e:
                if intento == max_reintentos - 1:
                    # Último intento fallido
                    raise ConcurrencyException(
                        f"Conflicto persistente después de {max_reintentos} intentos. "
                        f"Error: {str(e)}"
                    )
                # Esperar antes de reintentar
                import time
                time.sleep(0.1 * (intento + 1))  # Backoff exponencial
                continue
        
        raise ConcurrencyException("Error inesperado en reintentos")