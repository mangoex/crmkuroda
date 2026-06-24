from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from datetime import date, datetime, timedelta
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.models.usuario import Usuario
from app.models.company import Company
from app.models.slight_edge_plan import SlightEdgePlan
from app.models.slight_edge_log import SlightEdgeLog
from app.agents.slight_edge_agent import categorize_activity, generate_coordination_ai_goals

router = APIRouter()

require_admin_or_gerente = RoleChecker(["admin", "gerente"])

class CompanyTargetUpdate(BaseModel):
    global_sales_target: float
    global_goals: str

@router.get("/{company_code}/dashboard", status_code=status.HTTP_200_OK)
async def get_company_dashboard(
    company_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_gerente)
):
    """Gets aggregate company dashboard metrics and individual seller statistics."""
    # Find company
    comp_res = await db.execute(select(Company).filter(Company.code == company_code))
    company = comp_res.scalars().first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró la empresa con el código {company_code}."
        )

    # Get all users (vendedores)
    sellers_res = await db.execute(select(Usuario).filter(Usuario.rol == "vendedor"))
    sellers = sellers_res.scalars().all()

    sellers_data = []
    thirty_days_ago = date.today() - timedelta(days=30)

    total_sales_val = 0.0
    total_target_val = 0.0
    conversions = []
    rois = []

    for s in sellers:
        # Get SlightEdgePlan
        p_res = await db.execute(select(SlightEdgePlan).filter(SlightEdgePlan.user_id == s.id))
        plan = p_res.scalars().first()

        # Get logs for last 30 days
        l_res = await db.execute(
            select(SlightEdgeLog).filter(
                SlightEdgeLog.user_id == s.id,
                SlightEdgeLog.date >= thirty_days_ago
            )
        )
        logs = l_res.scalars().all()

        # Group completed activities by standard categories
        calls = 0
        meetings = 0
        quotes = 0
        sales = 0
        total_points_sum = 0
        logged_days = len(logs)

        for log in logs:
            total_points_sum += log.total_points
            for act, count in log.completed_activities.items():
                cat = categorize_activity(act)
                if cat == "llamada":
                    calls += count
                elif cat == "cita":
                    meetings += count
                elif cat == "cotizacion":
                    quotes += count
                elif cat == "venta":
                    sales += count

        avg_points = (total_points_sum / logged_days) if logged_days > 0 else 0.0

        target = plan.monthly_income_goal if plan else 0.0
        ticket = plan.ticket_average if plan else 0.0
        planned_conversion_rate = plan.conversion_rate if plan else 0.0
        sales_amount = sales * ticket

        total_sales_val += sales_amount
        total_target_val += target

        real_conversion = (sales / meetings * 100.0) if meetings > 0 else planned_conversion_rate
        conversions.append(real_conversion)
        rois.append(avg_points)

        disciplines_str = "Ninguna"
        if plan and plan.activities_config:
            disciplines_str = ", ".join(
                f"{item['activity']} ({item['points']} pts)" 
                for item in plan.activities_config
            )

        sellers_data.append({
            "id": str(s.id),
            "name": s.nombre_completo or s.email,
            "email": s.email,
            "role": s.rol,
            "metrics": {
                "sales": sales_amount,
                "target": target,
                "conversion_rate": round(real_conversion, 1),
                "roi": round(avg_points, 1)  # consistency score
              },
            "slight_edge": {
                "planned_conversion_rate": planned_conversion_rate,
                "ticket_average": ticket,
                "logged_days": logged_days,
                "actual_calls": calls,
                "actual_meetings": meetings,
                "actual_quotes": quotes,
                "actual_sales": sales,
                "actual_avg_points": round(avg_points, 1),
                "daily_points_goal": plan.daily_points_goal if plan else 10,
                "disciplines": disciplines_str
            }
        })

    avg_conversion = (sum(conversions) / len(conversions)) if conversions else 0.0
    avg_roi = (sum(rois) / len(rois)) if rois else 0.0

    return {
        "status": "success",
        "company_name": company.name,
        "global_sales_target": company.global_sales_target,
        "global_goals": company.global_goals,
        "aggregated": {
            "total_sales": total_sales_val,
            "total_target": total_target_val,
            "avg_conversion": round(avg_conversion, 1),
            "avg_roi": round(avg_roi, 1)
        },
        "sellers": sellers_data
    }

@router.post("/{company_code}/dashboard/target", status_code=status.HTTP_200_OK)
async def update_company_target(
    company_code: str,
    target_in: CompanyTargetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_gerente)
):
    """Updates company's global target and goals."""
    comp_res = await db.execute(select(Company).filter(Company.code == company_code))
    company = comp_res.scalars().first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró la empresa con el código {company_code}."
        )

    company.global_sales_target = target_in.global_sales_target
    company.global_goals = target_in.global_goals
    await db.commit()
    await db.refresh(company)

    return {
        "status": "success",
        "message": "Metas de la empresa actualizadas con éxito.",
        "data": {
            "code": company.code,
            "name": company.name,
            "global_sales_target": company.global_sales_target,
            "global_goals": company.global_goals
        }
    }

@router.post("/{company_code}/sellers/{seller_id}/ai-goals", status_code=status.HTTP_200_OK)
async def audit_seller_performance(
    company_code: str,
    seller_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_admin_or_gerente)
):
    """Invokes Gemini to audit a seller's plan vs actual consistency metrics."""
    comp_res = await db.execute(select(Company).filter(Company.code == company_code))
    company = comp_res.scalars().first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró la empresa con el código {company_code}."
        )

    user_res = await db.execute(select(Usuario).filter(Usuario.id == seller_id))
    seller = user_res.scalars().first()
    if not seller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendedor no encontrado."
        )

    # Fetch Slight Edge plan and logs
    p_res = await db.execute(select(SlightEdgePlan).filter(SlightEdgePlan.user_id == seller_id))
    plan = p_res.scalars().first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este vendedor no tiene configurado un plan de consistencia en La Ventaja."
        )

    thirty_days_ago = date.today() - timedelta(days=30)
    l_res = await db.execute(
        select(SlightEdgeLog).filter(
            SlightEdgeLog.user_id == seller_id,
            SlightEdgeLog.date >= thirty_days_ago
        )
    )
    logs = l_res.scalars().all()

    # Sum metrics
    calls = 0
    meetings = 0
    quotes = 0
    sales = 0
    total_points_sum = 0
    logged_days = len(logs)

    for log in logs:
        total_points_sum += log.total_points
        for act, count in log.completed_activities.items():
            cat = categorize_activity(act)
            if cat == "llamada":
                calls += count
            elif cat == "cita":
                meetings += count
            elif cat == "cotizacion":
                quotes += count
            elif cat == "venta":
                sales += count

    avg_points = (total_points_sum / logged_days) if logged_days > 0 else 0.0
    sales_amount = sales * plan.ticket_average

    disciplines_str = ", ".join(f"{item['activity']} ({item['points']} pts)" for item in plan.activities_config)

    # Call AI Suggestions
    ai_suggestion = await generate_coordination_ai_goals(
        company_name=company.name,
        global_sales_target=company.global_sales_target,
        global_goals=company.global_goals,
        seller_name=seller.nombre_completo or seller.email,
        seller_target_income=plan.monthly_income_goal,
        seller_ticket=plan.ticket_average,
        seller_conversion_rate=plan.conversion_rate,
        seller_daily_points=plan.daily_points_goal,
        seller_disciplines=disciplines_str,
        actual_calls=calls,
        actual_meetings=meetings,
        actual_quotes=quotes,
        actual_sales=sales,
        actual_sales_amount=sales_amount,
        actual_avg_points=avg_points,
        logged_days=logged_days
    )

    return {
        "status": "success",
        "ai_suggestion": ai_suggestion
    }
