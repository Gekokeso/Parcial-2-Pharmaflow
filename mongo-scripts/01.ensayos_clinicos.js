db = db.getSiblingDB('pharmaflow');

// Crear colección de ensayos clínicos
db.createCollection("ensayos_clinicos");

// Crear índices para búsqueda eficiente
db.ensayos_clinicos.createIndex({ "farmaco": 1 });
db.ensayos_clinicos.createIndex({ "fase": 1 });
db.ensayos_clinicos.createIndex({ "fecha_inicio": 1 });
db.ensayos_clinicos.createIndex({ "estado": 1 });

// Insertar datos de ejemplo de ensayos clínicos
db.ensayos_clinicos.insertMany([
    {
        codigo_ensayo: "PF-CL-2024-001",
        farmaco: "InnovaStat",
        principio_activo: "estatina_nueva_generacion",
        fase: 3,
        fecha_inicio: ISODate("2024-01-15T00:00:00Z"),
        fecha_fin_estimada: ISODate("2024-12-20T00:00:00Z"),
        estado: "en_curso",
        objetivo_principal: "Evaluar eficacia en reducción de colesterol LDL",
        criterios_inclusion: {
            edad_minima: 18,
            edad_maxima: 75,
            condiciones_medicas: ["hipertension", "diabetes_tipo2", "dislipidemia"],
            exclusiones: ["embarazo", "enfermedad_hepatica"]
        },
        centros_participantes: [
            {
                nombre: "Hospital Central de Madrid",
                ciudad: "Madrid",
                investigador_principal: "Dr. Rodríguez",
                pacientes_reclutados: 150,
                meta_pacientes: 200
            },
            {
                nombre: "Clínica Universitaria Barcelona",
                ciudad: "Barcelona", 
                investigador_principal: "Dra. Martínez",
                pacientes_reclutados: 120,
                meta_pacientes: 180
            }
        ],
        resultados_intermedios: {
            efectividad_global: 87.5,
            efectos_secundarios_frecuentes: [
                {
                    tipo: "cefalea",
                    frecuencia: "15%",
                    severidad: "leve",
                    duracion_promedio: "2-3 días"
                },
                {
                    tipo: "nauseas",
                    frecuencia: "8%", 
                    severidad: "leve",
                    duracion_promedio: "1-2 días"
                }
            ],
            abandonos_tratamiento: 12,
            motivo_abandonos: ["efectos secundarios", "problemas logísticos"]
        },
        documentos_adjuntos: [
            {
                nombre: "protocolo_estudio_v3.pdf",
                tipo: "protocolo",
                fecha_subida: ISODate("2024-01-10T10:00:00Z"),
                tamaño: 2540000,
                version: "3.0"
            },
            {
                nombre: "formulario_consentimiento.pdf",
                tipo: "consentimiento", 
                fecha_subida: ISODate("2024-01-12T14:30:00Z"),
                tamaño: 1200000,
                version: "1.2"
            }
        ],
        metadata: {
            creado_por: "investigador_maria",
            fecha_creacion: ISODate("2024-01-10T10:00:00Z"),
            ultima_modificacion: ISODate("2024-06-15T14:30:00Z"),
            version_documento: 4
        }
    },
    {
        codigo_ensayo: "PF-CL-2024-002",
        farmaco: "NeuroCalm",
        principio_activo: "ansiolitico_novedoso",
        fase: 2,
        fecha_inicio: ISODate("2024-03-01T00:00:00Z"),
        fecha_fin_estimada: ISODate("2025-03-01T00:00:00Z"),
        estado: "reclutamiento",
        objetivo_principal: "Evaluar seguridad y eficacia en trastorno de ansiedad generalizada",
        criterios_inclusion: {
            edad_minima: 20,
            edad_maxima: 65,
            condiciones_medicas: ["tag", "ansiedad_cronica"],
            exclusiones: ["depresion_mayor", "uso_benzodiacepinas"]
        },
        centros_participantes: [
            {
                nombre: "Instituto Psiquiátrico Nacional",
                ciudad: "Madrid",
                investigador_principal: "Dr. Sánchez",
                pacientes_reclutados: 45,
                meta_pacientes: 100
            }
        ],
        resultados_intermedios: {
            efectividad_global: null,
            efectos_secundarios_frecuentes: [],
            abandonos_tratamiento: 3,
            motivo_abandonos: ["cambio_domicilio"]
        },
        documentos_adjuntos: [
            {
                nombre: "protocolo_neurocalm_v2.pdf",
                tipo: "protocolo",
                fecha_subida: ISODate("2024-02-15T09:00:00Z"),
                tamaño: 3100000,
                version: "2.1"
            }
        ],
        metadata: {
            creado_por: "investigador_maria",
            fecha_creacion: ISODate("2024-02-15T09:00:00Z"),
            ultima_modificacion: ISODate("2024-05-20T11:15:00Z"),
            version_documento: 3
        }
    }
]);

// Crear colección para cache de informes
db.createCollection("cache_informes");

// Índices para cache
db.cache_informes.createIndex({ "tipo_informe": 1 });
db.cache_informes.createIndex({ "fecha_creacion": 1 }, { expireAfterSeconds: 3600 }); // Expira en 1 hora

print("Base de datos MongoDB inicializada con éxito");