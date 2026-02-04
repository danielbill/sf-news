"""Legend 基础数据 API

/biz/legend_basedata 路由 - Legend 档案管理 API
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from ...models.legend import (
    Legend,
    LegendCreate,
    LegendUpdate,
    LegendFilters,
    LegendType,
    LegendTier,
    ImpactLevel,
    LegendDetail,
    SyncResult,
)
from ...services.legend_db import LegendDB
from ...services.legend_file import LegendFileService
from ...services.legend_sync import LegendSyncService


router = APIRouter(
    prefix="/biz/legend_basedata",
    tags=["legend-basedata"]
)

# 初始化服务
db = LegendDB()
file_service = LegendFileService()
sync_service = LegendSyncService(db=db)


# =============================================================================
# Legend CRUD
# =============================================================================


@router.get("/", response_model=dict)
async def list_legends(
    type: Optional[LegendType] = None,
    tier: Optional[LegendTier] = None,
    impact_level: Optional[ImpactLevel] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """列出所有 Legend 实体"""
    filters = LegendFilters(
        type=type,
        tier=tier,
        impact_level=impact_level,
        limit=limit,
        offset=offset
    )
    legends = db.list_legends(filters)

    return {
        "code": 200,
        "message": "success",
        "data": [legend.model_dump(mode="json") for legend in legends],
        "total": len(legends)
    }


@router.get("/{legend_id}", response_model=dict)
async def get_legend(legend_id: str):
    """获取单个 Legend 详情（含关联数据）"""
    legend = db.get_legend(legend_id)
    if not legend:
        raise HTTPException(status_code=404, detail=f"Legend {legend_id} not found")

    # 获取关联数据
    keywords = db.get_keywords(legend_id)
    products = db.list_products(legend_id)

    # 获取人物-公司关联（仅当是人物时）
    companies = []
    if legend.type == LegendType.PERSON:
        companies = db.list_person_companies(legend_id)

    # 读取 Markdown 文件内容
    markdown_content = file_service.read_file(legend_id, legend.type)

    detail = LegendDetail(
        **legend.model_dump(),
        keywords=keywords,
        products=products,
        companies=companies,
        markdown_content=markdown_content
    )

    return {
        "code": 200,
        "message": "success",
        "data": detail.model_dump(mode="json")
    }


@router.post("/", response_model=dict)
async def create_legend(data: LegendCreate):
    """手动创建 Legend"""
    if db.legend_exists(data.id):
        raise HTTPException(status_code=400, detail=f"Legend {data.id} already exists")

    legend_id = db.create_legend(data)

    return {
        "code": 200,
        "message": "Legend created",
        "data": {"id": legend_id}
    }


@router.put("/{legend_id}", response_model=dict)
async def update_legend(legend_id: str, data: LegendUpdate):
    """更新 Legend"""
    if not db.legend_exists(legend_id):
        raise HTTPException(status_code=404, detail=f"Legend {legend_id} not found")

    success = db.update_legend(legend_id, data)
    if not success:
        raise HTTPException(status_code=400, detail="No fields to update")

    return {
        "code": 200,
        "message": "Legend updated",
        "data": {"id": legend_id}
    }


@router.delete("/{legend_id}", response_model=dict)
async def delete_legend(legend_id: str):
    """删除 Legend（软删除/归档）"""
    if not db.legend_exists(legend_id):
        raise HTTPException(status_code=404, detail=f"Legend {legend_id} not found")

    db.delete_legend(legend_id)

    return {
        "code": 200,
        "message": "Legend deleted",
        "data": {"id": legend_id}
    }


# =============================================================================
# 同步操作
# =============================================================================


@router.post("/sync", response_model=dict)
async def sync_legends(auto_fetch: bool = False):
    """手动触发同步（扫描 news_keywords.yaml）

    Args:
        auto_fetch: 是否自动调用 /baidu-ai-search 采集数据（暂未实现）
    """
    try:
        result = sync_service.sync(auto_fetch=auto_fetch)

        return {
            "code": 200,
            "message": "Sync completed",
            "data": result.model_dump(mode="json")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync/log", response_model=dict)
async def get_sync_logs(limit: int = Query(50, ge=1, le=500)):
    """查看同步日志"""
    logs = db.get_sync_logs(limit=limit)

    return {
        "code": 200,
        "message": "success",
        "data": [log.model_dump(mode="json") for log in logs],
        "total": len(logs)
    }


# =============================================================================
# 关键词
# =============================================================================


@router.get("/keywords", response_model=dict)
async def get_all_keywords():
    """获取所有关键词配置（从 YAML 读取）"""
    yaml_config = sync_service.get_yaml_legends()

    return {
        "code": 200,
        "message": "success",
        "data": {
            "legends": yaml_config.legends,
            "front": yaml_config.front
        }
    }


@router.get("/{legend_id}/keywords", response_model=dict)
async def get_legend_keywords(legend_id: str):
    """获取单个 Legend 的关键词"""
    if not db.legend_exists(legend_id):
        raise HTTPException(status_code=404, detail=f"Legend {legend_id} not found")

    keywords = db.get_keywords(legend_id)

    return {
        "code": 200,
        "message": "success",
        "data": [kw.model_dump(mode="json") for kw in keywords],
        "total": len(keywords)
    }


# =============================================================================
# 产品
# =============================================================================


@router.get("/{legend_id}/products", response_model=dict)
async def get_legend_products(legend_id: str):
    """获取 Legend 的产品列表"""
    if not db.legend_exists(legend_id):
        raise HTTPException(status_code=404, detail=f"Legend {legend_id} not found")

    products = db.list_products(legend_id)

    return {
        "code": 200,
        "message": "success",
        "data": [p.model_dump(mode="json") for p in products],
        "total": len(products)
    }


# =============================================================================
# 人物-公司关联
# =============================================================================


@router.get("/people/{person_id}/companies", response_model=dict)
async def get_person_companies(person_id: str):
    """获取人物关联的公司列表"""
    if not db.legend_exists(person_id):
        raise HTTPException(status_code=404, detail=f"Legend {person_id} not found")

    companies = db.list_person_companies(person_id)

    return {
        "code": 200,
        "message": "success",
        "data": [c.model_dump(mode="json") for c in companies],
        "total": len(companies)
    }


@router.get("/orgs/{company_id}/people", response_model=dict)
async def get_company_people(company_id: str):
    """获取公司关联的人物列表"""
    if not db.legend_exists(company_id):
        raise HTTPException(status_code=404, detail=f"Legend {company_id} not found")

    people = db.list_company_people(company_id)

    return {
        "code": 200,
        "message": "success",
        "data": [p.model_dump(mode="json") for p in people],
        "total": len(people)
    }
