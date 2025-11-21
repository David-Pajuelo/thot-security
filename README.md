# thot-security

Monorepo inicial que consolida los servicios `cryptotrace` y `hps-system` en un único repositorio antes de abordar la integración técnica. Sirve como **punto cero** para versionar ambos proyectos de forma coordinada y documentar el plan de convergencia.

## Estructura
```
thot-security/
├── cryptotrace/          # Plataforma Django + microservicios OCR/Processing/PDF
├── hps-system/           # Plataforma FastAPI + Celery + agente IA + extensiones
└── AUDITORIA-INTEGRACION-HPS-CRYPTOTRACE.md   # Informe de evaluación y plan
```

## Objetivos del monorepo
- Mantener una referencia común del estado actual de ambos backends.
- Compartir documentación, decisiones de arquitectura y scripts de automatización.
- Facilitar propuestas de integración (Docker Compose combinado, identidad unificada, etc.) sin alterar los repos originales hasta que se aprueben los cambios.

## Cómo crear el repositorio
1. **Inicializar Git en la raíz actual**  
   ```bash
   cd thot-security
   git init
   git branch -m main
   ```
2. **Configurar remotos (ejemplo en GitHub/GitLab)**  
   ```bash
   git remote add origin git@github.com:tu-org/thot-security.git
   ```
3. **Agregar contenido existente**  
   ```bash
   git add .
   git commit -m "chore: punto cero cryptotrace + hps-system"
   git push -u origin main
   ```
4. **(Opcional) Submódulos**: Si se prefiere mantener cada servicio como submódulo conectado a sus repos originales, reemplazar los directorios por submódulos con `git submodule add`.

## Próximos pasos sugeridos
- Mantener sincronizados los cambios procedentes de cada repositorio fuente.
- Crear scripts de bootstrap (entornos virtuales, Docker) compartidos en esta raíz.
- Usar la auditoría (`AUDITORIA-INTEGRACION-HPS-CRYPTOTRACE.md`) para guiar el roadmap y registrar decisiones.

> Nota: Este repositorio no reemplaza a los originales; actúa como capa de coordinación hasta completar la integración.

