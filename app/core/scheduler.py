import logging
from datetime import date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import async_session_maker
from app.models.usuario import Usuario
from app.models.meta import Meta
from app.models.cotizacion import Cotizacion
from app.models.seguimiento import SeguimientoDiario
from app.agents.seguimiento_agent import generate_followup_message, generate_whatsapp_link

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def job_generar_seguimientos_diarios():
    """
    Tarea programada para generar los enlaces de WhatsApp diariamente para todos los vendedores.
    """
    logger.info("Iniciando generación de seguimientos diarios...")
    hoy = date.today()

    async with async_session_maker() as session:
        # Obtener todos los vendedores
        result = await session.execute(
            select(Usuario).filter(Usuario.rol == "vendedor").options(
                selectinload(Usuario.metas),
                selectinload(Usuario.cotizaciones)
            )
        )
        vendedores = result.scalars().all()

        for vendedor in vendedores:
            # Check si ya se generó hoy para no duplicar
            existente = await session.execute(
                select(SeguimientoDiario).filter(
                    SeguimientoDiario.vendedor_id == vendedor.id,
                    SeguimientoDiario.fecha == hoy
                )
            )
            if existente.scalars().first():
                continue # Ya existe

            try:
                # Filtrar metas y cotizaciones activas/recientes
                metas_vigentes = [
                    {"descripcion": m.descripcion, "monto_objetivo": str(m.monto_objetivo), "estado": m.estado}
                    for m in vendedor.metas if m.estado != "Completada"
                ]
                
                # Para simplificar, tomamos las últimas 5 cotizaciones del vendedor
                cotizaciones_recientes = [
                    {"cliente_nombre": c.cliente_nombre, "total": str(c.total)}
                    for c in sorted(vendedor.cotizaciones, key=lambda x: x.fecha_registro or date.min, reverse=True)[:5]
                ]

                # Llamar a la IA
                nombre = vendedor.nombre_completo or vendedor.email.split("@")[0]
                mensaje = await generate_followup_message(
                    vendedor_nombre=nombre,
                    metas_vigentes=metas_vigentes,
                    cotizaciones_recientes=cotizaciones_recientes
                )

                # Generar link manual
                link = generate_whatsapp_link(vendedor.telefono_whatsapp or "", mensaje)

                nuevo_seguimiento = SeguimientoDiario(
                    vendedor_id=vendedor.id,
                    fecha=hoy,
                    mensaje_generado=mensaje,
                    enlace_whatsapp=link
                )
                session.add(nuevo_seguimiento)

            except Exception as e:
                logger.error(f"Error generando seguimiento para {vendedor.email}: {e}")

        await session.commit()
        logger.info("Generación de seguimientos diarios finalizada.")

def start_scheduler():
    """Inicia el planificador de tareas en segundo plano"""
    scheduler.add_job(
        job_generar_seguimientos_diarios,
        trigger=CronTrigger(hour=8, minute=0), # Todos los días a las 8:00 AM
        id="generar_seguimientos_8am",
        replace_existing=True
    )
    scheduler.start()
    logger.info("Scheduler iniciado correctamente.")
