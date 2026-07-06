"""
Inventory module, managed primarily by the Store Keeper.
Inventory workflow: Store Keeper -> Manager (for approval / oversight, see approvals.py).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.audit import log_action
from app.core.notify import notify_user
from app.models.user import User, Role
from app.models.inventory import InventoryItem, StockIn, StockOut
from app.schemas.inventory import (
    InventoryItemCreate, InventoryItemOut,
    StockInCreate, StockInOut,
    StockOutCreate, StockOutOut,
)
from app.api.deps import get_current_user, require_permission

router = APIRouter(tags=["Inventory"])


@router.get("/inventory", response_model=list[InventoryItemOut])
def list_inventory(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(InventoryItem).all()


@router.get("/inventory/items", response_model=list[InventoryItemOut])
def list_inventory_items(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(InventoryItem).all()


@router.post("/inventory/items", response_model=InventoryItemOut, status_code=status.HTTP_201_CREATED)
def create_inventory_item(
    payload: InventoryItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_inventory")),
):
    item = InventoryItem(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    log_action(db, user_id=current_user.id, action="Inventory item created", table_name="inventory_items", record_id=item.id, new_value=payload.model_dump())
    return item


@router.post("/stock-in", response_model=StockInOut, status_code=status.HTTP_201_CREATED)
def stock_in(
    payload: StockInCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_inventory")),
):
    item = db.get(InventoryItem, payload.item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    record = StockIn(**payload.model_dump(), recorded_by=current_user.id)
    item.quantity = float(item.quantity) + payload.quantity
    db.add(record)
    db.commit()
    db.refresh(record)

    log_action(db, user_id=current_user.id, action="Stock in recorded", table_name="stock_in", record_id=record.id, new_value=payload.model_dump())
    return record


@router.post("/stock-out", response_model=StockOutOut, status_code=status.HTTP_201_CREATED)
def stock_out(
    payload: StockOutCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_inventory")),
):
    item = db.get(InventoryItem, payload.item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    if float(item.quantity) < payload.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock quantity")

    record = StockOut(**payload.model_dump(), recorded_by=current_user.id)
    item.quantity = float(item.quantity) - payload.quantity
    db.add(record)
    db.commit()
    db.refresh(record)

    log_action(db, user_id=current_user.id, action="Stock out recorded", table_name="stock_out", record_id=record.id, new_value=payload.model_dump())

    if item.is_below_minimum:
        manager = db.query(User).join(Role).filter(Role.name == "Manager").first()
        if manager:
            notify_user(db, user_id=manager.id, message=f"Inventory item '{item.name}' is below minimum stock ({item.quantity} {item.unit or ''})")

    return record
