from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QComboBox, QPushButton, QMessageBox
)
from PySide6.QtGui import QDoubleValidator, QFont
from PySide6.QtCore import Signal, Qt
import datetime
from models.payment import PaymentModel
from controllers.payment_controller import PaymentController


class PaymentEditWindow(QWidget):
    payment_added = Signal()

    def __init__(self, db, payment_id):
        super().__init__()
        self.setWindowTitle("Editar Pago")
        self.db = db  # SQLAlchemy Database instance
        self.payment_id = payment_id

        # Inicializar modelos y controladores
        self.payment_model = PaymentModel(self.db)
        self.payment_controller = PaymentController(self.db)

        # Configurar tamaño de ventana
        self.setMinimumSize(500, 250)
        self.resize(550, 300)

        self.setup_ui()
        self.load_payment()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(Qt.AlignRight)

        # Fuente para los campos
        field_font = QFont()
        field_font.setPointSize(11)

        self.name_input = QLineEdit()
        self.name_input.setMinimumHeight(30)
        self.name_input.setFont(field_font)
        self.name_input.setReadOnly(True)  # No editing client name

        self.amount_input = QLineEdit()
        self.amount_input.setMinimumHeight(30)
        self.amount_input.setFont(field_font)
        # limit 2 to float
        validator = QDoubleValidator(0.00, 1e9, 2, self)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.amount_input.setValidator(validator)
        # Enter to save changes
        self.amount_input.returnPressed.connect(self.save_changes)

        self.month_combo = QComboBox()
        self.month_combo.setMinimumHeight(30)
        self.month_combo.setFont(field_font)
        spanish_months = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        for i, mes in enumerate(spanish_months, start=1):
            self.month_combo.addItem(mes, i)

        self.year_combo = QComboBox()
        self.year_combo.setMinimumHeight(30)
        self.year_combo.setFont(field_font)
        current_year = datetime.datetime.now().year
        for y in range(current_year - 5, current_year + 5):
            self.year_combo.addItem(str(y), y)

        self.description_input = QLineEdit()
        self.description_input.setMinimumHeight(30)
        self.description_input.setFont(field_font)

        form_layout.addRow("Nombre del cliente:", self.name_input)
        form_layout.addRow("Monto a pagar:", self.amount_input)
        form_layout.addRow("Mes a pagar:", self.month_combo)
        form_layout.addRow("Año a pagar:", self.year_combo)
        form_layout.addRow("Descripción:", self.description_input)

        self.submit_btn = QPushButton("Guardar Cambios")
        self.submit_btn.setMinimumHeight(30)
        self.submit_btn.setFont(field_font)
        self.submit_btn.clicked.connect(self.save_changes)

        layout.addLayout(form_layout)
        layout.addWidget(self.submit_btn)

    def load_payment(self):
        """Carga los datos del pago a editar"""
        # Usar el modelo para obtener los datos del pago
        payment_data = self.payment_model.get_payment_by_id(self.payment_id)

        if payment_data:
            self.name_input.setText(payment_data['name'])
            self.amount_input.setText(str(payment_data['amount']))
            month = payment_data['month']
            year = payment_data['year']
            self.client_id = payment_data['client_id']
            self.month_combo.setCurrentIndex(month - 1)
            idx = self.year_combo.findData(year)
            self.description_input.setText(payment_data['description'] or "")
            if idx >= 0:
                self.year_combo.setCurrentIndex(idx)
        else:
            QMessageBox.critical(self, "Error", "No se pudo cargar el pago.")
            self.close()

    def save_changes(self):
        """Guarda los cambios del pago editado"""
        amount_text = self.amount_input.text().strip()
        month = self.month_combo.currentData()
        year = self.year_combo.currentData()

        if not amount_text:
            QMessageBox.warning(self, "Error", "Debe completar todos los campos")
            return

        try:
            amount = float(amount_text)
        except ValueError:
            QMessageBox.warning(self, "Error", "Monto inválido. Ingrese un número válido.")
            return

        description = self.description_input.text().strip()

        # Usar el controlador para actualizar el pago
        success, message = self.payment_controller.update_payment(
            self.payment_id, amount, month, year, description
        )

        if success:
            QMessageBox.information(self, "Éxito", message)
            self.payment_added.emit()
            self.close()
        else:
            QMessageBox.critical(self, "Error", message)