# Checklist: backups PostgreSQL y prueba de restauración

**Estado:** Vigente  
**Fecha:** 2026-09-19  
**Referencia:** ISO/IEC 27001 A.8.13 · Plan de seguridad §9 Fase S3

## Objetivo

Garantizar que la base de datos del sistema (datos personales, equipos, movimientos, auditoría) tenga copias cifradas y una restauración probada al menos una vez.

## Checklist operativo (hosting)

- [ ] Backup automático diario de PostgreSQL habilitado en el proveedor (Railway / Render / VPS)
- [ ] Retención mínima definida (recomendado: 7–30 días)
- [ ] Backups cifrados en reposo (cifrado del proveedor o archivo `pg_dump` + GPG)
- [ ] Acceso a backups restringido al personal de TI autorizado
- [ ] Credenciales de restauración almacenadas fuera del repositorio de código

## Prueba de restauración (ejecutar al menos 1 vez por semestre)

1. Tomar un backup reciente.
2. Restaurar en un entorno **no productivo** (staging o máquina local aislada).
3. Verificar:
   - [ ] La aplicación arranca contra la BD restaurada
   - [ ] Existen usuarios, personas y equipos esperados
   - [ ] La tabla `auditoria_cambio` tiene registros coherentes
4. Documentar fecha, responsable y resultado (OK / fallos) en bitácora de TI.

## Comandos de referencia (local / VPS)

```bash
# Volcado (ejemplo)
pg_dump -Fc -h $DB_HOST -U $DB_USER $DB_NAME > backup_$(date +%Y%m%d).dump

# Restauración en entorno de prueba
pg_restore -h $DB_HOST_TEST -U $DB_USER -d $DB_NAME_TEST --clean backup_YYYYMMDD.dump
```

> No ejecutar restauración destructiva contra producción sin ventana de mantenimiento aprobada.
