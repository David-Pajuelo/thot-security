# Plan de Reestructuración del Flujo de Procesamiento AC21

## Objetivo

Reestructurar el flujo de procesamiento de AC21 para que:
1. Siempre se trate como ENTRADA (sin validación)
2. Siempre requiera número de registro de salida
3. El guardado en línea temporal se elimine
4. El modal de línea temporal se abra directamente con datos en memoria
5. La detección de documento existente y guardado final ocurra al completar el modal

---

## Cambios Principales

### 1. Eliminar validación ENTRADA/SALIDA
- **Antes:** Se validaba si era AC21 de ENTRADA o SALIDA
- **Ahora:** Siempre se trata como ENTRADA cuando viene del OCR

### 2. Validación simplificada de número de registro
- **Antes:** Validaba número de registro de salida O entrada
- **Ahora:** Solo valida número de registro de salida (obligatorio)

### 3. Eliminar guardado en línea temporal inicial
- **Antes:** Al hacer "Confirmar y guardar", se guardaba en `LineaTemporalProducto`
- **Ahora:** Los datos se mantienen en memoria del frontend

### 4. Modal de línea temporal con datos en memoria
- **Antes:** El modal cargaba datos agrupados desde `LineaTemporalProducto` en BD
- **Ahora:** El modal recibe datos directamente desde el estado del componente
- **Importante:** El modal muestra **códigos únicos** (sin agrupar por cantidad)
- **Propósito:** Asignar TipoProducto (CC) a cada código único, que luego se guardará en `CatalogoProducto.tipo`

### 5. Detección de documento existente al final
- **Antes:** Se detectaba antes de abrir el modal
- **Ahora:** Se detecta cuando el usuario completa el modal de tipificación

### 6. Guardado final único
- **Antes:** Se guardaba en línea temporal, luego se procesaba
- **Ahora:** Se guarda directamente: Albaran + Movimientos + Inventario en un solo paso

---

## Plan de Implementación

### FASE 1: Modificar Frontend - Validaciones y Flujo Inicial

#### 1.1. Modificar `handleConfirm` en `upload-ac21/page.tsx`

**Archivo:** `cryptotrace/cryptotrace-frontend/src/app/albaranes/upload-ac21/page.tsx`

**Cambios:**
- Eliminar validación de AC21 de ENTRADA vs SALIDA
- Simplificar validación: solo verificar `numero_registro_salida`
- Eliminar llamada a `guardarEnLineaTemporal`
- Eliminar llamada a `verificarDocumentoExistente` en este punto
- Abrir directamente el modal de línea temporal con datos en memoria

**Código aproximado:**
```typescript
const handleConfirm = async () => {
  // 1. Validación: Solo número de registro de salida
  const numeroRegistroSalida = processedData.cabecera?.numero_registro_salida;
  if (!numeroRegistroSalida || numeroRegistroSalida.trim() === '') {
    toast.error("Debes introducir el 'Número de Registro de Salida' en la cabecera del documento.", { duration: 7000 });
    return;
  }

  // 2. Validar que hay artículos seleccionados
  if (articulosAInsertar.length === 0) {
    toast.error("Debes seleccionar al menos un artículo para procesar.");
    return;
  }

  // 3. Abrir modal de línea temporal directamente (sin guardar en BD)
  setShowLineaTemporalModal(true);
};
```

**Tareas:**
- [ ] Eliminar lógica de detección de AC21 de ENTRADA
- [ ] Eliminar llamada a `verificarDocumentoExistente`
- [ ] Eliminar llamada a `guardarEnLineaTemporal`
- [ ] Simplificar validación a solo número de registro de salida
- [ ] Modificar para abrir modal directamente

---

#### 1.2. Modificar `LineaTemporalModal` para recibir datos en memoria

**Archivo:** `cryptotrace/cryptotrace-frontend/src/components/albaranes/LineaTemporalModal.tsx`

**Cambios:**
- Añadir prop para recibir datos del AC21 directamente
- Eliminar llamada a `fetchProductosAgrupados` (que carga desde BD)
- **Extraer códigos únicos** de los artículos (sin agrupar por cantidad)
- Mostrar lista de códigos únicos con dropdown para asignar TipoProducto
- Mantener lógica de tipificación en memoria

**Props nuevas:**
```typescript
interface LineaTemporalModalProps {
  isOpen: boolean;
  onClose: () => void;
  ac21Data: {
    cabecera: any;
    empresa_origen: any;
    empresa_destino: any;
    articulos: any[];  // Todos los artículos del OCR
    accesorios: any[];
    equipos_prueba: any[];
    firmas: any;
    observaciones: string;
    imagen?: File;
  };
}
```

**Lógica de extracción de códigos únicos:**
```typescript
// Extraer códigos únicos de los artículos (SIN agrupar por cantidad)
// El propósito es asignar TipoProducto (CC) a cada código único
const codigosUnicos = Array.from(
  new Set(ac21Data.articulos.map(art => art.codigo_producto))
).map(codigo => {
  // Encontrar un artículo con este código para obtener descripción
  const articuloEjemplo = ac21Data.articulos.find(a => a.codigo_producto === codigo);
  return {
    codigo_producto: codigo,
    descripcion: articuloEjemplo?.observaciones || articuloEjemplo?.descripcion || '',
    tipo_producto_id: null,  // Se asignará en el modal
    tipo_producto_nombre: null
  };
});
```

**Nota importante:** 
- NO se muestra cantidad (no se agrupa)
- Solo se muestran códigos únicos
- El objetivo es asignar TipoProducto a cada código
- Esta asignación se guardará en `CatalogoProducto.tipo` al procesar

**Tareas:**
- [ ] Añadir prop `ac21Data` al modal
- [ ] Eliminar llamada a `fetchProductosAgrupados`
- [ ] Crear función para extraer códigos únicos (sin agrupar, sin cantidad)
- [ ] Modificar tabla para mostrar solo códigos únicos (eliminar columna de cantidad)
- [ ] Mostrar dropdown de TipoProducto (CC) para cada código
- [ ] Cargar tipos disponibles desde API (GET /api/tipos-producto/)
- [ ] Mantener estado de tipificación (código → tipo_producto_id) en memoria del componente
- [ ] Opcional: Cargar tipo desde CatalogoProducto si ya existe (para mostrar como sugerencia)

---

#### 1.3. Modificar `GestionLineaTemporal` para trabajar con datos en memoria

**Archivo:** `cryptotrace/cryptotrace-frontend/src/components/albaranes/GestionLineaTemporal.tsx`

**Cambios:**
- Modificar para recibir datos desde props en lugar de cargar desde BD
- **Extraer códigos únicos** de los artículos (sin agrupar)
- Mantener estado de tipificación (código → tipo_producto_id) en memoria
- Al procesar, llamar a nuevo endpoint que guarde todo directamente

**Estructura de datos:**
```typescript
interface CodigoTipificado {
  codigo_producto: string;
  descripcion: string;
  tipo_producto_id: number | null;  // TipoProducto asignado
  tipo_producto_nombre: string | null;
}

// Estado en el componente
const [codigosTipificados, setCodigosTipificados] = useState<CodigoTipificado[]>([]);
const [tiposDisponibles, setTiposDisponibles] = useState<TipoProducto[]>([]);
```

**Tareas:**
- [ ] Modificar para recibir datos desde props
- [ ] Eliminar `cargarProductos` que carga desde BD
- [ ] Crear función `extraerCodigosUnicos` que obtiene códigos únicos de artículos
- [ ] Cargar `tiposDisponibles` desde API (GET /api/tipos-producto/)
- [ ] Mantener estado de `codigosTipificados` en memoria
- [ ] Modificar `handleGuardarTipoProducto` para actualizar estado en memoria (sin llamar a API)
- [ ] Modificar `handleProcesarAlbaran` para construir payload con todos los artículos y sus tipos asignados

---

### FASE 2: Crear Nuevo Endpoint Backend - Guardado Directo

#### 2.1. Crear endpoint `procesar_directo` en `LineaTemporalProductoViewSet`

**Archivo:** `cryptotrace/cryptotrace-backend/src/productos/views.py`

**Nuevo método:**
```python
@action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
def procesar_directo(self, request):
    """
    Procesa un AC21 directamente desde el frontend sin usar línea temporal.
    Recibe todos los datos del AC21 y crea directamente:
    - Albaran
    - Movimientos
    - Inventario
    
    También detecta si existe documento con mismo número y permite crear
    página adicional o documento independiente.
    """
```

**Flujo del método:**
1. Recibir payload completo del AC21:
   - Cabecera
   - Empresas
   - Artículos (con tipo_producto_id ya asignado)
   - Firmas
   - Accesorios, equipos_prueba
   - Imagen (opcional)

2. Validar número de registro de salida

3. Detectar si existe documento con mismo número:
   - Si existe → devolver información del documento existente
   - Si no existe → continuar con creación

4. Si existe documento, el frontend preguntará:
   - ¿Crear página adicional?
   - ¿Crear documento independiente?

5. Crear Albaran (nuevo o página adicional según decisión)

6. Para cada artículo:
   - Buscar/crear CatalogoProducto
   - Actualizar CatalogoProducto.tipo si hay tipo_producto
   - Crear MovimientoProducto
   - El save() de MovimientoProducto crea/actualiza InventarioProducto

7. Si hay imagen, guardarla en el albarán

8. Devolver respuesta con información del albarán creado

**Tareas:**
- [ ] Crear método `procesar_directo`
- [ ] Implementar validación de número de registro de salida
- [ ] Implementar detección de documento existente
- [ ] Implementar lógica de creación de albarán (nuevo o página adicional)
- [ ] Implementar creación de movimientos e inventario
- [ ] Implementar manejo de imagen
- [ ] Añadir logging detallado

---

#### 2.2. Modificar endpoint `procesar` (mantener para compatibilidad o eliminar)

**Decisión:** 
- Opción A: Mantener `procesar` para compatibilidad con flujos antiguos
- Opción B: Eliminar `procesar` y migrar todo a `procesar_directo`

**Recomendación:** Opción A (mantener ambos por ahora)

**Tareas:**
- [ ] Decidir si mantener o eliminar `procesar`
- [ ] Si se mantiene, documentar que está deprecado
- [ ] Si se elimina, verificar que no hay otros flujos que lo usen

---

### FASE 3: Modificar Frontend - Procesamiento Final

#### 3.1. Modificar `handleProcesarAlbaran` en `GestionLineaTemporal.tsx`

**Archivo:** `cryptotrace/cryptotrace-frontend/src/components/albaranes/GestionLineaTemporal.tsx`

**Cambios:**
- Construir payload completo con todos los datos del AC21
- Incluir tipos de producto asignados en memoria
- Llamar a nuevo endpoint `procesar_directo`
- Manejar respuesta de documento existente
- Mostrar modal de decisión si existe documento

**Código aproximado:**
```typescript
const handleProcesarAlbaran = async () => {
  // 1. Crear mapa de código → tipo_producto_id desde la tipificación
  const codigoATipo = new Map(
    codigosTipificados
      .filter(c => c.tipo_producto_id !== null)
      .map(c => [c.codigo_producto, c.tipo_producto_id])
  );

  // 2. Construir payload completo con todos los artículos
  const payload = {
    cabecera: ac21Data.cabecera,
    empresa_origen: ac21Data.empresa_origen,
    empresa_destino: ac21Data.empresa_destino,
    articulos: ac21Data.articulos.map(art => ({
      codigo_producto: art.codigo_producto,
      numero_serie: art.numero_serie_inicio || art.numero_serie_fin || '',
      cantidad: art.cantidad || 1,
      descripcion: art.observaciones || art.descripcion || '',
      tipo_producto_id: codigoATipo.get(art.codigo_producto) || null, // Tipo asignado en modal
      observaciones: art.observaciones || '',
      cc: art.cc || 1 // CC del OCR
    })),
    accesorios: ac21Data.accesorios,
    equipos_prueba: ac21Data.equipos_prueba,
    firmas: ac21Data.firmas,
    observaciones: ac21Data.observaciones
  };

  // 2. Llamar a procesar_directo
  const result = await procesarAlbaranDirecto(payload, ac21Data.imagen);

  // 3. Si existe documento, mostrar modal de decisión
  if (result.documento_existente) {
    setDocumentoExistente(result.documento_existente);
    setShowDocumentoExistenteModal(true);
    return;
  }

  // 4. Si no existe, mostrar éxito y cerrar
  toast.success("AC21 procesado correctamente");
  onClose();
};
```

**Tareas:**
- [ ] Modificar `handleProcesarAlbaran` para construir payload completo
- [ ] Añadir función `procesarAlbaranDirecto` en `api.ts`
- [ ] Manejar respuesta de documento existente
- [ ] Integrar con modal de documento existente

---

#### 3.2. Crear/Modificar función `procesarAlbaranDirecto` en `api.ts`

**Archivo:** `cryptotrace/cryptotrace-frontend/src/lib/api.ts`

**Nueva función:**
```typescript
export const procesarAlbaranDirecto = async (
  data: any,
  imagen?: File
): Promise<any> => {
  const formData = new FormData();
  formData.append('data', JSON.stringify(data));
  if (imagen) {
    formData.append('imagen_documento', imagen);
  }

  return apiFetch('/lineas-temporales/procesar-directo/', {
    method: 'POST',
    body: formData,
  });
};
```

**Tareas:**
- [ ] Crear función `procesarAlbaranDirecto`
- [ ] Manejar FormData con imagen opcional
- [ ] Manejar errores apropiadamente

---

#### 3.3. Modificar `DocumentoExistenteModal` para nuevo flujo

**Archivo:** `cryptotrace/cryptotrace-frontend/src/components/albaranes/DocumentoExistenteModal.tsx`

**Cambios:**
- Modificar para recibir datos del AC21 y tipos asignados
- Al elegir "Crear página adicional" o "Documento independiente", llamar a `procesar_directo` con flag correspondiente

**Tareas:**
- [ ] Modificar props para recibir datos del AC21
- [ ] Modificar botones para llamar a `procesar_directo` con flag
- [ ] Manejar respuesta y cerrar modal

---

### FASE 4: Modificar Backend - Endpoint `procesar_directo` Completo

#### 4.1. Implementar detección de documento existente

**En `procesar_directo`:**
```python
# Detectar si existe documento
numero_registro_salida = cabecera.get('numero_registro_salida')
documento_existente = None

if numero_registro_salida:
    documento_existente = Albaran.encontrar_documento_existente(numero_registro_salida)
    
    if documento_existente:
        # Devolver información del documento existente
        return Response({
            "documento_existente": {
                "id": documento_existente.id,
                "numero": documento_existente.numero,
                "fecha": documento_existente.fecha,
                "total_paginas": documento_existente.total_paginas
            },
            "requiere_decision": True
        }, status=200)
```

**Tareas:**
- [ ] Implementar detección de documento existente
- [ ] Devolver información del documento si existe
- [ ] Manejar caso de no existencia

---

#### 4.2. Implementar creación con decisión de página adicional

**En `procesar_directo`:**
```python
# Recibir flag de decisión desde frontend
crear_pagina_adicional = request.data.get('crear_pagina_adicional', False)
documento_existente_id = request.data.get('documento_existente_id', None)

if crear_pagina_adicional and documento_existente_id:
    documento_existente = Albaran.objects.get(id=documento_existente_id)
    # Crear página adicional
    albaran = documento_existente.crear_pagina_adicional(...)
else:
    # Crear documento nuevo
    albaran = Albaran.objects.create(...)
```

**Tareas:**
- [ ] Implementar lógica de creación según decisión
- [ ] Manejar creación de página adicional
- [ ] Manejar creación de documento nuevo

---

#### 4.3. Implementar creación de movimientos e inventario

**Reutilizar lógica de `procesar` pero adaptada:**
```python
# Crear mapa de código → tipo_producto_id para actualizar catálogo
codigo_a_tipo = {}
for articulo in articulos:
    codigo = articulo.get('codigo_producto')
    tipo_id = articulo.get('tipo_producto_id')
    if tipo_id and codigo:
        codigo_a_tipo[codigo] = tipo_id

# Actualizar tipos en catálogo (una vez por código único)
for codigo, tipo_id in codigo_a_tipo.items():
    producto = CatalogoProducto.objects.filter(codigo_producto=codigo).first()
    if producto:
        tipo_producto = TipoProducto.objects.get(id=tipo_id)
        producto.tipo = tipo_producto
        producto.save()

# Crear movimientos para cada artículo
for articulo in articulos:
    # 1. Buscar/crear producto
    producto = CatalogoProducto.objects.filter(
        codigo_producto=articulo.get('codigo_producto')
    ).first()
    if not producto:
        producto, created = CatalogoProducto.objects.get_or_create(
            codigo_producto=articulo.get('codigo_producto'),
            defaults={'descripcion': articulo.get('descripcion', '')}
        )
    
    # 2. Determinar estados
    # ... (igual que en procesar)
    
    # 3. Crear movimiento
    movimiento = MovimientoProducto.objects.create(...)
    # El save() automáticamente crea/actualiza inventario
```

**Tareas:**
- [ ] Implementar creación de movimientos
- [ ] Implementar actualización de tipos de producto
- [ ] Verificar que inventario se crea correctamente

---

### FASE 5: Limpieza y Eliminación de Código Obsoleto

#### 5.1. Eliminar llamadas a `bulk_create` desde frontend

**Archivo:** `cryptotrace/cryptotrace-frontend/src/app/albaranes/upload-ac21/page.tsx`

**Tareas:**
- [ ] Eliminar import de `guardarEnLineaTemporal`
- [ ] Eliminar llamada a `guardarEnLineaTemporal`
- [ ] Verificar que no se usa en otros lugares

---

#### 5.2. Decidir sobre `bulk_create` y `procesar` en backend

**Opciones:**
- **Opción A:** Mantener ambos endpoints para compatibilidad
- **Opción B:** Deprecar `bulk_create` y `procesar`, mantener solo `procesar_directo`
- **Opción C:** Eliminar completamente después de migración

**Recomendación:** Opción A (mantener por ahora, documentar como deprecados)

**Tareas:**
- [ ] Decidir estrategia
- [ ] Documentar endpoints deprecados
- [ ] Añadir warnings en logs si se usan

---

#### 5.3. Limpiar código no utilizado

**Tareas:**
- [ ] Revisar y eliminar funciones no utilizadas
- [ ] Limpiar imports no utilizados
- [ ] Actualizar comentarios y documentación

---

## Orden de Implementación Recomendado

### Paso 1: Backend - Crear endpoint `procesar_directo` básico
- Crear método vacío
- Implementar validación de número de registro
- Implementar detección de documento existente
- Devolver respuesta básica

### Paso 2: Frontend - Modificar validaciones y flujo inicial
- Simplificar `handleConfirm`
- Eliminar llamadas a `guardarEnLineaTemporal`
- Modificar para abrir modal directamente

### Paso 3: Frontend - Modificar modal de línea temporal
- Modificar para recibir datos desde props
- Eliminar carga desde BD
- Mantener tipificación en memoria

### Paso 4: Backend - Completar `procesar_directo`
- Implementar creación de albarán
- Implementar creación de movimientos
- Implementar creación de inventario
- Manejar imagen

### Paso 5: Frontend - Integrar procesamiento final
- Crear función `procesarAlbaranDirecto`
- Modificar `handleProcesarAlbaran`
- Integrar con modal de documento existente

### Paso 6: Testing y ajustes
- Probar flujo completo
- Ajustar errores
- Optimizar si es necesario

### Paso 7: Limpieza
- Eliminar código obsoleto
- Documentar cambios
- Actualizar documentación

---

## Consideraciones Importantes

### 1. Compatibilidad hacia atrás
- Si hay otros flujos que usan `bulk_create` o `procesar`, mantenerlos funcionando
- Documentar claramente qué endpoints están deprecados

### 2. Manejo de errores
- Validar todos los datos antes de crear nada
- Manejar errores de forma clara para el usuario
- Logging detallado para debugging

### 3. Transacciones
- Todo el proceso de `procesar_directo` debe estar en `transaction.atomic()`
- Si algo falla, hacer rollback completo

### 4. Imágenes
- Manejar imagen opcional
- Validar tamaño y formato
- Guardar correctamente en el albarán

### 5. Performance
- El nuevo flujo es más eficiente (no guarda en línea temporal)
- Verificar que no hay problemas de performance con muchos artículos

---

## Checklist de Implementación

### Backend
- [ ] Crear método `procesar_directo` en `LineaTemporalProductoViewSet`
- [ ] Implementar validación de número de registro de salida
- [ ] Implementar detección de documento existente
- [ ] Implementar creación de albarán (nuevo o página adicional)
- [ ] Implementar creación de movimientos
- [ ] Implementar creación de inventario
- [ ] Manejar imagen opcional
- [ ] Añadir logging detallado
- [ ] Manejar errores apropiadamente
- [ ] Documentar endpoint

### Frontend
- [ ] Simplificar `handleConfirm` en `upload-ac21/page.tsx`
- [ ] Eliminar llamada a `guardarEnLineaTemporal`
- [ ] Modificar `LineaTemporalModal` para recibir datos desde props
- [ ] Modificar `GestionLineaTemporal` para trabajar en memoria
- [ ] Crear función `procesarAlbaranDirecto` en `api.ts`
- [ ] Modificar `handleProcesarAlbaran` para nuevo flujo
- [ ] Modificar `DocumentoExistenteModal` para nuevo flujo
- [ ] Eliminar código obsoleto
- [ ] Actualizar tipos TypeScript

### Testing
- [ ] Probar flujo completo con AC21 nuevo
- [ ] Probar flujo con AC21 existente (página adicional)
- [ ] Probar flujo con AC21 existente (documento independiente)
- [ ] Probar con muchos artículos
- [ ] Probar con imagen
- [ ] Probar sin imagen
- [ ] Probar validaciones de errores
- [ ] Verificar que inventario se crea correctamente

---

## Notas Finales

Este plan mantiene la funcionalidad existente mientras implementa el nuevo flujo. Se recomienda implementar paso a paso y probar cada fase antes de continuar.

Si encuentras algún problema o necesitas ajustar el plan, podemos modificar los pasos según sea necesario.
