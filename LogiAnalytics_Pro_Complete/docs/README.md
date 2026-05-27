# 🚚 LogiAnalytics Pro

**Plataforma SaaS de Análisis Logístico Inteligente**

LogiAnalytics Pro es una solución completa de análisis de datos enfocada en optimización logística que permite a las empresas mejorar su eficiencia operativa, reducir costos y tomar decisiones basadas en datos.

## ✨ Características Principales

### 📊 Dashboard Inteligente
- **KPIs en tiempo real**: Monitoreo de envíos, costos, tiempos de entrega y satisfacción del cliente
- **Visualizaciones interactivas**: Gráficos dinámicos con Plotly para análisis profundo
- **Análisis geográfico**: Mapas de calor y distribución de entregas
- **Alertas automáticas**: Notificaciones inteligentes de problemas críticos

### 🚛 Optimización Avanzada
- **Algoritmos de rutas**: Optimización de rutas usando algoritmos de TSP y VRP
- **Gestión de inventario**: Cálculo de EOQ, puntos de reorden y predicción de demanda
- **Análisis de costos**: Desglose detallado y recomendaciones de ahorro
- **Predicción de demanda**: Machine Learning para pronósticos precisos

### 📋 Reportes y Análisis
- **Reportes ejecutivos**: Resúmenes de alto nivel para toma de decisiones
- **Análisis detallado**: Deep dive en métricas operativas
- **Exportación flexible**: CSV, Excel, JSON, PDF
- **Alertas personalizables**: Sistema de notificaciones configurable

### 🔧 Configuración Empresarial
- **Gestión de usuarios**: Roles y permisos granulares
- **Integración API**: Conectores para sistemas ERP, WMS y GPS
- **Configuración de seguridad**: 2FA, logs de auditoría, políticas de acceso
- **Planes de suscripción**: Modelo SaaS escalable

## 🚀 Instalación y Configuración

### Requisitos del Sistema
- Python 3.8+
- PostgreSQL 12+ (opcional, incluye base de datos simulada)
- 4GB RAM mínimo
- 10GB espacio en disco

### Instalación Rápida

1. **Clonar el repositorio**
```bash
git clone https://github.com/tu-usuario/logi-analytics-pro.git
cd logi-analytics-pro
```

2. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

3. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

4. **Ejecutar la aplicación**
```bash
# Aplicación web
streamlit run app.py

# API (en terminal separado)
python api/main.py
```

### Configuración de Base de Datos

Para usar una base de datos real (PostgreSQL):

```bash
# Instalar PostgreSQL
# Crear base de datos
createdb logi_analytics

# Configurar en .env
DATABASE_URL=postgresql://usuario:password@localhost/logi_analytics
```

## 📖 Uso de la Aplicación

### Acceso Inicial
1. Abrir http://localhost:8501
2. Usar credenciales de demo:
   - **Usuario**: admin / **Contraseña**: admin123
   - **Usuario**: demo / **Contraseña**: demo123

### Navegación Principal

#### 📊 Dashboard
- **Métricas clave**: Envíos, costos, tiempos, satisfacción
- **Tendencias**: Gráficos de evolución temporal
- **Análisis geográfico**: Mapas de distribución
- **Alertas**: Notificaciones en tiempo real

#### 🚛 Optimización
- **Rutas**: Configurar parámetros y optimizar rutas
- **Costos**: Análisis detallado de costos por categoría
- **Inventario**: Gestión de stock y predicción de demanda
- **Predicción**: Modelos de machine learning

#### 📋 Reportes
- **Ejecutivos**: Resúmenes para alta dirección
- **Detallado**: Análisis profundo de operaciones
- **Alertas**: Sistema de notificaciones
- **Exportar**: Descarga en múltiples formatos

#### ⚙️ Configuración
- **Empresa**: Información y configuración regional
- **Usuarios**: Gestión de roles y permisos
- **Técnica**: Base de datos, APIs, integraciones
- **Facturación**: Planes y pagos
- **Seguridad**: Autenticación y auditoría

## 🔌 API REST

### Autenticación
```bash
# Login
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# Usar token en requests
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/shipments"
```

### Endpoints Principales

#### Envíos
- `GET /shipments` - Lista de envíos
- `POST /shipments` - Crear envío
- `GET /shipments/{id}` - Obtener envío específico
- `PUT /shipments/{id}` - Actualizar envío

#### Análisis
- `POST /analytics/dashboard` - Métricas del dashboard
- `POST /analytics/reports` - Generar reportes
- `GET /alerts` - Obtener alertas

#### Optimización
- `POST /optimization/routes` - Optimizar rutas
- `POST /optimization/inventory` - Optimizar inventario

#### Integración
- `POST /integrations/webhook` - Webhook para sistemas externos

### Documentación API
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 💰 Modelo de Monetización

### Planes de Suscripción

| Plan | Precio | Características |
|------|--------|----------------|
| **Básico** | $99/mes | Dashboard básico, 100 envíos/mes, 3 usuarios |
| **Pro** | $299/mes | Optimización avanzada, 1,000 envíos/mes, 10 usuarios |
| **Enterprise** | $999/mes | Personalización completa, envíos ilimitados, usuarios ilimitados |

### Servicios Adicionales
- **Consultoría**: $150/hora
- **Integración personalizada**: $2,000 - $10,000
- **Soporte prioritario**: $200/mes
- **Reportes personalizados**: $500/reporte

## 🏗️ Arquitectura Técnica

### Frontend
- **Streamlit**: Framework web para dashboards
- **Plotly**: Visualizaciones interactivas
- **Pandas**: Manipulación de datos
- **NumPy**: Cálculos numéricos

### Backend
- **FastAPI**: API REST moderna y rápida
- **Pydantic**: Validación de datos
- **SQLAlchemy**: ORM para base de datos
- **Uvicorn**: Servidor ASGI

### Algoritmos
- **Scikit-learn**: Machine Learning
- **SciPy**: Optimización matemática
- **Algoritmos personalizados**: TSP, VRP, EOQ

### Integraciones
- **Google Maps API**: Geocodificación y rutas
- **Twilio**: Notificaciones SMS
- **SendGrid**: Emails transaccionales
- **Webhooks**: Integración con ERPs

## 📈 Roadmap de Desarrollo

### Versión 1.1 (Q2 2024)
- [ ] Integración con GPS en tiempo real
- [ ] App móvil para conductores
- [ ] Machine Learning avanzado
- [ ] Integración con marketplaces

### Versión 1.2 (Q3 2024)
- [ ] Análisis de sostenibilidad
- [ ] Optimización de emisiones
- [ ] Dashboard de ESG
- [ ] Integración con IoT

### Versión 2.0 (Q4 2024)
- [ ] IA conversacional
- [ ] Predicción de demanda avanzada
- [ ] Optimización multi-objetivo
- [ ] Marketplace de algoritmos

## 🤝 Contribución

### Cómo Contribuir
1. Fork del repositorio
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

### Estándares de Código
- **Python**: PEP 8
- **Documentación**: Docstrings en inglés
- **Tests**: Cobertura mínima 80%
- **Commits**: Mensajes descriptivos

## 📞 Soporte

### Canales de Soporte
- **Email**: soporte@logianalytics.com
- **Chat**: Disponible en la aplicación
- **Documentación**: https://docs.logianalytics.com
- **GitHub Issues**: Para reportar bugs

### Niveles de Soporte
- **Básico**: Email (48h respuesta)
- **Pro**: Chat + Email (24h respuesta)
- **Enterprise**: Teléfono + Chat + Email (4h respuesta)

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 🙏 Agradecimientos

- **Streamlit** por el framework de dashboards
- **FastAPI** por la API REST moderna
- **Plotly** por las visualizaciones interactivas
- **Comunidad open source** por las librerías utilizadas

---

**Desarrollado con ❤️ para optimizar la logística empresarial**

*¿Preguntas? Contacta a nuestro equipo en contacto@logianalytics.com*
