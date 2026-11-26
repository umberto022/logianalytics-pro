# LogiAnalytics Pro

Aplicación web para gestionar inventario, registrar ventas y consultar la rentabilidad por producto y por ruta. Cada venta asociada a un producto actualiza sus existencias y deja un registro del movimiento.

[Arquitectura](#arquitectura) · [Estructura del repositorio](#estructura-del-repositorio) · [Inicio rápido](#inicio-rápido) · [Verificación](#verificación)

## Arquitectura

La aplicación se ejecuta en un proceso de **Streamlit**. `app.py` gestiona el inicio de sesión, la configuración inicial de empresa y la navegación. Las vistas consultan y actualizan los datos a través de la clase `Database`. **SQLite** guarda los datos en un archivo local y **pandas** y **Plotly** se usan para presentar tablas y gráficos en las vistas de análisis.

```mermaid
flowchart TD
    Browser["Usuario · Navegador"]

    subgraph Streamlit["Aplicación Streamlit"]
        App["app.py<br/>Acceso, configuración inicial y navegación"]
        subgraph Views["Vistas · views/"]
            Dashboard["Dashboard"]
            Sales["Ventas"]
            Profit["Rentabilidad"]
            Inventory["Inventario"]
            Settings["Configuración"]
        end
        App --> Dashboard & Sales & Profit & Inventory & Settings
    end

    Data["database.py<br/>Consultas y operaciones de negocio"]
    SQLite[("SQLite<br/>logi_analytics.db")]

    Browser <--> App
    App --> Data
    Dashboard & Sales & Profit & Inventory & Settings --> Data
    Data <--> SQLite
```

### Flujo de una venta

```mermaid
sequenceDiagram
    actor U as Usuario
    participant V as Ventas
    participant D as Database
    participant S as SQLite

    U->>V: Selecciona producto, cantidad y precio
    V->>D: Solicita registrar la venta
    D->>S: Consulta el producto y el stock del usuario
    alt Producto disponible y stock suficiente
        D->>D: Calcula ingreso, costo y ganancia
        D->>S: Inserta la venta
        Note over S: Un trigger descuenta el stock<br/>y registra el movimiento de salida
        D->>S: Confirma la transacción
        D-->>V: Venta registrada
        V-->>U: Muestra la confirmación
    else Producto inexistente o stock insuficiente
        D-->>V: Devuelve el motivo del rechazo
        V-->>U: Muestra el mensaje
    end
```

| Vista | Función |
| --- | --- |
| **Dashboard** | Resume ingresos, ganancias, ventas, valor de inventario y alertas de stock. |
| **Ventas** | Registra ventas, muestra el historial y permite descargarlo en CSV. |
| **Rentabilidad** | Compara ingresos, costos y márgenes por producto y ruta. |
| **Inventario** | Gestiona productos, niveles de stock y movimientos. Permite importar y exportar CSV. |
| **Configuración** | Permite gestionar los datos del perfil y de la empresa. |

## Estructura del repositorio

```text
logianalytics-pro/
├── app.py                          # Punto de entrada, acceso y navegación
├── database.py                     # Esquema SQLite y operaciones de datos
├── views/
│   ├── dashboard.py                # Indicadores y alertas
│   ├── sales.py                    # Registro e historial de ventas
│   ├── profitability.py            # Rentabilidad por producto y ruta
│   ├── inventory.py                # Productos, existencias y movimientos
│   └── settings.py                 # Perfil y empresa
├── .streamlit/config.toml          # Configuración y tema de Streamlit
├── static/                         # Iconos y manifiesto web
├── requirements.txt                # Dependencias de Python
├── test_app.py                     # Script de comprobación de una versión anterior
└── LogiAnalytics_Pro_Complete/      # Implementaciones y archivos de hosting anteriores
```

Para ejecutar o modificar la aplicación principal, usa [`app.py`](app.py), [`views/`](views/) y [`database.py`](database.py) en la raíz del repositorio. Allí está el flujo descrito en los diagramas.

## Inicio rápido

Los siguientes comandos usan un entorno virtual y funcionan en macOS y Linux. La instalación se verificó con **Python 3.12**.

```bash
git clone https://github.com/umberto022/logianalytics-pro.git
cd logianalytics-pro
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

En Windows PowerShell, activa el entorno con `.\.venv\Scripts\Activate.ps1`.

Abre **http://localhost:8501** y usa la pestaña **Crear cuenta** para empezar. Puedes registrar una empresa durante la configuración inicial u omitir ese paso. La aplicación inicializa `logi_analytics.db` en la raíz al acceder por primera vez a la base de datos. Ese archivo guarda los datos entre ejecuciones y está excluido de Git.

## Verificación

1. Crea una cuenta e inicia sesión.
2. En **Inventario**, agrega un producto con 10 unidades y un costo unitario de 4.
3. En **Ventas**, registra 3 unidades de ese producto a un precio unitario de 9 y asigna una ruta.
4. Comprueba que quedan 7 unidades en **Inventario** y que aparece el movimiento de salida.
5. Consulta **Dashboard** y **Rentabilidad**. La venta debe sumar 27 de ingresos y 15 de ganancia en el período correspondiente.

El script [`test_app.py`](test_app.py) todavía espera la estructura y la interfaz de base de datos de una versión anterior. La comprobación anterior recorre el flujo de la aplicación actual.
