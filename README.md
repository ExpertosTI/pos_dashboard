# Dashboard POS Avanzado

**Versión:** 18.0.1.0.0  
**Autor:** Adderly Marte - Renace Tech  
**Licencia:** AGPL-3

## Descripción

Dashboard avanzado para análisis de ventas en Punto de Venta (POS) con métricas en tiempo real, diseño moderno y responsive.

## Características Principales

### 📊 Métricas en Tiempo Real
- **Venta Total**: Monto total de ventas en el período seleccionado
- **Total de Artículos**: Cantidad total de productos vendidos
- **Producto Más Vendido**: Muestra el producto con mayor cantidad vendida, incluyendo su imagen
- **Ganancias Totales**: Cálculo automático de ganancias (precio venta - costo)

### 🔍 Filtros Dinámicos
- Filtro por rango de fechas (inicio y fin)
- Filtro por configuraciones POS
- Diseño moderno con chips seleccionables
- Aplicación instantánea de filtros

### 📈 Análisis Detallado
- **Ventas por Vendedor**: Ranking de vendedores con pedidos y montos
- **Métodos de Pago**: Distribución de pagos por método
- **Estado de Sesiones**: Monitoreo de sesiones POS activas/cerradas
- **Gráficos Interactivos**: Visualización de ventas diarias, semanales, quincenales y mensuales

### 🎨 Diseño Moderno
- Interfaz limpia y profesional
- Tarjetas con gradientes de colores
- Totalmente responsive (Desktop, Tablet, Móvil)
- Animaciones y transiciones suaves
- Iconos FontAwesome integrados

## Requisitos

### Dependencias de Odoo
- `hr` - Recursos Humanos
- `point_of_sale` - Punto de Venta
- `web` - Framework Web
- `account` - Contabilidad

### Bibliotecas Externas (CDN)
- Chart.js 4.4.0 - Gráficos interactivos
- jQuery 3.7.1 - Manipulación DOM

## Instalación

1. Copiar el módulo en la carpeta de addons de Odoo
2. Actualizar la lista de aplicaciones
3. Buscar "Dashboard POS Avanzado"
4. Instalar el módulo

## Configuración

### Configurar Costos de Productos
Para que el cálculo de ganancias funcione correctamente:

1. Ir a **Inventario → Productos → Productos**
2. Seleccionar un producto
3. En la pestaña **Información General**, configurar el campo **Costo**
4. Guardar

> **Nota:** Si un producto no tiene costo configurado, la ganancia será igual al precio de venta.

### Acceso al Dashboard

1. Ir a **Punto de Venta → Reportes → Dashboard POS**
2. O buscar en el menú: "Dashboard POS"

## Uso

### Filtrar Datos
1. Seleccionar **Fecha inicio** y **Fecha fin**
2. Marcar las **Configuraciones POS** deseadas
3. Hacer clic en **Aplicar filtros**

### Visualizar Gráficos
- Seleccionar el tipo de reporte: Diario, Semanal, Quincenal o Mensual
- El gráfico se actualiza automáticamente

### Ver Detalles
- Hacer clic en las tarjetas superiores para ver detalles de:
  - Pedidos de Hoy
  - Pedidos Totales
  - Ventas Totales
  - Sesiones
  - Reembolsos

## Estructura del Proyecto

```
dashboard_pos/
├── __init__.py
├── __manifest__.py
├── README.md
├── REFACTORIZACION.md
├── models/
│   ├── __init__.py
│   └── pos_order.py
├── views/
│   └── pos_order_views.xml
└── static/
    └── src/
        ├── css/
        │   └── pos_dashboard.css
        ├── js/
        │   └── pos_dashboard.js
        └── xml/
            └── pos_dashboard.xml
```

## Características Técnicas

### Backend (Python)
- Uso eficiente del ORM de Odoo
- Cálculos optimizados con `defaultdict`
- Logging para debugging
- Manejo de errores robusto
- Normalización de fechas automática

### Frontend (JavaScript/OWL)
- Componente OWL moderno
- Estado reactivo con `useState`
- Hooks: `onWillStart`, `onMounted`
- Formateo de moneda y números
- Integración con Chart.js

### Estilos (CSS)
- Grid CSS para layouts responsive
- Gradientes modernos
- Sombras y elevaciones
- Transiciones suaves
- Media queries para móvil

## Cálculos

### Ganancias
```python
ganancia = precio_venta_con_impuestos - (costo_producto * cantidad)
```

### Producto Más Vendido
Se determina por la mayor cantidad vendida en el período filtrado.

## Responsive Design

### Desktop (>768px)
- 4 columnas para métricas
- 2 columnas para filtros de fecha
- Layout horizontal

### Tablet (≤768px)
- 2 columnas para métricas
- 1 columna para filtros de fecha
- Elementos reducidos

### Móvil (≤480px)
- 1 columna para todo
- Layout vertical
- Elementos compactos

## Solución de Problemas

### La imagen del producto no aparece
1. Verificar que el producto tenga imagen en Odoo
2. Revisar logs del servidor: `"Top product: [nombre], has image: true/false"`
3. Verificar permisos de acceso a imágenes

### Las ganancias aparecen en 0
1. Verificar que los productos tengan **Costo** configurado
2. Revisar logs del servidor para ver el cálculo

### Los filtros no funcionan
1. Verificar que haya datos en el rango de fechas seleccionado
2. Verificar que las configuraciones POS estén seleccionadas
3. Revisar la consola del navegador por errores

## Changelog

### v18.0.1.0.0 (2025-01-07)
- ✅ Versión inicial para Odoo 18
- ✅ Dashboard con 4 métricas principales
- ✅ Filtros modernos y responsive
- ✅ Imagen del producto más vendido
- ✅ Cálculo de ganancias
- ✅ Gráficos interactivos
- ✅ Diseño completamente responsive
- ✅ Integración con contabilidad

## Soporte

**Desarrollado por:** Adderly Marte  
**Empresa:** Renace Tech  
**Email:** adderly@renace.tech  
**Website:** https://renace.tech

## Licencia

Este módulo está licenciado bajo AGPL-3. Ver el archivo LICENSE para más detalles.

---

© 2025 Renace Tech. Todos los derechos reservados.
