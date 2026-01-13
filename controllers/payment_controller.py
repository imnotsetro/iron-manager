from models.client import ClientModel
from models.payment import PaymentModel


class PaymentController:
    """Controlador para gestionar la lógica de negocio de pagos"""

    def __init__(self, db):
        self.db = db
        self.client_model = ClientModel(db)
        self.payment_model = PaymentModel(db)

    def register_payment(self, name: str, amount: float, month: int, year: int, description: str = "",
                         skip_validation: bool = False):
        """
        Registra un nuevo pago.
        Retorna (success: bool, message: str, should_confirm: bool, expected_month: int, expected_year: int)
        """
        # Buscar o crear cliente
        client_data = self.client_model.get_client_by_name(name)
        if client_data:
            client_id, last_payment_id = client_data
        else:
            client_id = self.client_model.create_client(name)
            if not client_id:
                return False, "No se pudo crear el cliente", False, None, None
            last_payment_id = None

        # Verificar duplicado
        if self.payment_model.check_duplicate_payment(client_id, month, year):
            return False, "El cliente ya pagó ese mes.", False, None, None

        # Validar secuencia de pagos
        update_last_payment = False
        expected_month, expected_year = None, None

        if last_payment_id is not None:
            last_month, last_year = self.payment_model.get_last_payment_info(last_payment_id)
            if last_month is not None and last_year is not None:
                # Comparar fechas
                if (year, month) > (last_year, last_month):
                    update_last_payment = True

                # Calcular mes/año esperado
                if last_month == 12:
                    expected_month = 1
                    expected_year = last_year + 1
                else:
                    expected_month = last_month + 1
                    expected_year = last_year

                # Si no coincide, pedir confirmación
                if not skip_validation:
                    if (year, month) != (expected_year, expected_month):
                        return True, "", True, expected_month, expected_year
        else:
            update_last_payment = True

        # Crear el pago
        new_payment_id = self.payment_model.create_payment(client_id, amount, month, year, description)
        if not new_payment_id:
            return False, "No se pudo registrar el pago", False, None, None

        # Actualizar último pago si corresponde
        if update_last_payment:
            self.client_model.update_last_payment(client_id, new_payment_id)

        return True, "Pago registrado correctamente", False, None, None

    def update_payment(self, payment_id: int, amount: float, month: int, year: int, description: str = ""):
        """
        Actualiza un pago existente.
        Retorna (success: bool, message: str)
        """
        # Obtener datos del pago
        payment_data = self.payment_model.get_payment_by_id(payment_id)
        if not payment_data:
            return False, "No se pudo cargar el pago."

        client_id = payment_data['client_id']

        # Verificar duplicado (excluyendo este pago)
        if self.payment_model.check_duplicate_payment(client_id, month, year, payment_id):
            return False, "El cliente ya pagó ese mes."

        # Actualizar el pago
        if not self.payment_model.update_payment(payment_id, amount, month, year, description):
            return False, "No se pudo actualizar el pago"

        # Actualizar last_payment_id si este es el pago más reciente
        if self.payment_model.is_latest_payment(payment_id, client_id):
            self.client_model.update_last_payment(client_id, payment_id)

        return True, "Pago actualizado correctamente"

    def delete_payment(self, payment_id: int):
        """
        Elimina un pago y actualiza el cliente.
        Retorna (success: bool, message: str)
        """
        # Eliminar el pago y obtener client_id
        client_id = self.payment_model.delete_payment(payment_id)
        if client_id is None:
            return False, "No se encontró el pago o no se pudo borrar."

        # Buscar el pago más reciente del cliente
        last_payment_id = self.payment_model.get_latest_payment_for_client(client_id)

        if last_payment_id:
            # Actualizar last_payment_id
            if not self.client_model.update_last_payment(client_id, last_payment_id):
                return False, "No se pudo actualizar el último pago del cliente."
        else:
            # No hay más pagos, eliminar el cliente
            if not self.client_model.delete_client(client_id):
                return False, "No se pudo borrar el cliente."

        return True, "Pago eliminado correctamente"