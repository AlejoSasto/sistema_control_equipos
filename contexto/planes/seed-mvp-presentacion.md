# Datos MVP / catálogos institucionales

| Campo | Valor |
|-------|--------|
| **Estado** | Completado |
| **Fecha** | 2026-09-19 |
| **Comando** | `python manage.py seed_data` |
| **Fuente org.** | `seed_organizacion_data.py` (Excel `data/Universidad_de_Cundinamarca_Info.xlsx`) |

## Qué carga

| Catálogo | Contenido |
|----------|-----------|
| Sedes | 7 activas (Fusagasugá, Girardot, Ubaté, Chía, Facatativá, Soacha, Zipaquirá) |
| Facultades | 7 activas |
| Programas | 45 pregrados por sede/facultad |
| Áreas | 8 dependencias (CGCA, ISU, CTeI, etc.) |
| Tipo de vínculo | 4 activos: gestor_administrativo, creador_oportunidades, gestor_conocimiento, egresado |
| Roles activos | Administrador del sistema, Miembro de la comunidad |
| Permisos | 13 permisos con descripción en español |

## Qué elimina

- Usuarios demo `celador1`, `docente1`
- Personas y equipos de demostración
- Rol celador queda **inactivo**

## Acceso

- Usuario: `admin`
- Contraseña: `Udec2026!Admin`
