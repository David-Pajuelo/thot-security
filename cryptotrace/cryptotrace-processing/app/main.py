from fastapi import FastAPI, UploadFile, File, Header, HTTPException
import pandas as pd
import aiofiles
import os
import traceback
import httpx
from fastapi.middleware.cors import CORSMiddleware

BACKEND_URL = os.getenv("BACKEND_URL", "http://cryptotrace-backend:8080/api/lineas-temporales/bulk_create/")
root_path = os.getenv("FASTAPI_ROOT_PATH", "")
app = FastAPI(title="CryptoTrace Processing API", version="1.0", root_path=root_path)

# 🔹 Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Para desarrollo local
        "https://cryptotrace.idiaicox.com"  # Para producción
    ],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "*"],  
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.post("/upload-excel/")
async def upload_excel(
    file: UploadFile = File(...),
    authorization: str = Header(None)
):
    """
    Recibe un archivo Excel, extrae los datos y los envía al backend para guardarlos en la tabla temporal.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="No se proporcionó token")

    print(f"📢 Token recibido en FastAPI: {authorization}")

    try:
        file_location = os.path.join(UPLOAD_FOLDER, file.filename)
        async with aiofiles.open(file_location, 'wb') as out_file:
            while chunk := await file.read(1024 * 1024):  
                await out_file.write(chunk)

        df = pd.read_excel(file_location, engine='openpyxl')
        df.columns = df.columns.str.strip()

        # 🔹 Renombrar solo las columnas que existan
        # Columnas esperadas: ORDER (opcional), Packing List, Part. N, Descripción, CANTIDAD, S/N, BULTOS TOTAL, OBSERVACIONES
        rename_map = {
            "Packing List": "numero_albaran",
            "Part. N": "codigo_producto",
            "Descripción": "descripcion",
            "S/N": "numero_serie",
            "BULTOS TOTAL": "bultos_total",
            "OBSERVACIONES": "observaciones",
            "CANTIDAD": "cantidad",
        }
        df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
        # Si hay dos columnas CANTIDAD, pandas suele crear "cantidad" y "CANTIDAD.1"; nos quedamos con "cantidad"

        # 🔹 Añadir columnas faltantes (Excel mínimo puede tener solo numero_albaran y codigo_producto)
        for col in ["numero_albaran", "codigo_producto", "descripcion", "numero_serie", "bultos_total", "observaciones", "cantidad"]:
            if col not in df.columns:
                df[col] = None

        df = df.replace([float("nan"), float("inf"), float("-inf")], None)

        # 🔹 Filtrar solo filas sin código de producto (no exigir S/N para Excel mínimo)
        df = df[df["codigo_producto"].notna() & (df["codigo_producto"].astype(str).str.strip() != "")]
        if df.empty:
            raise HTTPException(status_code=400, detail="No se encontraron filas con Part. N (código de producto) en el archivo Excel.")

        lineas_temporales = df[["numero_albaran", "codigo_producto", "descripcion", "numero_serie", "bultos_total", "observaciones", "cantidad"]].to_dict(orient="records")

        # 🔹 Filtrar registros inválidos antes de enviarlos al backend
        lineas_temporales = [
            item for item in lineas_temporales 
            if item.get("codigo_producto") and str(item["codigo_producto"]).strip() != ""
        ]

        if not lineas_temporales:
            raise HTTPException(status_code=400, detail="No se encontraron datos válidos en el archivo Excel.")

        # 🔹 Transformar datos para que coincidan con la API del backend
        numero_albaran_raw = lineas_temporales[0].get('numero_albaran')
        if numero_albaran_raw is None or (isinstance(numero_albaran_raw, float) and pd.isna(numero_albaran_raw)):
            raise HTTPException(status_code=400, detail="No se encontró número de albarán (Packing List) en el archivo Excel.")
        # Normalizar (evitar "12345.0" si Packing List es numérico en Excel)
        numero_albaran = str(int(numero_albaran_raw)) if isinstance(numero_albaran_raw, float) and numero_albaran_raw == int(numero_albaran_raw) else str(numero_albaran_raw).strip()
        
        def _normalizar_celda(val):
            """Convierte a string; si es float entero (ej. 12345.0) quita el .0 para que no salga en código_producto."""
            if val is None or (isinstance(val, float) and pd.isna(val)):
                return ""
            if isinstance(val, float) and val == int(val):
                return str(int(val)).strip()
            return str(val).strip()

        articulos_transformados = []
        for linea in lineas_temporales:
            codigo = linea.get("codigo_producto")
            descripcion = linea.get("descripcion")
            numero_serie = linea.get("numero_serie")

            # Limpiar NaN/None
            if codigo and isinstance(codigo, float) and pd.isna(codigo):
                codigo = None
            if descripcion and isinstance(descripcion, float) and pd.isna(descripcion):
                descripcion = None
            if numero_serie and isinstance(numero_serie, float) and pd.isna(numero_serie):
                numero_serie = None

            # Normalizar a string (evitar "12345.0" cuando Excel trae número en Part. N o S/N)
            codigo = _normalizar_celda(codigo)
            descripcion = _normalizar_celda(descripcion)
            numero_serie = _normalizar_celda(numero_serie)

            # Asegurar que al menos haya código o descripción
            if not codigo and not descripcion:
                print(f"⚠️ Saltando línea sin código ni descripción: {linea}")
                continue

            # Código de producto: siempre Part. N si tiene valor; si no, Descripción
            if not codigo:
                codigo = descripcion

            # Cantidad: desde columna CANTIDAD del Excel (mínimo 1)
            cantidad_raw = linea.get("cantidad")
            try:
                if cantidad_raw is None or (isinstance(cantidad_raw, float) and pd.isna(cantidad_raw)):
                    cantidad = 1
                else:
                    cantidad = int(float(cantidad_raw))
                    cantidad = max(1, cantidad)
            except (ValueError, TypeError):
                cantidad = 1
            
            observaciones = _normalizar_celda(linea.get("observaciones"))
            
            articulos_transformados.append({
                "codigo": codigo,
                "codigo_producto": codigo,
                "descripcion": descripcion if descripcion else codigo,
                "numero_serie": numero_serie,
                "observaciones": observaciones,
                "cantidad": cantidad,
                "cc": 1
            })

        payload = {
            "cabecera": { "numero": numero_albaran },
            "articulos": articulos_transformados
        }

        print(f"🎯 Usando BACKEND_URL: {BACKEND_URL}")
        print("📢 Enviando payload transformado al backend:", payload)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                BACKEND_URL, 
                json=payload,  # 🔹 Enviar payload transformado
                headers={"Authorization": authorization}
            )

        print(f"📦 Respuesta del backend recibida. Status: {response.status_code}")
        print(f"📦 Contenido de la respuesta del backend: {response.text}")

        # Verificar si la respuesta del backend es exitosa
        if response.status_code >= 400:
            print(f"❌ Error del backend: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"Error del backend: {response.text}"
            )

        return {
            "filename": file.filename,
            "structured_data": payload,
            "backend_response": response.json()
        }

    except Exception as e:
        print(f"🔥 Se ha producido una excepción no controlada: {e}")
        print(f"🔥 Traceback: {traceback.format_exc()}")
        return {"error": str(e), "traceback": traceback.format_exc()}
