"""
多智能体编排层 — 基于 LangGraph 的 StateGraph
实现 "编剧 → 导演 → 评审" 协作流水线

★ 成本控制：
   1. MAX_SCENES 限制场景总数
   2. MAX_CLIP_DURATION 限制片段时长
   3. 遇到 InsufficientFundsError 立即停止后续提交
   4. 累计成本超预算时停止
"""
import os
import json
import uuid
import logging
from typing import TypedDict, List, Dict, Any, Optional, Annotated
from operator import add

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.services.video_generation_service import (
    VideoGenerationService,
    InsufficientFundsError,
)
from app.services.tts_service import TTSService

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# LLM 配置
# ──────────────────────────────────────────────
LLM_API_BASE = os.getenv("LLM_API_BASE", "https://api.groq.com/openai/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen/qwen3.8-27b")

AI_VIDEO_BACKEND = os.getenv("AI_VIDEO_BACKEND", "mock")

# ★ 成本控制参数
MAX_SCENES = int(os.getenv("AI_VIDEO_MAX_SCENES", "3"))            # 最多几个场景
CLIP_DURATION = int(os.getenv("AI_VIDEO_CLIP_DURATION", "8"))      # 每片段秒数
MAX_BUDGET_CENTS = float(os.getenv("AI_VIDEO_MAX_BUDGET_CENTS", "200"))  # 总预算（美分）


# ──────────────────────────────────────────────
# 状态定义
# ──────────────────────────────────────────────
class VideoPipelineState(TypedDict):
    user_idea: str
    target_duration: int
    language: str
    script: str
    scenes: List[Dict[str, Any]]
    clips: Annotated[List[Dict[str, Any]], add]
    errors: Annotated[List[str], add]
    review_passed: bool
    review_notes: str
    final_video_path: Optional[str]
    final_video_id: Optional[str]
    current_step: str
    progress: float
    total_cost_cents: float                 # ★ 累计成本


# ──────────────────────────────────────────────
# LLM 调用
# ──────────────────────────────────────────────
async def call_llm(prompt: str, system_prompt: str = "") -> str:
    import httpx

    if not LLM_API_KEY or not LLM_API_KEY.strip():
        raise RuntimeError(
            "LLM_API_KEY 未配置（请设置 .env 或使用 AI_VIDEO_BACKEND=mock）"
        )
    try:
        LLM_API_KEY.encode("ascii")
    except UnicodeEncodeError:
        raise RuntimeError("LLM_API_KEY 含非 ASCII 字符（可能还是占位符）")

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLM_API_KEY.strip()}",
    }
    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 4096,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{LLM_API_BASE}/chat/completions",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


# ──────────────────────────────────────────────
# ScripterAgent
# ──────────────────────────────────────────────
async def scripter_agent(state: VideoPipelineState) -> Dict[str, Any]:
    logger.info("[ScripterAgent] 开始编剧...")
    user_idea = state["user_idea"]
    target_duration = state.get("target_duration", 24)
    language = state.get("language", "en")

    # ★ 场景数控制：先按目标时长算，再被 MAX_SCENES 限
    raw_scenes = max(1, target_duration // CLIP_DURATION)
    num_scenes = min(raw_scenes, MAX_SCENES)

    logger.info(
        f"[ScripterAgent] target={target_duration}s "
        f"clip={CLIP_DURATION}s "
        f"→ 场景数={num_scenes}（原 {raw_scenes}，上限 {MAX_SCENES}）"
    )

    # mock 模式
    if AI_VIDEO_BACKEND == "mock":
        logger.info("[ScripterAgent] mock 模式")
        scenes = []
        for i in range(num_scenes):
            scenes.append({
                "scene_number": i + 1,
                "description": f"Mock scene {i + 1}: {user_idea}",
                "camera": "Wide shot",
                "characters": ["protagonist"],
                "dialogue": f"This is mock dialogue for scene {i + 1}.",
                "audio_effects": "Ambient background music",
            })
        return {
            "script": f"Mock script for: {user_idea}",
            "scenes": scenes,
            "current_step": "scripting_done",
            "progress": 0.2,
        }

    # ★ 严格告诉 LLM 场景数上限
    system_prompt = (
        "You are a professional AI video screenwriter.\n"
        "\n"
        "Your task: expand the user's idea into a detailed storyboard script.\n"
        "\n"
        "Requirements:\n"
        f"1. Generate EXACTLY {num_scenes} scenes. Do NOT generate more.\n"
        f"2. Each scene should be about {CLIP_DURATION} seconds long.\n"
        "3. Each scene must contain: scene_number, description, camera, "
        "characters, dialogue, audio_effects.\n"
        "4. Ensure narrative coherence and character consistency.\n"
        f"5. IMPORTANT: Write ALL text fields (description, dialogue, "
        f"audio_effects) in the language with BCP-47 code: **{language}**.\n"
        "   Examples: 'en'=English, 'zh-CN'=Simplified Chinese, 'es'=Spanish.\n"
        "6. The `description` field goes directly to a video generation model — "
        "make it visual and concrete (subjects, actions, lighting, mood, motion).\n"
        "7. Output strict JSON only, no markdown fences, no extra text."
    )

    prompt = (
        f"User idea: {user_idea}\n\n"
        f"Generate EXACTLY {num_scenes} scenes.\n\n"
        "Output JSON:\n"
        "{\n"
        '  "script_summary": "...",\n'
        '  "scenes": [\n'
        "    {\n"
        '      "scene_number": 1,\n'
        '      "description": "...",\n'
        '      "camera": "...",\n'
        '      "characters": ["..."],\n'
        '      "dialogue": "...",\n'
        '      "audio_effects": "..."\n'
        "    }\n"
        "  ]\n"
        "}"
    )

    try:
        result = await call_llm(prompt, system_prompt)
        result = result.strip()
        if result.startswith("```json"):
            result = result[7:]
        if result.startswith("```"):
            result = result[3:]
        if result.endswith("```"):
            result = result[:-3]
        parsed = json.loads(result.strip())

        scenes = parsed.get("scenes", [])

        # ★ 二次防御：LLM 可能不听话，超出 MAX_SCENES 就截断
        if len(scenes) > num_scenes:
            logger.warning(
                f"[ScripterAgent] LLM 返回 {len(scenes)} 个场景，"
                f"超出上限 {num_scenes}，已截断"
            )
            scenes = scenes[:num_scenes]

        script = parsed.get("script_summary", "")
        logger.info(f"[ScripterAgent] 完成，{len(scenes)} 个场景（language={language}）")
        return {
            "script": script,
            "scenes": scenes,
            "current_step": "scripting_done",
            "progress": 0.2,
        }
    except Exception as e:
        logger.error(f"[ScripterAgent] 失败: {e}")
        return {
            "script": "",
            "scenes": [],
            "errors": [f"ScripterAgent 失败: {str(e)}"],
            "current_step": "scripting_error",
            "progress": 0.2,
        }


# ──────────────────────────────────────────────
# DirectorAgent
# ──────────────────────────────────────────────
async def director_agent(state: VideoPipelineState) -> Dict[str, Any]:
    logger.info("[DirectorAgent] 开始生成视频片段...")
    scenes = state.get("scenes", [])
    if not scenes:
        return {
            "errors": ["没有可用的场景"],
            "current_step": "directing_error",
            "progress": 0.3,
        }

    video_service = VideoGenerationService()
    clips = []
    errors = []
    total_cost = 0.0
    stopped_by_funds = False

    for i, scene in enumerate(scenes):
        scene_num = scene.get("scene_number", i + 1)

        # ★ 预算检查
        if total_cost >= MAX_BUDGET_CENTS:
            msg = (
                f"累计成本 {total_cost:.1f} 美分已达上限 "
                f"{MAX_BUDGET_CENTS:.1f}，停止生成后续场景"
            )
            logger.warning(f"[DirectorAgent] {msg}")
            errors.append(msg)
            break

        description = scene.get("description", "")
        dialogue = scene.get("dialogue", "")
        audio_effects = scene.get("audio_effects", "")

        video_prompt = description
        if scene.get("camera"):
            video_prompt += f", {scene['camera']}"

        audio_prompt = ""
        if dialogue:
            audio_prompt += f"Dialogue: {dialogue}. "
        if audio_effects:
            audio_prompt += f"Sound effects: {audio_effects}"

        try:
            clip = await video_service.generate_clip(
                prompt=video_prompt,
                audio_prompt=audio_prompt,
                duration=CLIP_DURATION,
            )
            clip["scene_number"] = scene_num
            clip["dialogue"] = dialogue
            clips.append(clip)
            total_cost += clip.get("cost_cents", 0)
            logger.info(
                f"[DirectorAgent] 场景 {scene_num} 生成完成 "
                f"(累计成本 {total_cost:.1f} 美分)"
            )

        except InsufficientFundsError as e:
            # ★ 余额不足 → 立即停止
            error_msg = f"场景 {scene_num} 生成失败（余额不足）: {str(e)}"
            logger.error(f"[DirectorAgent] {error_msg}")
            errors.append(error_msg)
            stopped_by_funds = True
            break

        except Exception as e:
            error_msg = f"场景 {scene_num} 生成失败: {str(e)}"
            logger.error(f"[DirectorAgent] {error_msg}")
            errors.append(error_msg)
            # 继续尝试下一个场景（除非是余额问题）

        progress = 0.3 + (i + 1) / len(scenes) * 0.4

    if stopped_by_funds:
        logger.warning("[DirectorAgent] 因余额不足提前终止")

    return {
        "clips": clips,
        "errors": errors,
        "total_cost_cents": total_cost,
        "current_step": "directing_done",
        "progress": 0.7,
    }


# ──────────────────────────────────────────────
# CriticAgent
# ──────────────────────────────────────────────
async def critic_agent(state: VideoPipelineState) -> Dict[str, Any]:
    logger.info("[CriticAgent] 开始评审...")
    clips = state.get("clips", [])
    errors = state.get("errors", [])

    if not clips:
        return {
            "review_passed": False,
            "review_notes": "没有生成任何有效片段",
            "current_step": "review_failed",
            "progress": 0.8,
        }

    scenes = state.get("scenes", [])
    expected = len(scenes)
    actual = len(clips)
    cost = state.get("total_cost_cents", 0)

    passed = actual == expected and len(errors) == 0
    notes = (
        f"预期 {expected} 个片段，实际生成 {actual} 个。"
        f"累计花费 {cost:.1f} 美分（${cost/100:.2f}）。"
    )
    if errors:
        notes += f" 错误: {'; '.join(errors[:3])}"

    logger.info(f"[CriticAgent] 评审结果: {'通过' if passed else '未通过'} — {notes}")

    return {
        "review_passed": passed,
        "review_notes": notes,
        "current_step": "review_done",
        "progress": 0.8,
    }


# ──────────────────────────────────────────────
# FinalAssembly
# ──────────────────────────────────────────────
async def final_assembly(state: VideoPipelineState) -> Dict[str, Any]:
    logger.info("[FinalAssembly] 开始拼接长视频...")
    clips = state.get("clips", [])
    if not clips:
        return {
            "errors": ["没有可拼接的片段"],
            "current_step": "assembly_failed",
            "progress": 0.9,
        }

    video_service = VideoGenerationService()
    tts_service = TTSService()

    clip_paths = [c["path"] for c in clips if c.get("path")]

    try:
        result = await video_service.stitch_clips(clip_paths)
        final_path = result["path"]
        final_id = result["video_id"]
    except Exception as e:
        logger.error(f"[FinalAssembly] 拼接失败: {e}")
        return {
            "errors": [f"拼接失败: {str(e)}"],
            "current_step": "assembly_failed",
            "progress": 0.9,
        }

    # TTS 配音
    all_dialogue = " ".join(
        c.get("dialogue", "") for c in clips if c.get("dialogue")
    )
    if all_dialogue.strip():
        language = state.get("language", "en")
        try:
            await tts_service.generate_speech(
                text=all_dialogue,
                language=language,
                output_id=f"{final_id}_dub",
            )
            logger.info(f"[FinalAssembly] 配音生成完成（language={language}）")
        except Exception as e:
            logger.warning(f"[FinalAssembly] 配音生成失败（不影响视频）: {e}")

    logger.info(f"[FinalAssembly] 完成，最终视频: {final_path}")
    return {
        "final_video_path": final_path,
        "final_video_id": final_id,
        "current_step": "completed",
        "progress": 1.0,
    }


# ──────────────────────────────────────────────
# 路由 + 工作流
# ──────────────────────────────────────────────
def should_continue_after_review(state: VideoPipelineState) -> str:
    if state.get("review_passed"):
        return "final_assembly"
    if state.get("clips"):
        return "final_assembly"
    return END


def build_video_pipeline() -> StateGraph:
    workflow = StateGraph(VideoPipelineState)
    workflow.add_node("scripter", scripter_agent)
    workflow.add_node("director", director_agent)
    workflow.add_node("critic", critic_agent)
    workflow.add_node("final_assembly", final_assembly)
    workflow.set_entry_point("scripter")
    workflow.add_edge("scripter", "director")
    workflow.add_edge("director", "critic")
    workflow.add_conditional_edges(
        "critic",
        should_continue_after_review,
        {"final_assembly": "final_assembly", END: END},
    )
    workflow.add_edge("final_assembly", END)
    return workflow


_compiled_pipeline = None


def get_compiled_pipeline():
    global _compiled_pipeline
    if _compiled_pipeline is None:
        _compiled_pipeline = build_video_pipeline().compile(
            checkpointer=MemorySaver()
        )
    return _compiled_pipeline


async def run_video_pipeline(
    user_idea: str,
    target_duration: int = 24,
    task_id: Optional[str] = None,
    language: str = "en",
) -> Dict[str, Any]:
    pipeline = get_compiled_pipeline()
    task_id = task_id or uuid.uuid4().hex[:12]

    initial_state = {
        "user_idea": user_idea,
        "target_duration": target_duration,
        "language": language,
        "script": "",
        "scenes": [],
        "clips": [],
        "errors": [],
        "review_passed": False,
        "review_notes": "",
        "final_video_path": None,
        "final_video_id": None,
        "current_step": "initialized",
        "progress": 0.0,
        "total_cost_cents": 0.0,
    }

    config = {"configurable": {"thread_id": task_id}}

    try:
        final_state = await pipeline.ainvoke(initial_state, config)
        logger.info(f"流水线完成: {task_id}")
        return final_state
    except Exception as e:
        logger.error(f"流水线异常: {e}")
        return {
            **initial_state,
            "errors": [str(e)],
            "current_step": "pipeline_error",
        }