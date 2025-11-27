#!/usr/bin/env python3
"""
Script para debuggear la búsqueda de HPS
"""

from src.database.database import SessionLocal
from src.models.hps import HPSRequest
from sqlalchemy import and_

def debug_hps_search():
    print("🔍 Debuggeando búsqueda de HPS...")
    
    db = SessionLocal()
    try:
        # Buscar exactamente como lo hace el monitor
        name_parts = 'Laur Jiemnez'.split()
        if len(name_parts) >= 2:
            first_name = name_parts[0]
            last_name = ' '.join(name_parts[1:])
            
            print(f'Buscando: primer_nombre="{first_name}", apellido="{last_name}"')
            
            hps = db.query(HPSRequest).filter(
                and_(
                    HPSRequest.first_name.ilike(f'%{first_name}%'),
                    HPSRequest.first_last_name.ilike(f'%{last_name}%'),
                    HPSRequest.status == 'pending'
                )
            ).first()
            
            if hps:
                print(f'✅ HPS encontrada: {hps.id} - {hps.first_name} {hps.first_last_name}')
            else:
                print('❌ No se encontró HPS')
                
                # Verificar qué hay en la base de datos
                all_hps = db.query(HPSRequest).filter(HPSRequest.status == 'pending').all()
                print('HPS pendientes en la base de datos:')
                for h in all_hps:
                    print(f'  - {h.first_name} {h.first_last_name}')
                    
    finally:
        db.close()

if __name__ == "__main__":
    debug_hps_search()
