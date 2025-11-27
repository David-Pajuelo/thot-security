#!/usr/bin/env python3
"""
Sistema de automatización para procesamiento de PDFs de HPS desde correo electrónico
"""

import os
import json
import imaplib
import email
import PyPDF2
import pdfplumber
import re
from datetime import datetime
from pathlib import Path
import tempfile

class HPSEmailProcessor:
    def __init__(self, email_config=None):
        """
        Inicializa el procesador de emails de HPS
        
        email_config: dict con configuración IMAP
        {
            'server': 'imap.gmail.com',
            'port': 993,
            'username': 'tu_email@gmail.com',
            'password': 'tu_password',
            'folder': 'INBOX'
        }
        """
        self.email_config = email_config
        self.processed_files = set()
        
    def connect_to_email(self):
        """Conecta al servidor de correo IMAP"""
        if not self.email_config:
            print("No hay configuracion de email disponible")
            return None
            
        try:
            mail = imaplib.IMAP4_SSL(self.email_config['server'], self.email_config['port'])
            mail.login(self.email_config['username'], self.email_config['password'])
            mail.select(self.email_config['folder'])
            return mail
        except Exception as e:
            print(f"Error conectando al email: {e}")
            return None
    
    def extract_pdf_text(self, pdf_path):
        """Extrae texto de un PDF usando pdfplumber"""
        try:
            text = ""
            tables = []
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- PAGINA {page_num + 1} ---\n"
                        text += page_text + "\n"
                    
                    page_tables = page.extract_tables()
                    if page_tables:
                        for table_num, table in enumerate(page_tables):
                            tables.append({
                                'page': page_num + 1,
                                'table': table_num + 1,
                                'data': table
                            })
            
            return text, tables
        except Exception as e:
            print(f"Error extrayendo texto del PDF: {e}")
            return None, None
    
    def analyze_hps_pdf(self, pdf_path, filename):
        """Analiza un PDF de HPS y extrae información"""
        
        print(f"Analizando PDF: {filename}")
        
        # Extraer texto
        text, tables = self.extract_pdf_text(pdf_path)
        if not text:
            return None
        
        # Determinar tipo de documento
        doc_type = self.determine_document_type(text)
        
        if doc_type == 'LISTADO_CONCESIONES':
            return self.process_concesiones(text, filename)
        elif doc_type == 'LISTADO_RECHAZOS':
            return self.process_rechazos(text, filename)
        else:
            print(f"Tipo de documento no reconocido en {filename}")
            return None
    
    def determine_document_type(self, text):
        """Determina el tipo de documento HPS"""
        text_upper = text.upper()
        
        if 'LISTADO DE CONCESIONES' in text_upper or 'CONCEDID' in text_upper:
            return 'LISTADO_CONCESIONES'
        elif 'LISTADO DE RECHAZOS' in text_upper or 'RECHAZAD' in text_upper or 'DENEGAD' in text_upper:
            return 'LISTADO_RECHAZOS'
        else:
            return 'DESCONOCIDO'
    
    def process_concesiones(self, text, filename):
        """Procesa un documento de concesiones (aprobaciones)"""
        
        # Extraer información básica
        empresa_match = re.search(r'Empresa:\s*([^N]+)(?:NIF|$)', text)
        nif_match = re.search(r'NIF:\s*([A-Z0-9]+)', text)
        fecha_match = re.search(r'(\d{2}/\d{2}/\d{4})', text)
        expediente_match = re.search(r'(E-\d+-\d+)', text)
        
        doc_info = {
            'tipo_documento': 'LISTADO DE CONCESIONES',
            'empresa': empresa_match.group(1).strip() if empresa_match else 'DESCONOCIDA',
            'nif_empresa': nif_match.group(1) if nif_match else 'DESCONOCIDO',
            'fecha_documento': fecha_match.group(1) if fecha_match else 'DESCONOCIDA',
            'expediente_base': expediente_match.group(1) if expediente_match else 'DESCONOCIDO',
            'estado_general': 'APROBADO',
            'archivo_origen': filename
        }
        
        # Extraer personas aprobadas
        persons = self.extract_persons_from_text(text, 'APROBADO')
        doc_info['total_personas'] = len(persons)
        
        return {
            'documento': doc_info,
            'personas': persons,
            'resumen': {
                'total_aprobadas': len(persons),
                'total_rechazadas': 0,
                'empresa': doc_info['empresa'],
                'fecha_procesamiento': datetime.now().isoformat()
            }
        }
    
    def process_rechazos(self, text, filename):
        """Procesa un documento de rechazos"""
        
        # Similar al de concesiones pero para rechazos
        empresa_match = re.search(r'Empresa:\s*([^N]+)(?:NIF|$)', text)
        nif_match = re.search(r'NIF:\s*([A-Z0-9]+)', text)
        fecha_match = re.search(r'(\d{2}/\d{2}/\d{4})', text)
        expediente_match = re.search(r'(E-\d+-\d+)', text)
        
        doc_info = {
            'tipo_documento': 'LISTADO DE RECHAZOS',
            'empresa': empresa_match.group(1).strip() if empresa_match else 'DESCONOCIDA',
            'nif_empresa': nif_match.group(1) if nif_match else 'DESCONOCIDO',
            'fecha_documento': fecha_match.group(1) if fecha_match else 'DESCONOCIDA',
            'expediente_base': expediente_match.group(1) if expediente_match else 'DESCONOCIDO',
            'estado_general': 'RECHAZADO',
            'archivo_origen': filename
        }
        
        # Extraer personas rechazadas
        persons = self.extract_persons_from_text(text, 'RECHAZADO')
        doc_info['total_personas'] = len(persons)
        
        return {
            'documento': doc_info,
            'personas': persons,
            'resumen': {
                'total_aprobadas': 0,
                'total_rechazadas': len(persons),
                'empresa': doc_info['empresa'],
                'fecha_procesamiento': datetime.now().isoformat()
            }
        }
    
    def extract_persons_from_text(self, text, estado):
        """Extrae personas del texto con el estado especificado"""
        persons = []
        
        # Patrón para extraer líneas con DNI
        pattern = r'(\d+)\s+([0-9]{8}[A-Z])\s+(.*?)\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s+(E-\d+-\d+)'
        matches = re.findall(pattern, text)
        
        for match in matches:
            numero, dni, grado_especialidad, fecha_inicio, fecha_fin, expediente = match
            
            persons.append({
                'numero': int(numero),
                'dni': dni,
                'grado_especialidad': grado_especialidad.strip(),
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'expediente': expediente,
                'estado': estado
            })
        
        return persons
    
    def process_email_attachments(self):
        """Procesa adjuntos PDF de emails (simulado)"""
        
        print("SIMULACION: Procesando emails con PDFs de HPS...")
        print("=" * 60)
        
        # En un caso real, aquí se conectaría al email y buscaría PDFs
        # Por ahora, procesamos el PDF de ejemplo
        
        pdf_file = "E-25-027334-AICOX-0312_25.pdf"
        if not Path(pdf_file).exists():
            print(f"No se encuentra el archivo de ejemplo: {pdf_file}")
            return []
        
        results = []
        
        # Procesar el PDF
        result = self.analyze_hps_pdf(pdf_file, pdf_file)
        if result:
            results.append(result)
            
            # Generar formato para base de datos
            db_records = self.generate_db_format(result)
            
            # Guardar resultados
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Archivo de análisis completo
            analysis_file = f"hps_analysis_{timestamp}.json"
            with open(analysis_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            # Archivo para base de datos
            db_file = f"hps_db_records_{timestamp}.json"
            with open(db_file, 'w', encoding='utf-8') as f:
                json.dump(db_records, f, indent=2, ensure_ascii=False)
            
            print(f"Procesado: {pdf_file}")
            print(f"- Tipo: {result['documento']['tipo_documento']}")
            print(f"- Empresa: {result['documento']['empresa']}")
            print(f"- Total personas: {result['documento']['total_personas']}")
            print(f"- Archivos generados:")
            print(f"  * {analysis_file}")
            print(f"  * {db_file}")
        
        return results
    
    def generate_db_format(self, result):
        """Genera formato para insertar en base de datos"""
        
        db_records = []
        
        for person in result['personas']:
            record = {
                'dni': person['dni'],
                'estado_hps': person['estado'],
                'fecha_aprobacion': person['fecha_inicio'] if person['estado'] == 'APROBADO' else None,
                'fecha_rechazo': person['fecha_inicio'] if person['estado'] == 'RECHAZADO' else None,
                'fecha_caducidad': person['fecha_fin'],
                'expediente': person['expediente'],
                'empresa': result['documento']['empresa'],
                'nif_empresa': result['documento']['nif_empresa'],
                'grado_especialidad': person['grado_especialidad'],
                'procesado_automaticamente': True,
                'archivo_origen': result['documento']['archivo_origen'],
                'fecha_procesamiento': datetime.now().isoformat(),
                'tipo_documento': result['documento']['tipo_documento']
            }
            
            db_records.append(record)
        
        return db_records
    
    def simulate_database_integration(self, db_records):
        """Simula la integración con la base de datos del sistema HPS"""
        
        print(f"\nSIMULACION: Integrando {len(db_records)} registros con la BD...")
        print("-" * 50)
        
        # Aquí se haría la integración real con la base de datos
        # Por ejemplo, usando SQLAlchemy para insertar en la tabla de usuarios
        
        for i, record in enumerate(db_records, 1):
            print(f"{i:2d}. DNI: {record['dni']} - Estado: {record['estado_hps']}")
            
            # Simulación de queries SQL que se ejecutarían:
            if record['estado_hps'] == 'APROBADO':
                print(f"    SQL: UPDATE users SET hps_status='APROBADO', hps_expiry='{record['fecha_caducidad']}' WHERE dni='{record['dni']}'")
            else:
                print(f"    SQL: UPDATE users SET hps_status='RECHAZADO' WHERE dni='{record['dni']}'")
        
        print(f"\nIntegracion completada: {len(db_records)} registros procesados")

def main():
    """Función principal de demostración"""
    
    print("SISTEMA DE AUTOMATIZACION HPS - PROCESAMIENTO DE PDFs")
    print("=" * 60)
    
    # Configuración de email (ejemplo)
    email_config = {
        'server': 'imap.gmail.com',
        'port': 993,
        'username': 'hps-system@empresa.com',  # Email del sistema
        'password': 'password_seguro',
        'folder': 'INBOX'
    }
    
    # Crear procesador
    processor = HPSEmailProcessor(email_config)
    
    # Procesar emails (simulado)
    results = processor.process_email_attachments()
    
    if results:
        # Simular integración con BD
        for result in results:
            db_records = processor.generate_db_format(result)
            processor.simulate_database_integration(db_records)
    
    print(f"\nPROCESAMIENTO COMPLETADO")
    print("=" * 60)
    
    return results

if __name__ == "__main__":
    main()
