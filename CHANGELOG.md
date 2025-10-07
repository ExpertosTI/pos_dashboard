# Changelog - Dashboard POS Avanzado

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [18.0.1.2.0] - 2025-01-07

### Añadido ✨
- **Nueva métrica**: 💎 PRODUCTO MÁS RENTABLE
  - Muestra el producto que genera más ganancias
  - Incluye imagen del producto
  - Muestra el monto de ganancia generado
- Grid de 5 columnas para las métricas principales
- Gradiente rosa/amarillo para la nueva tarjeta

### Mejorado
- Dashboard ahora muestra 5 métricas en lugar de 4
- Cálculo automático del producto más rentable
- Responsive design para 5 columnas (5 → 2 → 1)

### Técnico
- `top_profit_product_name`: Nombre del producto más rentable
- `top_profit_amount`: Ganancia generada
- `top_profit_product_image`: Imagen del producto
- Cálculo basado en `amount - cost` por producto

## [18.0.1.1.0] - 2025-01-07

### CAMBIO IMPORTANTE ⚠️
- **Ventas Totales**: Ahora INCLUYE anticipos (muestra el total real de ventas)
- **Ganancias Totales**: Ahora EXCLUYE anticipos (solo ganancias de productos reales)
- **Total de Artículos**: Ahora INCLUYE anticipos (muestra el total real de items)

### Mejorado
- Separación clara entre cálculos con y sin anticipos
- Logging detallado indicando qué incluye anticipos y qué no
- Función `is_anticipo()` centralizada para identificar anticipos

### Técnico
- `lines_sin_anticipo`: Para cálculo de ganancias
- `all_lines`: Para cálculo de ventas totales
- Logging mejorado con indicadores (CON/SIN anticipos)

## [18.0.1.0.5] - 2025-01-07

### Corregido
- Mejora en manejo de imágenes de productos
- Logging detallado de imágenes en backend y frontend
- Soporte para diferentes formatos de imagen (JPEG/PNG)

### Mejorado
- Console.log en JavaScript para debugging de imágenes
- Error handling mejorado para imágenes
- Fallback visual si la imagen no carga

## [18.0.1.0.4] - 2025-01-07

### Corregido
- Filtro de anticipos con coincidencia exacta
- Evita filtrar productos que solo contienen la palabra "anticipo"

## [18.0.1.0.3] - 2025-01-07

### Corregido
- Doble verificación en loop de cálculo para garantizar exclusión de anticipos
- Alerta de warning si un anticipo pasa el primer filtro
- Logging detallado de productos con ganancias significativas (>1000)

### Mejorado
- Validación adicional en cada iteración del loop de productos
- Logging de cada producto con ganancia alta para debugging

## [18.0.1.0.2] - 2025-01-07

### Corregido
- Filtro mejorado para detectar específicamente "Anticipo (PdV)"
- Logging detallado de cada anticipo filtrado con su monto
- Verificación de ganancias totales sin anticipos

### Mejorado
- Función `is_not_anticipo()` más robusta con múltiples keywords
- Keywords adicionales: 'anticipo', 'anticipo (pdv)', 'advance', 'deposit'
- Log de cantidad de anticipos excluidos

### Técnico
- Logging individual de cada anticipo filtrado
- Logging del total de ganancias calculadas sin anticipos

## [18.0.1.0.1] - 2025-01-07

### Añadido
- Filtro automático para excluir productos de "Anticipo" de los cálculos
- Logging mejorado para tracking de líneas filtradas

### Mejorado
- Cálculo de ventas totales ahora excluye anticipos
- Cálculo de ganancias ahora excluye anticipos
- Cálculo de cantidad de artículos ahora excluye anticipos
- Producto más vendido ahora excluye anticipos

### Técnico
- Filtrado case-insensitive de productos con "anticipo" en el nombre
- Cálculo de totales basado en líneas filtradas

## [18.0.1.0.0] - 2025-01-07

### Añadido
- Dashboard completo con 4 métricas principales
  - 💰 Venta Total
  - 📦 Total de Artículos
  - 🏆 Producto Más Vendido (con imagen)
  - 💵 Ganancias Totales
- Filtros dinámicos modernos
  - Filtro por rango de fechas
  - Filtro por configuraciones POS
  - Diseño con chips seleccionables
  - Botón "Aplicar filtros" con gradiente
- Análisis de ventas por vendedor
- Análisis de métodos de pago
- Estado de sesiones POS
- Gráficos interactivos (Chart.js)
  - Ventas diarias
  - Ventas semanales
  - Ventas quincenales
  - Ventas mensuales
- Gráficos de productos principales
- Gráficos de categorías principales
- Gráficos de clientes principales
- Diseño responsive completo
  - Desktop (>768px)
  - Tablet (≤768px)
  - Móvil (≤480px)
- Imagen del producto más vendido
- Cálculo automático de ganancias
- Logging para debugging
- Documentación completa (README.md)
- Documentación técnica (REFACTORIZACION.md)

### Mejorado
- Refactorización completa siguiendo mejores prácticas de Odoo
- Uso eficiente del ORM
- Optimización de consultas a base de datos
- Normalización de fechas automática
- Manejo de errores robusto
- Código limpio y documentado
- Estructura modular

### Corregido
- Error de claves duplicadas en `t-foreach`
- Responsividad del filtro en móviles
- Desbordamiento del calendario derecho
- Conversión de imagen a base64
- Cálculo de ganancias con productos sin costo

### Removido
- Dependencia innecesaria de `pandas`
- Dependencias de módulos opcionales (`accounting_pdf_reports`, `om_account_accountant`)
- Sección duplicada "PRODUCTO MÁS VENDIDO"
- Sección "REPORTE DE VENTAS" (simplificado)
- Código legacy no utilizado
- Imports innecesarios (`pytz`)

### Seguridad
- Validación de permisos de usuario
- Manejo seguro de imágenes en base64
- Sanitización de inputs de fecha

## Notas de Migración

### Desde versiones anteriores
Si estás actualizando desde una versión anterior:

1. **Backup de la base de datos** antes de actualizar
2. Actualizar el módulo desde Apps
3. Verificar que los costos de productos estén configurados
4. Limpiar caché del navegador (Ctrl+Shift+R)

### Compatibilidad
- ✅ Odoo 18.0
- ⚠️ Odoo 17.0 (requiere ajustes menores)
- ❌ Odoo 16.0 o anterior (no compatible)

## Roadmap

### Próximas versiones

#### v18.0.1.1.0 (Planificado)
- [ ] Exportación a PDF
- [ ] Exportación a Excel
- [ ] Filtro por vendedor
- [ ] Filtro por categoría de producto
- [ ] Comparación de períodos
- [ ] Alertas de bajo rendimiento
- [ ] Notificaciones en tiempo real

#### v18.0.2.0.0 (Futuro)
- [ ] Dashboard personalizable
- [ ] Widgets arrastrables
- [ ] Temas de color
- [ ] Modo oscuro
- [ ] Predicciones con IA
- [ ] Análisis de tendencias
- [ ] Recomendaciones automáticas

## Contribuciones

Este módulo es mantenido por **Renace Tech**.

Para reportar bugs o sugerir mejoras:
- Email: adderly@renace.tech
- Website: https://renace.tech

---

**Desarrollado con ❤️ por Adderly Marte - Renace Tech**
