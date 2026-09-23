"""Alert API Routes — Phase 12C.

Alert lifecycle management API endpoints.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from .dependencies import get_alert_store
from .schemas import (
    AlertResponse,
    AlertListResponse,
    AlertAcknowledgeRequest,
    AlertResolveRequest,
)
from ..alert.store import AlertStore
from ..alert.models import AlertStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["alerts"])


def _alert_to_response(alert) -> AlertResponse:
    """Map Alert domain model to API AlertResponse."""
    return AlertResponse(
        alert_id=alert.alert_id,
        fingerprint=alert.fingerprint,
        fingerprint_version=alert.fingerprint_version,
        server_id=alert.server_id,
        alert_type=alert.alert_type.value,
        resource_type=alert.resource_type.value,
        resource_id=alert.resource_id,
        condition=alert.condition,
        severity=alert.severity.value,
        status=alert.status.value,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
        acknowledged_at=alert.acknowledged_at,
        acknowledged_by=alert.acknowledged_by,
        acknowledge_note=alert.acknowledge_note,
        resolved_at=alert.resolved_at,
        resolution_note=alert.resolution_note,
        consecutive_failure_count=alert.consecutive_failure_count,
        consecutive_ok_count=alert.consecutive_ok_count,
        first_snapshot_id=alert.first_snapshot_id,
        last_snapshot_id=alert.last_snapshot_id,
        recovery_count=alert.recovery_count,
        metadata=alert.metadata_json,
    )

@router.get("/alerts", response_model=AlertListResponse)
def list_alerts(
    server_id: Optional[str] = None,
    status: Optional[str] = None,
    alert_store: AlertStore = Depends(get_alert_store),
) -> AlertListResponse:
    """List alerts with optional filtering."""
    status_filter = None
    if status:
        try:
            status_filter = [AlertStatus(status.upper())]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_STATUS",
                    "message": f"Invalid status: {status}",
                    "details": {},
                },
            )
    
    alerts = alert_store.list_alerts(server_id=server_id, status_filter=status_filter)
    return AlertListResponse(
        alerts=[_alert_to_response(alert) for alert in alerts],
        total=len(alerts),
    )


@router.get("/alerts/{alert_id}", response_model=AlertResponse)
def get_alert(
    alert_id: str,
    alert_store: AlertStore = Depends(get_alert_store),
) -> AlertResponse:
    """Get a specific alert by ID."""
    alert = alert_store.get_alert(alert_id)
    if alert is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "NOT_FOUND",
                "message": f"Alert '{alert_id}' not found",
                "details": {},
            },
        )
    return _alert_to_response(alert)


@router.post("/alerts/{alert_id}/ack", response_model=AlertResponse)
def acknowledge_alert(
    alert_id: str,
    request: AlertAcknowledgeRequest,
    alert_store: AlertStore = Depends(get_alert_store),
) -> AlertResponse:
    """Acknowledge an alert."""
    alert = alert_store.get_alert(alert_id)
    if alert is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "NOT_FOUND",
                "message": f"Alert '{alert_id}' not found",
                "details": {},
            },
        )
    
    if alert.status != AlertStatus.OPEN:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "CONFLICT",
                "message": f"Cannot acknowledge alert in {alert.status.value} status",
                "details": {
                    "current_status": alert.status.value,
                    "required_status": AlertStatus.OPEN.value,
                },
            },
        )
    
    alert_store.acknowledge_alert(
        alert_id,
        acknowledged_by=request.acknowledged_by,
        acknowledge_note=request.note,
    )
    
    updated_alert = alert_store.get_alert(alert_id)
    return _alert_to_response(updated_alert)


@router.post("/alerts/{alert_id}/resolve", response_model=AlertResponse)
def resolve_alert(
    alert_id: str,
    request: AlertResolveRequest,
    alert_store: AlertStore = Depends(get_alert_store),
) -> AlertResponse:
    """Resolve an alert."""
    alert = alert_store.get_alert(alert_id)
    if alert is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "NOT_FOUND",
                "message": f"Alert '{alert_id}' not found",
                "details": {},
            },
        )
    
    if alert.status not in [AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED]:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "CONFLICT",
                "message": f"Cannot resolve alert in {alert.status.value} status",
                "details": {
                    "current_status": alert.status.value,
                    "allowed_statuses": [
                        AlertStatus.OPEN.value,
                        AlertStatus.ACKNOWLEDGED.value,
                    ],
                },
            },
        )
    
    alert_store.resolve_alert(alert_id, resolution_note=request.resolution_note)
    
    updated_alert = alert_store.get_alert(alert_id)
    return _alert_to_response(updated_alert)


@router.get("/servers/{server_id}/alerts", response_model=AlertListResponse)
def list_server_alerts(
    server_id: str,
    status: Optional[str] = None,
    alert_store: AlertStore = Depends(get_alert_store),
) -> AlertListResponse:
    """List alerts for a specific server."""
    status_filter = None
    if status:
        try:
            status_filter = [AlertStatus(status.upper())]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_STATUS",
                    "message": f"Invalid status: {status}",
                    "details": {},
                },
            )
    
    alerts = alert_store.list_alerts(server_id=server_id, status_filter=status_filter)
    return AlertListResponse(
        alerts=[_alert_to_response(alert) for alert in alerts],
        total=len(alerts),
    )
