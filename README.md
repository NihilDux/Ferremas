# Ferremas

## Descripción
Ferremas es una aplicación web para la gestión de una ferretería. Permite a los usuarios consultar productos, realizar compras y gestionar inventarios.

## Lenguajes
- Python
- JavaScript
- HTML
- CSS

## Tecnología
- Django (Framework web principal)
- Flask (API para conexión con la base de datos PostgreSQL)
- PostgreSQL (Base de datos)
- Bootstrap (Para diseño responsivo)

## Arquitectura
El proyecto sigue la arquitectura MVT (Model-View-Template) proporcionada por Django:
- **Modelos (Models)**: Representan las estructuras de datos de la aplicación.
- **Vistas (Views)**: Gestionan la lógica de negocio y controlan el flujo de datos.
- **Plantillas (Templates)**: Se encargan de la presentación de la interfaz de usuario.

## Base de Datos
La base de datos utilizada es PostgreSQL. La conexión a la base de datos se realiza a través de una API desarrollada en Flask, la cual proporciona endpoints para la gestión y consulta de datos.

## Framework
- Django: Utilizado para el desarrollo de la aplicación web.
- Flask: Utilizado para la creación de la API de conexión con la base de datos.

## Instalación y Configuración
1. Clona el repositorio:
    ```sh
    git clone https://github.com/NihilDux/Ferremas.git
    cd Ferremas
    ```

2. Configura el entorno virtual:
    ```sh
    python -m venv venv
    source venv/bin/activate  # En Windows usa `venv\Scripts\activate`
    ```

3. Instala las dependencias:
    ```sh
    pip install -r requirements.txt
    ```

4. Ejecuta el servidor de Django:
    ```sh
    python manage.py runserver
    ```

5. Ejecuta la API de Flask:
    ```sh
    python app.py  # Asegúrate de estar en el directorio correcto para ejecutar este comando
    ```
