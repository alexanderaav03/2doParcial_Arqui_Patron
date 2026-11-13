# Requisitos previos (una sola vez)
- Tener Docker Desktop instalado y corriendo
- Tener Flutter instalado
- Clonar el repo: git clone https://github.com/alexanderaav03/2doParcial_Arqui_Patron.git
- Tener el celular conectado por USB con depuración USB activada (o por wifi con adb connect)

# Terminal 1 — levantar backend
cd 2doParcial_Arqui_Patron
docker-compose up

# Terminal 2 — poblar la base de datos (SOLO la primera vez)
pip install sqlalchemy psycopg2-binary python-dotenv passlib
python seed/seed_instructor_clientes.py --docker
python seed/seed_ejercicios.py --docker
python seed/seed_rutinas.py --docker

# Terminal 3 — correr la app móvil
cd app_movil
flutter devices
# copiar el ID que aparece para SU celular 
flutter run -d 15187705CJ007699  --dart-define=GATEWAY_BASE_URL=http://<IP-DE-SU-PC>:8000

# Despliegue en Render

Estructura: 1 instancia de Postgres con 2 bases (`ejercicios` y `rutinas`,
una por microservicio) + 3 web services Docker (gateway, ms-ejercicios,
ms-rutinas) definidos en `render.yaml`. La app Flutter queda en el celular
apuntando a la URL pública del gateway.

## 1. Crear la base `rutinas` dentro de la instancia
La instancia de Postgres trae una sola base (`ejercicios`). La segunda se
crea a mano, una sola vez. En Render → la base de datos → **Connect** →
copiar la **External Database URL** y ejecutar:

    psql "<EXTERNAL_DATABASE_URL>" -c "CREATE DATABASE rutinas;"

Las dos URLs son iguales salvo el nombre de la base al final:

    postgresql://<user>:<password>@<host>/ejercicios   -> ms-ejercicios
    postgresql://<user>:<password>@<host>/rutinas      -> ms-rutinas

Para los servicios usar la **Internal** Database URL (misma red de Render);
para los seeds desde la PC usar la **External** con `?sslmode=require`.

## 2. Crear los servicios y cargar las variables de entorno
Render → **New → Blueprint** → elegir este repo (lee `render.yaml`).
El `JWT_SECRET` lo genera Render una sola vez en el grupo `gym-comun` y
lo comparten los 3 servicios. Las variables marcadas `sync: false` se
piden en el dashboard al crear el Blueprint:

| Servicio | Variable | Valor |
|---|---|---|
| gym-ms-ejercicios | DATABASE_URL | Internal URL terminada en `/ejercicios` |
| gym-ms-ejercicios | SUPABASE_URL | `https://<proyecto>.supabase.co` |
| gym-ms-ejercicios | SUPABASE_KEY | service_role key de Supabase |
| gym-ms-ejercicios | MS_RUTINAS_URL | `https://gym-ms-rutinas.onrender.com` |
| gym-ms-rutinas | DATABASE_URL | Internal URL terminada en `/rutinas` |
| gym-ms-rutinas | MS_EJERCICIOS_URL | `https://gym-ms-ejercicios.onrender.com` |
| gym-gateway | MS_EJERCICIOS_URL | `https://gym-ms-ejercicios.onrender.com` |
| gym-gateway | MS_RUTINAS_URL | `https://gym-ms-rutinas.onrender.com` |

- En el plan gratuito los servicios NO reciben tráfico por la red privada,
  por eso las URLs entre servicios son las públicas `https://...onrender.com`.
- Confirmar la URL real de cada servicio en su página de Render (si el
  nombre ya estaba tomado, Render le agrega un sufijo). Sin barra final.
- Si una URL de base llega como `postgres://`, el código la convierte sola.

## 3. Poblar las bases desde la PC (SOLO la primera vez)
Crear dos `.env` locales (están en .gitignore, NO se suben) con la
**External** Database URL:

    ms-ejercicios/.env  ->  DATABASE_URL=postgresql://<user>:<password>@<host-externo>/ejercicios?sslmode=require
    ms-rutinas/.env     ->  DATABASE_URL=postgresql://<user>:<password>@<host-externo>/rutinas?sslmode=require

Esperar a que ms-ejercicios y ms-rutinas estén "Live" en Render (crean las
tablas al arrancar) y correr los seeds SIN `--docker`, en este orden.
Con `uv` se usa Python 3.11 y las mismas versiones que el servicio:

    uv run --python 3.11 --with-requirements ms-ejercicios/requirements.txt --with python-dotenv python seed/seed_instructor_clientes.py
    uv run --python 3.11 --with-requirements ms-ejercicios/requirements.txt --with python-dotenv python seed/seed_ejercicios.py
    uv run --python 3.11 --with-requirements ms-ejercicios/requirements.txt --with python-dotenv python seed/seed_rutinas.py

Los seeds imprimen la DATABASE_URL (con contraseña) en la consola: no
compartir esa salida. Al terminar se pueden borrar los dos `.env`.

## 4. Compilar la app apuntando al gateway

    cd app_movil
    flutter build apk --release --dart-define=GATEWAY_BASE_URL=https://<gateway>.onrender.com
    flutter install
    # o directo en el celular:
    flutter run --release -d <ID-DEL-CELULAR> --dart-define=GATEWAY_BASE_URL=https://<gateway>.onrender.com

- El build release solo permite HTTPS (el permiso para http:// está solo
  en el manifest de debug, para el desarrollo local).
- Plan gratuito: los servicios se duermen tras ~15 min sin uso y la primera
  petición tarda 30-60 s (los timeouts ya están en 60 s). Antes de una demo,
  abrir `https://<servicio>.onrender.com/health` de los 3 para despertarlos.
- La Postgres gratuita de Render expira a los 30 días de creada.
