import asyncio
import copy
import json
import logging
import os
import random
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
from fastapi import HTTPException


logger = logging.getLogger(__name__)


APP_DIR = Path(__file__).resolve().parent.parent
SERVER_DIR = APP_DIR.parent

DEFAULT_WORKFLOW_PATH = (
    APP_DIR
    / "workflows"
    / "prana_flux_schnell_api.json"
)

DEFAULT_OUTPUT_DIR = SERVER_DIR / "generated"


class ComfyUIProvider:
    """
    Local ComfyUI provider for PRANA.

    Current workflow mapping:

    Node 6:
        Positive CLIPTextEncode

    Node 33:
        Negative CLIPTextEncode

    Node 27:
        EmptySD3LatentImage
        width / height / batch_size

    Node 31:
        KSampler
        seed / steps / cfg / sampler / scheduler

    Node 9:
        SaveImage
    """

    POSITIVE_PROMPT_NODE = "6"
    NEGATIVE_PROMPT_NODE = "33"
    LATENT_NODE = "27"
    SAMPLER_NODE = "31"
    SAVE_IMAGE_NODE = "9"

    def __init__(self) -> None:
        self.base_url = os.getenv(
            "COMFYUI_BASE_URL",
            "http://127.0.0.1:8188",
        ).rstrip("/")

        configured_workflow = os.getenv(
            "COMFYUI_WORKFLOW_PATH"
        )

        if configured_workflow:
            workflow_path = Path(configured_workflow)

            if not workflow_path.is_absolute():
                workflow_path = SERVER_DIR / workflow_path

            self.workflow_path = workflow_path.resolve()
        else:
            self.workflow_path = DEFAULT_WORKFLOW_PATH.resolve()

        self.timeout_seconds = int(
            os.getenv(
                "COMFYUI_TIMEOUT_SECONDS",
                "300",
            )
        )

        self.poll_interval_seconds = float(
            os.getenv(
                "COMFYUI_POLL_INTERVAL_SECONDS",
                "1.0",
            )
        )

        self.output_dir = DEFAULT_OUTPUT_DIR.resolve()
        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    def _load_workflow(self) -> dict[str, Any]:
        if not self.workflow_path.exists():
            raise HTTPException(
                status_code=500,
                detail=(
                    "ComfyUI workflow file not found: "
                    f"{self.workflow_path.name}"
                ),
            )

        try:
            with self.workflow_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                workflow = json.load(file)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=500,
                detail=(
                    "ComfyUI workflow JSON is invalid"
                ),
            ) from exc
        except OSError as exc:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Unable to read ComfyUI workflow"
                ),
            ) from exc

        required_nodes = {
            self.POSITIVE_PROMPT_NODE,
            self.NEGATIVE_PROMPT_NODE,
            self.LATENT_NODE,
            self.SAMPLER_NODE,
            self.SAVE_IMAGE_NODE,
        }

        missing_nodes = (
            required_nodes - set(workflow.keys())
        )

        if missing_nodes:
            raise HTTPException(
                status_code=500,
                detail=(
                    "ComfyUI workflow missing required "
                    f"nodes: {sorted(missing_nodes)}"
                ),
            )

        return workflow

    def _prepare_workflow(
        self,
        prompt: str,
        negative_prompt: str,
        width: int,
        height: int,
        seed: int | None,
    ) -> tuple[dict[str, Any], int]:
        source_workflow = self._load_workflow()
        workflow = copy.deepcopy(source_workflow)

        actual_seed = (
            seed
            if seed is not None
            else random.SystemRandom().randint(
                0,
                0xFFFFFFFFFFFFFFFF,
            )
        )

        workflow[
            self.POSITIVE_PROMPT_NODE
        ]["inputs"]["text"] = prompt

        workflow[
            self.NEGATIVE_PROMPT_NODE
        ]["inputs"]["text"] = negative_prompt

        workflow[
            self.LATENT_NODE
        ]["inputs"]["width"] = width

        workflow[
            self.LATENT_NODE
        ]["inputs"]["height"] = height

        workflow[
            self.LATENT_NODE
        ]["inputs"]["batch_size"] = 1

        workflow[
            self.SAMPLER_NODE
        ]["inputs"]["seed"] = actual_seed

        workflow[
            self.SAVE_IMAGE_NODE
        ]["inputs"]["filename_prefix"] = "PRANA"

        return workflow, actual_seed

    async def health(self) -> dict[str, Any]:
        workflow_loaded = False

        try:
            self._load_workflow()
            workflow_loaded = True
        except HTTPException:
            workflow_loaded = False

        try:
            async with httpx.AsyncClient(
                timeout=10.0
            ) as client:
                response = await client.get(
                    f"{self.base_url}/system_stats"
                )

                response.raise_for_status()

            return {
                "provider": "comfyui",
                "status": "online",
                "base_url": self.base_url,
                "workflow_loaded": workflow_loaded,
                "workflow_name": self.workflow_path.name,
            }

        except httpx.HTTPError:
            return {
                "provider": "comfyui",
                "status": "offline",
                "base_url": self.base_url,
                "workflow_loaded": workflow_loaded,
                "workflow_name": self.workflow_path.name,
            }

    async def _queue_prompt(
        self,
        workflow: dict[str, Any],
    ) -> str:
        payload = {
            "prompt": workflow,
        }

        try:
            async with httpx.AsyncClient(
                timeout=30.0
            ) as client:
                response = await client.post(
                    f"{self.base_url}/prompt",
                    json=payload,
                )

        except httpx.ConnectError as exc:
            raise HTTPException(
                status_code=503,
                detail=(
                    "ComfyUI is offline. Start the local "
                    "ComfyUI server on port 8188."
                ),
            ) from exc

        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=502,
                detail=(
                    "Unable to contact local ComfyUI server"
                ),
            ) from exc

        if response.status_code >= 400:
            try:
                error_payload = response.json()
            except ValueError:
                error_payload = response.text

            logger.error(
                "ComfyUI queue rejected workflow: %s",
                error_payload,
            )

            raise HTTPException(
                status_code=502,
                detail=(
                    "ComfyUI rejected the generation "
                    "workflow"
                ),
            )

        try:
            data = response.json()
            prompt_id = data["prompt_id"]
        except (ValueError, KeyError, TypeError) as exc:
            raise HTTPException(
                status_code=502,
                detail=(
                    "ComfyUI returned an invalid queue "
                    "response"
                ),
            ) from exc

        return str(prompt_id)

    async def _wait_for_completion(
        self,
        prompt_id: str,
    ) -> dict[str, Any]:
        deadline = (
            asyncio.get_running_loop().time()
            + self.timeout_seconds
        )

        while (
            asyncio.get_running_loop().time()
            < deadline
        ):
            try:
                async with httpx.AsyncClient(
                    timeout=20.0
                ) as client:
                    response = await client.get(
                        f"{self.base_url}/history/"
                        f"{quote(prompt_id, safe='')}"
                    )

            except httpx.RequestError as exc:
                raise HTTPException(
                    status_code=502,
                    detail=(
                        "Lost connection to ComfyUI while "
                        "waiting for generation"
                    ),
                ) from exc

            if response.status_code >= 400:
                raise HTTPException(
                    status_code=502,
                    detail=(
                        "ComfyUI history request failed"
                    ),
                )

            try:
                history = response.json()
            except ValueError as exc:
                raise HTTPException(
                    status_code=502,
                    detail=(
                        "ComfyUI returned invalid history "
                        "data"
                    ),
                ) from exc

            job = history.get(prompt_id)

            if job:
                status = job.get("status", {})

                if (
                    status.get("status_str")
                    == "error"
                ):
                    raise HTTPException(
                        status_code=502,
                        detail=(
                            "ComfyUI generation execution "
                            "failed"
                        ),
                    )

                outputs = job.get("outputs", {})

                if outputs:
                    return job

            await asyncio.sleep(
                self.poll_interval_seconds
            )

        raise HTTPException(
            status_code=504,
            detail=(
                "ComfyUI generation timed out"
            ),
        )

    def _extract_image_metadata(
        self,
        job: dict[str, Any],
    ) -> dict[str, str]:
        outputs = job.get("outputs", {})

        save_output = outputs.get(
            self.SAVE_IMAGE_NODE,
            {},
        )

        images = save_output.get(
            "images",
            [],
        )

        if not images:
            for output in outputs.values():
                candidate_images = output.get(
                    "images",
                    [],
                )

                if candidate_images:
                    images = candidate_images
                    break

        if not images:
            raise HTTPException(
                status_code=502,
                detail=(
                    "ComfyUI completed without returning "
                    "an image"
                ),
            )

        image = images[0]

        filename = image.get("filename")

        if not filename:
            raise HTTPException(
                status_code=502,
                detail=(
                    "ComfyUI output is missing filename"
                ),
            )

        return {
            "filename": filename,
            "subfolder": image.get(
                "subfolder",
                "",
            ),
            "type": image.get(
                "type",
                "output",
            ),
        }

    async def _download_image(
        self,
        metadata: dict[str, str],
    ) -> bytes:
        params = {
            "filename": metadata["filename"],
            "subfolder": metadata["subfolder"],
            "type": metadata["type"],
        }

        try:
            async with httpx.AsyncClient(
                timeout=60.0
            ) as client:
                response = await client.get(
                    f"{self.base_url}/view",
                    params=params,
                )

        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=502,
                detail=(
                    "Unable to retrieve generated image "
                    "from ComfyUI"
                ),
            ) from exc

        if response.status_code >= 400:
            raise HTTPException(
                status_code=502,
                detail=(
                    "ComfyUI generated image retrieval "
                    "failed"
                ),
            )

        content_type = response.headers.get(
            "content-type",
            "",
        )

        if not content_type.startswith("image/"):
            raise HTTPException(
                status_code=502,
                detail=(
                    "ComfyUI returned non-image output"
                ),
            )

        return response.content

    async def generate_image(
        self,
        prompt: str,
        negative_prompt: str,
        width: int,
        height: int,
        seed: int | None,
    ) -> dict[str, Any]:
        workflow, actual_seed = (
            self._prepare_workflow(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                seed=seed,
            )
        )

        prompt_id = await self._queue_prompt(
            workflow
        )

        job = await self._wait_for_completion(
            prompt_id
        )

        metadata = self._extract_image_metadata(
            job
        )

        image_bytes = await self._download_image(
            metadata
        )

        safe_filename = (
            f"{prompt_id}.png"
        )

        destination = (
            self.output_dir / safe_filename
        ).resolve()

        if self.output_dir not in destination.parents:
            raise HTTPException(
                status_code=500,
                detail="Unsafe output path",
            )

        try:
            destination.write_bytes(image_bytes)
        except OSError as exc:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Unable to persist generated image"
                ),
            ) from exc

        return {
            "provider": "comfyui",
            "status": "completed",
            "prompt_id": prompt_id,
            "asset_url": (
                f"/generated/{safe_filename}"
            ),
            "filename": safe_filename,
            "width": width,
            "height": height,
            "seed": actual_seed,
        }


comfyui_provider = ComfyUIProvider()