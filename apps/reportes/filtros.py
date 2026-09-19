"""Filtros reutilizables para reportes Excel."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Any

from django.db.models import QuerySet
from django.utils import timezone

from control_acceso.models import Movimiento
from reportes.umbrales import MAX_DIAS_MOVIMIENTOS


class FiltroError(ValueError):
    """Error de validación de filtros de reporte."""


def _parse_date(valor: str | None, nombre: str) -> date | None:
    if not valor:
        return None
    try:
        return date.fromisoformat(valor)
    except ValueError as exc:
        raise FiltroError(f"Fecha inválida en {nombre}. Use AAAA-MM-DD.") from exc


def _ids_lista(valor) -> list[int]:
    if valor is None:
        return []
    if isinstance(valor, (list, tuple)):
        raw = valor
    else:
        raw = str(valor).split(",")
    ids = []
    for item in raw:
        item = str(item).strip()
        if not item:
            continue
        try:
            ids.append(int(item))
        except ValueError as exc:
            raise FiltroError(f"Identificador inválido: {item}") from exc
    return ids


def acotar_por_alcance(user, qs: QuerySet) -> QuerySet:
    """
    Punto de extensión (§7 doc 12): filtrar por facultad/programa del usuario.
    Hoy no-op; quien tiene reportes.ver/exportar ve el alcance global.
    """
    return qs


@dataclass
class FiltroFecha:
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    obligatorio: bool = False
    max_dias: int | None = MAX_DIAS_MOVIMIENTOS

    @classmethod
    def from_data(cls, data, *, obligatorio: bool = False, max_dias: int | None = MAX_DIAS_MOVIMIENTOS):
        inicio = _parse_date(data.get("fecha_inicio"), "fecha_inicio")
        fin = _parse_date(data.get("fecha_fin"), "fecha_fin")
        return cls(fecha_inicio=inicio, fecha_fin=fin, obligatorio=obligatorio, max_dias=max_dias)

    def validar(self):
        if self.obligatorio and (not self.fecha_inicio or not self.fecha_fin):
            raise FiltroError("Debe indicar fecha_inicio y fecha_fin.")
        if self.fecha_inicio and self.fecha_fin and self.fecha_inicio > self.fecha_fin:
            raise FiltroError("fecha_inicio no puede ser posterior a fecha_fin.")
        if self.fecha_inicio and self.fecha_fin and self.max_dias is not None:
            dias = (self.fecha_fin - self.fecha_inicio).days + 1
            if dias > self.max_dias:
                raise FiltroError(
                    f"El rango no puede superar {self.max_dias} días "
                    f"(solicitó {dias}). Acote el periodo."
                )

    def aplicar(self, qs: QuerySet, campo: str = "timestamp") -> QuerySet:
        self.validar()
        if self.fecha_inicio:
            inicio_dt = timezone.make_aware(datetime.combine(self.fecha_inicio, time.min))
            qs = qs.filter(**{f"{campo}__gte": inicio_dt})
        if self.fecha_fin:
            fin_dt = timezone.make_aware(datetime.combine(self.fecha_fin, time.max))
            qs = qs.filter(**{f"{campo}__lte": fin_dt})
        return qs

    def como_dict(self) -> dict:
        return {
            "fecha_inicio": self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            "fecha_fin": self.fecha_fin.isoformat() if self.fecha_fin else None,
        }


@dataclass
class FiltroSede:
    sede_id: int | None = None
    lookup: str = "sede_id"

    @classmethod
    def from_data(cls, data, lookup: str = "sede_id"):
        raw = (data.get("sede") or "").strip()
        return cls(sede_id=int(raw) if raw else None, lookup=lookup)

    def aplicar(self, qs: QuerySet) -> QuerySet:
        if self.sede_id:
            qs = qs.filter(**{self.lookup: self.sede_id})
        return qs

    def como_dict(self) -> dict:
        return {"sede": self.sede_id}


@dataclass
class FiltroFacultad:
    facultad_id: int | None = None
    lookup: str = "programa__facultad_id"

    @classmethod
    def from_data(cls, data, lookup: str = "programa__facultad_id"):
        raw = (data.get("facultad") or "").strip()
        return cls(facultad_id=int(raw) if raw else None, lookup=lookup)

    def aplicar(self, qs: QuerySet) -> QuerySet:
        if self.facultad_id:
            qs = qs.filter(**{self.lookup: self.facultad_id})
        return qs

    def como_dict(self) -> dict:
        return {"facultad": self.facultad_id}


@dataclass
class FiltroPrograma:
    programa_id: int | None = None
    lookup: str = "programa_id"

    @classmethod
    def from_data(cls, data, lookup: str = "programa_id"):
        raw = (data.get("programa") or "").strip()
        return cls(programa_id=int(raw) if raw else None, lookup=lookup)

    def aplicar(self, qs: QuerySet) -> QuerySet:
        if self.programa_id:
            qs = qs.filter(**{self.lookup: self.programa_id})
        return qs

    def como_dict(self) -> dict:
        return {"programa": self.programa_id}


@dataclass
class FiltroArea:
    area_id: int | None = None
    lookup: str = "area_id"

    @classmethod
    def from_data(cls, data, lookup: str = "area_id"):
        raw = (data.get("area") or "").strip()
        return cls(area_id=int(raw) if raw else None, lookup=lookup)

    def aplicar(self, qs: QuerySet) -> QuerySet:
        if self.area_id:
            qs = qs.filter(**{self.lookup: self.area_id})
        return qs

    def como_dict(self) -> dict:
        return {"area": self.area_id}


@dataclass
class FiltroTipoVinculo:
    ids: list[int] = field(default_factory=list)
    lookup: str = "tipo_vinculo_id__in"

    @classmethod
    def from_data(cls, data, lookup: str = "tipo_vinculo_id__in"):
        # GET puede enviar tipo_vinculo o tipo_vinculo[]
        vals = data.getlist("tipo_vinculo") if hasattr(data, "getlist") else data.get("tipo_vinculo")
        return cls(ids=_ids_lista(vals), lookup=lookup)

    def aplicar(self, qs: QuerySet) -> QuerySet:
        if self.ids:
            qs = qs.filter(**{self.lookup: self.ids})
        return qs

    def como_dict(self) -> dict:
        return {"tipo_vinculo": self.ids}


@dataclass
class FiltroEstado:
    activo: bool | None = None
    lookup: str = "activo"

    @classmethod
    def from_data(cls, data, lookup: str = "activo"):
        raw = (data.get("estado") or "").strip()
        if raw == "1":
            return cls(activo=True, lookup=lookup)
        if raw == "0":
            return cls(activo=False, lookup=lookup)
        return cls(activo=None, lookup=lookup)

    def aplicar(self, qs: QuerySet) -> QuerySet:
        if self.activo is not None:
            qs = qs.filter(**{self.lookup: self.activo})
        return qs

    def como_dict(self) -> dict:
        if self.activo is None:
            return {"estado": None}
        return {"estado": "1" if self.activo else "0"}


@dataclass
class FiltroPropiedad:
    propiedad: str | None = None

    @classmethod
    def from_data(cls, data):
        raw = (data.get("propiedad") or "").strip()
        return cls(propiedad=raw or None)

    def aplicar(self, qs: QuerySet) -> QuerySet:
        if self.propiedad:
            qs = qs.filter(propiedad=self.propiedad)
        return qs

    def como_dict(self) -> dict:
        return {"propiedad": self.propiedad}


@dataclass
class FiltroTipoEquipo:
    tipo: str | None = None

    @classmethod
    def from_data(cls, data):
        raw = (data.get("tipo") or "").strip()
        return cls(tipo=raw or None)

    def aplicar(self, qs: QuerySet) -> QuerySet:
        if self.tipo:
            qs = qs.filter(tipo=self.tipo)
        return qs

    def como_dict(self) -> dict:
        return {"tipo": self.tipo}


@dataclass
class FiltroResultado:
    resultados: list[str] = field(default_factory=list)

    @classmethod
    def from_data(cls, data):
        vals = data.getlist("resultado") if hasattr(data, "getlist") else data.get("resultado")
        if vals is None:
            return cls(resultados=[])
        if isinstance(vals, str):
            vals = [v.strip() for v in vals.split(",") if v.strip()]
        else:
            vals = [str(v).strip() for v in vals if str(v).strip()]
        validos = {c for c, _ in Movimiento.OPCIONES_RESULTADO}
        for v in vals:
            if v not in validos:
                raise FiltroError(f"Resultado inválido: {v}")
        return cls(resultados=vals)

    def aplicar(self, qs: QuerySet) -> QuerySet:
        if self.resultados:
            qs = qs.filter(resultado__in=self.resultados)
        return qs

    def como_dict(self) -> dict:
        return {"resultado": self.resultados}


@dataclass
class FiltroCelador:
    usuario_id: int | None = None

    @classmethod
    def from_data(cls, data):
        raw = (data.get("celador") or "").strip()
        return cls(usuario_id=int(raw) if raw else None)

    def aplicar(self, qs: QuerySet) -> QuerySet:
        if self.usuario_id:
            qs = qs.filter(usuario_control_id=self.usuario_id)
        return qs

    def como_dict(self) -> dict:
        return {"celador": self.usuario_id}


@dataclass
class FiltroTipoAlerta:
    """Filtra movimientos de alerta por resultado (alerta / no_encontrado)."""

    resultados: list[str] = field(default_factory=list)

    @classmethod
    def from_data(cls, data):
        vals = data.getlist("tipo_alerta") if hasattr(data, "getlist") else data.get("tipo_alerta")
        if not vals:
            return cls(resultados=[])
        if isinstance(vals, str):
            vals = [v.strip() for v in vals.split(",") if v.strip()]
        else:
            vals = [str(v).strip() for v in vals if str(v).strip()]
        permitidos = {Movimiento.RESULTADO_ALERTA, Movimiento.RESULTADO_NO_ENCONTRADO}
        for v in vals:
            if v not in permitidos:
                raise FiltroError(f"Tipo de alerta inválido: {v}")
        return cls(resultados=vals)

    def aplicar(self, qs: QuerySet) -> QuerySet:
        if self.resultados:
            qs = qs.filter(resultado__in=self.resultados)
        return qs

    def como_dict(self) -> dict:
        return {"tipo_alerta": self.resultados}


def fusionar_filtros(*filtros) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for f in filtros:
        if f is None:
            continue
        out.update(f.como_dict())
    return out


def defaults_fecha_rango(dias: int = 30) -> tuple[str, str]:
    fin = timezone.localdate()
    inicio = fin - timedelta(days=dias - 1)
    return inicio.isoformat(), fin.isoformat()
