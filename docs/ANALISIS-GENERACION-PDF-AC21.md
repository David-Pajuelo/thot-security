# Análisis: Generación de PDF Imprimible AC21

## 📋 Resumen Ejecutivo

El sistema actual de generación de PDFs AC21 está generando productos que no existen en el documento original. Este documento analiza el flujo actual, identifica los problemas y propone alternativas de solución.

---

## 🔍 1. Flujo Actual del Sistema

### 1.1. Proceso Completo

```
1. Usuario sube PDF → OCR (OpenAI GPT-4 Vision)
   ↓
2. OCR extrae datos → Frontend muestra resultados
   ↓
3. Usuario edita/valida → Guarda en Línea Temporal
   ↓
4. Usuario procesa → Backend crea Albaran + MovimientoProducto
   ↓
5. Usuario genera PDF → Backend consulta BD → PDF Generator → HTML
```

### 1.2. Flujo Detallado de Generación de PDF

#### **Paso 1: Frontend solicita PDF**
- **Archivo**: `AC21Detail.tsx` o `AlbaranesTable.tsx`
- **Endpoint**: `GET /api/albaranes/{id}/generar-ac21-html/`
- **Acción**: Usuario hace clic en "Imprimir" o "Ver PDF"

#### **Paso 2: Backend recopila datos**
- **Archivo**: `cryptotrace-backend/src/productos/views.py` → `generar_ac21_html()`
- **Proceso**:
  1. Obtiene el `Albaran` principal
  2. Llama a `albaran.obtener_todas_las_paginas()` para documentos multipágina
  3. Para cada página:
     - Consulta `MovimientoProducto.objects.filter(albaran=pagina)`
     - Extrae productos y los agrega a `productos_por_pagina[]`
  4. **Combina todos los productos** en `todos_los_productos[]`
  5. Envía estructura: `productos_por_pagina_estructura = [18, 3]` (ejemplo)

#### **Paso 3: PDF Generator recibe datos**
- **Archivo**: `cryptotrace-pdf-generator/app/main.py` → `generate_pdf_endpoint()`
- **Datos recibidos**:
  ```json
  {
    "lineas_producto": [31 productos combinados],
    "total_paginas": 2,
    "productos_por_pagina_estructura": [21, 10],  // ⚠️ PROBLEMA AQUÍ
    "accesorios_por_pagina": [[], []],
    "equipos_por_pagina": [[], []]
  }
  ```

#### **Paso 4: PDF Generator divide productos**
- **Lógica actual**:
  ```python
  inicio = 0
  for pagina in range(1, total_paginas + 1):
      productos_en_esta_pagina = estructura_original[pagina - 1]  # 21, luego 10
      fin = inicio + productos_en_esta_pagina
      productos_pagina = lineas_producto[inicio:fin]  # Slice del array combinado
      inicio = fin
  ```

#### **Paso 5: Plantilla Jinja2 renderiza**
- **Archivo**: `ac21_pdf_template.html`
- **Lógica**:
  ```jinja2
  {% for i in range(18) %}
    {% if i < num_productos %}
      {{ lineas_producto[i].codigo_producto }}  // ⚠️ Accede por índice
    {% endif %}
  {% endfor %}
  ```

---

## ⚠️ 2. Problemas Identificados

### 2.1. Problema Principal: Productos Ficticios

**Síntoma**: El PDF muestra productos con números de línea 19-28 que no existen en el documento original.

**Causa Raíz**:
1. **Backend cuenta productos incorrectamente**: 
   - Página 1 tiene 21 productos cuando debería tener 18
   - Página 2 tiene 10 productos cuando debería tener 3
   - Total: 31 productos cuando debería haber 21

2. **División incorrecta en PDF Generator**:
   - Si `estructura_original = [21, 10]` pero hay 31 productos
   - Página 1: productos 0-20 (21 productos) ✅
   - Página 2: productos 21-30 (10 productos) ❌ (debería ser 21-23, solo 3)

3. **Plantilla accede a índices fuera de rango**:
   - La plantilla itera siempre 18 veces
   - Si `lineas_producto` tiene más de 18 productos, accede a índices que no deberían mostrarse
   - Si hay menos de 18, muestra celdas vacías (correcto)

### 2.2. Problemas Secundarios

1. **Datos combinados vs. estructura original**:
   - El backend combina todos los productos en un solo array
   - Luego intenta dividirlos usando la estructura original
   - Si la estructura no coincide con el total, se generan inconsistencias

2. **Falta de validación**:
   - No se valida que `sum(productos_por_pagina_estructura) == len(todos_los_productos)`
   - No se valida que cada página tenga exactamente los productos que debería tener

3. **Orden de productos**:
   - Los productos se ordenan por `id` en la consulta, pero no hay garantía de que este orden corresponda al orden original del documento

4. **Productos duplicados**:
   - Posible que se estén creando `MovimientoProducto` duplicados cuando se procesa una segunda página
   - La validación `unique_together = ['producto', 'numero_serie', 'albaran']` solo previene duplicados dentro del mismo albarán

---

## 🔧 3. Alternativas de Solución

### 3.1. Opción A: Arreglar el Sistema Actual (Recomendada para solución rápida)

#### **Ventajas**:
- ✅ Cambios mínimos en el código existente
- ✅ Mantiene la arquitectura actual
- ✅ Implementación rápida (1-2 días)

#### **Desventajas**:
- ⚠️ Sigue siendo frágil ante inconsistencias de datos
- ⚠️ Requiere validaciones adicionales en múltiples puntos

#### **Cambios Necesarios**:

1. **Backend - Validar productos por página**:
   ```python
   # En generar_ac21_html()
   for pagina in todas_las_paginas:
       movimientos_pagina = MovimientoProducto.objects.filter(
           albaran=pagina
       ).order_by('id')
       
       # Validar que no haya más de 18 productos por página
       if movimientos_pagina.count() > 18:
           print(f"⚠️ ADVERTENCIA: Página {pagina.pagina_numero} tiene más de 18 productos")
           # Opción: Truncar o lanzar error
   ```

2. **Backend - Validar estructura antes de enviar**:
   ```python
   suma_estructura = sum([len(p) for p in productos_por_pagina])
   total_productos = len(todos_los_productos)
   
   if suma_estructura != total_productos:
       raise ValueError(f"Estructura inconsistente: {suma_estructura} vs {total_productos}")
   ```

3. **PDF Generator - Validar y corregir estructura**:
   ```python
   # Ya implementado parcialmente, pero mejorar:
   if suma_estructura != len(lineas_producto):
       # En lugar de ajustar automáticamente, lanzar error o usar fallback seguro
       raise ValueError("Estructura de productos inconsistente")
   ```

4. **Plantilla - Protección contra índices fuera de rango**:
   ```jinja2
   {% for i in range(18) %}
     {% if i < num_productos and i < lineas_producto|length %}
       {{ lineas_producto[i].codigo_producto | default('') }}
     {% else %}
       <!-- Celda vacía -->
     {% endif %}
   {% endfor %}
   ```

#### **Estimación**: 1-2 días de desarrollo + pruebas

---

### 3.2. Opción B: Refactorizar - Enviar Productos por Página Separadamente

#### **Ventajas**:
- ✅ Elimina la necesidad de combinar y dividir productos
- ✅ Cada página se genera independientemente
- ✅ Más robusto ante inconsistencias

#### **Desventajas**:
- ⚠️ Requiere cambios significativos en el backend y PDF generator
- ⚠️ Más tiempo de implementación (3-5 días)

#### **Cambios Necesarios**:

1. **Backend - Enviar estructura por página**:
   ```python
   # En lugar de combinar todos los productos:
   ac21_data = {
       'paginas': [
           {
               'pagina_numero': 1,
               'lineas_producto': productos_pagina_1,  # Solo productos de esta página
               'accesorios': accesorios_pagina_1,
               'equipos_prueba': equipos_pagina_1,
               # ... otros datos de la página
           },
           {
               'pagina_numero': 2,
               'lineas_producto': productos_pagina_2,
               # ...
           }
       ],
       'datos_generales': {
           # Datos compartidos (empresas, fechas, etc.)
       }
   }
   ```

2. **PDF Generator - Procesar páginas independientemente**:
   ```python
   if 'paginas' in ac21_data:
       for pagina_data in ac21_data['paginas']:
           datos_pagina = {**ac21_data['datos_generales'], **pagina_data}
           html_pagina = template.render(datos_pagina)
           html_pages.append(html_pagina)
   ```

#### **Estimación**: 3-5 días de desarrollo + pruebas

---

### 3.3. Opción C: Cambio Arquitectónico - Generar PDF Directamente desde BD

#### **Ventajas**:
- ✅ Elimina la necesidad de pasar datos entre servicios
- ✅ PDF Generator consulta directamente la BD
- ✅ Más eficiente para documentos grandes

#### **Desventajas**:
- ⚠️ Requiere acceso a BD desde PDF Generator
- ⚠️ Cambio arquitectónico significativo
- ⚠️ Más tiempo de implementación (1-2 semanas)

#### **Cambios Necesarios**:

1. **PDF Generator - Acceso a BD Django**:
   ```python
   # Instalar django en PDF generator
   import os
   import django
   os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cryptotrace_backend.settings')
   django.setup()
   
   from productos.models import Albaran, MovimientoProducto
   
   @app.route('/generate-ac21-pdf/<int:albaran_id>', methods=['GET'])
   def generate_pdf_from_db(albaran_id):
       albaran = Albaran.objects.get(id=albaran_id)
       # Consultar productos directamente desde BD
       # Generar PDF
   ```

2. **Backend - Endpoint simplificado**:
   ```python
   # Solo redirige al PDF generator con el ID
   return redirect(f'http://pdf-generator:5003/generate-ac21-pdf/{albaran.id}')
   ```

#### **Estimación**: 1-2 semanas de desarrollo + pruebas + migración

---

### 3.4. Opción D: Usar WeasyPrint para Generar PDF Real (No HTML)

#### **Ventajas**:
- ✅ Genera PDFs reales (no HTML renderizado en navegador)
- ✅ Mejor para impresión y almacenamiento
- ✅ Más profesional

#### **Desventajas**:
- ⚠️ Requiere instalar WeasyPrint (dependencias pesadas)
- ⚠️ Cambios en la plantilla (CSS para impresión)
- ⚠️ Más tiempo de implementación (1 semana)

#### **Cambios Necesarios**:

1. **PDF Generator - Usar WeasyPrint**:
   ```python
   from weasyprint import HTML
   
   html_string = template.render(datos_pagina)
   pdf_bytes = HTML(string=html_string).write_pdf()
   return send_file(pdf_bytes, mimetype='application/pdf')
   ```

2. **Frontend - Descargar PDF**:
   ```typescript
   const response = await fetch(`/api/albaranes/${id}/generar-ac21-pdf/`);
   const blob = await response.blob();
   const url = window.URL.createObjectURL(blob);
   const a = document.createElement('a');
   a.href = url;
   a.download = `AC21-${numero}.pdf`;
   a.click();
   ```

#### **Estimación**: 1 semana de desarrollo + pruebas

---

## 📊 4. Comparativa de Opciones

| Opción | Complejidad | Tiempo | Robustez | Mantenibilidad |
|--------|------------|--------|----------|----------------|
| **A: Arreglar actual** | Baja | 1-2 días | Media | Media |
| **B: Refactorizar estructura** | Media | 3-5 días | Alta | Alta |
| **C: PDF desde BD** | Alta | 1-2 semanas | Alta | Alta |
| **D: WeasyPrint PDF real** | Media | 1 semana | Alta | Alta |

---

## 💡 5. Recomendación

### **Recomendación Inmediata: Opción A + Investigación de Datos**

1. **Implementar Opción A** (arreglos rápidos):
   - Validaciones en backend
   - Protección en plantilla
   - Logs detallados para debugging

2. **Investigar el problema de datos**:
   - Verificar por qué hay 21 productos en página 1 en lugar de 18
   - Verificar por qué hay 10 productos en página 2 en lugar de 3
   - Revisar si hay productos duplicados en la BD
   - Revisar el proceso de creación de páginas adicionales

3. **Si el problema persiste después de Opción A**:
   - Considerar **Opción B** (refactorizar estructura)
   - Es un cambio más robusto pero requiere más tiempo

### **Recomendación a Largo Plazo: Opción B o C**

- **Opción B** si se quiere mantener la arquitectura de microservicios
- **Opción C** si se quiere simplificar y mejorar rendimiento

---

## 🔍 6. Puntos de Investigación Inmediata

1. **Verificar datos en BD**:
   ```sql
   -- Contar productos por página
   SELECT a.pagina_numero, COUNT(mp.id) as total_productos
   FROM productos_albaran a
   LEFT JOIN productos_movimientoproducto mp ON mp.albaran_id = a.id
   WHERE a.documento_principal_id = [ID_DOC_PRINCIPAL]
   GROUP BY a.pagina_numero
   ORDER BY a.pagina_numero;
   ```

2. **Verificar duplicados**:
   ```sql
   -- Buscar productos duplicados
   SELECT producto_id, numero_serie, albaran_id, COUNT(*) as count
   FROM productos_movimientoproducto
   WHERE albaran_id IN (SELECT id FROM productos_albaran WHERE documento_principal_id = [ID])
   GROUP BY producto_id, numero_serie, albaran_id
   HAVING COUNT(*) > 1;
   ```

3. **Revisar logs del proceso de creación**:
   - Buscar en logs cuando se procesó la segunda página
   - Verificar cuántos productos temporales se procesaron
   - Verificar si se crearon productos duplicados

---

## 📝 7. Plan de Acción Sugerido

### **Fase 1: Diagnóstico (1 día)**
- [ ] Ejecutar queries SQL para verificar datos en BD
- [ ] Revisar logs del proceso de creación de páginas
- [ ] Identificar exactamente dónde se están creando productos extra

### **Fase 2: Arreglos Inmediatos (1 día)**
- [ ] Implementar validaciones en backend (Opción A)
- [ ] Proteger plantilla contra índices fuera de rango
- [ ] Añadir logs detallados

### **Fase 3: Pruebas (1 día)**
- [ ] Probar con documento de 21 productos (18+3)
- [ ] Verificar que no se generen productos ficticios
- [ ] Validar numeración correcta de líneas

### **Fase 4: Decisión (si persisten problemas)**
- [ ] Evaluar si implementar Opción B
- [ ] O considerar Opción C para largo plazo

---

## 📌 Conclusión

El problema actual es una **combinación de inconsistencias en los datos de la BD y falta de validaciones** en el flujo de generación de PDF. 

**Recomendación**: Implementar **Opción A** primero para solucionar el problema inmediato, mientras se investiga la causa raíz de los datos incorrectos. Si el problema persiste, considerar **Opción B** para una solución más robusta a largo plazo.
