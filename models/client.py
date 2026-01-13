from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from models.database import Base


class Client(Base):
    """Modelo de Cliente"""
    __tablename__ = 'clients'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    last_payment_id = Column(Integer, ForeignKey('payments.id'), nullable=True)

    # Relaciones
    payments = relationship('Payment', back_populates='client', foreign_keys='Payment.client_id')
    last_payment = relationship('Payment', foreign_keys=[last_payment_id], post_update=True)


class ClientModel:
    """Modelo para operaciones CRUD de clientes"""

    def __init__(self, db):
        self.db = db
        self.session = db.get_session()

    def get_client_by_name(self, name: str):
        """Obtiene un cliente por nombre. Retorna (id, last_payment_id) o None."""
        client = self.session.query(Client).filter_by(name=name).first()
        if client:
            return client.id, client.last_payment_id
        return None

    def create_client(self, name: str):
        """Crea un nuevo cliente. Retorna el ID del cliente creado o None si falla."""
        try:
            client = Client(name=name, last_payment_id=None)
            self.session.add(client)
            self.session.commit()
            return client.id
        except Exception as e:
            self.session.rollback()
            print(f"Error creating client: {e}")
            return None

    def update_last_payment(self, client_id: int, payment_id: int):
        """Actualiza el último pago de un cliente."""
        try:
            client = self.session.query(Client).filter_by(id=client_id).first()
            if client:
                client.last_payment_id = payment_id
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            print(f"Error updating last payment: {e}")
            return False

    def delete_client(self, client_id: int):
        """Elimina un cliente."""
        try:
            client = self.session.query(Client).filter_by(id=client_id).first()
            if client:
                self.session.delete(client)
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            print(f"Error deleting client: {e}")
            return False

    def get_all_names(self):
        """Obtiene todos los nombres de clientes para autocompletado."""
        clients = self.session.query(Client.name).all()
        return [client.name for client in clients]

    def get_client_status(self, name_filter: str = None):
        """Obtiene el estado de todos los clientes con filtro opcional."""
        from models.payment import Payment
        from sqlalchemy import case

        query = self.session.query(
            Client.name.label('Cliente'),
            case(
                (Payment.month.isnot(None), Payment.month),
                else_='-'
            ).label('Último Mes'),
            case(
                (Payment.year.isnot(None), Payment.year),
                else_='-'
            ).label('Último Año')
        ).outerjoin(
            Payment,
            Client.last_payment_id == Payment.id
        )

        if name_filter:
            query = query.filter(Client.name.like(f"%{name_filter}%"))

        query = query.order_by(Client.name)

        return query.all()