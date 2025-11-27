"""
Esquemas Pydantic para la API de HPS (Habilitación Personal de Seguridad)
"""
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator
from enum import Enum


class HPSRequestType(str, Enum):
    NEW = "new"
    RENEWAL = "renewal"
    TRANSFER = "transfer"


class HPSStatus(str, Enum):
    PENDING = "pending"           # Solicitud creada, pendiente de envío
    WAITING_DPS = "waiting_dps"   # En espera DPS
    SUBMITTED = "submitted"       # Enviada a entidad externa, esperando respuesta
    APPROVED = "approved"         # Aprobada por la entidad externa
    REJECTED = "rejected"         # Rechazada por la entidad externa
    EXPIRED = "expired"           # HPS expirada (para las aprobadas)


# Enums eliminados - ahora se usan strings directamente para mayor flexibilidad
# Los valores válidos se definen en el frontend (hpsOptions.js)

# class DocumentType(str, Enum):
# class Nationality(str, Enum):
class HPSRequestCreate(BaseModel):
    """Esquema para crear una nueva solicitud HPS"""
    request_type: HPSRequestType = Field(..., description="Tipo de solicitud HPS")
    
    # Datos personales del formulario (11 campos obligatorios)
    document_type: str = Field(..., description="Tipo de documento")
    document_number: str = Field(..., min_length=1, max_length=50, description="Número de documento")
    birth_date: date = Field(..., description="Fecha de nacimiento")
    first_name: str = Field(..., min_length=1, max_length=100, description="Nombre")
    first_last_name: str = Field(..., min_length=1, max_length=100, description="Primer apellido")
    second_last_name: Optional[str] = Field(None, max_length=100, description="Segundo apellido")
    nationality: str = Field(..., description="Nacionalidad")
    birth_place: str = Field(..., min_length=1, max_length=255, description="Lugar de nacimiento")
    email: EmailStr = Field(..., description="Correo electrónico")
    phone: str = Field(..., min_length=1, max_length=50, description="Teléfono")
    
    # Metadatos opcionales
    user_id: Optional[str] = Field(None, description="ID del usuario (si se especifica)")

    @validator('birth_date')
    def validate_birth_date(cls, v):
        """Validar que la fecha de nacimiento sea válida"""
        if v >= date.today():
            raise ValueError('La fecha de nacimiento debe ser anterior a hoy')
        
        # Validar edad mínima (18 años)
        from datetime import datetime
        age = (date.today() - v).days // 365.25
        if age < 18:
            raise ValueError('El usuario debe ser mayor de 18 años')
        
        return v

    @validator('document_number')
    def validate_document_number(cls, v):
        """Validar formato del número de documento"""
        if not v.replace('-', '').replace(' ', '').isalnum():
            raise ValueError('El número de documento solo puede contener letras, números, guiones y espacios')
        return v.strip().upper()

    @validator('phone')
    def validate_phone(cls, v):
        """Validar formato básico del teléfono"""
        cleaned = v.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('+', '')
        if not cleaned.isdigit():
            raise ValueError('El teléfono debe contener solo números, espacios, guiones, paréntesis y el símbolo +')
        if len(cleaned) < 9 or len(cleaned) > 15:
            raise ValueError('El teléfono debe tener entre 9 y 15 dígitos')
        return v.strip()


class HPSRequestUpdate(BaseModel):
    """Esquema para actualizar una solicitud HPS"""
    status: Optional[HPSStatus] = Field(None, description="Estado de la solicitud")
    expires_at: Optional[date] = Field(None, description="Fecha de expiración")
    notes: Optional[str] = Field(None, description="Notas adicionales")

    @validator('expires_at')
    def validate_expires_at(cls, v):
        """Validar que la fecha de expiración sea futura"""
        if v and v <= date.today():
            raise ValueError('La fecha de expiración debe ser futura')
        return v


class UserInfo(BaseModel):
    """Información básica del usuario para respuestas"""
    id: str
    email: str
    first_name: str
    last_name: str
    full_name: str

    class Config:
        from_attributes = True


class HPSRequestResponse(BaseModel):
    """Esquema de respuesta para solicitudes HPS"""
    id: str
    user_id: str
    request_type: HPSRequestType
    status: HPSStatus
    type: str  # Campo para distinguir entre solicitud y traslado
    
    # Datos personales
    document_type: str
    document_number: str
    birth_date: date
    first_name: str
    first_last_name: str
    second_last_name: Optional[str]
    nationality: str
    birth_place: str
    email: str
    phone: str
    
    # Metadatos
    submitted_by: str
    submitted_at: datetime
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    expires_at: Optional[date]
    notes: Optional[str]
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    # Propiedades calculadas
    is_expired: bool
    can_be_approved: bool
    
    # Información de usuarios relacionados
    user: Optional[UserInfo] = None
    submitted_by_user: Optional[UserInfo] = None
    approved_by_user: Optional[UserInfo] = None
    
    # Credenciales temporales (solo cuando se crea un nuevo usuario)
    temp_password: Optional[str] = None
    user_created: bool = False

    class Config:
        from_attributes = True

    @classmethod
    def from_hps_request(cls, hps_request, include_user_details: bool = True, temp_password: str = None, user_created: bool = False):
        """Crear respuesta desde el modelo HPSRequest"""
        # Propiedades calculadas
        is_expired = hps_request.is_expired if hasattr(hps_request, 'is_expired') else False
        can_be_approved = hps_request.can_be_approved if hasattr(hps_request, 'can_be_approved') else False
        
        # Información de usuarios relacionados
        user_info = None
        submitted_by_info = None
        approved_by_info = None
        
        if include_user_details:
            if hasattr(hps_request, 'user') and hps_request.user:
                user_info = UserInfo(
                    id=str(hps_request.user.id),
                    email=hps_request.user.email,
                    first_name=hps_request.user.first_name,
                    last_name=hps_request.user.last_name,
                    full_name=f"{hps_request.user.first_name} {hps_request.user.last_name}".strip()
                )
            
            if hasattr(hps_request, 'submitted_by_user') and hps_request.submitted_by_user:
                submitted_by_info = UserInfo(
                    id=str(hps_request.submitted_by_user.id),
                    email=hps_request.submitted_by_user.email,
                    first_name=hps_request.submitted_by_user.first_name,
                    last_name=hps_request.submitted_by_user.last_name,
                    full_name=f"{hps_request.submitted_by_user.first_name} {hps_request.submitted_by_user.last_name}".strip()
                )
            
            if hasattr(hps_request, 'approved_by_user') and hps_request.approved_by_user:
                approved_by_info = UserInfo(
                    id=str(hps_request.approved_by_user.id),
                    email=hps_request.approved_by_user.email,
                    first_name=hps_request.approved_by_user.first_name,
                    last_name=hps_request.approved_by_user.last_name,
                    full_name=f"{hps_request.approved_by_user.first_name} {hps_request.approved_by_user.last_name}".strip()
                )
        
        return cls(
            id=str(hps_request.id),
            user_id=str(hps_request.user_id),
            request_type=hps_request.request_type,
            status=hps_request.status,
            type=getattr(hps_request, 'type', 'solicitud'),  # Campo type con valor por defecto
            document_type=hps_request.document_type,
            document_number=hps_request.document_number,
            birth_date=hps_request.birth_date,
            first_name=hps_request.first_name,
            first_last_name=hps_request.first_last_name,
            second_last_name=hps_request.second_last_name,
            nationality=hps_request.nationality,
            birth_place=hps_request.birth_place,
            email=hps_request.email,
            phone=hps_request.phone,
            submitted_by=str(hps_request.submitted_by),
            submitted_at=hps_request.submitted_at,
            approved_by=str(hps_request.approved_by) if hps_request.approved_by else None,
            approved_at=hps_request.approved_at,
            expires_at=hps_request.expires_at,
            notes=hps_request.notes,
            created_at=hps_request.created_at,
            updated_at=hps_request.updated_at,
            is_expired=is_expired,
            can_be_approved=can_be_approved,
            user=user_info,
            submitted_by_user=submitted_by_info,
            approved_by_user=approved_by_info,
            temp_password=temp_password,
            user_created=user_created
        )


class HPSRequestList(BaseModel):
    """Esquema para lista paginada de solicitudes HPS"""
    requests: List[HPSRequestResponse]
    total: int
    page: int
    per_page: int
    pages: int

    class Config:
        from_attributes = True


class HPSStatsResponse(BaseModel):
    """Esquema para estadísticas de solicitudes HPS"""
    total_requests: int
    pending_requests: int
    waiting_dps_requests: int
    submitted_requests: int
    approved_requests: int
    rejected_requests: int
    expired_requests: int
    requests_by_type: dict
    recent_requests: List[HPSRequestResponse]

    class Config:
        from_attributes = True


# Diccionarios para mapear códigos a nombres legibles
NATIONALITY_NAMES = {
    "1": "ESPAÑA",
    "2": "DESCONOCIDO",
    "3": "AFGANISTAN",
    "4": "ALBANIA",
    "5": "ALEMANIA",
    "6": "ANDORRA",
    "7": "ANGOLA",
    "8": "ANTIGUA Y BARBUDA",
    "9": "APATRIDA",
    "10": "ARABIA SAUDITA",
    "11": "ARGELIA",
    "12": "ARGENTINA",
    "13": "ARMENIA",
    "14": "ARUBA",
    "15": "AUSTRALIA",
    "16": "AUSTRIA",
    "17": "AZERBAIYAN",
    "18": "BAHAMAS (LAS)",
    "19": "BAHREIN",
    "20": "BANGLADESH",
    "21": "BARBADOS",
    "22": "BELARUS (BIELORRUSIA)",
    "23": "BELGICA",
    "24": "BELICE",
    "25": "BENIN",
    "26": "BERMUDAS",
    "27": "BHUTAN (BUTAN)",
    "28": "BOLIVIA",
    "29": "BOSNIA Y HERZEGOVINA",
    "30": "BOTSWANA (BOSTSUANA)",
    "31": "BRASIL",
    "32": "BRUNEI DARUSSALAM",
    "33": "BULGARIA",
    "34": "BURKINA FASO",
    "35": "BURUNDI",
    "36": "CABO VERDE",
    "37": "CAIMAN, ISLAS",
    "38": "CAMBOYA",
    "39": "CAMERUN",
    "40": "CANADA",
    "41": "CHAD",
    "42": "CHEQUIA (REPUBLICA CHECA)",
    "43": "CHILE",
    "44": "CHINA",
    "45": "CHIPRE",
    "46": "COLOMBIA",
    "47": "CONGO",
    "48": "CONGO (REPUBLICA DEMOCRATICA DEL)",
    "49": "COREA DEL NORTE",
    "50": "COREA DEL SUR",
    "51": "COSTA RICA",
    "52": "COTE D'IVOIRE (COSTA DE MARFIL)",
    "53": "CROACIA",
    "54": "CUBA",
    "55": "DINAMARCA",
    "56": "DJIBOUTI (YIBUTI)",
    "57": "DOMINICA",
    "58": "DOMINICANA (REPUBLICA)",
    "59": "ECUADOR",
    "60": "EGIPTO",
    "61": "EL SALVADOR",
    "62": "EMIRATOS ARABES UNIDOS",
    "63": "ERITREA",
    "64": "ESLOVAQUIA",
    "65": "ESLOVENIA",
    "66": "ESTADOS UNIDOS",
    "67": "ESTONIA",
    "68": "ETIOPIA",
    "69": "FIJI (FIYI)",
    "70": "FILIPINAS",
    "71": "FINLANDIA",
    "72": "FRANCIA",
    "73": "GABON",
    "74": "GAMBIA",
    "75": "GEORGIA",
    "76": "GHANA",
    "77": "GRANADA",
    "78": "GRECIA",
    "79": "GUADALOUPE (GUADALUPE)",
    "80": "GUATEMALA",
    "81": "GUAYANA FRANCESA",
    "82": "GUINEA",
    "83": "GUINEA BISSAU",
    "84": "GUINEA ECUATORIAL",
    "85": "GUYANA",
    "86": "HAITI",
    "87": "HONDURAS",
    "88": "HONG KONG",
    "89": "HUNGRIA",
    "90": "INDIA",
    "91": "INDONESIA",
    "92": "IRAN",
    "93": "IRAQ",
    "94": "IRLANDA",
    "95": "ISLANDIA",
    "96": "ISRAEL",
    "97": "ITALIA",
    "98": "JAMAICA",
    "99": "JAPON",
    "100": "JORDANIA",
    "101": "KAZAJSTAN (KAZAJISTAN)",
    "102": "KENYA (KENIA)",
    "103": "KIRGUISTAN",
    "104": "KIRIBATI",
    "105": "KUWAIT",
    "106": "LAO (LAOS)",
    "107": "LESOTHO",
    "108": "LETONIA",
    "109": "LIBANO",
    "110": "LIBERIA",
    "111": "LIBIA",
    "112": "LIECHTENSTEIN",
    "113": "LITUANIA",
    "114": "LUXEMBURGO",
    "115": "MACEDONIA DEL NORTE",
    "116": "MADAGASCAR",
    "117": "MALASIA",
    "118": "MALAWI (MALAUI)",
    "119": "MALDIVAS",
    "120": "MALI",
    "121": "MALTA",
    "122": "MALVINAS (FALKLAND), ISLAS",
    "123": "MARRUECOS",
    "124": "MAURITANIA",
    "125": "MEXICO",
    "126": "MOLDOVA (MOLDAVIA)",
    "127": "MONACO",
    "128": "MONGOLIA",
    "129": "MONTENEGRO",
    "130": "MOZAMBIQUE",
    "131": "MYANMAR",
    "132": "NAMIBIA",
    "133": "NEPAL",
    "134": "NICARAGUA",
    "135": "NIGER",
    "136": "NIGERIA",
    "137": "NORUEGA",
    "138": "NUEVA ZELANDA",
    "139": "OMAN",
    "140": "PAISES BAJOS",
    "141": "PAKISTAN",
    "142": "PALESTINA",
    "143": "PANAMA",
    "144": "PARAGUAY",
    "145": "PERU",
    "146": "POLINESIA FRANCESA",
    "147": "POLONIA",
    "148": "PORTUGAL",
    "149": "PUERTO RICO",
    "150": "QATAR (CATAR)",
    "151": "REINO UNIDO DE GRAN BRETAÑA E IRLANDA DEL NORTE",
    "152": "REPUBLICA CENTROAFRICANA",
    "153": "RUMANIA",
    "154": "RUSIA",
    "155": "RWANDA (RUANDA)",
    "156": "SAHARA OCCIDENTAL (REPUBLICA ARABE SAHARAUI DEMOCRATICA)",
    "157": "SANTO TOME Y PRINCIPE",
    "158": "SENEGAL",
    "159": "SERBIA",
    "160": "SEYCHELLES",
    "161": "SIERRA LEONA",
    "162": "SINGAPUR",
    "163": "SIRIA",
    "164": "SOMALIA",
    "165": "SRI LANKA (CEILAN)",
    "166": "SUDAFRICA",
    "167": "SUDAN",
    "168": "SUDAN DEL SUR",
    "169": "SUECIA",
    "170": "SUIZA",
    "171": "TAILANDIA",
    "172": "TAIWAN",
    "173": "TANZANIA",
    "174": "TAYIKISTAN",
    "175": "TOGO",
    "176": "TONGA",
    "177": "TRINIDAD Y TOBAGO",
    "178": "TUNEZ",
    "179": "TURKMENISTAN",
    "180": "TURQUIA",
    "181": "UCRANIA",
    "182": "UGANDA",
    "183": "URUGUAY",
    "184": "UZBEKISTAN",
    "185": "VENEZUELA",
    "186": "VIETNAM",
    "187": "YEMEN",
    "188": "ZAMBIA",
    "189": "ZIMBABWE (ZIMBABUE)"
}

DOCUMENT_TYPE_NAMES = {
    "206": "DNI / NIF",
    "207": "NIE",
    "208": "Tarjeta Residente",
    "209": "Pasaporte",
    "210": "Otros"
}
