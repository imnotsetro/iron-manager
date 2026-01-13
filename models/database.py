from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()


class Database:
    """Clase para manejar la conexión a la base de datos con SQLAlchemy"""

    def __init__(self, db_filename="data.db"):
        self.engine = create_engine(f'sqlite:///{db_filename}', echo=False)
        self.Session = sessionmaker(bind=self.engine)
        self._session = None

    def get_session(self):
        """Obtiene o crea una sesión de base de datos"""
        if self._session is None:
            self._session = self.Session()
        return self._session

    def close_session(self):
        """Cierra la sesión actual"""
        if self._session:
            self._session.close()
            self._session = None

    def initialize_db(self):
        """Crea todas las tablas definidas en los modelos"""
        Base.metadata.create_all(self.engine)


def create_connection(db_filename="data.db"):
    """Crea y retorna una instancia de Database"""
    db = Database(db_filename)
    return db


def initialize_db(db):
    """Inicializa las tablas de la base de datos"""
    db.initialize_db()