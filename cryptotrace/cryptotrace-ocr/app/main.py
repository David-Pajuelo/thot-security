from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import tempfile
import shutil
from enum import Enum
from app.ocr.processors.ac21_processor import AC21Processor
from app.ocr.processors.telefonica_processor import TelefonicaDeliveryProcessor
from app.ocr.processors.elbit_processor import ElbitProcessor
import traceback

# Cargar variables de entorno
load_dotenv()

# Diagnóstico de variables de entorno
print("🔍 Diagnóstico de variables de entorno:")
print(f"📁 Directorio actual: {os.getcwd()}")
print(f"📄 Ruta del archivo .env: {os.path.join(os.getcwd(), '.env')}")
print(f"🔑 OPENAI_API_KEY presente: {'✅' if os.getenv('OPENAI_API_KEY') else '❌'}")
print(f"🔑 OPENAI_API_KEY valor: {'Presente' if os.getenv('OPENAI_API_KEY') else 'No encontrada'}")
print("----------------------------------------")

class DocumentType(str, Enum):
    AC21 = "ac21"
    ALBARAN_TELEFONICA = "albaran_telefonica"
    ELBIT_COC = "elbit_coc"

app = FastAPI(
    title="CryptoTrace OCR Service",
    description="Microservicio para procesamiento de imágenes y extracción de datos de documentos",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos los orígenes en desarrollo
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos
    allow_headers=["*"],  # Permitir todos los headers
    expose_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "CryptoTrace OCR Service", "status": "running"}

@app.post("/process-image/")
async def process_image(
    file: UploadFile = File(...),
    document_type: str = Form(...)
):
    print("="*50)
    print("📥 NUEVA PETICIÓN DE PROCESAMIENTO DE IMAGEN")
    print("="*50)
    print(f"📄 Tipo de documento recibido (raw): {document_type}")
    print(f"📁 Nombre del archivo: {file.filename}")
    print(f"📦 Content-Type: {file.content_type}")
    
    try:
        # Convertir el tipo de documento a enum
        doc_type = DocumentType(document_type.lower())
        print(f"📄 Tipo de documento convertido: {doc_type}")
        
        # Crear un archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            print("💾 Guardando archivo temporal...")
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name
            print(f"✅ Archivo temporal guardado en: {temp_path}")
        
        try:
            # Leer el contenido del archivo
            print("📖 Leyendo contenido del archivo...")
            with open(temp_path, 'rb') as f:
                file_content = f.read()
            print(f"✅ Archivo leído, tamaño: {len(file_content)} bytes")
            
            # Procesar según el tipo de documento
            print(f"🔍 Procesando documento tipo: {doc_type}")
            if doc_type == DocumentType.AC21:
                processor = AC21Processor()
                result = processor.process_image(file_content)
            elif doc_type == DocumentType.ALBARAN_TELEFONICA:
                processor = TelefonicaDeliveryProcessor()
                result = processor.process_image(file_content)
            elif doc_type == DocumentType.ELBIT_COC:
                processor = ElbitProcessor()
                result = processor.process_image(file_content)
            else:
                raise HTTPException(status_code=400, detail=f"Tipo de documento no soportado: {doc_type}")
            
            print("✅ Procesamiento completado")
            print("="*50)
            return result
            
        except Exception as e:
            print(f"❌ Error durante el procesamiento: {str(e)}")
            print(f"📚 Stack trace: {traceback.format_exc()}")
            print("="*50)
            raise HTTPException(status_code=500, detail=str(e))
            
        finally:
            # Limpiar archivo temporal
            print("🧹 Limpiando archivo temporal...")
            os.unlink(temp_path)
            print("✅ Archivo temporal eliminado")
            
    except ValueError as e:
        print(f"❌ Error de validación: {str(e)}")
        print("="*50)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        print(f"📚 Stack trace: {traceback.format_exc()}")
        print("="*50)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 