# Análisis del Funcionamiento de Empresas en AC-21

## Resumen Ejecutivo

Este documento analiza el flujo completo de datos de empresas entre las secciones "Datos Principales" y "Detalles de Empresa" en el formulario de AC-21, identificando fallos lógicos, contradicciones y proponiendo soluciones.

---

## 1. Arquitectura del Sistema

### 1.1 Estructura de Datos

**Estado Principal (`processedData`):**
```typescript
{
  empresa_origen: {
    nombre: string | null,
    direccion: string | null,
    codigo_postal: string | null,
    ciudad: string | null,
    provincia: string | null,
    codigo_odmc: string | null,  // ⚠️ Frontend usa codigo_odmc
    id: number | undefined,
    numero_odmc?: string          // ⚠️ Backend devuelve numero_odmc
  },
  empresa_destino: { ... }        // Misma estructura
}
```

**Backend (Django):**
- Campo en BD: `numero_odmc` (CharField)
- Serializer devuelve: `numero_odmc`
- Frontend espera: `codigo_odmc` (para compatibilidad con OCR)

### 1.2 Flujos de Datos

#### Flujo A: OCR → Frontend
1. OCR extrae datos → devuelve `codigo_odmc`
2. `cleanEmpresa()` procesa → mantiene `codigo_odmc` y crea `numero_odmc` (duplicado)
3. `setProcessedData()` actualiza estado
4. Auto-match intenta encontrar empresa existente

#### Flujo B: Selector → Frontend
1. Usuario selecciona empresa del dropdown
2. Backend devuelve empresa con `numero_odmc`
3. `onChange` mapea `numero_odmc` → `codigo_odmc`
4. `setProcessedData()` actualiza estado

#### Flujo C: Guardar desde Pestaña "Detalles"
1. Usuario edita campos en pestaña "Empresas"
2. Al hacer clic en "Guardar", se lee `processedData.empresa_origen/destino`
3. Se mapea `codigo_odmc` → `numero_odmc` para enviar al backend
4. Backend crea/actualiza empresa
5. Backend devuelve empresa con `numero_odmc`
6. Se actualiza `processedData` con respuesta del backend
7. **PROBLEMA**: No se mapea `numero_odmc` → `codigo_odmc` después de guardar

#### Flujo D: Guardar desde Modal
1. Usuario hace clic en "+" en selector
2. Se abre modal con datos del OCR (si existen)
3. Usuario completa formulario
4. Se guarda empresa
5. Se actualiza `processedData` con respuesta
6. **PROBLEMA**: Similar al Flujo C

---

## 2. Problemas Identificados

### 2.1 Inconsistencia en Nomenclatura ODMC

**Problema:**
- Backend usa `numero_odmc`
- Frontend usa `codigo_odmc` internamente
- OCR devuelve `codigo_odmc`
- Hay mapeo inconsistente entre ambos

**Ubicaciones del problema:**
1. **Línea 2583**: Selector empresa_origen mapea correctamente
2. **Línea 2639**: Selector empresa_destino mapea correctamente
3. **Línea 2795-2797**: Guardar desde pestaña NO mapea después de guardar
4. **Línea 2922-2924**: Guardar desde pestaña NO mapea después de guardar
5. **Línea 1528**: Guardar desde modal NO mapea después de guardar

**Impacto:**
- Después de guardar una empresa, el ODMC puede desaparecer de la UI
- El selector puede no mostrar el ODMC correctamente si la empresa fue guardada recientemente

### 2.2 Sincronización entre Pestañas

**Problema:**
Las dos pestañas ("Datos Principales" y "Empresas") comparten el mismo estado `processedData`, pero:

1. **Edición en "Datos Principales":**
   - Los campos son de solo lectura (excepto selector)
   - No hay inputs editables para empresa_origen/destino
   - Solo se puede seleccionar empresa existente o abrir modal

2. **Edición en "Empresas":**
   - Todos los campos son editables
   - Se puede guardar directamente desde aquí
   - Los cambios se reflejan inmediatamente en `processedData`

**Contradicción:**
- Si editas en "Empresas" y luego cambias a "Datos Principales", los cambios se ven
- Si editas en "Datos Principales" (selector) y luego cambias a "Empresas", los cambios se ven
- **PERO**: Si guardas desde "Empresas", el selector en "Datos Principales" puede no reflejar el `id` correctamente si la empresa es nueva

### 2.3 Auto-match y Actualización del Selector

**Problema:**
El auto-match se ejecuta después del OCR (línea 945-989), pero:

1. Si el auto-match encuentra una empresa, actualiza `processedData.empresa_origen` con el `id`
2. El selector usa `value={processedData.empresa_origen?.id || ''}`
3. **PERO**: Si guardas una empresa nueva desde la pestaña "Empresas", el selector puede no actualizarse correctamente porque:
   - Se actualiza `processedData` con la nueva empresa (incluye `id`)
   - Se recarga la lista de empresas (`fetchEmpresas()`)
   - **PERO**: El selector puede no reflejar el cambio si el `id` no coincide exactamente

**Código problemático:**
```typescript
// Línea 2795-2797: Guardar desde pestaña
setProcessedData((prev: any) => ({
  ...prev,
  empresa_origen: { ...nuevaEmpresa, es_nueva: false }
}));
// ⚠️ nuevaEmpresa viene del backend con numero_odmc, no codigo_odmc
// ⚠️ No se mapea numero_odmc → codigo_odmc
```

### 2.4 Pérdida de Datos al Guardar

**Problema:**
Cuando guardas una empresa desde la pestaña "Empresas":

1. Se lee `processedData.empresa_origen` (tiene `codigo_odmc`)
2. Se mapea `codigo_odmc` → `numero_odmc` para enviar al backend ✅
3. Backend devuelve empresa con `numero_odmc` (no `codigo_odmc`)
4. Se actualiza `processedData` con la respuesta del backend
5. **PROBLEMA**: El `codigo_odmc` se pierde porque la respuesta del backend no lo incluye

**Flujo actual:**
```
processedData.empresa_origen = { codigo_odmc: "EMAD-004", ... }
  ↓
Guardar → Backend recibe: { numero_odmc: "EMAD-004", ... }
  ↓
Backend devuelve: { id: 1, numero_odmc: "EMAD-004", ... }
  ↓
setProcessedData({ empresa_origen: { ...nuevaEmpresa } })
  ↓
processedData.empresa_origen = { id: 1, numero_odmc: "EMAD-004", codigo_odmc: undefined }
  ↓
UI muestra: ODMC Nº: - (vacío)
```

### 2.5 Inconsistencia en Limpieza de Datos

**Problema:**
La función `cleanEmpresa()` (línea 849) crea ambos campos:
```typescript
return {
  ...
  numero_odmc: odmc,  // Duplicado
  codigo_odmc: odmc,  // Duplicado
  ...
};
```

Esto crea redundancia y confusión sobre cuál campo usar.

### 2.6 Selector No Sincronizado con Estado

**Problema:**
El selector usa `value={processedData.empresa_origen?.id || ''}`, pero:

1. Si `processedData.empresa_origen` tiene datos del OCR pero no tiene `id`, el selector muestra "Selecciona empresa..."
2. Si guardas una empresa nueva, se actualiza `processedData` con el `id`
3. **PERO**: Si la lista de empresas (`empresas`) no se ha actualizado aún, el selector puede no mostrar la empresa correctamente

**Código:**
```typescript
// Línea 2574
value={processedData.empresa_origen?.id || ''}
// Si id existe pero no está en la lista empresas[], el selector puede fallar
```

---

## 3. Contradicciones Lógicas

### 3.1 Doble Fuente de Verdad

**Contradicción:**
- `processedData.empresa_origen` es la fuente de verdad para la UI
- `empresas[]` es la fuente de verdad para el selector
- Ambas deben estar sincronizadas, pero no siempre lo están

**Ejemplo:**
1. OCR extrae empresa "EMAD" sin `id`
2. `processedData.empresa_origen = { nombre: "EMAD", codigo_odmc: "EMAD-004" }`
3. Auto-match encuentra empresa existente con `id: 2`
4. `processedData.empresa_origen = { id: 2, nombre: "EMAD", ... }`
5. Selector muestra empresa correctamente ✅
6. Usuario guarda empresa desde pestaña "Empresas"
7. Se crea nueva empresa con `id: 5`
8. `processedData.empresa_origen = { id: 5, ... }`
9. Selector puede no actualizarse si `empresas[]` no se recarga a tiempo

### 3.2 Estado vs. Backend

**Contradicción:**
- El estado local puede tener datos que no existen en el backend (empresas del OCR)
- El backend puede tener empresas que no están en el estado local
- No hay validación cruzada

### 3.3 Mapeo Bidireccional Incompleto

**Contradicción:**
- Al recibir datos del backend → frontend: se mapea `numero_odmc` → `codigo_odmc` (solo en selectores)
- Al enviar datos del frontend → backend: se mapea `codigo_odmc` → `numero_odmc` ✅
- Al recibir respuesta del backend → frontend: NO se mapea `numero_odmc` → `codigo_odmc` ❌

---

## 4. Soluciones Propuestas

### 4.1 Solución 1: Normalizar a un Solo Campo (Recomendada)

**Enfoque:** Usar `codigo_odmc` en todo el frontend y mapear solo en los puntos de entrada/salida.

**Cambios necesarios:**

1. **Función helper para normalizar empresa del backend:**
```typescript
const normalizeEmpresaFromBackend = (empresa: any) => {
  return {
    ...empresa,
    codigo_odmc: empresa.numero_odmc || empresa.codigo_odmc || ''
  };
};
```

2. **Actualizar todos los puntos donde se recibe empresa del backend:**
   - Línea 2795-2797: Después de guardar desde pestaña
   - Línea 2922-2924: Después de guardar desde pestaña
   - Línea 1528: Después de guardar desde modal
   - Línea 2580-2584: En selector empresa_origen (ya está, pero usar helper)
   - Línea 2636-2640: En selector empresa_destino (ya está, pero usar helper)

3. **Eliminar duplicación en `cleanEmpresa()`:**
```typescript
const cleanEmpresa = (emp: any) => {
  const odmc = cleanString(emp?.codigo_odmc || '');
  // ... resto del código ...
  return {
    ...
    codigo_odmc: odmc,  // Solo codigo_odmc
    id: emp?.id || undefined
  };
};
```

**Ventajas:**
- Consistencia en todo el frontend
- Un solo campo a mantener
- Menos errores de mapeo

**Desventajas:**
- Requiere cambios en múltiples lugares
- Necesita testing exhaustivo

### 4.2 Solución 2: Mapeo Automático en Helper

**Enfoque:** Crear helper que siempre mapee correctamente.

**Implementación:**
```typescript
const syncEmpresaData = (empresa: any, source: 'backend' | 'ocr' | 'local') => {
  if (source === 'backend') {
    // Backend → Frontend: mapear numero_odmc → codigo_odmc
    return {
      ...empresa,
      codigo_odmc: empresa.numero_odmc || empresa.codigo_odmc || ''
    };
  } else if (source === 'ocr') {
    // OCR → Frontend: ya viene con codigo_odmc
    return empresa;
  } else {
    // Local: mantener como está
    return empresa;
  }
};
```

**Usar en:**
- Después de `createEmpresa()` / `updateEmpresa()`
- En `onChange` de selectores
- En auto-match

### 4.3 Solución 3: Estado Unificado con Sincronización

**Enfoque:** Crear estado derivado que siempre esté sincronizado.

**Implementación:**
```typescript
// Estado para empresas disponibles
const [empresas, setEmpresas] = useState<any[]>([]);

// Estado derivado: empresas normalizadas
const empresasNormalizadas = useMemo(() => {
  return empresas.map(emp => ({
    ...emp,
    codigo_odmc: emp.numero_odmc || emp.codigo_odmc || ''
  }));
}, [empresas]);

// Función para actualizar processedData después de guardar
const updateEmpresaInProcessedData = (empresa: any, tipo: 'origen' | 'destino') => {
  const normalized = normalizeEmpresaFromBackend(empresa);
  setProcessedData((prev: any) => ({
    ...prev,
    [`empresa_${tipo}`]: normalized
  }));
};
```

### 4.4 Solución 4: Validación y Sincronización Forzada

**Enfoque:** Añadir validación y sincronización explícita.

**Implementación:**
```typescript
// Después de guardar empresa
const nuevaEmpresa = await createEmpresa(dataToSave);

// 1. Normalizar empresa
const empresaNormalizada = normalizeEmpresaFromBackend(nuevaEmpresa);

// 2. Actualizar processedData
setProcessedData((prev: any) => ({
  ...prev,
  empresa_origen: empresaNormalizada
}));

// 3. Recargar lista de empresas
const empresasActualizadas = await fetchEmpresas();
setEmpresas(empresasActualizadas);

// 4. Asegurar que el selector se actualice
// (React debería hacerlo automáticamente, pero podemos forzarlo)
setTimeout(() => {
  setProcessedData((prev: any) => ({
    ...prev,
    empresa_origen: {
      ...prev.empresa_origen,
      id: nuevaEmpresa.id  // Asegurar que el id esté presente
    }
  }));
}, 100);
```

---

## 5. Recomendación Final

**Solución Recomendada: Combinación de Solución 1 + Solución 2**

1. **Crear helper de normalización:**
```typescript
const normalizeEmpresaFromBackend = (empresa: any) => {
  if (!empresa) return null;
  return {
    ...empresa,
    codigo_odmc: empresa.numero_odmc || empresa.codigo_odmc || ''
  };
};
```

2. **Usar en todos los puntos de entrada del backend:**
   - Después de `createEmpresa()`
   - Después de `updateEmpresa()`
   - En `onChange` de selectores (ya está, pero usar helper)
   - En auto-match

3. **Eliminar duplicación en `cleanEmpresa()`:**
   - Solo mantener `codigo_odmc`
   - Eliminar `numero_odmc` del objeto retornado

4. **Añadir sincronización forzada después de guardar:**
   - Recargar lista de empresas
   - Normalizar empresa guardada
   - Actualizar `processedData` con empresa normalizada

5. **Añadir validación:**
   - Verificar que `codigo_odmc` esté presente después de guardar
   - Log de advertencia si falta

---

## 6. Plan de Implementación

### Fase 1: Preparación
1. Crear función `normalizeEmpresaFromBackend()`
2. Crear función `prepareEmpresaForBackend()` (mapea codigo_odmc → numero_odmc)
3. Añadir tests unitarios

### Fase 2: Refactorización
1. Actualizar `cleanEmpresa()` para eliminar duplicación
2. Actualizar todos los puntos donde se recibe empresa del backend
3. Actualizar selectores para usar helper

### Fase 3: Sincronización
1. Añadir sincronización forzada después de guardar
2. Añadir validación y logs
3. Añadir indicadores visuales de sincronización

### Fase 4: Testing
1. Test: Guardar empresa nueva desde pestaña "Empresas"
2. Test: Guardar empresa desde modal
3. Test: Seleccionar empresa del selector
4. Test: Auto-match después de OCR
5. Test: Editar empresa en pestaña "Empresas" y verificar sincronización

---

## 7. Checklist de Verificación

Después de implementar las soluciones, verificar:

- [ ] ODMC se muestra correctamente después de guardar empresa desde pestaña "Empresas"
- [ ] ODMC se muestra correctamente después de guardar empresa desde modal
- [ ] ODMC se muestra correctamente al seleccionar empresa del selector
- [ ] ODMC se muestra correctamente después de auto-match
- [ ] Selector muestra empresa correcta después de guardar empresa nueva
- [ ] No hay pérdida de datos al cambiar entre pestañas
- [ ] No hay duplicación de campos ODMC en el estado
- [ ] Los logs muestran mapeo correcto en todos los flujos

---

## 8. Notas Adicionales

- El problema del ODMC es el más crítico y visible para el usuario
- La sincronización entre pestañas funciona bien, pero puede mejorarse
- El auto-match funciona correctamente, pero depende de la calidad del nombre
- Considerar añadir indicador visual cuando hay empresas nuevas sin guardar
- Considerar añadir validación antes de guardar albarán completo
