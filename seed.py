"""
Script para poblar la base de datos con datos de prueba
Ejecutar desde la raíz del proyecto: python seed.py
"""
import random
import datetime
from models.database import create_connection, initialize_db
from controllers.payment_controller import PaymentController

# Nombres comunes para generar clientes
FIRST_NAMES = [
    "JUAN", "MARIA", "CARLOS", "ANA", "LUIS", "SOFIA", "DIEGO", "VALENTINA",
    "MATEO", "CAMILA", "SEBASTIAN", "ISABELLA", "NICOLAS", "MIA", "SANTIAGO",
    "EMMA", "LUCAS", "OLIVIA", "BENJAMIN", "AVA", "MATIAS", "LUCIA", "AGUSTIN",
    "MARTINA", "TOMAS", "EMILIA", "SANTIAGO", "CATALINA", "JOAQUIN", "JULIA",
    "GABRIEL", "CLARA", "MARTIN", "PAULA", "FRANCISCO", "CAROLINA", "MANUEL",
    "FERNANDA", "PEDRO", "DANIELA", "ALEJANDRO", "GABRIELA", "RICARDO", "LAURA",
    "FERNANDO", "ANDREA", "ANDRES", "NATALIA", "MIGUEL", "PATRICIA", "JORGE",
    "ELENA", "RAMON", "MONICA", "ALBERTO", "VERONICA", "RAUL", "SILVIA",
    "ANTONIO", "CLAUDIA", "JAVIER", "CECILIA", "DANIEL", "BEATRIZ", "PABLO",
    "MERCEDES", "ROBERTO", "ALEJANDRA", "EDUARDO", "MARIANA", "GUSTAVO", "ROSA",
    "OSCAR", "TERESA", "SERGIO", "ADRIANA", "MARCO", "LETICIA", "VICTOR",
    "SANDRA", "HUGO", "JULIA", "ARMANDO", "ROCIO", "MAURICIO", "PILAR"
]

LAST_NAMES = [
    "PEREZ", "GONZALEZ", "RODRIGUEZ", "MARTINEZ", "FERNANDEZ", "LOPEZ", "SANCHEZ",
    "DIAZ", "RAMIREZ", "TORRES", "FLORES", "GARCIA", "ROMERO", "RUIZ", "MORENO",
    "CASTRO", "ORTIZ", "SILVA", "ROJAS", "MENDOZA", "ALVAREZ", "JIMENEZ", "CRUZ",
    "REYES", "VARGAS", "HERRERA", "MEDINA", "AGUILAR", "RAMOS", "NAVARRO",
    "GUERRERO", "VAZQUEZ", "NUÑEZ", "GUTIERREZ", "DOMINGUEZ", "GOMEZ", "CAMPOS",
    "LEON", "RIOS", "MORALES", "SOTO", "CASTILLO", "MENDEZ", "PONCE", "VEGA",
    "LUNA", "BENITEZ", "CORTEZ", "MIRANDA", "RIVERA", "FUENTES", "SALAZAR",
    "SANTOS", "MOLINA", "ORTEGA", "CONTRERAS", "VILLALOBOS", "PACHECO", "ROMAN",
    "CERVANTES", "SOLIS", "CORDOVA", "DUARTE", "FIGUEROA", "AGUIRRE", "DELGADO"
]

# Descripciones de ejemplo
DESCRIPTIONS = [
    "Pago mensual",
    "Cuota al día",
    "Abono completo",
    "Pago puntual",
    "Mensualidad",
    "Pago regular",
    "Cuota mensual",
    "Abono",
    "",
    "",
    "",
    ""
]


def generate_client_name(existing_names):
    """Genera un nombre único de cliente"""
    max_attempts = 1000
    for _ in range(max_attempts):
        first = random.choice(FIRST_NAMES)
        last1 = random.choice(LAST_NAMES)
        last2 = random.choice(LAST_NAMES)

        # 70% de probabilidad de tener dos apellidos
        if random.random() < 0.7:
            name = f"{first} {last1} {last2}"
        else:
            name = f"{first} {last1}"

        if name not in existing_names:
            return name

    # Si no encuentra un nombre único, agregar un número
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)} {random.randint(1, 999)}"


def generate_payment_date(year, month):
    """Genera una fecha aleatoria dentro del mes especificado"""
    # Determinar el último día del mes
    if month == 12:
        next_month = datetime.date(year + 1, 1, 1)
    else:
        next_month = datetime.date(year, month + 1, 1)

    last_day = (next_month - datetime.timedelta(days=1)).day

    # Generar un día aleatorio (más probabilidad en los primeros 15 días)
    if random.random() < 0.7:
        day = random.randint(1, min(15, last_day))
    else:
        day = random.randint(1, last_day)

    return datetime.date(year, month, day)


def generate_seed_data(num_clients=500):
    """Genera datos de prueba en la base de datos"""

    print("Conectando a la base de datos...")
    db = create_connection("data.db")
    initialize_db(db)

    controller = PaymentController(db)

    print(f"\n🚀 Generando datos de prueba para {num_clients} clientes...")
    print("Esto puede tomar varios minutos...\n")

    current_date = datetime.datetime.now()
    current_year = current_date.year
    current_month = current_date.month

    existing_names = set()
    total_payments = 0
    clients_created = 0

    # Barra de progreso simple
    progress_interval = max(1, num_clients // 20)

    for i in range(num_clients):
        # Generar nombre único
        client_name = generate_client_name(existing_names)
        existing_names.add(client_name)

        # Decidir perfil del cliente
        client_profile = random.choices(
            ['excellent', 'good', 'irregular', 'new', 'delinquent'],
            weights=[20, 35, 25, 15, 5]
        )[0]

        # Configurar pagos según perfil
        if client_profile == 'excellent':
            # Cliente excelente: 12-36 meses consecutivos, hasta el mes actual
            num_months = random.randint(12, 36)
            skip_probability = 0.0
        elif client_profile == 'good':
            # Cliente bueno: 6-24 meses, pocas faltas
            num_months = random.randint(6, 24)
            skip_probability = 0.05
        elif client_profile == 'irregular':
            # Cliente irregular: 3-18 meses con varias faltas
            num_months = random.randint(3, 18)
            skip_probability = 0.25
        elif client_profile == 'new':
            # Cliente nuevo: 1-6 meses recientes
            num_months = random.randint(1, 6)
            skip_probability = 0.0
        else:  # delinquent
            # Cliente moroso: pagos antiguos, sin pagos recientes
            num_months = random.randint(2, 8)
            skip_probability = 0.15

        # Decidir mes de inicio
        if client_profile == 'delinquent':
            # Cliente moroso: comenzó hace mucho tiempo
            start_months_ago = random.randint(6, 24)
        elif client_profile == 'new':
            # Cliente nuevo: comenzó hace poco
            start_months_ago = random.randint(0, 6)
        else:
            # Otros: rango normal
            start_months_ago = random.randint(0, 36)

        # Calcular fecha de inicio
        start_date = current_date - datetime.timedelta(days=start_months_ago * 30)
        start_year = start_date.year
        start_month = start_date.month

        # Generar pagos
        year = start_year
        month = start_month
        payments_created = 0
        consecutive_months = 0

        for _ in range(num_months):
            # No generar pagos futuros
            if year > current_year or (year == current_year and month > current_month):
                break

            # Decidir si se salta este mes (según perfil)
            if random.random() < skip_probability:
                month += 1
                if month > 12:
                    month = 1
                    year += 1
                continue

            # Generar monto aleatorio
            # Montos más altos para clientes con más antigüedad
            if consecutive_months > 12:
                amount = 30000
            elif consecutive_months > 6:
                amount = 40000
            else:
                amount = 50000

            # Seleccionar descripción aleatoria
            description = random.choice(DESCRIPTIONS)

            # Registrar el pago
            success, message, _, _, _ = controller.register_payment(
                client_name,
                amount,
                month,
                year,
                description,
                skip_validation=True
            )

            if success:
                total_payments += 1
                payments_created += 1
                consecutive_months += 1

            # Avanzar al siguiente mes
            month += 1
            if month > 12:
                month = 1
                year += 1

        if payments_created > 0:
            clients_created += 1

        # Mostrar progreso
        if (i + 1) % progress_interval == 0:
            progress = int((i + 1) / num_clients * 100)
            print(f"Progreso: {progress}% ({i + 1}/{num_clients} clientes procesados)")

    print("\n" + "="*70)
    print(f"✅ Seed completado exitosamente!")
    print(f"   Total de clientes creados: {clients_created}")
    print(f"   Total de pagos registrados: {total_payments}")
    print(f"   Promedio de pagos por cliente: {total_payments / clients_created:.1f}")
    print("="*70)
    print("\n📊 Distribución aproximada de perfiles:")
    print("   • Clientes excelentes (12-36 meses): ~20%")
    print("   • Clientes buenos (6-24 meses): ~35%")
    print("   • Clientes irregulares (3-18 meses): ~25%")
    print("   • Clientes nuevos (1-6 meses): ~15%")
    print("   • Clientes morosos (pagos antiguos): ~5%")
    print("="*70)

    db.close_session()


def clear_database():
    """Limpia toda la base de datos (usar con precaución)"""
    print("\n⚠️  ADVERTENCIA: Esta acción eliminará todos los datos de la base de datos.")
    response = input("¿Está seguro de que desea continuar? (escriba 'SI' para confirmar): ")

    if response.upper() != 'SI':
        print("Operación cancelada.")
        return

    db = create_connection("data.db")
    session = db.get_session()

    from models.payment import Payment
    from models.client import Client

    try:
        # Eliminar todos los pagos
        deleted_payments = session.query(Payment).delete()
        session.commit()
        print(f"✓ {deleted_payments} pagos eliminados")

        # Eliminar todos los clientes
        deleted_clients = session.query(Client).delete()
        session.commit()
        print(f"✓ {deleted_clients} clientes eliminados")

        print("\n✅ Base de datos limpiada exitosamente")
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error al limpiar la base de datos: {e}")
    finally:
        db.close_session()


def show_statistics():
    """Muestra estadísticas de la base de datos actual"""
    db = create_connection("data.db")
    session = db.get_session()

    from models.payment import Payment
    from models.client import Client
    from sqlalchemy import func, extract

    try:
        # Contar clientes y pagos
        total_clients = session.query(Client).count()
        total_payments = session.query(Payment).count()

        # Obtener rango de fechas
        oldest = session.query(func.min(extract('year', Payment.date))).scalar()
        newest = session.query(func.max(extract('year', Payment.date))).scalar()

        # Calcular total recaudado
        total_amount = session.query(func.sum(Payment.amount)).scalar() or 0

        # Promedio de pagos por cliente
        avg_payments = total_payments / total_clients if total_clients > 0 else 0

        print("\n" + "="*70)
        print("📊 ESTADÍSTICAS DE LA BASE DE DATOS")
        print("="*70)
        print(f"Total de clientes: {total_clients}")
        print(f"Total de pagos: {total_payments}")
        print(f"Promedio de pagos por cliente: {avg_payments:.1f}")
        print(f"Total recaudado: ${total_amount:,.2f}")
        if oldest and newest:
            print(f"Rango de años: {int(oldest)} - {int(newest)}")
        print("="*70)

    except Exception as e:
        print(f"Error al obtener estadísticas: {e}")
    finally:
        db.close_session()


if __name__ == "__main__":
    print("="*70)
    print("SEED DE BASE DE DATOS - IRON MANAGER")
    print("="*70)
    print("\nOpciones:")
    print("1. Generar datos de prueba (500 clientes)")
    print("2. Generar datos de prueba (cantidad personalizada)")
    print("3. Limpiar base de datos")
    print("4. Limpiar y generar datos nuevos (500 clientes)")
    print("5. Ver estadísticas actuales")
    print("6. Salir")

    option = input("\nSeleccione una opción (1-6): ").strip()

    if option == "1":
        generate_seed_data(500)
    elif option == "2":
        try:
            num = int(input("Ingrese la cantidad de clientes a generar: "))
            if num > 0 and num <= 10000:
                generate_seed_data(num)
            else:
                print("Por favor ingrese un número entre 1 y 10000")
        except ValueError:
            print("Número inválido")
    elif option == "3":
        clear_database()
    elif option == "4":
        clear_database()
        print("\n")
        generate_seed_data(500)
    elif option == "5":
        show_statistics()
    elif option == "6":
        print("Saliendo...")
    else:
        print("Opción inválida")