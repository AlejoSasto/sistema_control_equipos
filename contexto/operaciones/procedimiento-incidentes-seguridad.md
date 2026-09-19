# Procedimiento mínimo de gestión de incidentes de seguridad

**Estado:** Vigente  
**Fecha:** 2026-09-19  
**Referencia:** ISO/IEC 27001 A.5.24–A.5.28 · Ley 1581 de 2012

## 1. Quién se entera

| Rol | Responsabilidad |
|-----|-----------------|
| Administrador del sistema (`admin_sistema`) | Primera contención técnica (revocar sesiones, inactivar cuentas, rotar secretos) |
| Oficina de TI / hosting | Aislar infraestructura, revisar logs del proveedor |
| Oficina jurídica / protección de datos | Evaluar si hay fuga de datos personales y obligación de notificar |

Contacto ARCO / datos personales: el definido en `DATOS_PERSONALES_CONTACTO` (ver `.env.example`).

## 2. Contención (primeras horas)

1. Confirmar el incidente (logs de Axes, `auditoria_cambio`, logs del hosting).
2. Si hay compromiso de cuenta admin: forzar cambio de contraseña, revisar dispositivos MFA, inactivar usuarios sospechosos.
3. Si hay fuga de `SECRET_KEY` o credenciales de BD: rotar secretos, redeploy, invalidar sesiones.
4. Si hay exposición de datos personales: preservar evidencia, no borrar logs, escalar a jurídica.

## 3. Notificación (Ley 1581)

Si se confirma afectación a datos personales de titulares:

1. Documentar qué datos, cuántos registros y vector probable.
2. Coordinar con la universidad la notificación a titulares y, si aplica, a la SIC.
3. Registrar acciones en bitácora interna (quién, cuándo, qué se hizo).

## 4. Recuperación y lecciones

1. Restaurar desde backup verificado si hubo alteración de datos.
2. Cerrar el incidente con informe breve (causa, impacto, acciones).
3. Actualizar controles (parches, rate limits, permisos) según la causa raíz.

## 5. Ítems universitarios (fuera del repositorio)

- [ ] Pentest externo al menos sobre login, panel y kiosco (antes de escalar a ~20.000 usuarios)
- [ ] Validar con jurídica si el volumen obliga inscripción en el RNBD (SIC)
