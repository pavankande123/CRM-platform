import datetime
import hashlib
import json
import logging
import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.models.workflow import WorkflowDefinition, WorkflowExecution
from app.models.customer import Customer
from app.models.project import Project
from app.models.follow_up import FollowUp
from app.models.payment import Payment
from app.models.activity import Activity
from app.schemas.workflow import WorkflowCreate, WorkflowUpdate
from app.services import notification_service

logger = logging.getLogger("enermax.workflow")


# ---------------------------------------------------------------------------
# 1. Workflow Definition Management
# ---------------------------------------------------------------------------

async def list_workflows(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    entity_type: Optional[str] = None,
    trigger_event: Optional[str] = None,
) -> List[WorkflowDefinition]:
    stmt = select(WorkflowDefinition).where(WorkflowDefinition.tenant_id == tenant_id)
    if entity_type:
        stmt = stmt.where(WorkflowDefinition.entity_type == entity_type.strip().lower())
    if trigger_event:
        stmt = stmt.where(WorkflowDefinition.trigger_event == trigger_event.strip().lower())
    stmt = stmt.order_by(WorkflowDefinition.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_workflow(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    workflow_id: uuid.UUID,
) -> WorkflowDefinition:
    stmt = select(WorkflowDefinition).where(
        WorkflowDefinition.id == workflow_id,
        WorkflowDefinition.tenant_id == tenant_id,
    )
    workflow = (await db.execute(stmt)).scalar_one_or_none()
    if not workflow:
        raise NotFoundError(message="Workflow not found.")
    return workflow


async def create_workflow(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: WorkflowCreate,
) -> WorkflowDefinition:
    wf = WorkflowDefinition(
        tenant_id=tenant_id,
        name=data.name.strip(),
        description=data.description,
        entity_type=data.entity_type.strip().lower(),
        trigger_event=data.trigger_event.strip().lower(),
        is_active=data.is_active,
        conditions=[c.model_dump() for c in data.conditions],
        actions=[a.model_dump() for a in data.actions],
    )
    db.add(wf)
    await db.commit()
    await db.refresh(wf)
    return wf


async def update_workflow(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    workflow_id: uuid.UUID,
    data: WorkflowUpdate,
) -> WorkflowDefinition:
    wf = await get_workflow(db, tenant_id, workflow_id)
    if data.name is not None:
        wf.name = data.name.strip()
    if data.description is not None:
        wf.description = data.description
    if data.is_active is not None:
        wf.is_active = data.is_active
    if data.conditions is not None:
        wf.conditions = [c.model_dump() for c in data.conditions]
    if data.actions is not None:
        wf.actions = [a.model_dump() for a in data.actions]

    await db.commit()
    await db.refresh(wf)
    return wf


async def delete_workflow(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    workflow_id: uuid.UUID,
) -> dict:
    wf = await get_workflow(db, tenant_id, workflow_id)
    await db.delete(wf)
    await db.commit()
    return {"status": "deleted", "message": f"Workflow '{wf.name}' deleted successfully."}


async def list_workflow_executions(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    workflow_id: Optional[uuid.UUID] = None,
    limit: int = 50,
) -> List[WorkflowExecution]:
    stmt = select(WorkflowExecution).where(WorkflowExecution.tenant_id == tenant_id)
    if workflow_id:
        stmt = stmt.where(WorkflowExecution.workflow_id == workflow_id)
    stmt = stmt.order_by(WorkflowExecution.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# 2. Condition Evaluator
# ---------------------------------------------------------------------------

def evaluate_conditions(record_data: Dict[str, Any], conditions: List[Dict[str, Any]]) -> bool:
    """
    Evaluates declarative conditions against record state.
    Returns True if all conditions pass (logical AND).
    """
    if not conditions:
        return True

    for cond in conditions:
        field = cond.get("field")
        op = str(cond.get("operator", "eq")).lower()
        target_val = cond.get("value")

        actual_val = record_data.get(field)

        # Handle numeric conversion if comparing numbers
        if isinstance(actual_val, (int, float, Decimal)) and target_val is not None:
            try:
                target_val = float(target_val)
                actual_val = float(actual_val)
            except Exception:
                pass

        if op in ("eq", "="):
            if actual_val != target_val and str(actual_val).lower() != str(target_val).lower():
                return False
        elif op in ("neq", "!="):
            if actual_val == target_val or str(actual_val).lower() == str(target_val).lower():
                return False
        elif op in ("gt", ">"):
            if actual_val is None or actual_val <= target_val:
                return False
        elif op in ("gte", ">="):
            if actual_val is None or actual_val < target_val:
                return False
        elif op in ("lt", "<"):
            if actual_val is None or actual_val >= target_val:
                return False
        elif op in ("lte", "<="):
            if actual_val is None or actual_val > target_val:
                return False
        elif op == "contains":
            if not actual_val or str(target_val).lower() not in str(actual_val).lower():
                return False
        elif op == "in":
            if isinstance(target_val, list):
                if actual_val not in target_val and str(actual_val) not in [str(x) for x in target_val]:
                    return False
        elif op == "is_empty":
            if actual_val not in (None, "", []):
                return False
        elif op == "is_not_empty":
            if actual_val in (None, "", []):
                return False

    return True


# ---------------------------------------------------------------------------
# 3. Action Handlers
# ---------------------------------------------------------------------------

async def execute_action(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    action: Dict[str, Any],
    entity_type: str,
    entity_id: uuid.UUID,
    record_data: Dict[str, Any],
) -> Dict[str, Any]:
    action_type = action.get("action_type")
    params = action.get("params", {})

    if action_type == "create_follow_up":
        title = params.get("title", f"Automated follow-up for {entity_type}")
        days_offset = int(params.get("days_offset", 1))
        priority = params.get("priority", "medium")
        assigned_to_id = params.get("assigned_to_id") or record_data.get("owner_id")

        due_date = datetime.date.today() + datetime.timedelta(days=days_offset)

        target_project_id = entity_id if entity_type == "project" else (uuid.UUID(str(record_data.get("project_id"))) if record_data.get("project_id") else None)
        target_customer_id = entity_id if entity_type == "customer" else (uuid.UUID(str(record_data.get("customer_id"))) if record_data.get("customer_id") else None)

        follow_up = FollowUp(
            tenant_id=tenant_id,
            title=title,
            due_date=due_date,
            priority=priority,
            assigned_to_id=uuid.UUID(str(assigned_to_id)) if assigned_to_id else None,
            project_id=target_project_id,
            customer_id=target_customer_id,
            status="pending",
        )
        db.add(follow_up)
        await db.flush()
        return {"action": "create_follow_up", "follow_up_id": str(follow_up.id), "title": title}

    elif action_type == "create_notification":
        recipient_id = params.get("user_id") or record_data.get("owner_id") or record_data.get("created_by_id")
        if recipient_id:
            title = params.get("title", f"Workflow Alert: {entity_type}")
            message = params.get("message", "An automated workflow triggered for this record.")
            notif = await notification_service.create_notification(
                db,
                tenant_id=tenant_id,
                user_id=uuid.UUID(str(recipient_id)),
                title=title,
                message=message,
                notification_type=params.get("notification_type", "info"),
                link_url=f"/{entity_type}s/{entity_id}",
            )
            return {"action": "create_notification", "notification_id": str(notif.id)}
        return {"action": "create_notification", "status": "skipped", "reason": "No recipient user identified"}

    elif action_type == "assign_record":
        target_user_id = params.get("user_id")
        if target_user_id:
            target_uuid = uuid.UUID(str(target_user_id))
            if entity_type == "project":
                stmt = select(Project).where(Project.id == entity_id, Project.tenant_id == tenant_id)
                proj = (await db.execute(stmt)).scalar_one_or_none()
                if proj:
                    proj.owner_id = target_uuid
            elif entity_type == "customer":
                stmt = select(Customer).where(Customer.id == entity_id, Customer.tenant_id == tenant_id)
                cust = (await db.execute(stmt)).scalar_one_or_none()
                if cust:
                    cust.created_by_id = target_uuid
            return {"action": "assign_record", "assigned_to": str(target_user_id)}
        return {"action": "assign_record", "status": "skipped"}

    elif action_type == "update_record":
        fields_to_update = params.get("fields", {})
        if entity_type == "project":
            stmt = select(Project).where(Project.id == entity_id, Project.tenant_id == tenant_id)
            proj = (await db.execute(stmt)).scalar_one_or_none()
            if proj:
                for k, v in fields_to_update.items():
                    if hasattr(proj, k):
                        setattr(proj, k, v)
        elif entity_type == "payment":
            stmt = select(Payment).where(Payment.id == entity_id, Payment.tenant_id == tenant_id)
            pmt = (await db.execute(stmt)).scalar_one_or_none()
            if pmt:
                for k, v in fields_to_update.items():
                    if hasattr(pmt, k):
                        setattr(pmt, k, v)
        return {"action": "update_record", "updated_fields": list(fields_to_update.keys())}

    elif action_type == "add_activity":
        activity_type = params.get("activity_type", "system")
        target_project_id = entity_id if entity_type == "project" else (uuid.UUID(str(record_data.get("project_id"))) if record_data.get("project_id") else None)
        target_customer_id = entity_id if entity_type == "customer" else (uuid.UUID(str(record_data.get("customer_id"))) if record_data.get("customer_id") else None)
        act = Activity(
            tenant_id=tenant_id,
            activity_type=activity_type,
            title="Workflow Automation",
            description=description,
            project_id=target_project_id,
            customer_id=target_customer_id,
        )
        db.add(act)
        return {"action": "add_activity", "description": description}

    return {"action": action_type, "status": "unsupported"}


# ---------------------------------------------------------------------------
# 4. Dispatcher, Idempotency & Execution
# ---------------------------------------------------------------------------

async def dispatch_event(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    trigger_event: str,
    entity_type: str,
    entity_id: uuid.UUID,
    record_data: Dict[str, Any],
    event_timestamp: Optional[str] = None,
) -> List[WorkflowExecution]:
    """
    Main Event Dispatcher entry point.
    Matches active tenant workflows, evaluates conditions, guarantees idempotency,
    executes actions, and logs executions.
    """
    clean_event = trigger_event.strip().lower()
    clean_entity = entity_type.strip().lower()

    # Fast indexed lookup for matching workflows
    stmt = (
        select(WorkflowDefinition)
        .where(
            WorkflowDefinition.tenant_id == tenant_id,
            WorkflowDefinition.trigger_event == clean_event,
            WorkflowDefinition.is_active == True,  # noqa: E712
        )
    )
    workflows = (await db.execute(stmt)).scalars().all()
    if not workflows:
        return []

    executed_list: List[WorkflowExecution] = []
    ts = event_timestamp or datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M")

    for wf in workflows:
        # Check conditions
        if not evaluate_conditions(record_data, wf.conditions or []):
            continue

        # Compute deterministic idempotency key
        # Incorporates workflow ID, event name, entity ID, and event timestamp
        idemp_payload = f"{wf.id}:{clean_event}:{entity_id}:{ts}"
        idempotency_key = hashlib.sha256(idemp_payload.encode()).hexdigest()

        # Check existing execution
        check_stmt = select(WorkflowExecution).where(
            WorkflowExecution.tenant_id == tenant_id,
            WorkflowExecution.idempotency_key == idempotency_key,
        )
        existing_exec = (await db.execute(check_stmt)).scalar_one_or_none()

        if existing_exec:
            if existing_exec.status in ("completed", "running"):
                # Idempotency triggered: duplicate event skipped
                logger.info(f"Duplicate event skipped for idempotency key {idempotency_key}")
                executed_list.append(existing_exec)
                continue
            else:
                exec_record = existing_exec
                exec_record.status = "running"
                exec_record.retry_count += 1
        else:
            exec_record = WorkflowExecution(
                tenant_id=tenant_id,
                workflow_id=wf.id,
                trigger_event=clean_event,
                entity_type=clean_entity,
                entity_id=entity_id,
                idempotency_key=idempotency_key,
                status="running",
                retry_count=0,
                started_at=datetime.datetime.now(datetime.timezone.utc),
            )
            db.add(exec_record)
            await db.flush()

        # Execute actions
        results: List[Dict[str, Any]] = []
        try:
            for action in (wf.actions or []):
                res = await execute_action(db, tenant_id, action, clean_entity, entity_id, record_data)
                results.append(res)

            exec_record.status = "completed"
            exec_record.completed_at = datetime.datetime.now(datetime.timezone.utc)
            exec_record.execution_data = results
            exec_record.error_message = None
            await db.commit()
            await db.refresh(exec_record)
            executed_list.append(exec_record)

        except Exception as exc:
            logger.error(f"Workflow execution {exec_record.id} failed: {exc}", exc_info=True)
            await db.rollback()
            exec_record.status = "failed"
            exec_record.error_message = str(exc)
            exec_record.execution_data = results
            db.add(exec_record)
            await db.commit()
            executed_list.append(exec_record)

    return executed_list


async def retry_workflow_execution(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    execution_id: uuid.UUID,
) -> WorkflowExecution:
    stmt = (
        select(WorkflowExecution)
        .options(selectinload(WorkflowExecution.workflow))
        .where(WorkflowExecution.id == execution_id, WorkflowExecution.tenant_id == tenant_id)
    )
    exec_record = (await db.execute(stmt)).scalar_one_or_none()
    if not exec_record:
        raise NotFoundError(message="Workflow execution not found.")

    if exec_record.status == "completed":
        raise ValidationError(message="Workflow execution has already completed successfully.")

    wf = exec_record.workflow
    exec_record.status = "running"
    exec_record.retry_count += 1

    results: List[Dict[str, Any]] = []
    try:
        for action in (wf.actions or []):
            res = await execute_action(
                db, tenant_id, action, exec_record.entity_type, exec_record.entity_id, {}
            )
            results.append(res)

        exec_record.status = "completed"
        exec_record.completed_at = datetime.datetime.now(datetime.timezone.utc)
        exec_record.execution_data = results
        exec_record.error_message = None
        await db.commit()
        await db.refresh(exec_record)
        return exec_record

    except Exception as exc:
        await db.rollback()
        exec_record.status = "failed"
        exec_record.error_message = str(exc)
        db.add(exec_record)
        await db.commit()
        await db.refresh(exec_record)
        return exec_record
