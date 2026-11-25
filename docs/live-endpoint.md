# Live demo: add `GET /inventory/incidents` (Milestone 6)

Paste-ready. Two edits in `nova-inventory/`, then restart + discover.

## 1. New file `nova-inventory/app/routes/incidents.py`
```python
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import AS_OF, get_db
from ..models import SyncStatus

router = APIRouter(tags=["incidents"])


class IncidentOut(BaseModel):
    incident_id: str
    severity: str
    product_id: str
    warehouse_id: str
    incident_type: str
    occurred_at: datetime
    description: str


class IncidentPage(BaseModel):
    items: list[IncidentOut]
    total: int
    as_of: datetime = AS_OF


@router.get("/inventory/incidents", response_model=IncidentPage)
def get_inventory_incidents(db: Session = Depends(get_db)):
    """Open inventory incidents (failed syncs) per product and warehouse."""
    failed = db.scalars(select(SyncStatus).where(SyncStatus.status == "failed").order_by(SyncStatus.sync_id))
    pairs = [(s, p) for s in failed for p in s.affected_products]
    items = [IncidentOut(incident_id=f"INV-2026-{42 + i:03d}", severity=s.severity, product_id=p,
                         warehouse_id=s.warehouse_id, incident_type="inventory_sync_failure",
                         occurred_at=s.failing_since,
                         description="Inventory synchronization failed; availability may be stale.")
             for i, (s, p) in enumerate(pairs)]
    return IncidentPage(items=items, total=len(items))
```

## 2. `nova-inventory/app/main.py` — register it
```python
from .routes import analytics, incidents, products, stock, sync, warehouses
...
for r in (products, stock, warehouses, sync, analytics, incidents):
```

## 3. Restart, discover, verify (PowerShell)
In the **nova-inventory :8002** window: Ctrl+C, then type (don't use ↑, it shows other windows' commands):
```powershell
.venv\Scripts\python -m uvicorn app.main:app --port 8002
```
In a separate terminal from the project folder:
```powershell
curl.exe http://127.0.0.1:8002/inventory/incidents   # must show INV-2026-042 (SKU-104, W1, critical); "Not Found" = main.py not edited or API not restarted
# rebuild the MCP server from the changed code (same server name keeps the same server_id).
# One line on purpose: Synapse must run inside nova-inventory/ (where .synapse/ lives), and the line returns to the project folder.
cd nova-inventory; synapse -y build --auto --discover --server-name nova-inventory --base-url http://localhost:8002 --endpoints "list_products,get_product_details,get_warehouse_inventory,get_low_stock_products,get_product_stock,get_warehouse_status,get_inventory_sync_status,get_stock_health,get_inventory_incidents"; cd ..
```
4. UI → Systems / MCP → **Refresh tools**: `get_inventory_incidents` shows **★ newly discovered** (open the page once *before* step 1 so the baseline is the old tool list).
5. UI → Investigations → **Run investigation**: activity shows **★ New capability in use: get_inventory_incidents**, root cause gains evidence `Inventory system incident INV-2026-042 (critical)…`.

## Reset after a rehearsal (PowerShell, from the project folder)
```powershell
git checkout nova-inventory/app/main.py
Remove-Item nova-inventory\app\routes\incidents.py
```
Restart the **nova-inventory :8002** window as in step 3, then rebuild WITHOUT `get_inventory_incidents`:
```powershell
cd nova-inventory; synapse -y build --auto --server-name nova-inventory --base-url http://localhost:8002 --endpoints "list_products,get_product_details,get_warehouse_inventory,get_low_stock_products,get_product_stock,get_warehouse_status,get_inventory_sync_status,get_stock_health"; cd ..
```
After the real demo: keep the endpoint, flip the absence assert in `nova-inventory/tests/test_api.py` into a test for it, commit.
