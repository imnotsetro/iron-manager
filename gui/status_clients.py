from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QTableView, QCompleter, QHeaderView
)
from PySide6.QtCore import Qt, QAbstractTableModel
from PySide6.QtGui import QColor
import datetime
from models.client import ClientModel


class StatusColorModel(QAbstractTableModel):
    """Modelo personalizado para mostrar el estado de clientes con colores y meses por nombre"""

    MONTHS_ES = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }

    # Colores (alineados con la leyenda)
    COLOR_OK = QColor("#A5D6A7")      # Verde: al día
    COLOR_WARN = QColor("#FFA726")    # Naranja: debe el mes actual (atraso leve)
    COLOR_LATE = QColor("#FF5252")    # Rojo: más de 1 mes o nunca pagó (atraso grave)

    def __init__(self, data):
        super().__init__()
        self._data = data
        self._headers = ["Cliente", "Último Mes", "Último Año"]

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return 3

    def _status_for_row(self, row):
        """
        Devuelve (months_ago, status_text, color) para una fila.
        months_ago:
          - None: nunca pagó / datos inválidos
          - 0: pagó este mes
          - 1: falta el mes actual
          - >1: atraso grave
        """
        month = row[1]
        year = row[2]

        if month != "-" and year != "-":
            try:
                month_num = int(month)
                year_num = int(year)
                now = datetime.datetime.now()
                months_ago = (now.year - year_num) * 12 + (now.month - month_num)

                if months_ago <= 0:
                    return 0, "Al día (pagó este mes)", self.COLOR_OK
                if months_ago == 1:
                    return 1, "Atraso leve (falta el mes actual)", self.COLOR_WARN
                return months_ago, "Atraso grave (más de 1 mes)", self.COLOR_LATE
            except Exception:
                pass

        return None, "Atraso grave (nunca pagó o sin datos)", self.COLOR_LATE

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        row = self._data[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            # Mostrar mes por nombre en la columna "Último Mes"
            if col == 1:
                raw = row[1]
                if raw == "-":
                    return "-"
                try:
                    month_num = int(raw)
                    return self.MONTHS_ES.get(month_num, str(raw))
                except Exception:
                    return str(raw)

            return str(row[col])

        # Colorear toda la fila (todas las columnas) según el estado
        if role == Qt.BackgroundRole and col in (0, 1, 2):
            _, _, color = self._status_for_row(row)
            return color

        # Tooltip para que se entienda al pasar el mouse
        if role == Qt.ToolTipRole:
            months_ago, status_text, _ = self._status_for_row(row)

            # Mostrar detalle adicional
            if months_ago is None:
                detail = "No hay pagos registrados."
            elif months_ago == 0:
                detail = "Último pago corresponde al mes actual."
            elif months_ago == 1:
                detail = "El último pago es del mes anterior."
            else:
                detail = f"El último pago fue hace {months_ago} meses."

            return f"{status_text}\n{detail}"

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._headers[section]
        return None


class ClientStatusViewer(QWidget):
    def __init__(self, db):
        super().__init__()
        self.setWindowTitle("Estado de Pagos de Clientes")
        # Ventana más ancha para mostrar nombres largos
        self.resize(700, 500)
        self.setMinimumSize(800, 600)
        self.db = db  # SQLAlchemy Database instance

        # Inicializar modelo
        self.client_model = ClientModel(self.db)

        self.setup_ui()
        self.update_table()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Buscador
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Buscar cliente:"))

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
        filter_layout.addWidget(self.search_input)

        layout.addLayout(filter_layout)

        # Tabla
        self.table = QTableView()
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        layout.addWidget(self.table)

        # Leyenda de colores (explica el significado)
        legend_layout = QHBoxLayout()

        def legend_item(color_hex: str, text: str):
            box = QLabel()
            box.setFixedSize(16, 16)
            box.setStyleSheet(f"background-color: {color_hex}; border: 1px solid #444;")
            lbl = QLabel(text)
            item = QHBoxLayout()
            item.addWidget(box)
            item.addWidget(lbl)
            item.setSpacing(8)
            wrap = QHBoxLayout()
            # devolver layout + widgets ya armados no es necesario; usamos contenedor simple:
            container = QHBoxLayout()
            container.addWidget(box)
            container.addWidget(lbl)
            container.setSpacing(8)
            return container

        legend_layout.addLayout(legend_item("#A5D6A7", "Al día (pagó este mes)"))
        legend_layout.addSpacing(12)
        legend_layout.addLayout(legend_item("#FFA726", "Atraso leve (falta el mes actual)"))
        legend_layout.addSpacing(12)
        legend_layout.addLayout(legend_item("#FF5252", "Atraso grave (más de 1 mes o nunca pagó)"))
        legend_layout.addStretch(1)

        layout.addLayout(legend_layout)

        self.setup_autocomplete()

    def setup_autocomplete(self):
        """Configura el autocompletado usando SQLAlchemy"""
        names = self.client_model.get_all_names()

        completer = QCompleter(names, self)
        completer.setCompletionColumn(0)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.search_input.setCompleter(completer)

    def update_table(self):
        """Actualiza la tabla con el estado de los clientes"""
        name = self.search_input.text()

        # Usar el modelo para obtener el estado de los clientes
        results = self.client_model.get_client_status(name)

        # Crear modelo personalizado con colores + meses por nombre
        model = StatusColorModel(results)
        self.table.setModel(model)

        # Configuración del header de la tabla
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)

        col_count = model.columnCount()
        if col_count > 0:
            # Hacer que la primera columna (Cliente) ocupe el espacio restante
            header.setSectionResizeMode(0, QHeaderView.Stretch)

            # Columnas restantes con ancho fijo razonable
            other_width = 120
            for col in range(1, col_count):
                header.setSectionResizeMode(col, QHeaderView.Fixed)
                self.table.setColumnWidth(col, other_width)
