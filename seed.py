"""
Script para poblar la base de datos con datos de prueba
Ejecutar desde la raíz del proyecto: python seed.py
"""
import random
import datetime
import time
from models.database import create_connection, initialize_db
from models.payment import Payment
from models.client import Client

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


def generate_insertion_delay(payment_date, profile='normal'):
    """
    Calcula cuántos días después del pago se ingresó al sistema.
    
    Args:
        payment_date: Fecha del pago
        profile: 'punctual', 'normal', 'delayed', 'very_delayed'
    
    Returns:
        int: Días de retraso en el ingreso al sistema
    """
    if profile == 'punctual':
        # Registrado el mismo día o al día siguiente
        return random.randint(0, 1)
    elif profile == 'normal':
        # Registrado entre el mismo día y 5 días después
        return random.randint(0, 5)
    elif profile == 'delayed':
        # Registrado entre 5 y 15 días después
        return random.randint(5, 15)
    else:  # very_delayed
        # Registrado entre 15 y 45 días después
        return random.randint(15, 45)


def generate_seed_data(num_clients=500):
    """Genera datos de prueba en la base de datos"""

    print("Conectando a la base de datos...")
    db = create_connection("data.db")
    initialize_db(db)
    session = db.get_session()

    print(f"\n🚀 Generando datos de prueba para {num_clients} clientes...")
    print("Esto puede tomar varios minutos...\n")

    current_date = datetime.datetime.now()
    current_year = current_date.year
    current_month = current_date.month

    existing_names = set()
    total_payments = 0
    clients_created = 0
    
    # Lista para almacenar todos los pagos con su timestamp de inserción
    all_payments = []

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
            num_months = random.randint(12, 36)
            skip_probability = 0.0
            entry_profile = random.choices(
                ['punctual', 'normal', 'delayed'],
                weights=[50, 40, 10]
            )[0]
        elif client_profile == 'good':
            num_months = random.randint(6, 24)
            skip_probability = 0.05
            entry_profile = random.choices(
                ['punctual', 'normal', 'delayed'],
                weights=[30, 50, 20]
            )[0]
        elif client_profile == 'irregular':
            num_months = random.randint(3, 18)
            skip_probability = 0.25
            entry_profile = random.choices(
                ['normal', 'delayed', 'very_delayed'],
                weights=[30, 50, 20]
            )[0]
        elif client_profile == 'new':
            num_months = random.randint(1, 6)
            skip_probability = 0.0
            entry_profile = random.choices(
                ['punctual', 'normal'],
                weights=[40, 60]
            )[0]
        else:  # delinquent
            num_months = random.randint(2, 8)
            skip_probability = 0.15
            entry_profile = random.choices(
                ['delayed', 'very_delayed'],
                weights=[40, 60]
            )[0]

        # Decidir mes de inicio
        if client_profile == 'delinquent':
            start_months_ago = random.randint(6, 24)
        elif client_profile == 'new':
            start_months_ago = random.randint(0, 6)
        else:
            start_months_ago = random.randint(0, 36)

        # Calcular fecha de inicio
        start_date = current_date - datetime.timedelta(days=start_months_ago * 30)
        start_year = start_date.year
        start_month = start_date.month

        # Crear el cliente primero
        client = Client(name=client_name, last_payment_id=None)
        session.add(client)
        session.flush()  # Para obtener el ID sin hacer commit
        
        # Generar pagos para este cliente
        year = start_year
        month = start_month
        payments_created = 0
        consecutive_months = 0
        client_payments = []

        for _ in range(num_months):
            # No generar pagos futuros
            if year > current_year or (year == current_year and month > current_month):
                break

            # Decidir si se salta este mes
            if random.random() < skip_probability:
                month += 1
                if month > 12:
                    month = 1
                    year += 1
                continue

            # Generar monto aleatorio
            if consecutive_months > 12:
                amount = 30000
            elif consecutive_months > 6:
                amount = 40000
            else:
                amount = 50000

            # Seleccionar descripción aleatoria
            description = random.choice(DESCRIPTIONS)

            # Generar fecha de pago
            payment_date = generate_payment_date(year, month)
            
            # Calcular cuándo se ingresó al sistema
            payment_entry_profile = entry_profile
            if random.random() < 0.2:  # 20% de variación
                payment_entry_profile = random.choice(['punctual', 'normal', 'delayed', 'very_delayed'])
            
            insertion_delay = generate_insertion_delay(payment_date, payment_entry_profile)
            insertion_datetime = datetime.datetime.combine(payment_date, datetime.time(
                hour=random.randint(8, 18),  # Entre 8am y 6pm
                minute=random.randint(0, 59),
                second=random.randint(0, 59)
            )) + datetime.timedelta(days=insertion_delay)
            
            # No permitir fechas futuras
            if insertion_datetime > datetime.datetime.now():
                insertion_datetime = datetime.datetime.now()

            # Crear el objeto Payment
            payment = Payment(
                client_id=client.id,
                date=payment_date.isoformat(),
                amount=amount,
                month=month,
                year=year,
                description=description
            )
            
            # Guardar el pago con su timestamp de inserción
            all_payments.append((payment, insertion_datetime))
            client_payments.append(payment)
            
            payments_created += 1
            consecutive_months += 1

            # Avanzar al siguiente mes
            month += 1
            if month > 12:
                month = 1
                year += 1

        if payments_created > 0:
            clients_created += 1
            total_payments += payments_created

        # Mostrar progreso
        if (i + 1) % progress_interval == 0:
            progress = int((i + 1) / num_clients * 100)
            print(f"Progreso: {progress}% ({i + 1}/{num_clients} clientes procesados)")

    # Ordenar todos los pagos por fecha de inserción
    all_payments.sort(key=lambda x: x[1])
    
    print("\n📥 Insertando pagos en orden cronológico...")
    
    # Insertar los pagos en orden cronológico de inserción
    progress_interval = max(1, len(all_payments) // 20)
    for idx, (payment, insertion_time) in enumerate(all_payments):
        session.add(payment)
        
        if (idx + 1) % 100 == 0:  # Commit cada 100 registros
            session.commit()
        
        if (idx + 1) % progress_interval == 0:
            progress = int((idx + 1) / len(all_payments) * 100)
            print(f"Insertando: {progress}% ({idx + 1}/{len(all_payments)} pagos)")
    
    # Commit final
    session.commit()
    
    # Actualizar last_payment_id para cada cliente
    print("\n🔄 Actualizando últimos pagos de clientes...")
    clients = session.query(Client).all()
    for client in clients:
        latest_payment = session.query(Payment).filter_by(
            client_id=client.id
        ).order_by(
            Payment.year.desc(),
            Payment.month.desc(),
            Payment.id.desc()
        ).first()
        
        if latest_payment:
            client.last_payment_id = latest_payment.id
    
    session.commit()

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
    print("\n📅 Retrasos en el ingreso al sistema:")
    print("   • Puntuales (0-1 días): ~25%")
    print("   • Normales (0-5 días): ~45%")
    print("   • Demorados (5-15 días): ~20%")
    print("   • Muy demorados (15-45 días): ~10%")
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