import asyncio
import copy
import json
import logging
import os
import random
from pathlib import Path
from typing import Any
from urllib.parse import quote
from datetime import datetime, timezone

from app.repositories.project_repository import project_repository
import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)

APP_DIR = Path(__file__).resolve().parent.parent
SERVER_DIR = APP_DIR.parent
DEFAULT_OUTPUT_DIR = SERVER_DIR / "generated"

class ComfyUIProvider:
    def __init__(self) -> None:
        self.base_url = os.getenv("COMFYUI_BASE_URL", "http://127.0.0.1:8188").rstrip("/")
        self.workflows_dir = (APP_DIR / "workflows").resolve()
        
        # Extended configuration timeout limits tailored for heavy Qwen pipeline execution blocks (1200 seconds / 20 mins)
        self.timeout_seconds = int(os.getenv("COMFYUI_TIMEOUT_SECONDS", "1200"))
        self.poll_interval_seconds = float(os.getenv("COMFYUI_POLL_INTERVAL_SECONDS", "2.0"))
        
        self.output_dir = DEFAULT_OUTPUT_DIR.resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _load_workflow(self, target_workflow: str, fallback_workflow: str) -> tuple[dict[str, Any], str]:
        target_path = (self.workflows_dir / target_workflow).resolve()
        fallback_path = (self.workflows_dir / fallback_workflow).resolve()

        if target_path.exists() and self.workflows_dir in target_path.parents:
            active_path = target_path
            is_fallback = False
        else:
            active_path = fallback_path
            is_fallback = True
            logger.warning(f"Target workflow {target_workflow} missing. Falling back to default system track: {fallback_workflow}")

        if self.workflows_dir not in active_path.parents or not active_path.exists():
            raise HTTPException(status_code=500, detail="Core fallback system layout configuration asset missing.")

        try:
            with active_path.open("r", encoding="utf-8") as file:
                workflow = json.load(file)
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Target processing graph template configuration structure is unreadable") from exc

        return workflow, is_fallback

    def _prepare_workflow(
        self, prompt: str, negative_prompt: str, width: int, height: int, seed: int | None, 
        pipeline: dict[str, Any]
    ) -> tuple[dict[str, Any], int, str, str, str]:
        
        target_wf = pipeline["target_workflow"]
        fallback_wf = pipeline["fallback_workflow"]
        
        source_workflow, is_fallback = self._load_workflow(target_wf, fallback_wf)
        workflow = copy.deepcopy(source_workflow)
        
        # Route mapping structural selection flags
        active_wf_name = fallback_wf if is_fallback else target_wf
        active_model = pipeline["fallback_model"] if is_fallback else pipeline["target_model"]
        node_map = ModelRouter.PIPELINES["image-generation"]["nodes"] if is_fallback else pipeline["nodes"]

        actual_seed = seed if seed is not None else random.SystemRandom().randint(0, 0xFFFFFFFFFFFFFFFF)

        # Dynamic variable injection tracking map targets extracted in Phase 1
        pos_id = node_map["positive_prompt"]
        neg_id = node_map["negative_prompt"]
        sampler_id = node_map["sampler"]
        latent_id = node_map["latent"]
        output_id = node_map["output"]

        # Safeguard structural check before manipulation bounds are hit
        for nid in [pos_id, sampler_id, latent_id, output_id]:
            if nid not in workflow:
                raise HTTPException(status_code=500, detail=f"Graph structure invariant mutation fault. Node {nid} missing.")

        workflow[pos_id]["inputs"]["text"] = prompt
        if neg_id and neg_id in workflow:
            workflow[neg_id]["inputs"]["text"] = negative_prompt
            
        workflow[latent_id]["inputs"]["width"] = width
        workflow[latent_id]["inputs"]["height"] = height
        workflow[latent_id]["inputs"]["batch_size"] = 1
        workflow[sampler_id]["inputs"]["seed"] = actual_seed
        workflow[output_id]["inputs"]["filename_prefix"] = "PRANA"

        return workflow, actual_seed, active_wf_name, active_model, output_id

    async def health(self) -> dict[str, Any]:
        try:
            self._load_workflow("prana_flux_schnell_api.json", "prana_flux_schnell_api.json")
            workflow_loaded = True
        except HTTPException:
            workflow_loaded = False

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/system_stats")
                response.raise_for_status()
            return {"provider": "comfyui", "status": "online", "base_url": self.base_url, "workflow_loaded": workflow_loaded, "workflow_name": "prana_flux_schnell_api.json"}
        except httpx.HTTPError:
            return {"provider": "comfyui", "status": "offline", "base_url": self.base_url, "workflow_loaded": workflow_loaded, "workflow_name": "prana_flux_schnell_api.json"}

    async def _queue_prompt(self, workflow: dict[str, Any]) -> str:
        payload = {"prompt": workflow}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(f"{self.base_url}/prompt", json=payload)
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail="ComfyUI engine dropped operational tracking connection links") from exc

        if response.status_code >= 400:
            raise HTTPException(status_code=502, detail="Execution vector target frame stack execution payload execution dropped")
        return str(response.json()["prompt_id"])

    async def _wait_for_completion(self, prompt_id: str) -> dict[str, Any]:
        deadline = asyncio.get_running_loop().time() + self.timeout_seconds
        while asyncio.get_running_loop().time() < deadline:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(f"{self.base_url}/history/{quote(prompt_id, safe='')}")
            except httpx.RequestError as exc:
                raise HTTPException(status_code=502, detail="State synchronizer link tracking window fault sequence hit") from exc

            history = response.json()
            job = history.get(prompt_id)
            if job:
                if job.get("status", {}).get("status_str") == "error":
                    raise HTTPException(status_code=502, detail="ComfyUI engine internal pipeline compute tracking graph failure execution state caught")
                if job.get("outputs"):
                    return job
            await asyncio.sleep(self.poll_interval_seconds)
            
        raise HTTPException(status_code=504, detail="PRANA local core compute thread allocation request processing timeout exceeded threshold execution")

    def _extract_image_metadata(self, job: dict[str, Any], output_node_id: str) -> dict[str, str]:
        outputs = job.get("outputs", {})
        images = outputs.get(output_node_id, {}).get("images", [])
        if not images:
            for output in outputs.values():
                if candidate := output.get("images", []):
                    images = candidate
                    break
        if not images:
            raise HTTPException(status_code=502, detail="Compute operations executed successfully but returned zero file layout metadata streams")
        return {"filename": images[0]["filename"], "subfolder": images[0].get("subfolder", ""), "type": images[0].get("type", "output")}

    async def _download_image(self, metadata: dict[str, str]) -> bytes:
        try:
            # Scaled retrieval timeout frame parameters supporting large binary output structures
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.get(f"{self.base_url}/view", params=metadata)
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail="Extraction intercept processing on image buffer streams dropped out frame context") from exc
        return response.content

    async def generate_image(
        self, prompt: str, effective_prompt: str, negative_prompt: str, width: int, height: int, seed: int | None, 
        mode: str, pipeline: dict[str, Any]
    ) -> dict[str, Any]:
        
        workflow, actual_seed, active_workflow_name, active_model, output_node_id = self._prepare_workflow(
            effective_prompt, negative_prompt, width, height, seed, pipeline
        )
        
        prompt_id = await self._queue_prompt(workflow)
        job = await self._wait_for_completion(prompt_id)
        metadata = self._extract_image_metadata(job, output_node_id)
        image_bytes = await self._download_image(metadata)

        safe_filename = f"{prompt_id}.png"
        destination = (self.output_dir / safe_filename).resolve()
        destination.write_bytes(image_bytes)

        asset_url = f"/generated/{safe_filename}"
        
        project = {
            "id": prompt_id,
            "name": prompt[:100],
            "prompt": prompt,
            "effective_prompt": effective_prompt,
            "provider": "comfyui",
            "model": active_model,
            "seed": actual_seed,
            "width": width,
            "height": height,
            "filename": safe_filename,
            "asset_url": asset_url,
            "mode": mode,
            "workflow": active_workflow_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "assets": [{"url": asset_url, "kind": "image"}],
        }
        
        try:
            await project_repository.create_project(project)
        except RuntimeError as exc:
            if destination.exists(): destination.unlink()
            raise HTTPException(status_code=500, detail="Local persistent project relational entry write verification trace block drop exception") from exc

        return {
            "provider": "comfyui",
            "status": "completed",
            "prompt_id": prompt_id,
            "original_prompt": prompt,
            "effective_prompt": effective_prompt,
            "mode": mode,
            "model": active_model,
            "workflow": active_workflow_name,
            "asset_url": asset_url,
            "filename": safe_filename,
            "width": width,
            "height": height,
            "seed": actual_seed,
        }

comfyui_provider = ComfyUIProvider()