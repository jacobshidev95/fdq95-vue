"""
多智能体编排层 — 基于 LangGraph 的 StateGraph
实现 "编剧 → 导演 → 评审" 协作流水线

设计参考：
- ViMax 的多智能体协作框架 (HKUDS/ViMax)
- ScriptAgent 的 ScripterAgent / DirectorAgent / CriticAgent 架构
- LangGraph 的状态管理机制
"""
import os
import json
import uuid
import logging
from typing import TypedDict, List, Dict, Any, Optional, Annotated
from operator import add

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.services.video_generation_service import VideoGenerationService
from app.services.tts_service import TTSService

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# LLM 配置（兼容 OpenAI 格式）
# ──────────────────────────────────────────────
LLM_API_BASE = os.getenv("LLM_API_BASE", "https://api.openai.com/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# 生成后端（mock / ltx2 / mova）
AI_VIDEO_BACKEND = os.getenv("AI_VIDEO_BACKEND", "mock")


# ──────────────────────────────────────────────
# 状态定义 — 在整个流水线中流转
# ──────────────────────────────────────────────
class VideoPipelineState(TypedDict):
    """视频生成流水线的全局状态"""
    # 输入
    user_idea: str                          # 用户输入的创意/对话
    target_duration: int                    # 目标时长（秒）

    language: str  # ★ 新增

    # 编剧阶段
    script: str                             # 完整剧本
    scenes: List[Dict[str, Any]]            # 分镜列表

    # 导演阶段
    clips: Annotated[List[Dict[str, Any]], add]  # 生成的视频片段
    errors: Annotated[List[str], add]       # 错误记录

    # 评审阶段
    review_passed: bool                     # 评审是否通过
    review_notes: str                       # 评审意见

    # 最终输出
    final_video_path: Optional[str]
    final_video_id: Optional[str]

    # 进度追踪
    current_step: str
    progress: float                         # 0.0 ~ 1.0


# ──────────────────────────────────────────────
# LLM 调用工具函数
# ──────────────────────────────────────────────
async def call_llm(prompt: str, system_prompt: str = "") -> str:
    """调用 LLM 生成文本（兼容 OpenAI 格式的 API）"""
    import httpx

    # ★ 防御：key 为空时给出清晰错误，避免 Illegal header value
    if not LLM_API_KEY or not LLM_API_KEY.strip():
        raise RuntimeError(
            "LLM_API_KEY 未配置，无法调用 LLM（请设置 .env 或使用 AI_VIDEO_BACKEND=mock）"
        )

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
# 智能体 1：编剧智能体 (ScripterAgent)
# ──────────────────────────────────────────────
async def scripter_agent(state: VideoPipelineState) -> Dict[str, Any]:
    """
    将用户创意扩写为专业分镜剧本
    - 若 AI_VIDEO_BACKEND=mock：跳过 LLM
    - 否则：把 language 传进 prompt，让 LLM 用该语言输出
    """
    logger.info("[ScripterAgent] 开始编剧...")
    user_idea = state["user_idea"]
    target_duration = state.get("target_duration", 60)
    language = state.get("language", "en")          # 'en' / 'zh-CN' / 'es' / ...
    clip_duration = 10
    num_scenes = max(1, target_duration // clip_duration)

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

    # ★ 唯一的改动：把 language 传给 LLM
    system_prompt = (
        "You are a professional AI video screenwriter.\n"
        "\n"
        "Your task: expand the user's idea into a detailed storyboard script.\n"
        "\n"
        "Requirements:\n"
        "1. Split the content into multiple scenes, each about 10 seconds.\n"
        "2. Each scene must contain: scene_number, description, camera, "
        "characters, dialogue, audio_effects.\n"
        "3. Ensure narrative coherence and character consistency.\n"
        f"4. IMPORTANT: Write ALL text fields (description, dialogue, "
        f"audio_effects) in the language with BCP-47 code: **{language}**.\n"
        "   Examples: 'en'=English, 'zh-CN'=Simplified Chinese, 'es'=Spanish, "
        "'fr'=French, 'ja'=Japanese.\n"
        "5. The `description` field goes directly to a video generation model — "
        "make it visual and concrete (subjects, actions, lighting, mood, motion).\n"
        "6. Output strict JSON only, no markdown fences, no extra text."
    )

    prompt = (
        f"User idea: {user_idea}\n\n"
        f"Generate {num_scenes} scenes.\n\n"
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
# 智能体 2：导演智能体 (DirectorAgent)
# ──────────────────────────────────────────────
async def director_agent(state: VideoPipelineState) -> Dict[str, Any]:
    """
    调用视频生成模型，逐场景生成视频片段

    参考 ScriptAgent 的 DirectorAgent：
    拆分场景 → 锚定帧 → 调用视频模型 → 保证一致性
    """
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

    for i, scene in enumerate(scenes):
        scene_num = scene.get("scene_number", i + 1)
        description = scene.get("description", "")
        dialogue = scene.get("dialogue", "")
        audio_effects = scene.get("audio_effects", "")

        # 构建视频生成 prompt
        video_prompt = description
        if scene.get("camera"):
            video_prompt += f", {scene['camera']}"

        # 构建音频 prompt
        audio_prompt = ""
        if dialogue:
            audio_prompt += f"Dialogue: {dialogue}. "
        if audio_effects:
            audio_prompt += f"Sound effects: {audio_effects}"

        try:
            clip = await video_service.generate_clip(
                prompt=video_prompt,
                audio_prompt=audio_prompt,
                duration=10,
            )
            clip["scene_number"] = scene_num
            clip["dialogue"] = dialogue
            clips.append(clip)
            logger.info(f"[DirectorAgent] 场景 {scene_num} 生成完成")
        except Exception as e:
            error_msg = f"场景 {scene_num} 生成失败: {str(e)}"
            logger.error(f"[DirectorAgent] {error_msg}")
            errors.append(error_msg)

        # 更新进度
        progress = 0.3 + (i + 1) / len(scenes) * 0.4

    return {
        "clips": clips,
        "errors": errors,
        "current_step": "directing_done",
        "progress": 0.7,
    }


# ──────────────────────────────────────────────
# 智能体 3：评审智能体 (CriticAgent)
# ──────────────────────────────────────────────
async def critic_agent(state: VideoPipelineState) -> Dict[str, Any]:
    """
    对生成的视频片段进行质量评审

    参考 ScriptAgent 的 CriticAgent：
    检查视觉质量、叙事连贯性、音画同步
    """
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

    # 评审逻辑：检查是否所有场景都成功生成
    scenes = state.get("scenes", [])
    expected = len(scenes)
    actual = len(clips)

    passed = actual == expected and len(errors) == 0
    notes = f"预期 {expected} 个片段，实际生成 {actual} 个。"
    if errors:
        notes += f" 错误: {'; '.join(errors)}"

    logger.info(f"[CriticAgent] 评审结果: {'通过' if passed else '未通过'} — {notes}")

    return {
        "review_passed": passed,
        "review_notes": notes,
        "current_step": "review_done",
        "progress": 0.8,
    }


# ──────────────────────────────────────────────
# 最终组装节点：拼接长视频 + 配音
# ──────────────────────────────────────────────
async def final_assembly(state: VideoPipelineState) -> Dict[str, Any]:
    """
    将生成的片段拼接为长视频，并叠加 TTS 配音
    """
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

    # 1. 提取所有片段路径
    clip_paths = [c["path"] for c in clips if c.get("path")]

    # 2. 拼接视频
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

    # 3. 如果有对白，生成配音（可选）
    # 3. 如果有对白，生成配音
    all_dialogue = " ".join(
        c.get("dialogue", "") for c in clips if c.get("dialogue")
    )
    if all_dialogue.strip():
        language = state.get("language", "en")  # ★ 取语言
        try:
            await tts_service.generate_speech(
                text=all_dialogue,
                language=language,  # ★ 传给 TTS
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
# 条件路由
# ──────────────────────────────────────────────
def should_continue_after_review(state: VideoPipelineState) -> str:
    """评审后的路由决策"""
    if state.get("review_passed"):
        return "final_assembly"
    else:
        # 评审未通过，检查是否有片段
        if state.get("clips"):
            return "final_assembly"  # 有片段就继续拼接
        return END  # 完全没有片段，终止


# ──────────────────────────────────────────────
# 构建 LangGraph 工作流
# ──────────────────────────────────────────────
def build_video_pipeline() -> StateGraph:
    """
    构建视频生成多智能体工作流

    流程：
    scripter → director → critic → (条件) → final_assembly → END
    """
    workflow = StateGraph(VideoPipelineState)

    # 添加节点
    workflow.add_node("scripter", scripter_agent)
    workflow.add_node("director", director_agent)
    workflow.add_node("critic", critic_agent)
    workflow.add_node("final_assembly", final_assembly)

    # 设置入口
    workflow.set_entry_point("scripter")

    # 添加边
    workflow.add_edge("scripter", "director")
    workflow.add_edge("director", "critic")

    # 条件边：评审后决定是否继续
    workflow.add_conditional_edges(
        "critic",
        should_continue_after_review,
        {
            "final_assembly": "final_assembly",
            END: END,
        },
    )

    workflow.add_edge("final_assembly", END)

    return workflow


# ──────────────────────────────────────────────
# 对外接口：编译并运行流水线
# ──────────────────────────────────────────────
_compiled_pipeline = None


def get_compiled_pipeline():
    """获取编译后的流水线（单例）"""
    global _compiled_pipeline
    if _compiled_pipeline is None:
        workflow = build_video_pipeline()
        _compiled_pipeline = workflow.compile(checkpointer=MemorySaver())
    return _compiled_pipeline


async def run_video_pipeline(
    user_idea: str,
    target_duration: int = 60,
    task_id: Optional[str] = None,
    language: str = "en",                       # ★ 新增
) -> Dict[str, Any]:
    """
    运行完整的视频生成流水线

    Args:
        user_idea: 用户创意
        target_duration: 目标时长（秒）
        task_id: 任务 ID（用于状态追踪）

    Returns:
        最终状态字典
    """
    pipeline = get_compiled_pipeline()
    task_id = task_id or uuid.uuid4().hex[:12]

    initial_state = {
        "user_idea": user_idea,
        "target_duration": target_duration,
        "language": language,  # ★ 加进 state
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