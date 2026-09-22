"""Agregados y presets del dashboard de administrador (doc 13)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from django.conf import settings
from django.core.cache import cache
from django.db.models import Count
from django.db.models.functions import TruncDay, TruncHour
from django.utils import timezone

from control_acceso.models import Movimiento
from equipos.models import Equipo
from personas.models import Persona
from reportes.filtros import (
    FiltroError,
    FiltroFecha,
    FiltroResultado,
    FiltroSede,
    FiltroTipoVinculo,
    acotar_por_alcance,
)
from reportes.umbrales import MAX_DIAS_MOVIMIENTOS

PRESETS = ("hoy", "ayer", "7d", "mes", "custom")


@dataclass
class DashboardFiltros:
    preset: str
    fecha: FiltroFecha
    sede: FiltroSede
    vinculo: FiltroTipoVinculo
    resultado: FiltroResultado

    def cache_key(self, prefijo: str) -> str:
        payload = {
            "preset": self.preset,
            "fecha": self.fecha.como_dict(),
            "sede": self.sede.como_dict(),
            "vinculo": self.vinculo.como_dict(),
            "resultado": self.resultado.como_dict(),
        }
        digest = hashlib.md5(
            json.dumps(payload, sort_keys=True, default=str).encode(),
            usedforsecurity=False,
        ).hexdigest()
        return f"dash:{prefijo}:{digest}"

    def query_params(self) -> dict[str, Any]:
        params: dict[str, Any] = {"preset": self.preset}
        if self.preset == "custom":
            params["fecha_inicio"] = self.fecha.fecha_inicio.isoformat() if self.fecha.fecha_inicio else ""
            params["fecha_fin"] = self.fecha.fecha_fin.isoformat() if self.fecha.fecha_fin else ""
        if self.sede.sede_id:
            params["sede"] = self.sede.sede_id
        if self.vinculo.ids:
            params["tipo_vinculo"] = self.vinculo.ids
        if self.resultado.resultados:
            params["resultado"] = self.resultado.resultados
        return params


def _rango_preset(preset: str) -> tuple[date, date]:
    hoy = timezone.localdate()
    if preset == "hoy":
        return hoy, hoy
    if preset == "ayer":
        ayer = hoy - timedelta(days=1)
        return ayer, ayer
    if preset == "7d":
        return hoy - timedelta(days=6), hoy
    if preset == "mes":
        return hoy.replace(day=1), hoy
    raise FiltroError(f"Preset de fecha inválido: {preset}")


def parse_dashboard_filtros(data) -> DashboardFiltros:
    preset = (data.get("preset") or "hoy").strip().lower()
    if preset not in PRESETS:
        raise FiltroError("Preset de fecha inválido.")

    if preset == "custom":
        fecha = FiltroFecha.from_data(data, obligatorio=True, max_dias=MAX_DIAS_MOVIMIENTOS)
        fecha.validar()
    else:
        inicio, fin = _rango_preset(preset)
        fecha = FiltroFecha(
            fecha_inicio=inicio,
            fecha_fin=fin,
            obligatorio=True,
            max_dias=MAX_DIAS_MOVIMIENTOS,
        )
        fecha.validar()

    sede = FiltroSede.from_data(data, lookup="equipo__persona__sede_id")
    vinculo = FiltroTipoVinculo.from_data(data, lookup="equipo__persona__tipo_vinculo_id__in")
    resultado = FiltroResultado.from_data(data)
    return DashboardFiltros(
        preset=preset,
        fecha=fecha,
        sede=sede,
        vinculo=vinculo,
        resultado=resultado,
    )


def _movimientos_filtrados(user, filtros: DashboardFiltros):
    qs = Movimiento.objects.all()
    qs = filtros.fecha.aplicar(qs, campo="timestamp")
    qs = filtros.sede.aplicar(qs)
    qs = filtros.vinculo.aplicar(qs)
    qs = filtros.resultado.aplicar(qs)
    return acotar_por_alcance(user, qs)


def kpis_estructurales() -> dict[str, int]:
    ttl = getattr(settings, "DASHBOARD_CACHE_TTL_ESTRUCTURAL", 300)

    def _calc():
        return {
            "equipos_activos": Equipo.objects.filter(activo=True).count(),
            "personas_activas": Persona.objects.filter(activo=True).count(),
        }

    return cache.get_or_set("dash:estructurales", _calc, ttl)


def kpis_periodo(user, filtros: DashboardFiltros) -> dict[str, Any]:
    ttl = getattr(settings, "DASHBOARD_CACHE_TTL", 45)
    umbral = getattr(settings, "DASHBOARD_ALERTA_UMBRAL", 0.05)
    key = filtros.cache_key(f"kpis:u{getattr(user, 'pk', 0)}")

    def _calc():
        qs = _movimientos_filtrados(user, filtros)
        total = qs.count()
        alertas = qs.filter(resultado=Movimiento.RESULTADO_ALERTA).count()
        pct = (alertas / total) if total else 0.0

        por_sede = (
            qs.exclude(equipo__persona__sede__isnull=True)
            .values("equipo__persona__sede__nombre")
            .annotate(n=Count("id"))
            .order_by("-n")
        )
        sedes_con_datos = list(por_sede)
        sede_lider = None
        if len(sedes_con_datos) > 1:
            sede_lider = {
                "nombre": sedes_con_datos[0]["equipo__persona__sede__nombre"],
                "movimientos": sedes_con_datos[0]["n"],
            }

        return {
            "movimientos": total,
            "alertas": alertas,
            "alertas_pct": round(pct * 100, 1),
            "alertas_sobre_umbral": pct > umbral,
            "umbral_pct": round(umbral * 100, 1),
            "sede_lider": sede_lider,
        }

    return cache.get_or_set(key, _calc, ttl)


def series_graficos(user, filtros: DashboardFiltros) -> dict[str, Any]:
    ttl = getattr(settings, "DASHBOARD_CACHE_TTL", 45)
    key = filtros.cache_key(f"series:u{getattr(user, 'pk', 0)}")

    def _calc():
        qs = _movimientos_filtrados(user, filtros)
        inicio = filtros.fecha.fecha_inicio
        fin = filtros.fecha.fecha_fin
        un_dia = inicio is not None and fin is not None and inicio == fin

        # Línea temporal
        if un_dia:
            trunc = TruncHour("timestamp")
            label_fmt = "%H:00"
        else:
            trunc = TruncDay("timestamp")
            label_fmt = "%d/%m"

        serie_tiempo = (
            qs.annotate(bucket=trunc)
            .values("bucket")
            .annotate(n=Count("id"))
            .order_by("bucket")
        )
        labels_tiempo = []
        valores_tiempo = []
        for row in serie_tiempo:
            bucket = row["bucket"]
            if bucket is None:
                continue
            local = timezone.localtime(bucket) if timezone.is_aware(bucket) else bucket
            labels_tiempo.append(local.strftime(label_fmt))
            valores_tiempo.append(row["n"])

        # Dona resultados
        por_resultado = {
            r["resultado"]: r["n"]
            for r in qs.values("resultado").annotate(n=Count("id"))
        }
        dona = {
            "labels": ["OK", "Alerta", "No encontrado"],
            "values": [
                por_resultado.get(Movimiento.RESULTADO_OK, 0),
                por_resultado.get(Movimiento.RESULTADO_ALERTA, 0),
                por_resultado.get(Movimiento.RESULTADO_NO_ENCONTRADO, 0),
            ],
            "colors": ["#007B3E", "#C62828", "#5B615D"],
        }

        # Barras por sede
        por_sede = (
            qs.values("equipo__persona__sede__nombre")
            .annotate(n=Count("id"))
            .order_by("-n")
        )
        labels_sede = []
        valores_sede = []
        for row in por_sede:
            nombre = row["equipo__persona__sede__nombre"] or "(Sin sede)"
            labels_sede.append(nombre)
            valores_sede.append(row["n"])

        # Top 5 personas con alertas
        alertas_qs = qs.filter(resultado=Movimiento.RESULTADO_ALERTA)
        top = (
            alertas_qs.exclude(equipo__persona__isnull=True)
            .values("equipo__persona__nombres", "equipo__persona__apellidos")
            .annotate(n=Count("id"))
            .order_by("-n")[:5]
        )
        labels_top = []
        valores_top = []
        for row in top:
            labels_top.append(
                f"{row['equipo__persona__nombres']} {row['equipo__persona__apellidos']}".strip()
            )
            valores_top.append(row["n"])

        # Desglose por motivo_alerta (doc 15)
        por_motivo = (
            alertas_qs.exclude(motivo_alerta__isnull=True)
            .exclude(motivo_alerta="")
            .values("motivo_alerta")
            .annotate(n=Count("id"))
            .order_by("-n")
        )
        motivo_labels_map = dict(Movimiento.OPCIONES_MOTIVO_ALERTA)
        labels_motivo = []
        valores_motivo = []
        for row in por_motivo:
            labels_motivo.append(
                motivo_labels_map.get(row["motivo_alerta"], row["motivo_alerta"])
            )
            valores_motivo.append(row["n"])

        return {
            "agrupacion": "hora" if un_dia else "dia",
            "linea": {
                "labels": labels_tiempo,
                "values": valores_tiempo,
                "vacio": not valores_tiempo,
            },
            "dona": {
                **dona,
                "vacio": sum(dona["values"]) == 0,
            },
            "sedes": {
                "labels": labels_sede,
                "values": valores_sede,
                "vacio": not valores_sede,
            },
            "top_alertas": {
                "labels": labels_top,
                "values": valores_top,
                "vacio": not valores_top,
            },
            "motivos_alerta": {
                "labels": labels_motivo,
                "values": valores_motivo,
                "vacio": not valores_motivo,
            },
        }

    return cache.get_or_set(key, _calc, ttl)


def contexto_kpis(user, filtros: DashboardFiltros) -> dict[str, Any]:
    periodo = kpis_periodo(user, filtros)
    estructural = kpis_estructurales()
    return {
        "filtros": filtros,
        "preset": filtros.preset,
        "fecha_inicio": filtros.fecha.fecha_inicio,
        "fecha_fin": filtros.fecha.fecha_fin,
        **periodo,
        **estructural,
    }
