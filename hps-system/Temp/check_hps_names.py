#!/usr/bin/env python3
"""
Script para verificar nombres en HPS pendientes
"""

from src.database.database import SessionLocal
from src.models.hps import HPSRequest

def check_hps_names():
    db = SessionLocal()
    try:
        # Obtener todas las HPS pendientes con sus nombres
        pending_hps = db.query(HPSRequest).filter(HPSRequest.status == 'pending').all()
        print('HPS pendientes disponibles:')
        for hps in pending_hps:
            full_name = f'{hps.first_name} {hps.first_last_name}'
            print(f'  - Nombre completo: "{full_name}"')
            print(f'    Primer nombre: "{hps.first_name}"')
            print(f'    Apellido: "{hps.first_last_name}"')
            print(f'    Email: {hps.email}')
            print()
    finally:
        db.close()

if __name__ == "__main__":
    check_hps_names()
