from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableView, QLabel, QLineEdit, QComboBox,
    QPushButton, QMessageBox, QHeaderView, QCompleter, QStackedLayout, QTableWidget, QTableWidgetItem
)
from PySide6.QtCore import Qt, QAbstractTableModel
from PySide6.QtGui import QStandardItemModel, QStandardItem
import datetime
from gui.payment import PaymentWindow
from gui.statistics import StatisticsWindow
from gui.status_clients import ClientStatusViewer
from gui.payment_edit import PaymentEditWindow
from models.payment import PaymentModel
from models.client import ClientModel
from controllers.payment_controller import PaymentController


class SQLAlchemyTableModel(QAbstractTableModel):
    """Modelo personalizado para mostrar resultados de SQLAlchemy en QTableView"""

    def __init__(self, data, headers):
        super().__init__()
        self._data = data
        self._headers = headers

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._headers) if self._data else 0

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            row = self._data[index.row()]
            return str(row[index.column()])
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._headers[section]
        return None


class PagosViewer(QWidget):
    def __init__(self, db):
        super().__init__()
        self.setWindowTitle("Iron Manager")
        self.resize(1280, 720)
        self.db = db  # SQLAlchemy Database instance

        # Inicializar modelos y controladores
        self.payment_model = PaymentModel(self.db)
        self.client_model = ClientModel(self.db)
        self.payment_controller = PaymentController(self.db)

        self.setup_ui()
        self.load_filters()
        self.update_table()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        filter_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar cliente...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                color: black;
            }
            QLineEdit::placeholder {
                color: black;
            }
        """)
        self.search_input.textChanged.connect(self.update_table)

        self.month_combo = QComboBox()
        spanish_months = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        for i, mes in enumerate(spanish_months, start=1):
            self.month_combo.addItem(mes, i)
        self.month_combo.setCurrentIndex(datetime.datetime.now().month - 1)
        self.month_combo.currentIndexChanged.connect(self.update_table)

        self.year_combo = QComboBox()
        self.year_combo.currentIndexChanged.connect(self.update_table)

        self.add_payment_button = QPushButton("Agregar Pago")
        self.add_payment_button.clicked.connect(self.open_payment_window)
        self.add_payment_button.setStyleSheet("background-color: #4CAF50; color: white;")

        self.edit_payment_button = QPushButton("Editar Pago")
        self.edit_payment_button.clicked.connect(self.edit_payment)
        self.edit_payment_button.setStyleSheet("background-color: #FFD600; color: black;")

        self.delete_payment_button = QPushButton("Borrar Pago")
        self.delete_payment_button.clicked.connect(self.borrar_pago)
        self.delete_payment_button.setStyleSheet("background-color: #F44336; color: white;")

        self.status_btn = QPushButton("Lista de Clientes")
        self.status_btn.clicked.connect(self.open_status)
        filter_layout.addWidget(self.status_btn)

        self.stats_button = QPushButton("Estadisticas")
        self.stats_button.clicked.connect(self.open_statistics)
        filter_layout.addWidget(self.stats_button)

        self.statistics_window = None

        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(QLabel("Mes"))
        filter_layout.addWidget(self.month_combo)
        filter_layout.addWidget(QLabel("Año"))
        filter_layout.addWidget(self.year_combo)
        filter_layout.addWidget(self.add_payment_button)
        filter_layout.addWidget(self.edit_payment_button)
        filter_layout.addWidget(self.delete_payment_button)

        self.table = QTableView()
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableView.SelectRows)

        self.no_data_label = QLabel("No existen pagos registrados en este mes")
        self.no_data_label.setAlignment(Qt.AlignCenter)
        self.no_data_label.setStyleSheet("font-size: 18px; color: gray;")
        self.no_data_label.setVisible(False)

        self.stacked_layout = QStackedLayout()
        self.stacked_layout.addWidget(self.table)
        self.stacked_layout.addWidget(self.no_data_label)

        layout.addLayout(filter_layout)
        layout.addLayout(self.stacked_layout)

        self.setup_autocomplete()

    def setup_autocomplete(self):
        """Configura el autocompletado usando SQLAlchemy"""
        names = self.client_model.get_all_names()

        self.completer = QCompleter(names, self)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setMaxVisibleItems(10)

        self.search_input.setCompleter(self.completer)

    def refresh_autocomplete(self):
        """Refresca el autocompletado con los nombres actualizados"""
        try:
            names = self.client_model.get_all_names()
            self.completer.model().setStringList(names)
        except Exception as e:
            print("DEBUG: refresh_autocomplete failed:", e)

    def open_statistics(self):
        if self.statistics_window is None:
            self.statistics_window = StatisticsWindow(self.db)
        self.statistics_window.show()
        self.statistics_window.raise_()
        self.statistics_window.activateWindow()

    def open_payment_window(self):
        self.payment_window = PaymentWindow(self.db)
        self.payment_window.payment_added.connect(self.on_payment_added)
        self.payment_window.show()

    def open_status(self):
        self.status_window = ClientStatusViewer(self.db)
        self.status_window.show()

    def on_payment_added(self):
        self.load_filters()
        self.update_table()
        self.refresh_autocomplete()

    def edit_payment(self):
        index = self.table.currentIndex()
        if not index.isValid():
            QMessageBox.warning(self, "Seleccionar pago", "Seleccione un pago para editar.")
            return
        payment_id = self.get_selected_payment_id()
        if payment_id is None:
            QMessageBox.warning(self, "Error", "No se pudo obtener el ID del pago.")
            return
        self.payment_window = PaymentEditWindow(self.db, payment_id=payment_id)
        self.payment_window.payment_added.connect(self.update_table)
        self.payment_window.show()

    def borrar_pago(self):
        index = self.table.currentIndex()
        if not index.isValid():
            QMessageBox.warning(self, "Seleccionar pago", "Seleccione un pago para borrar.")
            return
        payment_id = self.get_selected_payment_id()
        if payment_id is None:
            QMessageBox.warning(self, "Error", "No se pudo obtener el ID del pago.")
            return

        reply = QMessageBox.question(
            self,
            "Confirmar borrado",
            "¿Está seguro de que desea borrar este pago?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        # Usar el controlador para eliminar el pago
        success, message = self.payment_controller.delete_payment(payment_id)

        if success:
            QMessageBox.information(self, "Éxito", message)
            self.update_table()
        else:
            QMessageBox.critical(self, "Error", message)

    def get_selected_payment_id(self):
        """Obtiene el ID del pago seleccionado"""
        index = self.table.currentIndex()
        if not index.isValid():
            return None
        row = index.row()
        model = self.table.model()
        # La primera columna (índice 0) contiene el PagoID
        return model.data(model.index(row, 0), Qt.DisplayRole)

    def load_filters(self):
        """Carga los años disponibles en el combo"""
        self.year_combo.blockSignals(True)
        self.year_combo.clear()
        current_year = datetime.datetime.now().year

        # Usar el modelo para obtener los años
        years = self.payment_model.get_distinct_years()

        default_index = 0
        for i, year in enumerate(years):
            self.year_combo.addItem(str(year), year)
            if year == current_year:
                default_index = i

        if years:
            self.year_combo.setCurrentIndex(default_index)

        self.year_combo.blockSignals(False)

    def update_table(self):
        """Actualiza la tabla con los pagos filtrados"""
        name = self.search_input.text()
        month = self.month_combo.currentData()
        year = self.year_combo.currentData()

        # Usar el modelo para obtener los pagos filtrados
        results = self.payment_model.get_payments_filtered(name, month, year)

        # Convertir resultados a formato para el modelo
        headers = ['PagoID', 'Cliente', 'Monto', 'Fecha de Pago', 'Descripcion']
        model = SQLAlchemyTableModel(results, headers)
        self.table.setModel(model)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        self.table.hideColumn(0)  # Ocultar columna PagoID

        if len(results) == 0:
            self.stacked_layout.setCurrentWidget(self.no_data_label)
        else:
            self.stacked_layout.setCurrentWidget(self.table)