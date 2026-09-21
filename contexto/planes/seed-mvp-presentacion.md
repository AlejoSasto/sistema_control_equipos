# Datos MVP / catálogos institucionales

| Campo | Valor |
|-------|--------|
| **Estado** | Completado |
| **Fecha** | 2026-09-21 |
| **Comando** | `python manage.py seed_data` |
| **Fuente org.** | `seed_organizacion_data.py` (Excel `data/Universidad_de_Cundinamarca_Info.xlsx`) |
| **Deploy** | Corre automáticamente en `entrypoint.sh` tras `migrate` |

## Qué carga

| Catálogo | Contenido |
|----------|-----------|
| Sedes | 7 activas (Fusagasugá, Girardot, Ubaté, Chía, Facatativá, Soacha, Zipaquirá) |
| Facultades | 7 activas |
| Programas | 45 pregrados por sede/facultad |
| Áreas | 8 dependencias (CGCA, ISU, CTeI, etc.) |
| Tipo de vínculo | 6 canónicos: 4 comunidad + `personal_externo` + `vigilante` |
| Roles activos | `admin_sistema`, `miembro_comunidad`, `responsable_dependencia`, `vigilante` |
| Permisos | Catálogo completo (incl. inventario/asignación institucional y reportes) |

## Qué desactiva / limpia

- Tipos legado de migración `0002`: `estudiante`, `graduado`, `administrativo`, `docente` (`activo=False`)
- Usuarios demo `celador1`, `docente1`
- Personas y equipos de demostración
- Rol `celador` queda **inactivo** (usar `vigilante`)

## Acceso

- Usuario: `admin`
- Contraseña inicial: `Udec2026!Admin` (solo al **crear** el usuario; re-ejecutar seed no la resetea)
