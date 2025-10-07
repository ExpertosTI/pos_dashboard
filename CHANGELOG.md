# Changelog - Dashboard POS Avanzado

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

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
