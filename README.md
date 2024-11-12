# **Proyecto de Reconocimiento de Patentes (OCR) con Server Web Asíncrono**

Este proyecto implementa un sistema completo de reconocimiento de patentes con **Python**, utilizando tecnologías como **aiohttp** para servir un servidor web asíncrono, **OpenCV** y **ONNX** para el procesamiento de imágenes y **MySQL** para almacenar los resultados. Además, el sistema está optimizado con **Docker** para facilitar la configuración y el despliegue, y con **SSL** para habilitar comunicaciones seguras (HTTPS).

## **Características**

- **Carga de imágenes**: Permite a los usuarios cargar imágenes de patentes a través de un formulario web.
- **Reconocimiento de patentes**: El sistema utiliza un modelo de reconocimiento de patentes (CNN) implementado con **ONNX** para identificar patentes en las imágenes.
- **Base de datos**: Los resultados del reconocimiento se almacenan en una base de datos **MySQL**.
- **Dashboard**: Interfaz web para visualizar los registros de las patentes procesadas.
- **API RESTful**: Exposición de datos mediante una API REST para integrar con otras aplicaciones.
- **Servidor Asíncrono**: El servidor web está basado en **aiohttp** para permitir un manejo eficiente de múltiples solicitudes simultáneas.
- **SSL y Seguridad**: La aplicación puede configurarse para usar HTTPS con un certificado SSL.

---

## **Contenido**

1. [Requisitos](#requisitos)
2. [Instalación y Configuración](#instalación-y-configuración)
3. [Despliegue con Docker](#despliegue-con-docker)
4. [Uso](#uso)
5. [Estructura del Proyecto](#estructura-del-proyecto)
6. [Servidor Web y Rutas](#servidor-web-y-rutas)
7. [Base de Datos](#base-de-datos)
8. [Contribuciones](#contribuciones)
9. [Licencia](#licencia)

---

## **Requisitos**

Para ejecutar este proyecto, necesitas tener instaladas las siguientes herramientas y dependencias:

- **Docker** y **Docker Compose**: Para contenerizar la aplicación y facilitar el despliegue.
- **Python 3.10+**: Para ejecutar la aplicación.
- **ONNX** y **Fast Plate OCR**: Para el reconocimiento de patentes.
- **aiohttp**: Framework para manejar solicitudes asíncronas.
- **MySQL**: Base de datos para almacenar los resultados.
- **SSL**: Para habilitar HTTPS (opcional).

### **Dependencias de Python**

Asegúrate de instalar todas las dependencias de Python, que se encuentran en el archivo `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

## **Instalación y Configuración**

### **1. Clonar el repositorio**

Primero, clona el repositorio en tu máquina local:

```bash
git clone https://github.com/tu_usuario/nombre_del_repositorio.git
cd nombre_del_repositorio
```

### **2. Crear un entorno virtual (opcional)**

Para mantener las dependencias organizadas, es recomendable usar un entorno virtual de Python:

```bash
python3 -m venv venv
source venv/bin/activate  # En Unix/macOS
venv\Scripts\activate  # En Windows
```

### **3. Configurar la base de datos**

Configura tu base de datos **MySQL** de acuerdo a tus necesidades, o usa Docker para levantar un contenedor de base de datos.

Las credenciales de conexión se definen en el código de la aplicación y en las variables de entorno.

---

## **Despliegue con Docker**

Este proyecto utiliza **Docker** para contenerizar los servicios. Para desplegar la aplicación junto con la base de datos y phpMyAdmin, sigue estos pasos:

1. **Crea un archivo `docker-compose.yml`** con la siguiente configuración (ajusta las credenciales y configuraciones a tus necesidades):

```yaml
version: '3.8'
services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root_password
      MYSQL_DATABASE: registros_patentes
    volumes:
      - mysql_data:/var/lib/mysql
    networks:
      - backend_network
    ports:
      - "3306:3306"

  phpmyadmin:
    image: phpmyadmin/phpmyadmin
    environment:
      PMA_HOST: mysql
      PMA_USER: root
      PMA_PASSWORD: root_password
    networks:
      - backend_network
    ports:
      - "8080:80"
      
  python_app:
    build: .
    command: python3 servidor.py
    networks:
      - backend_network
    depends_on:
      - mysql
    ports:
      - "8000:8000"

networks:
  backend_network:
    driver: bridge

volumes:
  mysql_data:
```

2. **Levanta los servicios con Docker Compose**:

```bash
docker-compose up --build
```

Este comando construirá y levantará los contenedores de la aplicación Python, MySQL y phpMyAdmin.

---

## **Uso**

### **Acceso a la aplicación**

Una vez que el servidor esté corriendo, puedes acceder a los siguientes servicios:

- **Aplicación web (backend)**: `http://localhost:8000`
- **phpMyAdmin (gestión de la base de datos)**: `http://localhost:8080`
  - Usuario: `root`
  - Contraseña: `root_password`

### **Cargar una imagen**

Para cargar una imagen, ve a `http://localhost:8000/upload.html` y utiliza el formulario de carga. La imagen se procesará y se almacenará en la base de datos.

### **Ver registros de patentes**

Accede al dashboard en `http://localhost:8000/show.html` para ver las patentes procesadas, su ubicación y el tiempo transcurrido desde su carga.

---

## **Servidor Web y Rutas**

La aplicación utiliza **aiohttp** como servidor web asíncrono. A continuación se detallan las principales rutas y funciones:

### **1. Ruta de Inicio**

- **URL**: `/`
- **Método**: `GET`
- **Descripción**: Carga la página de inicio con un formulario básico de carga de imágenes.

### **2. Ruta de Carga de Imágenes**

- **URL**: `/upload`
- **Método**: `POST`
- **Descripción**: Recibe una imagen y la guarda en el servidor para su procesamiento. El procesamiento se realiza en segundo plano.

### **3. Ruta para Ver los Registros**

- **URL**: `/show.html`
- **Método**: `GET`
- **Descripción**: Muestra una tabla con las imágenes procesadas y los detalles como la patente, la ubicación, el tiempo transcurrido y un botón de cobro si corresponde.

### **4. Ruta de Cobro**

- **URL**: `/cobrar`
- **Método**: `POST`
- **Descripción**: Permite calcular el monto a pagar basado en el tiempo transcurrido desde que la patente fue capturada.

### **5. Ruta de Dashboard (API)**

- **URL**: `/api/dashboard-data`
- **Método**: `GET`
- **Descripción**: Devuelve los datos de las patentes procesadas en formato JSON para ser utilizados en un dashboard.

### **6. Ruta de Carga Asíncrona**

- **URL**: `/upload.html`
- **Método**: `GET`
- **Descripción**: Sirve la página HTML para cargar las imágenes.

### **7. Ruta de Cargar y Pagar Imagen**

- **URL**: `/pagar`
- **Método**: `POST`
- **Descripción**: Permite cargar una imagen y recibir un procesamiento de la patente y el cálculo de su monto.

---

## **Base de Datos**

La base de datos utilizada en este proyecto es **MySQL**. Los resultados del procesamiento de imágenes se almacenan en una tabla con los siguientes campos:

- **Fecha y Hora**: Timestamp cuando la imagen fue procesada.
- **Imagen**: Los datos binarios de la imagen cargada.
- **Ubicación**: Un enlace generado o predeterminado.
- **Patente**: El número de patente reconocido en la imagen.

La aplicación se conecta a la base de datos a través de un módulo de conexión que maneja las operaciones de inserción y consulta.

---

## **Contribuciones**

Las contribuciones son bienvenidas. Si deseas mejorar o añadir nuevas funcionalidades, sigue estos pasos:

1. Haz un fork del repositorio.
2. Crea una nueva rama para tu funcionalidad: `git checkout -b mi-feature`.
3. Realiza tus cambios y haz commit: `git commit -am 'Agrega nueva funcionalidad'`.
4. Empuja tus cambios a tu repositorio: `git push origin mi-feature`.
5. Abre un pull request desde tu rama a la rama principal.

---

## **Licencia**

Este proyecto está licenciado bajo la Licencia MIT - consulta el archivo [LICENSE](LICENSE) para más detalles.

---

Este conjunto de documentación cubre los aspectos esenciales del proyecto, incluyendo la configuración, el servidor web y la estructura de la base de datos. Puedes adaptarla según el progreso del proyecto o las futuras características.
