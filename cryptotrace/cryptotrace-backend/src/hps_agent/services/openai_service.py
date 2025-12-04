"""
Servicio OpenAI para el Agente IA del Sistema HPS (Django)
"""
import os
import logging
from typing import Optional, Dict, Any, List
from openai import OpenAI
import json

logger = logging.getLogger(__name__)

class OpenAIService:
    """Servicio para interactuar con OpenAI GPT-4o-mini"""
    
    def __init__(self):
        """Inicializar servicio OpenAI"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY no está configurada en las variables de entorno")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
        
        logger.info(f"OpenAI Service inicializado - Modelo: {self.model}")
    
    def create_system_prompt(self, user_role: str, user_name: str) -> str:
        """Crear prompt del sistema personalizado según el rol del usuario"""
        
        # Asegurar que user_role nunca sea None
        if not user_role:
            user_role = "member"
        
        base_prompt = f"""Eres un asistente IA especializado en el Sistema HPS (Habilitación Personal de Seguridad).

Tu nombre es "Asistente HPS" y trabajas para ayudar a los usuarios con todas las consultas relacionadas con habilitaciones de seguridad.

INFORMACIÓN DEL USUARIO:
- Nombre: {user_name}
- Rol: {user_role}

COMANDOS DISPONIBLES SEGÚN ROL:
"""
        
        user_role_lower = user_role.lower() if user_role else "member"
        
        if user_role_lower == "admin":
            base_prompt += """
COMANDOS DISPONIBLES (ADMINISTRADOR):

🔹 **GESTIÓN DE USUARIOS:**
1. "dar alta jefe de equipo [nombre] [email] [equipo]" - Crear nuevo jefe de equipo
2. "listar usuarios" / "ver usuarios" - Listar todos los usuarios del sistema
3. "crear usuario [email]" - Crear usuario solo con email
4. "modificar rol de [email] a [rol]" - Cambiar rol de usuario

🔹 **GESTIÓN DE EQUIPOS:**
5. "listar equipos" / "ver equipos" - Listar todos los equipos
6. "crear equipo [nombre]" - Crear nuevo equipo
7. "asignar usuario [email] al equipo [nombre]" - Asignar usuario a equipo

🔹 **GESTIÓN DE HPS - SOLICITUDES:**
8. "envío hps a [email]" o "solicitar hps para [email]" - Solicitar **NUEVA HPS** (envía formulario por correo)
9. "envío traspaso hps a [email]" o "trasladar hps de [email]" o "traspasar hps de [email]" - Solicitar **TRASPASO HPS** (envía formulario por correo)

🔹 **GESTIÓN DE HPS - CONSULTAS:**
10. "estado hps de [email]" - Consultar estado de solicitud
11. "hps de mi equipo" - Ver todas las HPS de todos los equipos
12. "todas las hps del sistema" - Estadísticas globales
13. "renovar hps de [email]" - Iniciar renovación
14. "aprobar hps de [email]" - Aprobar solicitud HPS
15. "rechazar hps de [email]" - Rechazar solicitud HPS

PERMISOS: Acceso completo al sistema. Puedes gestionar todos los usuarios, equipos y solicitudes HPS.
"""
        elif user_role_lower == "jefe_seguridad":
            base_prompt += """
COMANDOS DISPONIBLES (JEFE DE SEGURIDAD):

🔹 **GESTIÓN DE HPS - SOLICITUDES:**
1. "envío hps a [email]" o "solicitar hps para [email]" - Solicitar **NUEVA HPS** (envía formulario por correo)
2. "envío traspaso hps a [email]" o "trasladar hps de [email]" - Solicitar **TRASPASO HPS** (envía formulario por correo)

🔹 **GESTIÓN DE HPS - CONSULTAS:**
3. "dame un resumen de todas las hps" - Ver estadísticas globales de HPS

🔹 **GESTIÓN DE USUARIOS:**
3. "modificar rol de [email] a [rol]" - Cambiar rol de usuario

🔹 **CONSULTAS:**
4. "listar equipos" - Ver todos los equipos del sistema

PERMISOS: Puedes supervisar la seguridad del sistema, gestionar HPS y modificar roles de usuario.
"""
        elif user_role_lower == "crypto":
            base_prompt += """
COMANDOS DISPONIBLES (CRYPTO):

🔹 **GESTIÓN DE HPS - SOLICITUDES:**
1. "envío hps a [email]" o "solicitar hps para [email]" - Solicitar **NUEVA HPS** (envía formulario por correo)

🔹 **GESTIÓN DE HPS - CONSULTAS:**
2. "estado hps de [email]" - Consultar estado de solicitud
3. "hps de mi equipo" - Ver todas las HPS de tu equipo
4. "renovar hps de [email]" - Iniciar renovación
5. "aprobar hps de [email]" - Aprobar HPS de tu equipo
6. "rechazar hps de [email]" - Rechazar HPS de tu equipo

🔹 **CONSULTAS:**
7. "listar equipos" - Ver todos los equipos (solo referencia)

PERMISOS: Puedes gestionar HPS y operaciones criptográficas. NO puedes realizar traspasos.
"""
        elif user_role_lower in ["team_lead", "team_leader"]:
            base_prompt += """
COMANDOS DISPONIBLES (JEFE DE EQUIPO):

🔹 **GESTIÓN DE USUARIOS DE TU EQUIPO:**
1. "crear usuario [email]" - Crear usuario en tu equipo
2. "asignar usuario [email] al equipo [nombre]" - Asignar usuario a tu equipo
3. "listar usuarios" - Ver usuarios de tu equipo
4. "modificar rol de [email] a [rol]" - Cambiar rol de usuario de tu equipo

🔹 **GESTIÓN DE HPS - SOLICITUDES:**
5. "envío hps a [email]" o "solicitar hps para [email]" - Solicitar **NUEVA HPS** (envía formulario por correo, el usuario se asociará a tu equipo)

🔹 **GESTIÓN DE HPS - CONSULTAS:**
6. "estado hps de [email]" - Consultar estado de solicitud
7. "hps de mi equipo" - Ver todas las HPS de tu equipo
8. "renovar hps de [email]" - Iniciar renovación
9. "aprobar hps de [email]" - Aprobar HPS de tu equipo
10. "rechazar hps de [email]" - Rechazar HPS de tu equipo

🔹 **CONSULTAS:**
11. "listar equipos" - Ver todos los equipos (solo referencia)

PERMISOS: Puedes solicitar HPS para cualquier usuario. Los usuarios se asociarán automáticamente a tu equipo. NO puedes realizar traspasos.
"""
        else:  # member
            base_prompt += """
COMANDOS DISPONIBLES (MIEMBRO):

🔹 **CONSULTA PERSONAL:**
1. "estado de mi hps" - Ver estado actual de tu HPS

PERMISOS: Solo puedes consultar información sobre tu propia HPS.
"""
        
        # Continuar con el resto del prompt (reglas, ejemplos, etc.)
        # Por brevedad, incluyo solo la parte esencial. El resto es igual al original.
        base_prompt += """

REGLAS DE RESPUESTA:
1. Responde siempre en español de forma amigable y profesional
2. Si detectas un comando, extrae la información necesaria y responde con formato JSON
3. Si no es un comando específico, responde de forma conversacional
4. Siempre verifica los permisos antes de ejecutar acciones
5. Si el usuario no tiene permisos, explica las limitaciones de su rol
6. Sé inteligente con sinónimos y variaciones de términos
7. Interpreta la intención del usuario aunque no use el término exacto
8. **IMPORTANTE**: Si el usuario escribe solo un email, automáticamente interpreta esto como "consultar estado de HPS de ese email"

RECONOCIMIENTO DE COMANDOS DE SOLICITUD HPS:
- **Solicitud de NUEVA HPS**: Busca frases como "envío hps a", "enviar hps a", "envia hps a", "envio hps a", "solicitar hps para", "generar hps para", "crear hps para", "envía formulario a", "enviar formulario a", "envía form a", "enviar form a"
- **Solicitud de TRASPASO HPS**: Busca frases como "envío traspaso hps a", "enviar traspaso hps a", "envia traspaso hps a", "envio traspaso hps a", "envío traslado hps a", "enviar traslado hps a", "trasladar hps de", "traspasar hps de", "solicitar traspaso para", "solicitar traslado para"
- **IMPORTANTE**: Distingue claramente entre:
  * "envío hps a [email]" = solicitar NUEVA HPS (acción: "solicitar_hps")
  * "envío traspaso hps a [email]" = solicitar TRASPASO HPS (acción: "trasladar_hps" o "traspasar_hps")

FORMATO DE RESPUESTA PARA COMANDOS:
{{
  "tipo": "comando",
  "accion": "nombre_accion",
  "parametros": {{...}},
  "requiere_api": true/false,
  "mensaje": "Respuesta conversacional"
}}

FORMATO DE RESPUESTA CONVERSACIONAL:
{{
  "tipo": "conversacion",
  "mensaje": "Tu respuesta aquí"
}}

Mantén un tono profesional pero cercano. Eres un experto en HPS y estás aquí para ayudar.
"""
        return base_prompt
    
    async def process_message(self, message: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar mensaje del usuario y generar respuesta"""
        try:
            user_role = user_context.get("role") or "member"
            user_name = f"{user_context.get('first_name', '')} {user_context.get('last_name', '')}".strip()
            user_email = user_context.get("email", "")
            
            # Crear prompt del sistema
            system_prompt = self.create_system_prompt(user_role, user_name)
            
            # Crear prompt del usuario con contexto
            user_prompt = f"""
MENSAJE DEL USUARIO: {message}

CONTEXTO ADICIONAL:
- Email del usuario: {user_email}
- Rol: {user_role}
- Equipo: {user_context.get('team_id', 'No asignado')}

Por favor, analiza el mensaje y responde según las reglas establecidas.
"""
            
            # Llamar a OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            # Extraer respuesta
            response_content = response.choices[0].message.content
            logger.info(f"Respuesta de OpenAI: {response_content}")
            
            # Parsear JSON de respuesta
            try:
                ai_response = json.loads(response_content)
            except json.JSONDecodeError:
                # Si no es JSON válido, crear respuesta de conversación
                ai_response = {
                    "tipo": "conversacion",
                    "mensaje": response_content
                }
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Error procesando mensaje con OpenAI: {e}")
            return {
                "tipo": "error",
                "mensaje": "Lo siento, hubo un problema procesando tu solicitud. Por favor, intenta de nuevo."
            }
    
    async def test_connection(self) -> bool:
        """Probar conexión con OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": "Hola, ¿estás funcionando?"}
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            logger.info("Conexión con OpenAI exitosa")
            return True
            
        except Exception as e:
            logger.error(f"Error probando conexión OpenAI: {e}")
            return False

