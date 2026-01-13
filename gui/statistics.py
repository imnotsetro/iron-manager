from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTableView
from PySide6.QtCore import Qt, QAbstractTableModel
from models.payment import PaymentModel


class SQLAlchemyStatsModel(QAbstractTableModel):
    """Modelo personalizado para mostrar estadísticas mensuales"""

    def __init__(self, data):
        super().__init__()
        self._data = data
        self._headers = ['Mes', 'Total Recaudado']
        # Nombres de meses en español
        self._month_names = [
            'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
        ]

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return 2

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            row = self._data[index.row()]
            col = index.column()

            if col == 0:  # Columna de Mes
                # Convertir número de mes a nombre
                month_num = int(row[0]) if row[0] else 0
                if 1 <= month_num <= 12:
                    return self._month_names[month_num - 1]
                return str(row[0])
            elif col == 1:  # Columna de Total Recaudado
                # Formatear el monto con separadores de miles y 2 decimales
                try:
                    amount = float(row[1]) if row[1] else 0
                    return f"${amount:,.2f}"
                except (ValueError, TypeError):
                    return str(row[1])

        elif role == Qt.TextAlignmentRole:
            # Alinear números a la derecha
            if index.column() == 1:
                return Qt.AlignRight | Qt.AlignVCenter
            return Qt.AlignLeft | Qt.AlignVCenter

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._headers[section]
        return None


class StatisticsWindow(QWidget):
    def __init__(self, db):
        super().__init__()
        self.setWindowTitle("Estadísticas de Recaudación")
        self.resize(400, 400)
        self.db = db  # SQLAlchemy Database instance

        # Inicializar modelo
        self.payment_model = PaymentModel(self.db)
        self.model = None

        self.setup_ui()
        self.load_years()
        self.update_table()

    def showEvent(self, event):
        """Se ejecuta cuando la ventana se muestra"""
        super().showEvent(event)
        self.refresh()

    def update_table(self):
        """Actualiza la tabla con las estadísticas del año seleccionado"""
        year = self.year_selector.currentText()
        if not year:
            self.table.setModel(None)
            self.total_label.setText("")
            return

        # Obtener estadísticas mensuales
        results = self.payment_model.get_monthly_stats(year)

        # Calcular el total anual
        total_annual = sum(float(row[1]) if row[1] else 0 for row in results)
        self.total_label.setText(f"Total Anual: ${total_annual:,.2f}")

        # Crear modelo personalizado con los resultados
        self.model = SQLAlchemyStatsModel(results)
        self.table.setModel(self.model)

    def setup_ui(self):
        layout = QVBoxLayout(self)

        year_layout = QHBoxLayout()
        year_layout.addWidget(QLabel("Año:"))
        self.year_selector = QComboBox()
        self.year_selector.currentIndexChanged.connect(self.update_table)
        year_layout.addWidget(self.year_selector)

        # Agregar label para mostrar el total anual
        self.total_label = QLabel()
        self.total_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #2E7D32;")
        year_layout.addStretch()
        year_layout.addWidget(self.total_label)

        layout.addLayout(year_layout)

        self.table = QTableView()
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)

        # Ajustar el ancho de las columnas
        self.table.setColumnWidth(0, 150)  # Columna de mes más estrecha

        layout.addWidget(self.table)

    def load_years(self):
        """Obtiene años existentes a partir de payment_date."""
        self.year_selector.clear()

        # Usar el modelo para obtener los años
        years = self.payment_model.get_years_from_dates()
        self.year_selector.addItems(years)

    def refresh(self):
        """Refresca la lista de años y actualiza la tabla"""
        self.year_selector.clear()
        self.load_years()
        if self.year_selector.count() > 0:
            self.year_selector.setCurrentIndex(0)
        self.update_table()