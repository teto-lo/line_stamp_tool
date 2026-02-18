import os
import asyncio
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

from ..db.models import init_db, get_session
from ..db.crud import StampSetCRUD, StampCRUD
from ..core.image_utils import ImageProcessor

load_dotenv()

app = FastAPI(title="LINE Stamp Tool Management", description="LINEスタンプ自動生成ツール管理画面")

# Initialize templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Initialize database
db_path = os.getenv('DB_PATH', './data/stamps.db')
engine = init_db(db_path)

# Initialize image processor
image_processor = ImageProcessor(
    os.getenv('OUTPUT_DIR', './output'),
    os.getenv('LORA_EXPORT_DIR', './lora_export')
)

# Mount static files for serving generated images
output_dir = Path(os.getenv('OUTPUT_DIR', './output'))
if output_dir.exists():
    app.mount("/static", StaticFiles(directory=str(output_dir)), name="static")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, status: Optional[str] = None, genre: Optional[str] = None):
    """スタンプセット一覧ページ"""
    db = get_session(engine)
    try:
        crud = StampSetCRUD(db)
        
        # Get stamp sets with optional filtering
        stamp_sets = crud.get_all(status=status)
        
        # Apply genre filter if specified
        if genre:
            stamp_sets = [s for s in stamp_sets if s.genre == genre]
        
        # Get unique genres for filter dropdown
        all_sets = crud.get_all()
        genres = list(set(s.genre for s in all_sets if s.genre))
        genres.sort()
        
        # Prepare data for template
        sets_data = []
        for stamp_set in stamp_sets:
            # Get stamp count
            stamp_db = StampCRUD(db)
            stamps = stamp_db.get_by_set(stamp_set.id)
            
            sets_data.append({
                'id': stamp_set.id,
                'name': stamp_set.name,
                'genre': stamp_set.genre,
                'status': stamp_set.status,
                'created_at': stamp_set.created_at,
                'approved_at': stamp_set.approved_at,
                'stamp_count': len(stamps),
                'lora_exported': stamp_set.lora_exported
            })
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "stamp_sets": sets_data,
            "genres": genres,
            "selected_status": status,
            "selected_genre": genre
        })
        
    finally:
        db.close()

@app.get("/set/{set_id}", response_class=HTMLResponse)
async def set_detail(request: Request, set_id: str):
    """スタンプセット詳細ページ"""
    db = get_session(engine)
    try:
        set_crud = StampSetCRUD(db)
        stamp_crud = StampCRUD(db)
        
        # Get stamp set
        stamp_set = set_crud.get(set_id)
        if not stamp_set:
            raise HTTPException(status_code=404, detail="Stamp set not found")
        
        # Get all stamps
        stamps = stamp_crud.get_by_set(set_id)
        
        # Prepare stamps data
        stamps_data = []
        for stamp in stamps:
            # Get relative path for static serving
            image_path = None
            if stamp.image_path and Path(stamp.image_path).exists():
                relative_path = Path(stamp.image_path).relative_to(output_dir)
                image_path = f"/static/{relative_path}"
            
            stamps_data.append({
                'id': stamp.id,
                'number': stamp.number,
                'phrase': stamp.phrase,
                'prompt': stamp.prompt,
                'negative_prompt': stamp.negative_prompt,
                'status': stamp.status,
                'image_path': image_path,
                'is_sample': stamp.is_sample,
                'seed': stamp.seed
            })
        
        # Get grid images
        sample_grid_path = None
        full_grid_path = None
        
        set_dir = output_dir / set_id
        if set_dir.exists():
            sample_grid_file = set_dir / "sample_grid.png"
            full_grid_file = set_dir / "grid.png"
            
            if sample_grid_file.exists():
                relative_path = sample_grid_file.relative_to(output_dir)
                sample_grid_path = f"/static/{relative_path}"
            
            if full_grid_file.exists():
                relative_path = full_grid_file.relative_to(output_dir)
                full_grid_path = f"/static/{relative_path}"
        
        return templates.TemplateResponse("set_detail.html", {
            "request": request,
            "stamp_set": stamp_set,
            "stamps": stamps_data,
            "sample_grid_path": sample_grid_path,
            "full_grid_path": full_grid_path
        })
        
    finally:
        db.close()

@app.get("/set/{set_id}/export-lora")
async def export_lora(set_id: str):
    """LoRA学習用データをエクスポート"""
    db = get_session(engine)
    try:
        set_crud = StampSetCRUD(db)
        stamp_crud = StampCRUD(db)
        
        # Get stamp set
        stamp_set = set_crud.get(set_id)
        if not stamp_set:
            raise HTTPException(status_code=404, detail="Stamp set not found")
        
        # Get all stamps with images
        stamps = stamp_crud.get_by_set(set_id)
        stamps_with_images = []
        
        for stamp in stamps:
            if stamp.image_path and Path(stamp.image_path).exists():
                stamps_with_images.append({
                    'number': stamp.number,
                    'image_path': stamp.image_path,
                    'phrase': stamp.phrase,
                    'prompt': stamp.prompt
                })
        
        if not stamps_with_images:
            raise HTTPException(status_code=400, detail="No stamps with images found")
        
        # Export for LoRA
        image_processor.export_for_lora(set_id, stamps_with_images)
        
        # Mark as exported
        set_crud.mark_lora_exported(set_id)
        
        return {"message": f"LoRA data exported for {len(stamps_with_images)} stamps"}
        
    finally:
        db.close()

@app.get("/download/{set_id}/{filename}")
async def download_file(set_id: str, filename: str):
    """ダウンロードファイルを提供"""
    file_path = output_dir / set_id / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type='application/octet-stream'
    )

@app.get("/api/sets")
async def get_sets_api(status: Optional[str] = None):
    """API: スタンプセット一覧をJSONで取得"""
    db = get_session(engine)
    try:
        crud = StampSetCRUD(db)
        stamp_sets = crud.get_all(status=status)
        
        sets_data = []
        for stamp_set in stamp_sets:
            sets_data.append({
                'id': stamp_set.id,
                'name': stamp_set.name,
                'genre': stamp_set.genre,
                'status': stamp_set.status,
                'created_at': stamp_set.created_at.isoformat(),
                'approved_at': stamp_set.approved_at.isoformat() if stamp_set.approved_at else None
            })
        
        return {"sets": sets_data}
        
    finally:
        db.close()

@app.get("/api/set/{set_id}")
async def get_set_api(set_id: str):
    """API: スタンプセット詳細をJSONで取得"""
    db = get_session(engine)
    try:
        set_crud = StampSetCRUD(db)
        stamp_crud = StampCRUD(db)
        
        stamp_set = set_crud.get(set_id)
        if not stamp_set:
            raise HTTPException(status_code=404, detail="Stamp set not found")
        
        stamps = stamp_crud.get_by_set(set_id)
        stamps_data = []
        
        for stamp in stamps:
            stamps_data.append({
                'id': stamp.id,
                'number': stamp.number,
                'phrase': stamp.phrase,
                'prompt': stamp.prompt,
                'negative_prompt': stamp.negative_prompt,
                'status': stamp.status,
                'is_sample': stamp.is_sample,
                'seed': stamp.seed,
                'created_at': stamp.created_at.isoformat()
            })
        
        return {
            'set': {
                'id': stamp_set.id,
                'name': stamp_set.name,
                'genre': stamp_set.genre,
                'character_description': stamp_set.character_description,
                'status': stamp_set.status,
                'created_at': stamp_set.created_at.isoformat(),
                'approved_at': stamp_set.approved_at.isoformat() if stamp_set.approved_at else None,
                'lora_exported': stamp_set.lora_exported
            },
            'stamps': stamps_data
        }
        
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('WEB_UI_PORT', 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
