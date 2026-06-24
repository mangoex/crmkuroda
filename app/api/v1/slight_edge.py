from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from datetime import date, datetime, timedelta
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.models.slight_edge_plan import SlightEdgePlan
from app.models.slight_edge_log import SlightEdgeLog
from app.schemas.slight_edge import SlightEdgePlanCreate, SlightEdgeLogCreate, ChatPayload
from app.agents.slight_edge_agent import run_coaching_chat

router = APIRouter()

@router.get("/plan/{user_id}", status_code=status.HTTP_200_OK)
async def get_plan(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Gets the Slight Edge plan for a user."""
    # Safety RBAC check
    if current_user.rol not in ["admin", "gerente"] and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver el plan de este usuario."
        )

    res = await db.execute(select(SlightEdgePlan).filter(SlightEdgePlan.user_id == user_id))
    plan = res.scalars().first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró un plan de consistencia para este usuario."
        )

    return {
        "status": "success",
        "data": {
            "id": str(plan.id),
            "user_id": str(plan.user_id),
            "monthly_income_goal": plan.monthly_income_goal,
            "ticket_average": plan.ticket_average,
            "conversion_rate": plan.conversion_rate,
            "funnel_metrics": plan.funnel_metrics,
            "activities_config": plan.activities_config,
            "daily_points_goal": plan.daily_points_goal
        }
    }

@router.post("/plan/{user_id}", status_code=status.HTTP_200_OK)
async def create_or_update_plan(
    user_id: UUID,
    plan_in: SlightEdgePlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Creates or updates a user's Slight Edge plan."""
    if current_user.rol not in ["admin", "gerente"] and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para modificar el plan de este usuario."
        )

    # Check if user exists
    user_res = await db.execute(select(Usuario).filter(Usuario.id == user_id))
    if not user_res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario especificado no existe."
        )

    # Calculate funnel metrics dynamically
    needed_sales = 0.0
    needed_quotes = 0.0
    needed_meetings = 0.0
    needed_calls = 0.0

    if plan_in.ticket_average > 0:
        needed_sales = plan_in.monthly_income_goal / plan_in.ticket_average
        if plan_in.conversion_rate > 0:
            needed_meetings = needed_sales / (plan_in.conversion_rate / 100.0)
            needed_quotes = needed_meetings * 0.8
            needed_calls = needed_meetings * 5.0

    funnel_metrics = {
        "ventas_mensuales": round(needed_sales, 1),
        "cotizaciones_mensuales": round(needed_quotes, 1),
        "citas_mensuales": round(needed_meetings, 1),
        "llamadas_mensuales": round(needed_calls, 1)
    }

    # Query for existing plan
    plan_res = await db.execute(select(SlightEdgePlan).filter(SlightEdgePlan.user_id == user_id))
    plan = plan_res.scalars().first()

    activities_list = [item.dict() for item in plan_in.activities_config]

    if plan:
        plan.monthly_income_goal = plan_in.monthly_income_goal
        plan.ticket_average = plan_in.ticket_average
        plan.conversion_rate = plan_in.conversion_rate
        plan.funnel_metrics = funnel_metrics
        plan.activities_config = activities_list
        plan.daily_points_goal = plan_in.daily_points_goal
    else:
        plan = SlightEdgePlan(
            user_id=user_id,
            monthly_income_goal=plan_in.monthly_income_goal,
            ticket_average=plan_in.ticket_average,
            conversion_rate=plan_in.conversion_rate,
            funnel_metrics=funnel_metrics,
            activities_config=activities_list,
            daily_points_goal=plan_in.daily_points_goal
        )
        db.add(plan)

    await db.commit()
    await db.refresh(plan)

    return {
        "status": "success",
        "message": "Plan de La Ventaja guardado con éxito.",
        "data": {
            "id": str(plan.id),
            "user_id": str(plan.user_id),
            "monthly_income_goal": plan.monthly_income_goal,
            "ticket_average": plan.ticket_average,
            "conversion_rate": plan.conversion_rate,
            "funnel_metrics": plan.funnel_metrics,
            "activities_config": plan.activities_config,
            "daily_points_goal": plan.daily_points_goal
        }
    }

@router.get("/log/{user_id}", status_code=status.HTTP_200_OK)
async def get_logs(
    user_id: UUID,
    date_str: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Gets daily logs. If date_str is provided (YYYY-MM-DD), gets that specific day. Otherwise gets last 30 days history."""
    if current_user.rol not in ["admin", "gerente"] and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver los registros de este usuario."
        )

    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de fecha no válido. Use YYYY-MM-DD."
            )

        res = await db.execute(
            select(SlightEdgeLog).filter(
                SlightEdgeLog.user_id == user_id,
                SlightEdgeLog.date == target_date
            )
        )
        log = res.scalars().first()
        if not log:
            return {
                "status": "success",
                "data": None
            }

        return {
            "status": "success",
            "data": {
                "id": str(log.id),
                "user_id": str(log.user_id),
                "date": str(log.date),
                "completed_activities": log.completed_activities,
                "total_points": log.total_points
            }
        }
    else:
        # History: last 30 days
        thirty_days_ago = date.today() - timedelta(days=30)
        res = await db.execute(
            select(SlightEdgeLog).filter(
                SlightEdgeLog.user_id == user_id,
                SlightEdgeLog.date >= thirty_days_ago
            ).order_by(SlightEdgeLog.date.asc())
        )
        logs = res.scalars().all()
        data = [
            {
                "id": str(l.id),
                "user_id": str(l.user_id),
                "date": str(l.date),
                "completed_activities": l.completed_activities,
                "total_points": l.total_points
            }
            for l in logs
        ]
        return {
            "status": "success",
            "data": data
        }

@router.post("/log/{user_id}", status_code=status.HTTP_200_OK)
async def create_or_update_log(
    user_id: UUID,
    log_in: SlightEdgeLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Saves the daily checklist. Calculates total points dynamically based on the user's Slight Edge Plan weights."""
    if current_user.rol not in ["admin", "gerente"] and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para registrar actividades para este usuario."
        )

    # Parse target date
    if log_in.date_str:
        try:
            target_date = datetime.strptime(log_in.date_str, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de fecha no válido. Use YYYY-MM-DD."
            )
    else:
        target_date = date.today()

    # Get SlightEdgePlan to fetch activity points config
    plan_res = await db.execute(select(SlightEdgePlan).filter(SlightEdgePlan.user_id == user_id))
    plan = plan_res.scalars().first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe configurar un plan de consistencia en La Ventaja antes de registrar actividades."
        )

    # Calculate points
    activity_points_map = {item["activity"]: item["points"] for item in plan.activities_config}
    
    total_points = 0
    for act, count in log_in.completed_activities.items():
        weight = activity_points_map.get(act, 0)
        total_points += count * weight

    # Check for existing log
    log_res = await db.execute(
        select(SlightEdgeLog).filter(
            SlightEdgeLog.user_id == user_id,
            SlightEdgeLog.date == target_date
        )
    )
    log = log_res.scalars().first()

    if log:
        log.completed_activities = log_in.completed_activities
        log.total_points = total_points
    else:
        log = SlightEdgeLog(
            user_id=user_id,
            date=target_date,
            completed_activities=log_in.completed_activities,
            total_points=total_points
        )
        db.add(log)

    await db.commit()
    await db.refresh(log)

    return {
        "status": "success",
        "message": "Actividades registradas con éxito.",
        "data": {
            "id": str(log.id),
            "user_id": str(log.user_id),
            "date": str(log.date),
            "completed_activities": log.completed_activities,
            "total_points": log.total_points
        }
    }

@router.post("/coaching-chat/{user_id}", status_code=status.HTTP_200_OK)
async def coaching_chat(
    user_id: UUID,
    payload: ChatPayload,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Conversational coaching chatbot endpoint. Automatically triggers plan updates if the assistant issues a function call."""
    if current_user.rol not in ["admin", "gerente"] and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para chatear con el coach de este usuario."
        )

    # Format conversation history
    messages_history = [
        {"role": msg.role, "content": msg.content}
        for msg in payload.messages
    ]

    # Run chatbot complete
    result = await run_coaching_chat(messages_history)
    
    response_text = result["response"]
    tool_call_data = result["tool_call"]
    
    plan_saved = False
    
    # Process tool call if present
    if tool_call_data:
        try:
            monthly_income_goal = float(tool_call_data["monthly_income_goal"])
            ticket_average = float(tool_call_data["ticket_average"])
            conversion_rate = float(tool_call_data["conversion_rate"])
            daily_points_goal = int(tool_call_data["daily_points_goal"])
            activities_config = tool_call_data["activities_config"]
            
            # Recalculate funnel
            needed_sales = 0.0
            needed_quotes = 0.0
            needed_meetings = 0.0
            needed_calls = 0.0

            if ticket_average > 0:
                needed_sales = monthly_income_goal / ticket_average
                if conversion_rate > 0:
                    needed_meetings = needed_sales / (conversion_rate / 100.0)
                    needed_quotes = needed_meetings * 0.8
                    needed_calls = needed_meetings * 5.0

            funnel_metrics = {
                "ventas_mensuales": round(needed_sales, 1),
                "cotizaciones_mensuales": round(needed_quotes, 1),
                "citas_mensuales": round(needed_meetings, 1),
                "llamadas_mensuales": round(needed_calls, 1)
            }
            
            # Query for existing plan
            p_res = await db.execute(select(SlightEdgePlan).filter(SlightEdgePlan.user_id == user_id))
            plan = p_res.scalars().first()
            
            if plan:
                plan.monthly_income_goal = monthly_income_goal
                plan.ticket_average = ticket_average
                plan.conversion_rate = conversion_rate
                plan.funnel_metrics = funnel_metrics
                plan.activities_config = activities_config
                plan.daily_points_goal = daily_points_goal
            else:
                plan = SlightEdgePlan(
                    user_id=user_id,
                    monthly_income_goal=monthly_income_goal,
                    ticket_average=ticket_average,
                    conversion_rate=conversion_rate,
                    funnel_metrics=funnel_metrics,
                    activities_config=activities_config,
                    daily_points_goal=daily_points_goal
                )
                db.add(plan)
                
            await db.commit()
            plan_saved = True
            response_text += "\n\n💡 *[Sistema: Tu plan de La Ligera Ventaja ha sido guardado exitosamente en el CRM]*"
        except Exception as e:
            print("Error processing tool call database write:", e)
            response_text += "\n\n⚠️ *[Sistema: Hubo un problema al registrar tu plan automáticamente. Por favor intenta de nuevo]*"

    return {
        "status": "success",
        "response": response_text,
        "plan_saved": plan_saved
    }
