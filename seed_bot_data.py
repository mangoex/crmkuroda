"""Siembra determinista de datos de prueba para el módulo /api/v1/bot.

Incluye:
- 3 vendedores activos (con metas del mes actual)
- 20 ventas concretadas/facturadas (con partidas en cotizacion_items)
- 10 cotizaciones adicionales (enviada, borrador, rechazada, vencida con partidas y notas)
- Clientes asociados en catálogo
- Citas y compromisos de seguimiento (pendiente, cumplido, vencido)
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.cliente import Cliente
from app.models.cotizacion import Cotizacion
from app.models.cotizacion_detalle import CotizacionComentario, CotizacionItem
from app.models.meta import Meta
from app.models.meta_comercial import MetaComercial
from app.models.recordatorio_seguimiento import RecordatorioSeguimiento
from app.models.usuario import Usuario

MAZATLAN_TZ = ZoneInfo("America/Mazatlan")
_DEFAULT_SELLER_HASH: Optional[str] = None


def _get_seller_password_hash() -> str:
    global _DEFAULT_SELLER_HASH
    if _DEFAULT_SELLER_HASH is None:
        _DEFAULT_SELLER_HASH = get_password_hash("VendedorBot2026!")
    return _DEFAULT_SELLER_HASH


SELLER_SPECS = [
    {
        "id": UUID("a1111111-1111-4111-8111-111111111101"),
        "email": "lorena.peraza@kuroda.com",
        "nombre_completo": "Lorena Peraza",
        "telefono_whatsapp": "+526677100001",
        "codigo_vendedor": "C01",
        "equipo": "Culiacán proyectos",
        "activo": True,
        "meta_monto": Decimal("100000.00"),
        "num_ventas": 8,
        "monto_por_venta": Decimal("5000.00"),  # 8 * 5000 = 40,000 (40.00%)
    },
    {
        "id": UUID("b2222222-2222-4222-8222-222222222202"),
        "email": "mario.navarro@kuroda.com",
        "nombre_completo": "Mario Navarro",
        "telefono_whatsapp": "+526677100002",
        "codigo_vendedor": "K96",
        "equipo": "Mazatlán comercial",
        "activo": True,
        "meta_monto": Decimal("80000.00"),
        "num_ventas": 7,
        "monto_por_venta": Decimal("4000.00"),  # 7 * 4000 = 28,000 (35.00%)
    },
    {
        "id": UUID("c3333333-3333-4333-8333-333333333303"),
        "email": "carlos.mendoza@kuroda.com",
        "nombre_completo": "Carlos Mendoza",
        "telefono_whatsapp": "+526677100003",
        "codigo_vendedor": "C03",
        "equipo": "Los Mochis industrial",
        "activo": True,
        "meta_monto": Decimal("60000.00"),
        "num_ventas": 5,
        "monto_por_venta": Decimal("3000.00"),  # 5 * 3000 = 15,000 (25.00%)
    },
]


async def seed_bot_test_data(
    session: AsyncSession,
    reference_date: Optional[date] = None,
) -> dict:
    """Siembra al menos 3 vendedores, 20 ventas, 10 cotizaciones y metas del mes actual."""
    today = reference_date or datetime.now(MAZATLAN_TZ).date()
    month_start = today.replace(day=1)
    pwd_hash = _get_seller_password_hash()

    sellers: list[Usuario] = []
    for idx, spec in enumerate(SELLER_SPECS):
        existing = (
            await session.execute(select(Usuario).where(Usuario.email == spec["email"]))
        ).scalars().first()
        if existing:
            existing.nombre_completo = spec["nombre_completo"]
            existing.telefono_whatsapp = spec["telefono_whatsapp"]
            existing.codigo_vendedor = spec["codigo_vendedor"]
            existing.equipo = spec["equipo"]
            existing.activo = spec["activo"]
            existing.rol = "vendedor"
            seller = existing
        else:
            seller = Usuario(
                id=spec["id"],
                email=spec["email"],
                hashed_password=pwd_hash,
                rol="vendedor",
                nombre_completo=spec["nombre_completo"],
                telefono_whatsapp=spec["telefono_whatsapp"],
                codigo_vendedor=spec["codigo_vendedor"],
                equipo=spec["equipo"],
                activo=spec["activo"],
                fecha_alta=datetime.combine(
                    date(today.year, 1, 10 + idx), time(9, 0, 0), tzinfo=MAZATLAN_TZ
                ),
            )
            session.add(seller)
        sellers.append(seller)

    await session.flush()

    # Sembrar Clientes asociados
    clientes_seed = [
        ("400101", "Constructora del Pacífico S.A. de C.V.", "Persona moral", "6677123401", "compras@conspacifico.mx"),
        ("400102", "Hidráulica y Plomería de Sinaloa S.A.", "Persona moral", "6677123402", "ventas@hidrosinaloa.mx"),
        ("400103", "Desarrollos Residenciales Humaya", "Persona moral", "6677123403", "obras@humaya.mx"),
        ("400104", "Ing. Roberto Valenzuela Castro", "Persona física", "6699887704", "rvalenzuela@obras.mx"),
        ("400105", "Agroindustrias del Valle del Fuerte", "Persona moral", "6688112205", "insumos@agrovalle.mx"),
    ]
    for num_cli, nombre_cli, tipo_p, tel, mail in clientes_seed:
        existing_cli = (
            await session.execute(select(Cliente).where(Cliente.numero_cliente == num_cli))
        ).scalars().first()
        if not existing_cli:
            session.add(
                Cliente(
                    sociedad="MKS",
                    numero_cliente=num_cli,
                    nombre=nombre_cli,
                    nombre_contacto=nombre_cli,
                    rfc="XAXX010101000",
                    tipo_persona=tipo_p,
                    poblacion="Culiacán",
                    estado="Sinaloa",
                    telefono=tel,
                    celular=tel,
                    email=mail,
                    created_at=datetime(today.year, 1, 15, 10, 0, 0),
                )
            )

    await session.flush()

    # Sembrar Metas del mes actual (MetaComercial)
    metas_created = []
    for seller, spec in zip(sellers, SELLER_SPECS):
        existing_mc = (
            await session.execute(
                select(MetaComercial).where(
                    MetaComercial.tipo == "vendedor",
                    MetaComercial.vendedor_id == seller.id,
                    MetaComercial.mes == month_start,
                )
            )
        ).scalars().first()
        if not existing_mc:
            mc = MetaComercial(
                id=uuid4(),
                tipo="vendedor",
                vendedor_id=seller.id,
                mes=month_start,
                monto_objetivo=spec["meta_monto"],
                descripcion=f"Meta mensual comercial {month_start.strftime('%Y-%m')}",
            )
            session.add(mc)
            metas_created.append(mc)
        else:
            existing_mc.monto_objetivo = spec["meta_monto"]
            metas_created.append(existing_mc)

    # Sembrar 20 Ventas concretadas (8 + 7 + 5 = 20 ventas en el mes actual)
    ventas_created: list[Cotizacion] = []
    sale_counter = 0
    for seller_idx, (seller, spec) in enumerate(zip(sellers, SELLER_SPECS)):
        for n in range(spec["num_ventas"]):
            sale_counter += 1
            folio_cot = f"COT-BOT-V{sale_counter:03d}"
            folio_fac = f"FAC-BOT-{sale_counter:04d}"
            existing_v = (
                await session.execute(
                    select(Cotizacion).where(Cotizacion.numero_cotizacion == folio_cot)
                )
            ).scalars().first()
            if existing_v:
                ventas_created.append(existing_v)
                continue

            cli_tuple = clientes_seed[(sale_counter - 1) % len(clientes_seed)]
            monto_venta = spec["monto_por_venta"]
            precio_unit = monto_venta / Decimal("2")
            sale_day = min(today.day, max(1, (n % max(1, today.day)) + 1))
            sale_date = today.replace(day=sale_day)

            quote_venta = Cotizacion(
                id=uuid4(),
                vendedor_id=seller.id,
                vendedor_nombre=seller.nombre_completo,
                grupo_vendedores=seller.codigo_vendedor,
                numero_cliente=cli_tuple[0],
                cliente_nombre=cli_tuple[1],
                datos_contacto={"telefono": cli_tuple[3], "email": cli_tuple[4]},
                items=[
                    {
                        "codigo_material": f"MAT-{sale_counter:03d}",
                        "producto": f"Tubería Hidráulica Serie {sale_counter}",
                        "cantidad": 2,
                        "precio_unitario": float(precio_unit),
                        "importe": float(monto_venta),
                    }
                ],
                total=monto_venta,
                importe_facturado=monto_venta,
                numero_cotizacion=folio_cot,
                numero_factura=folio_fac,
                fecha_registro=sale_date,
                fecha_factura=sale_date,
                canal="Pide y Recoge",
                plazo_entrega="Pide y Recoge",
                venta_perdida="No",
                texto_propuesta=f"Propuesta comercial aceptada y facturada ({folio_fac}).",
                comentarios="Entrega confirmada en sucursal.",
            )
            session.add(quote_venta)
            await session.flush()

            session.add(
                CotizacionItem(
                    id=uuid4(),
                    cotizacion_id=quote_venta.id,
                    codigo_material=f"MAT-{sale_counter:03d}",
                    descripcion=f"Tubería Hidráulica Serie {sale_counter}",
                    unidad_medida="PZA",
                    precio_venta=precio_unit,
                    cantidad_cotizada=Decimal("2.000"),
                    importe_cotizado=monto_venta,
                    cantidad_facturada=Decimal("2.000"),
                    importe_facturado=monto_venta,
                )
            )
            ventas_created.append(quote_venta)

    # Sembrar 10 Cotizaciones adicionales NO facturadas (enviada, borrador, rechazada, vencida)
    extra_quotes_spec = [
        (0, "COT-BOT-Q001", Decimal("12000.00"), today, "No", "Cotización enviada pendiente de aprobación."),
        (0, "COT-BOT-Q002", Decimal("15000.00"), today, "No", "Seguimiento de válvulas industriales."),
        (0, "COT-BOT-Q003", Decimal("8500.00"), today, "BORRADOR", "Borrador en preparación técnica."),
        (1, "COT-BOT-Q004", Decimal("22000.00"), today, "No", "Cotización enviada para proyecto hotelero."),
        (1, "COT-BOT-Q005", Decimal("9500.00"), today, "No", "Cotización enviada para plomería residencial."),
        (1, "COT-BOT-Q006", Decimal("14000.00"), today, "Si", "Rechazada por tiempo de importación."),
        (2, "COT-BOT-Q007", Decimal("18000.00"), today, "No", "Cotización enviada de bombas centrífugas."),
        (2, "COT-BOT-Q008", Decimal("11000.00"), today, "No", "Cotización enviada de conexiones CPVC."),
        (2, "COT-BOT-Q009", Decimal("7500.00"), today, "Si", "Rechazada por ajuste de presupuesto del cliente."),
        (0, "COT-BOT-Q010", Decimal("19500.00"), today - timedelta(days=45), "No", "Cotización vencida por antigüedad."),
    ]

    cotizaciones_extra: list[Cotizacion] = []
    for q_idx, (s_idx, folio_q, monto_q, fecha_q, vp_flag, nota_q) in enumerate(extra_quotes_spec, start=1):
        existing_q = (
            await session.execute(
                select(Cotizacion).where(Cotizacion.numero_cotizacion == folio_q)
            )
        ).scalars().first()
        if existing_q:
            cotizaciones_extra.append(existing_q)
            continue

        seller = sellers[s_idx]
        cli_tuple = clientes_seed[(q_idx - 1) % len(clientes_seed)]
        q_obj = Cotizacion(
            id=uuid4(),
            vendedor_id=seller.id,
            vendedor_nombre=seller.nombre_completo,
            grupo_vendedores=seller.codigo_vendedor,
            numero_cliente=cli_tuple[0],
            cliente_nombre=cli_tuple[1],
            datos_contacto={"telefono": cli_tuple[3], "email": cli_tuple[4]},
            items=[
                {
                    "codigo_material": f"EQ-{q_idx:03d}",
                    "producto": f"Equipo Hidroneumático Modelo {q_idx}",
                    "cantidad": 1,
                    "precio_unitario": float(monto_q),
                    "importe": float(monto_q),
                }
            ],
            total=monto_q,
            importe_facturado=Decimal("0.00"),
            numero_cotizacion=folio_q,
            numero_factura=None,
            fecha_registro=fecha_q,
            fecha_factura=None,
            canal="Envío a Domicilio",
            plazo_entrega="Envío a Domicilio",
            venta_perdida=vp_flag,
            texto_propuesta=f"Propuesta técnica {folio_q}",
            comentarios=nota_q,
        )
        session.add(q_obj)
        await session.flush()

        session.add(
            CotizacionItem(
                id=uuid4(),
                cotizacion_id=q_obj.id,
                codigo_material=f"EQ-{q_idx:03d}",
                descripcion=f"Equipo Hidroneumático Modelo {q_idx}",
                unidad_medida="PZA",
                precio_venta=monto_q,
                cantidad_cotizada=Decimal("1.000"),
                importe_cotizado=monto_q,
                cantidad_facturada=Decimal("0.000"),
                importe_facturado=Decimal("0.00"),
            )
        )
        session.add(
            CotizacionComentario(
                id=uuid4(),
                cotizacion_id=q_obj.id,
                autor_id=seller.id,
                comentario=f"Nota de seguimiento: {nota_q}",
                creado_en=datetime.combine(fecha_q, time(12, 30, 0)),
            )
        )
        cotizaciones_extra.append(q_obj)

    # Sembrar Citas / Compromisos (pendiente, cumplido, vencido)
    if cotizaciones_extra:
        compromisos_specs = [
            (sellers[0], cotizaciones_extra[0], today + timedelta(days=2), False, None, "Llamada de cierre con cliente"),
            (sellers[1], cotizaciones_extra[3], today - timedelta(days=1), True, datetime.combine(today - timedelta(days=1), time(16, 0, 0)), "Envío de ficha técnica completado"),
            (sellers[2], cotizaciones_extra[6], today - timedelta(days=3), False, None, "Visita a obra pendiente vencida"),
        ]
        for s_user, q_ref, f_prog, comp_bool, comp_dt, nota_rec in compromisos_specs:
            session.add(
                RecordatorioSeguimiento(
                    id=uuid4(),
                    cotizacion_id=q_ref.id,
                    vendedor_id=s_user.id,
                    fecha_programada=f_prog,
                    nota=nota_rec,
                    completado=comp_bool,
                    completado_en=comp_dt,
                )
            )

    await session.commit()
    return {
        "vendedores": len(sellers),
        "ventas": len(ventas_created),
        "cotizaciones_adicionales": len(cotizaciones_extra),
        "total_cotizaciones": len(ventas_created) + len(cotizaciones_extra),
        "metas_mes": len(metas_created),
    }


async def _main() -> None:
    from app.core.database import SessionLocal

    async with SessionLocal() as session:
        summary = await seed_bot_test_data(session)
        print(f"[Seed Bot Data] Completado: {summary}")


if __name__ == "__main__":
    asyncio.run(_main())
