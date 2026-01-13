from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QComboBox, QPushButton, QMessageBox, QCompleter
)
from PySide6.QtGui import QDoubleValidator, QFont
from PySide6.QtCore import Signal, Qt
import datetime
from models.client import ClientModel
from controllers.payment_controller import PaymentController


class PaymentWindow(QWidget):
    payment_added = Signal()

    def __init__(self, db):
        super().__init__()
        self.setWindowTitle("Agregar Pago")
        self.db = db  # SQLAlchemy Database instance

        # Inicializar modelos y controladores
        self.client_model = ClientModel(self.db)
        self.payment_controller = PaymentController(self.db)

        # Configurar tamaño de ventana
        self.setMinimumSize(500, 250)
        self.resize(550, 300)

        self.setup_ui()

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

        self.nombre_input = QLineEdit()
        self.nombre_input.setMinimumHeight(30)
        self.nombre_input.setFont(field_font)

        # Autocomplete setup usando el modelo
        names = self.client_model.get_all_names()
        completer = QCompleter(names, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setMaxVisibleItems(10)
        completer.popup().setStyleSheet("QListView { font-size: 11pt; }")
        self.nombre_input.setCompleter(completer)

        # Enter to register payment
        self.nombre_input.returnPressed.connect(self.register_payment)

        self.monto_input = QLineEdit()
        self.monto_input.setMinimumHeight(30)
        self.monto_input.setFont(field_font)
        # limit 2 to float
        validator = QDoubleValidator(0.00, 1e9, 2, self)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.monto_input.setValidator(validator)
        # Enter to continue
        self.monto_input.returnPressed.connect(self.register_payment)

        self.month_combo = QComboBox()
        self.month_combo.setMinimumHeight(30)
        self.month_combo.setFont(field_font)
        spanish_months = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        for i, mes in enumerate(spanish_months, start=1):
            self.month_combo.addItem(mes, i)
        self.month_combo.setCurrentIndex(datetime.datetime.now().month - 1)

        self.year_combo = QComboBox()
        self.year_combo.setMinimumHeight(30)
        self.year_combo.setFont(field_font)
        current_year = datetime.datetime.now().year
        for y in range(current_year - 5, current_year + 5):
            self.year_combo.addItem(str(y), y)
        self.year_combo.setCurrentText(str(current_year))

        self.descripcion_input = QLineEdit()
        self.descripcion_input.setMinimumHeight(30)
        self.descripcion_input.setFont(field_font)

        form_layout.addRow("Nombre del cliente:", self.nombre_input)
        form_layout.addRow("Monto a pagar:", self.monto_input)
        form_layout.addRow("Mes a pagar:", self.month_combo)
        form_layout.addRow("Año a pagar:", self.year_combo)
        form_layout.addRow("Descripción:", self.descripcion_input)

        self.submit_btn = QPushButton("Registrar Pago")
        self.submit_btn.setMinimumHeight(30)
        self.submit_btn.setFont(field_font)
        self.submit_btn.clicked.connect(self.register_payment)

        layout.addLayout(form_layout)
        layout.addWidget(self.submit_btn)

    def register_payment(self):
        nombre = self.nombre_input.text().strip().upper()
        monto_text = self.monto_input.text().strip()
        mes = self.month_combo.currentData()
        anio = self.year_combo.currentData()

        if not nombre or not monto_text:
            QMessageBox.warning(self, "Error", "Debe completar todos los campos")
            return

        # Validar monto
        try:
            monto = float(monto_text)
        except ValueError:
            QMessageBox.warning(self, "Error", "Monto inválido. Ingrese un número válido.")
            return

        descripcion = self.descripcion_input.text().strip()

        # Usar el controlador para registrar el pago
        success, message, should_confirm, expected_month, expected_year = self.payment_controller.register_payment(
            nombre, monto, mes, anio, descripcion
        )

        if should_confirm:
            # Pedir confirmación al usuario
            reply = QMessageBox.question(
                self, "Advertencia",
                f"El siguiente pago esperado es para {expected_month}/{expected_year}.\n"
                f"¿Desea registrar el pago de todas formas?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                # Intentar nuevamente omitiendo la validación de secuencia
                success, message, _, _, _ = self.payment_controller.register_payment(
                    nombre, monto, mes, anio, descripcion, skip_validation=True
                )
                if not success and message:
                    QMessageBox.critical(self, "Error", message)
                    return
            else:
                return

        if success:
            if message:
                QMessageBox.information(self, "Éxito", message)
            self.nombre_input.clear()
            self.monto_input.clear()
            self.payment_added.emit()
            self.close()
        else:
            if message:
                QMessageBox.warning(self, "Error", message)