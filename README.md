# Predicciones Inmobiliarias

Plataforma web desarrollada con Django para la recopilación, almacenamiento, análisis y visualización de datos inmobiliarios reales de distintas capitales españolas.

El objetivo principal del proyecto es ofrecer una herramienta que permita analizar el mercado inmobiliario mediante datos obtenidos de portales web, almacenados en una base de datos propia y representados visualmente en la aplicación.

---

## Descripción del proyecto

Este proyecto permite recopilar información de viviendas mediante técnicas de scraping web, procesarla y almacenarla en una base de datos MySQL.

La aplicación permite consultar propiedades, visualizar sus características principales y analizar información relevante del mercado, como precios, superficie, número de habitaciones, baños, ubicación, tipo de operación o evolución de precios.

El sistema está pensado para actualizar los datos de forma periódica y evitar duplicidades mediante identificadores únicos para cada propiedad.

---

## Tecnologías utilizadas

### Backend
- Python
- Django
- Django ORM

### Base de datos
- MySQL

### Scraping
- Requests
- BeautifulSoup
- lxml

### Frontend
- HTML5
- CSS3
- JavaScript
- Chart.js

### Control de versiones
- Git
- GitHub

---

## Funcionalidades principales

- Scraping de propiedades inmobiliarias desde portales externos.
- Almacenamiento estructurado de datos en MySQL.
- Gestión de duplicados mediante identificadores únicos.
- Histórico de precios por propiedad.
- Listado de viviendas.
- Filtros por ciudad, operación y precio.
- Visualización de datos mediante gráficas.
- Automatización del scraping cada cierto periodo.
- Sistema de logs para registrar ejecuciones del scraping.
- Cálculo automático del precio por metro cuadrado.
- Separación entre propiedades y listados para mantener historial.

---

## Estructura general del proyecto

```text
project/
│
├── manage.py
├── requirements.txt
├── README.md
│
├── project/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── estateAgency/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── middleware.py
│   │
│   ├── management/
│   │   └── commands/
│   │       ├── import_pisos.py
│   │       └── import_fotocasa.py
│   │
│   ├── services/
│   │   └── scraping/
│   │       ├── pisos_scraper.py
│   │       └── fotocasa_scraper.py
│   │
│   ├── templates/
│   └── static/
```

---

## Requisitos previos

Antes de instalar el proyecto, asegúrate de tener instalado:

- Python 3.10 o superior
- MySQL Server
- Git
- pip
- venv o virtualenv
- Navegador web actualizado

---

## Instalación del proyecto

### 1. Clonar el repositorio

```bash
git clone https://github.com/diegocrd02-prog/app_inmobiliaria
cd app_inmobiliaria
```

### 2. Crear entorno virtual

En Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

En Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## Configuración de la base de datos

### 1. Crear base de datos en MySQL

Accede a MySQL:

```bash
mysql -u root -p
```

Crea la base de datos:

```sql
CREATE DATABASE estateAgency CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. Configurar `settings.py`

En el archivo `settings.py`, configura la conexión a MySQL:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "estateAgency",
        "USER": "root",
        "PASSWORD": "tu_password",
        "HOST": "localhost",
        "PORT": "3306",
    }
}
```

### 3. Ejecutar migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## Crear superusuario

Para acceder al panel de administración de Django:

```bash
python manage.py createsuperuser
```

Después, accede a:

```text
http://127.0.0.1:8000/admin/
```

---

## Ejecutar el proyecto

```bash
python manage.py runserver
```

La aplicación estará disponible en:

```text
http://127.0.0.1:8000/
```

---

## Scraping de datos

El proyecto incluye comandos personalizados de Django para importar datos desde portales inmobiliarios.

### Scraping de pisos.com

Comandos para iniciar el scraping de forma manual:

Ejecutar scraping de venta de forma:

```bash
python manage.py import_pisos --operation sale --limit 15
```

Ejecutar scraping de alquiler largo:

```bash
python manage.py import_pisos --operation rent --rental-type long --limit 15
```

Ejecutar scraping solo para una ciudad:

```bash
python manage.py import_pisos --operation sale --city Madrid --limit 10
```

### Scraping de Fotocasa

Ejecutar scraping de venta:

```bash
python manage.py import_fotocasa --operation sale --limit 15
```

Ejecutar scraping de alquiler largo:

```bash
python manage.py import_fotocasa --operation rent --rental-type long --limit 15
```

Ejecutar scraping de alquiler temporal:

```bash
python manage.py import_fotocasa --operation rent --rental-type short --limit 15
```

---

## Parámetros disponibles en los comandos

| Parámetro | Descripción |
|---|---|
| `--operation` | Tipo de operación: `sale` o `rent` |
| `--rental-type` | Tipo de alquiler: `long` o `short` |
| `--limit` | Número máximo de propiedades a procesar por localización |
| `--city` | Permite limitar el scraping a una ciudad concreta |
| `--max-duplicates` | Número máximo de duplicados consecutivos antes de detener el scraping |

Ejemplo:

```bash
python manage.py import_pisos --operation sale --city Madrid --limit 10 --max-duplicates 5
```

---

## Automatización del scraping

El sistema puede ejecutar el scraping automáticamente al acceder a la aplicación.

La lógica se basa en:

- Consultar la tabla `ScrapingLog`.
- Comprobar la fecha del último scraping.
- Ejecutar una nueva actualización si han pasado 3 días o más.
- Usar caché para evitar ejecuciones simultáneas.
- Mostrar un estado de carga o aviso mientras se actualizan los datos.

Ejemplo conceptual:

```python
last_log = ScrapingLog.objects.order_by("-created_at").first()

if not last_log or last_log.created_at <= timezone.now() - timedelta(days=3):
    run_scraping()
```

---

## Endpoint de estado del scraping

La aplicación puede exponer una ruta para consultar si el scraping está activo:

```text
/scraping/status/
```

Ejemplo de respuesta:

```json
{
    "running": true,
    "pisos": true,
    "fotocasa": false
}
```

Este endpoint permite mostrar un loader o aviso visual en el frontend mientras se actualizan los datos.

---

## Sistema de logs

Cada ejecución del scraping queda registrada en la tabla `ScrapingLog`.

La tabla almacena:

- Fuente de datos.
- Estado de la ejecución (`success` o `error`).
- Mensaje descriptivo.
- Fecha de creación.

Esto permite controlar el funcionamiento del sistema y detectar posibles errores durante la importación de datos.

Ejemplo de tabla:

```sql
CREATE TABLE scraping_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source_id INT,
    status ENUM('success','error'),
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (source_id) REFERENCES source(id) ON DELETE SET NULL
);
```

---

## Modelo de datos principal

### Location

Representa una ubicación geográfica.

Campos principales:

- country
- region
- province
- city
- district
- neighborhood
- postal_code
- latitude
- longitude

### Source

Representa el portal de origen de los datos.

Campos principales:

- name
- base_url

### Property

Representa una vivienda.

Campos principales:

- external_id
- source
- location
- url
- title
- description
- property_type
- operation_type
- rental_type
- rooms
- bathrooms
- size_m2
- floor
- image_url

### Listing

Representa un precio asociado a una propiedad.

Campos principales:

- property
- price
- price_per_m2
- published_at
- scraped_at
- is_active

### PropertyFeature

Representa características adicionales de una vivienda.

Campos principales:

- has_elevator
- has_garage
- has_terrace
- has_pool
- condition_status

### ScrapingLog

Representa el histórico de ejecuciones del scraping.

Campos principales:

- source
- status
- message
- created_at

---

## Gestión de duplicados

Para evitar duplicados, cada propiedad utiliza un identificador externo generado a partir de la URL del anuncio.

Ejemplo:

```python
import hashlib

def make_external_id(url):
    return hashlib.sha256(url.encode("utf-8")).hexdigest()
```

Posteriormente, se usa `get_or_create`:

```python
prop, created = Property.objects.get_or_create(
    external_id=external_id,
    source=source,
    defaults={
        "title": item.title,
        "url": item.url,
        "location": location,
    }
)
```

---

## Histórico de precios

Cuando una propiedad ya existe, el sistema comprueba si el precio ha cambiado.

- Si el precio es igual, se omite.
- Si el precio cambia, se desactiva el listing anterior y se crea uno nuevo.

Esto permite analizar la evolución del precio de cada vivienda.

Ejemplo conceptual:

```python
latest_listing = (
    Listing.objects
    .filter(property=prop, is_active=True)
    .order_by("-id")
    .first()
)

if latest_listing and latest_listing.price == price:
    skipped += 1
else:
    if latest_listing:
        latest_listing.is_active = False
        latest_listing.save(update_fields=["is_active"])

    Listing.objects.create(
        property=prop,
        price=price,
        price_per_m2=price_per_m2,
        is_active=True,
    )
```

---

## Visualización de datos

La aplicación permite mostrar información inmobiliaria en formato visual mediante Chart.js.

Posibles gráficas:

- Precio medio por ciudad.
- Precio por metro cuadrado.
- Evolución de precios.
- Distribución de propiedades por tipo.
- Comparativa entre venta y alquiler.

---

## Buenas prácticas aplicadas

- Código modular.
- Scrapers separados por fuente.
- Uso de comandos personalizados de Django.
- Registro de logs.
- Control de duplicados.
- Separación entre datos estáticos y datos históricos.
- Automatización controlada mediante caché.
- Uso de entorno virtual.
- Separación de responsabilidades entre backend, frontend y scraping.

---

## Consideraciones sobre scraping

El scraping se realiza sobre información pública disponible en portales inmobiliarios.

Durante el desarrollo se han tenido en cuenta buenas prácticas como:

- Controlar la frecuencia de peticiones.
- Evitar ejecuciones simultáneas.
- Gestionar errores sin detener todo el proceso.
- No recopilar datos personales sensibles.
- Registrar errores para facilitar el mantenimiento.


---

## Posibles mejoras futuras

- Incorporación de nuevos portales inmobiliarios.
- Mejora de la deduplicación entre distintas fuentes.
- Integración de mapas interactivos.
- Desarrollo de una API pública.
- Implementación de modelos de Machine Learning para predicción de precios.
- Despliegue en entorno cloud.
- Panel de administración avanzado.
- Sistema de usuarios y favoritos.
- Mejoras en la visualización de gráficos.
- Exportación de datos en CSV o Excel.

---

## Problemas conocidos

- Algunos portales cargan contenido de forma dinámica mediante JavaScript.
- La estructura HTML de las páginas puede cambiar con el tiempo.
- Algunos anuncios pueden aparecer duplicados entre distintas fuentes.
- La extracción de datos depende de la disponibilidad pública de cada portal.
