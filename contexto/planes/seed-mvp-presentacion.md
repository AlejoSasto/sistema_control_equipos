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
| Tipo de vínculo | 4 activos con autorregistro: gestor_administrativo (área la asigna admin después), creador_oportunidades, gestor_conocimiento, egresado |
| Roles activos | admin_sistema, miembro_comunidad, responsable_dependencia |
| Permisos | 16 (incluye inventario/asignación institucional) |

## Qué elimina

- Usuarios demo `celador1`, `docente1`
- Personas y equipos de demostración
- Rol celador queda **inactivo**

## Acceso

- Usuario: `admin`
- Contraseña: `Udec2026!Admin`
