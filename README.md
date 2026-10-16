# 🏠 Proyecto Bienes Raíces — Data Warehouse Inmobiliario

> **Un proyecto colaborativo de análisis de datos aplicado al sector inmobiliario de Medellín.**
> Diseñado para aprender, para enseñar y para demostrar el poder de los datos bien organizados.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![pandas](https://img.shields.io/badge/pandas-2.2-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

---

## 🧭 Índice rápido

| Si eres... | Empieza por... |
|---|---|
| 🎯 **Reclutador / RRHH** | [Resumen ejecutivo](#-resumen-ejecutivo) |
| 🌱 **Junior en datos / software** | [Guía para principiantes](#-guía-para-principiantes) |
| 🤝 **Colaborador del proyecto** | [Cómo contribuir](#-cómo-contribuir) |
| 💻 **Desarrollador senior** | [Documentación técnica](#-documentación-técnica) |
| 👀 **Solo curioso** | [¿Qué problema resuelve?](#-qué-problema-resuelve) |

---

## 🎯 Resumen ejecutivo

**¿Qué es?** Un sistema que organiza y analiza información inmobiliaria de Medellín para tomar mejores decisiones de negocio.

**¿Qué problema resuelve?** Antes los datos estaban dispersos en archivos Excel y CSV con formatos distintos. Hoy están **centralizados, limpios y listos para consultar** en segundos.

**¿Qué tecnologías usa?** Python + MySQL, con un modelo de datos dimensional (esquema copo de nieve).

**¿Qué demuestra?** Capacidad para diseñar arquitecturas de datos, implementar pipelines ETL, aplicar buenas prácticas de ingeniería y comunicar resultados.

**Impacto medible:**
- 📊 **~1,200 propiedades** analizables
- 💰 **~758 transacciones** históricas procesadas
- 🗺️ **21 comunas** de Medellín cubiertas
- ⏱️ Reportes que antes tomaban horas → ahora **segundos**

---

## 💡 ¿Qué problema resuelve?

### 🚨 El contexto real

Una inmobiliaria maneja simultáneamente:
- **Propiedades** publicadas en distintos portales (Properati, Ciencuadras, Metrocuadrado)
- **Clientes** con perfiles variados (compradores, arrendatarios, inversionistas)
- **Agentes** con comisiones y desempeño
- **Transacciones** cerradas y canceladas
- **Datos catastrales** oficiales del municipio

Cada fuente tenía:
- ❌ Formatos distintos (`$ 550.000.000` vs `550000000` vs `550M`)
- ❌ Categorías inconsistentes (`"Venta"`, `"VENTA"`, `"En venta"`)
- ❌ Estructuras incompatibles entre archivos
- ❌ Sin forma de cruzarlos

### ✅ La solución

Un **Data Warehouse dimensional** que:

1. **Extrae** datos de múltiples fuentes heterogéneas
2. **Transforma** limpiando, normalizando y enriqueciendo
3. **Carga** en una base de datos organizada para análisis
📥 FUENTES 🔄 ETL 📊 ANÁLISIS
───────────────── ──────────────── ─────────────────
Propiedades (CSV) → Limpieza → Ventas por período
Ubicaciones (CSV) → Normalización → Rendimiento agentes
Catastro (CSV) → Integración → Propiedades demandadas
Clientes (XLSX) → Carga a BD → Evolución de precios
Transacciones (XLSX)→

## 🌱 Guía para principiantes

> **Esta sección es para ti si:**
> - Estás aprendiendo Python, SQL o análisis de datos
> - Quieres entender cómo funciona un proyecto real end-to-end
> - Necesitas un ejemplo práctico para tu portafolio

### 🗺️ Mapa mental del proyecto

Antes de tocar código, entiende este flujo:

1️⃣ TENEMOS DATOS SUCIOS
↓
2️⃣ LOS LIMPIAMOS CON PYTHON
↓
3️⃣ LOS GUARDAMOS EN MYSQL
↓
4️⃣ LOS CONSULTAMOS PARA RESPONDER PREGUNTAS

### 📚 Conceptos que vas a aprender

| Concepto | ¿Qué es? | ¿Dónde lo ves? |
|---|---|---|
| **ETL** | Extract, Transform, Load. Mover datos de un lugar a otro limpiándolos. | Carpeta `etl/` |
| **Data Warehouse** | Base de datos optimizada para análisis, no para operación. | MySQL `inmobiliaria_gold` |
| **Modelo dimensional** | Forma de organizar datos en "hechos" (lo que se mide) y "dimensiones" (cómo se filtra). | Carpetas `sql/` |
| **Esquema copo de nieve** | Modelo donde las dimensiones se ramifican en sub-dimensiones. | `dim_comuna` → `dim_ciudad` → `dim_departamento` |
| **Pipeline** | Cadena de pasos automatizados donde cada uno alimenta al siguiente. | `run_all.py` |

📊 ¿Qué se puede analizar?
El sistema responde preguntas como:

💹 Análisis de mercado
Precio promedio por comuna y tipo de propiedad

Precio por metro cuadrado por zona

Comparación entre precio de oferta y precio de cierre

Evolución de precios en el tiempo

🏆 Análisis comercial
Ranking de agentes por comisiones generadas

Tasa de conversión (oferta → cierre) por agente

Ticket promedio por tipo de cliente

Estacionalidad de las transacciones

🔍 Análisis de producto
Configuraciones más demandadas (habitaciones × baños × tamaño)

Zonas con mayor presión de demanda

Relación entre estrato y precio

Comparación entre avalúo catastral y precio de mercado

📁 Estructura del proyecto
proyecto_bienes_raices/
│
├── 📂 data/                    # Archivos fuente (no se suben al repo)
│   ├── propiedades.csv
│   ├── ubicaciones.csv
│   ├── catastro.csv
│   └── base_sintetica.xlsx
│
├── 📂 sql/                     # Scripts para crear la base de datos
│   ├── 01_gold_base.sql
│   ├── 02_gold_geo.sql
│   ├── 03_gold_comunas_catastro.sql
│   └── 04_gold_transaccional.sql
│
├── 📂 etl/                     # Pipeline de carga (Python)
│   ├── config.py               # Configuración central
│   ├── test_connection.py      # Verificar conexión
│   ├── 01_clean_silver.py      # Limpieza inicial
│   ├── 02_load_dimensions.py
│   ├── 03_load_comunas.py
│   ├── 04_load_fact_propiedades.py
│   ├── 05_enrich_comuna_lotes.py
│   ├── 06_load_dims_negocio.py
│   ├── 07_load_dim_propiedad.py
│   └── 08_load_fact_transacciones.py
│
├── 📂 analytics/               # Consultas y análisis
│   ├── verificacion.sql
│   └── consultas_gold.py
│
├── 📂 notebooks/               # Jupyter notebooks (opcional)
├── 📂 docs/                    # Imágenes y diagramas
├── 📂 logs/                    # Logs de ejecución
│
├── run_all.py                  # Orquestador del pipeline
├── requirements.txt
├── .env.example                # Plantilla de configuración
├── .gitignore
└── README.md

Instalación desde cero
# 1. Clonar el repositorio
git clone https://github.com/TU_USUARIO/proyecto_bienes_raices.git
cd proyecto_bienes_raices

# 2. Crear entorno virtual
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar credenciales
cp .env.example .env
# Editar .env con tus credenciales de MySQL

# 5. Crear base de datos (¡en orden!)
mysql -u root -p < sql/01_gold_base.sql
mysql -u root -p < sql/02_gold_geo.sql
mysql -u root -p < sql/03_gold_comunas_catastro.sql
mysql -u root -p < sql/04_gold_transaccional.sql

# 6. Verificar conexión
python etl/test_connection.py

# 7. Ejecutar el pipeline completo
python run_all.py

# 8. Analizar
python analytics/consultas_gold.py
