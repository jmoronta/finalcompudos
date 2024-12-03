# Proyecto Final: Aplicación de Gestión de Patentes Vehiculares

## Índice
1. [Descripción General de la Aplicación](#descripción-general-de-la-aplicación)
2. [Características Principales](#características-principales)
3. [Arquitectura de la Aplicación](#arquitectura-de-la-aplicación)
    - [Descripción Conceptual](#descripción-conceptual)
    - [Gráfico de la Arquitectura](#gráfico-de-la-arquitectura)
4. [Funcionalidades de Cada Componente](#funcionalidades-de-cada-componente)
    - [Cliente](#cliente)
    - [Servidor](#servidor)
    - [Base de Datos](#base-de-datos)
    - [Dashboard](#dashboard)
5. [Implementación Técnica](#implementación-técnica)
    - [Código del Servidor](#código-del-servidor)
    - [Estructura de la Base de Datos](#estructura-de-la-base-de-datos)
6. [Requisitos para Ejecutar el Proyecto](#requisitos-para-ejecutar-el-proyecto)
    - [Dependencias](#dependencias)
    - [Ejecución con Docker](#ejecución-con-docker)
    - [Configuración Manual](#configuración-manual)
7. [Contribuciones y Feedback](#contribuciones-y-feedback)

---

## Descripción General de la Aplicación
Este proyecto implementa una aplicación cliente-servidor diseñada para la gestión y monitoreo de registros de patentes vehiculares. La arquitectura combina concurrencia, comunicación asincrónica y manejo eficiente de datos, aprovechando una base de datos MySQL como sistema de almacenamiento persistente.

---

## Características Principales
- **Cliente**: Envío de imágenes de patentes junto con su ubicación geográfica (URL, latitud y longitud).
- **Servidor**: Procesa y almacena la información de las patentes en una base de datos relacional. Provee funcionalidades para visualizar estadísticas y generar reportes.
- **Concurrencia**: Múltiples clientes pueden interactuar simultáneamente con el servidor.
- **Comunicación Asincrónica**: Los datos entre cliente y servidor se transfieren usando solicitudes HTTP o sockets (dependiendo de la implementación final).
- **Persistencia**: La información se guarda en tablas estructuradas dentro de una base de datos MySQL.

---

## Arquitectura de la Aplicación

### Descripción Conceptual
**Cliente:**
- Captura imágenes de las patentes vehiculares.
- Obtiene la ubicación asociada (URL, latitud y longitud).
- Envía la información al servidor para ser procesada.

**Servidor:**
- Recibe los datos enviados por los clientes.
- Almacena las imágenes y los metadatos (fecha, patente, ubicación) en la base de datos.
- Genera estadísticas y permite consultas avanzadas.
- Calcula y almacena cobros asociados a las patentes.

---

### Gráfico de la Arquitectura

![Arquitectura1](https://github.com/user-attachments/assets/a0038dfa-b836-4a9d-9525-ac49abe7d025)

---![Arquitectura2](https://github.com/user-attachments/assets/47934a32-c3c2-4f11-b6cb-bae31298dfd8)


## Funcionalidades de Cada Componente

### Cliente
- Captura imágenes y metadatos asociados (fecha, patente, ubicación).
- Envía los datos al servidor utilizando un protocolo de comunicación definido (HTTP o sockets).

### Servidor
- Procesa las solicitudes entrantes de los clientes.
- Almacena los datos recibidos en la base de datos:
  - **Fecha y hora de registro.**
  - **Imagen** (en formato binario).
  - **Ubicación** (URL, latitud, longitud).
  - **Patente vehicular**.
- Genera estadísticas sobre:
  - Total de patentes registradas.
  - Número de ubicaciones únicas.
  - Total acumulado de cobros.
- Maneja concurrencia para admitir múltiples solicitudes simultáneamente.

### Base de Datos
- **Estructura principal:**
  - Tabla `patente`:
    - Registra fecha, imagen, ubicación y datos de la patente.
  - Tabla `cobros`:
    - Contiene tiempo y montos asociados a cada patente.
- **Consultas clave:**
  - Número total de registros de patentes.
  - Total acumulado de cobros.
  - Número de ubicaciones únicas.

### Dashboard
- Visualiza estadísticas generales:
  - Cantidad de patentes registradas.
  - Ubicaciones únicas.
  - Monto total de cobros generados.
- Permite acceder a datos históricos o en tiempo real.

---

## Implementación Técnica
1. Multiprocesamiento
Uso: Distribuir tareas en múltiples procesos del sistema operativo para aprovechar los núcleos disponibles.
Implementación:
Se utilizan módulos como multiprocessing para ejecutar tareas independientes, como el procesamiento de imágenes o cálculos de métricas, en procesos separados.
Esto asegura que las operaciones más intensivas no bloqueen el hilo principal.

2. Asincronismo
Uso: Manejar solicitudes de clientes sin esperar a que cada tarea termine (I/O no bloqueante).
Implementación:
asyncio o librerías similares permiten que el servidor procese múltiples conexiones de clientes al mismo tiempo.
Ideal para operaciones dependientes de I/O, como comunicación con la base de datos o envío/recepción de datos.

3. Workers
Uso: Delegar tareas específicas a procesos o threads secundarios, conocidos como trabajadores.
Implementación:
Se utiliza un pool de workers para manejar trabajos como:
Procesamiento de imágenes cargadas.
Registro de cobros en la base de datos.
Este enfoque combina concurrencia y eficiencia, ya que los workers ejecutan en paralelo y liberan al servidor principal de operaciones largas.

4. Mecanismos de Comunicación entre Procesos (IPC)
Uso: Coordinar y compartir datos entre procesos concurrentes.
Implementación:
Colas (Queue): Usadas para pasar mensajes o tareas entre el servidor principal y los workers.

5. Concurrencia en el Servidor
Uso: Permitir múltiples conexiones simultáneas sin bloquear operaciones críticas.
Implementación:
Se emplean threads o event loops para gestionar solicitudes entrantes de múltiples clientes.
Esto incluye el manejo de solicitudes HTTP, validación de datos, y enrutamiento hacia el almacenamiento o procesamiento.


### Código del Servidor
El servidor contiene funciones clave para interactuar con la base de datos:

1. **Insertar Registro de Patente:**
   ```python
   def insert_en_tabla(imagen, patente, link):
Obtener Datos:

def obtener_datos():
Recupera todos los registros de la tabla de patentes.

Insertar Cobro:

def insertar_cobro(patente, tiempo, monto):
Registra un nuevo cobro asociado a una patente.

Generar Datos del Dashboard:

def dashboard_data():
Obtiene estadísticas agregadas como el total de patentes y cobros.

Estructura de la Base de Datos
Tabla patente:

fecha_hora: Fecha y hora del registro.
imagen: Imagen en formato binario.
ubicacion: URL asociada a la ubicación.
patente: Texto de la patente.
latitud y longitud: Coordenadas geográficas.
Tabla cobros:

patente: Patente registrada.
tiempo: Tiempo asociado al cobro.
cobrar: Monto calculado.

Requisitos para Ejecutar el Proyecto
Dependencias
Python 3.x
MySQL
Librerías adicionales:
pip install pymysql

Ejecución con Docker
El proyecto incluye un archivo docker-compose.yml para simplificar la configuración.
Comando para iniciar el entorno:
docker-compose up

Configuración Manual
Crear la base de datos MySQL con las tablas necesarias.
Ajustar los valores de conexión en el código.

Contribuciones y Feedback
Este proyecto está diseñado para iteraciones rápidas.
Por favor, comparte tus observaciones o solicitudes de cambios directamente en el repositorio mediante issues o pull requests. Cada cambio será registrado y versionado.




