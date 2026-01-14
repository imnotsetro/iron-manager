from sqlalchemy import Column, Integer, String, Float, ForeignKey, UniqueConstraint, func, extract, cast
from sqlalchemy.orm import relationship
import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from models.database import Base


class Payment(Base):
    """Modelo de Pago"""
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    date = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    description = Column(String, nullable=True)

    # Relación con Client
    client = relationship('Client', back_populates='payments', foreign_keys=[client_id])

    # Constraint de unicidad
    __table_args__ = (
        UniqueConstraint('client_id', 'month', 'year', name='_client_month_year_uc'),
    )


class PaymentModel:
    """Modelo para operaciones CRUD de pagos"""

    def __init__(self, db):
        self.db = db
        self.session = db.get_session()

    def get_payment_by_id(self, payment_id: int):
        """Obtiene un pago por ID. Retorna diccionario con datos o None."""
        from models.client import Client

        result = self.session.query(
            Client.name,
            Payment.amount,
            Payment.month,
            Payment.year,
            Payment.client_id,
            Payment.description
        ).join(
            Client, Payment.client_id == Client.id
        ).filter(
            Payment.id == payment_id
        ).first()

        if result:
            return {
                'name': result[0],
                'amount': result[1],
                'month': result[2],
                'year': result[3],
                'client_id': result[4],
                'description': result[5]
            }
        return None

    def check_duplicate_payment(self, client_id: int, month: int, year: int, exclude_id: int = None):
        """Verifica si existe un pago duplicado."""
        query = self.session.query(Payment).filter_by(
            client_id=client_id,
            month=month,
            year=year
        )

        if exclude_id:
            query = query.filter(Payment.id != exclude_id)

        return query.first() is not None

    def get_last_payment_info(self, payment_id: int):
        """Obtiene mes y año del último pago."""
        payment = self.session.query(Payment.month, Payment.year).filter_by(id=payment_id).first()
        if payment:
            return payment.month, payment.year
        return None, None

    def create_payment(self, client_id: int, amount: float, month: int, year: int, description: str = ""):
        """Crea un nuevo pago. Retorna el ID del pago creado o None si falla."""
        try:
            today = datetime.date.today().isoformat()
            payment = Payment(
                client_id=client_id,
                date=today,
                amount=amount,
                month=month,
                year=year,
                description=description
            )
            self.session.add(payment)
            self.session.commit()
            return payment.id
        except Exception as e:
            self.session.rollback()
            print(f"Error creating payment: {e}")
            return None

    def update_payment(self, payment_id: int, amount: float, month: int, year: int, description: str = ""):
        """Actualiza un pago existente."""
        try:
            payment = self.session.query(Payment).filter_by(id=payment_id).first()
            if payment:
                payment.amount = amount
                payment.month = month
                payment.year = year
                payment.description = description
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            print(f"Error updating payment: {e}")
            return False

    def delete_payment(self, payment_id: int):
        """Elimina un pago y retorna el client_id asociado."""
        try:
            payment = self.session.query(Payment).filter_by(id=payment_id).first()
            if payment:
                client_id = payment.client_id
                self.session.delete(payment)
                self.session.commit()
                return client_id
            return None
        except Exception as e:
            self.session.rollback()
            print(f"Error deleting payment: {e}")
            return None

    def get_latest_payment_for_client(self, client_id: int):
        """Obtiene el ID del pago más reciente de un cliente."""
        payment = self.session.query(Payment.id).filter_by(
            client_id=client_id
        ).order_by(
            Payment.year.desc(),
            Payment.month.desc(),
            Payment.id.desc()
        ).first()

        if payment:
            return payment.id
        return None

    def update_client_last_payment(self, client_id: int):
        """
        Actualiza el último pago del cliente basándose en el pago más reciente.
        Retorna True si se actualizó correctamente, False en caso contrario.
        """
        from models.client import Client
        
        try:
            # Obtener el pago más reciente
            latest_payment_id = self.get_latest_payment_for_client(client_id)
            
            # Actualizar el cliente
            client = self.session.query(Client).filter_by(id=client_id).first()
            if client:
                client.last_payment_id = latest_payment_id
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            print(f"Error updating client last payment: {e}")
            return False

    def should_update_last_payment(self, payment_id: int, client_id: int):
        """
        Verifica si un pago debe ser el último pago del cliente.
        Retorna True si el pago es el más reciente.
        """
        latest = self.session.query(Payment.id).filter_by(
            client_id=client_id
        ).order_by(
            Payment.year.desc(),
            Payment.month.desc(),
            Payment.id.desc()
        ).first()

        return latest and latest.id == payment_id

    def get_payments_filtered(self, name: str = None, month: int = None, year: int = None):
        """Obtiene pagos filtrados por nombre, mes y año."""
        from models.client import Client

        query = self.session.query(
            Payment.id.label('PagoID'),
            Client.name.label('Cliente'),
            Payment.amount.label('Monto'),
            Payment.date.label('Fecha de Pago'),
            Payment.description.label('Descripcion')
        ).join(
            Client, Payment.client_id == Client.id
        )

        if name:
            query = query.filter(Client.name.like(f"%{name}%"))
        if month:
            query = query.filter(Payment.month == month)
        if year:
            query = query.filter(Payment.year == year)

        query = query.order_by(Client.name.asc())

        return query.all()

    def get_distinct_years(self):
        """Obtiene años distintos de los pagos."""
        years = self.session.query(Payment.year).distinct().order_by(Payment.year.desc()).all()
        return [year[0] for year in years]

    def get_monthly_stats(self, year: str):
        """Obtiene estadísticas mensuales para un año."""
        from sqlalchemy import func, extract, cast, Integer

        month_column = cast(extract('month', Payment.date), Integer).label('Mes')

        results = self.session.query(
            month_column,
            func.sum(Payment.amount).label('Total Recaudado')
        ).filter(
            extract('year', Payment.date) == year,
            Payment.date.isnot(None)
        ).group_by(
            month_column
        ).order_by(
            month_column
        ).all()

        return results

    def get_years_from_dates(self):
        """Obtiene años distintos desde payment_date."""
        from sqlalchemy import func, extract, distinct, desc

        year_column = extract('year', Payment.date).label('year')

        years = self.session.query(
            distinct(year_column)
        ).filter(
            Payment.date.isnot(None)
        ).order_by(
            desc(year_column)
        ).all()

        return [str(int(year[0])) for year in years if year[0]]

    def is_latest_payment(self, payment_id: int, client_id: int):
        """Verifica si un pago es el más reciente del cliente."""
        latest = self.session.query(Payment.id).filter_by(
            client_id=client_id
        ).order_by(
            Payment.date.desc(),
            Payment.id.desc()
        ).first()

        if latest and latest.id == payment_id:
            return True
        return False