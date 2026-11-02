# Sistema de Control de Caja y Gestión de Proveedores

Un sistema de escritorio desarrollado en Python utilizando la librería `customtkinter` para la interfaz gráfica y `SQLAlchemy` para la persistencia de datos en una base de datos SQLite local. 

El sistema está diseñado para pequeños y medianos comercios que necesitan llevar un control estricto de sus cierres de caja diarios (turnos) y administrar cuentas corrientes con proveedores.

## 🚀 Características Principales

### Control de Caja y Movimientos
- **Apertura de Caja:** Registro de saldo o fondo fijo inicial.
- **Registro de Movimientos:** Ingresos (Ventas) y Egresos (Gastos o Retiros) con múltiples métodos de pago (Efectivo, Transferencia, Tarjetas, QR).
- **Cierre de Caja Automático:** Calcula totales y exporta un resumen completo en formato PDF.
- **Historial de Cierres:** Visualización de cierres pasados con buscador de fechas y detalles completos de cada movimiento.
- **Anulación de Movimientos:** Permite anular errores antes de realizar el cierre de caja.

### Gestión de Proveedores
- **Registro de Cuentas:** Alta y modificación de perfiles de proveedores.
- **Carga de Pedidos/Facturas:** Suma saldos de deuda y permite asignar números de remito, factura y fechas de vencimiento.
- **Registro de Pagos:** Resta deuda y opcionalmente descuenta el dinero de la caja diaria de forma automática.
- **Historial de Cuenta Corriente:** Exportación de resúmenes de cuenta por proveedor en formato PDF.
- **Calendario de Vencimientos:** Sistema visual e interactivo de alertas de facturas próximas a vencer o vencidas.

### Resumen y Estadísticas
- Panel de indicadores clave (KPIs) con deudas acumuladas, ingresos y egresos históricos.
- Desglose de ingresos por método de pago.
- Sistema de backup (respaldo) integrado para la base de datos `caja_ventas.db`.

## 🛠️ Requisitos Técnicos

El sistema requiere Python 3.9 o superior. Las dependencias están listadas en el archivo `requirements.txt`:
- `sqlalchemy>=2.0.0`
- `fpdf2>=2.7.0`
- `customtkinter>=5.2.0`
- `pillow>=10.0.0`
- `tkcalendar>=1.6.1`

## 📦 Instalación y Uso

1. **Clonar o descargar** este repositorio en tu computadora.
2. Si tienes Windows, simplemente haz doble clic en el archivo **`Control de Caja.bat`**.
   - Este script instalará automáticamente las dependencias necesarias y creará un acceso directo en tu escritorio.
3. Si deseas correrlo manualmente desde la terminal:
   ```bash
   pip install -r requirements.txt
   python app.py
   ```

## 📁 Estructura del Proyecto

Los archivos necesarios que debes subir a GitHub (o mantener en tu carpeta) son:

*   **`app.py`**: Archivo principal que ejecuta la interfaz gráfica (las pestañas, tablas y cuadros de diálogo).
*   **`services.py`**: Contiene toda la lógica de negocio (funciones para registrar ingresos, cerrar caja, calcular vencimientos).
*   **`database.py`**: Configuración e inicialización de la conexión con la base de datos SQLite.
*   **`models.py`**: Modelos de datos (tablas `cierres_caja`, `movimientos_caja`, `proveedores`, `movimientos_proveedor`).
*   **`pdf_report.py`**: Clases y funciones que generan los reportes en PDF usando la librería fpdf2.
*   **`requirements.txt`**: Listado de dependencias de Python necesarias.
*   **`Control de Caja.bat`**: Script autoejecutable para usuarios de Windows.
*   **`icono.ico`**: (Opcional pero recomendado) Icono del programa para la barra de tareas y accesos directos.

*(Nota: El archivo `caja_ventas.db` **NO** debe subirse a GitHub, ya que contiene los datos privados del negocio. Se creará automáticamente la primera vez que se ejecute el sistema).*
