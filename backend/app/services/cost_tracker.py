"""
AI 视频成本追踪器

由于 LTX-2 没有公开的余额查询 API，本模块自己维护消费账本。
数据存储在 JSON 文件里（容器内 /app/outputs/ai_videos/.cost_ledger.json），
每次提交前查询、完成后更新。

★ 容器重建会丢这个文件。生产环境建议存到数据库或 named volume。
"""
import os
import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# 账本文件路径
LEDGER_PATH = Path(
    os.getenv("AI_VIDEO_COST_LEDGER", "/app/outputs/ai_videos/.cost_ledger.json")
)
LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)

# 每日消费上限（美分）—— 默认 $5/天
DAILY_LIMIT_CENTS = float(os.getenv("AI_VIDEO_DAILY_LIMIT_CENTS", "500"))

# 每次任务上限（美分）—— 默认 $2/次
PER_TASK_LIMIT_CENTS = float(os.getenv("AI_VIDEO_MAX_BUDGET_CENTS", "200"))

# 每秒钟的价格（美分）
PRICE_PER_SECOND_CENTS = float(
    os.getenv("LTX2_PRICE_PER_SECOND_CENTS", "7.5")
)


class CostTracker:
    """本地成本追踪器（JSON 文件持久化）"""

    def __init__(self):
        self._ledger = self._load()

    def _load(self) -> Dict[str, Any]:
        """加载账本"""
        if not LEDGER_PATH.exists():
            return {"daily": {}, "tasks": {}}
        try:
            with open(LEDGER_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"[CostTracker] 加载失败: {e}，重置")
            return {"daily": {}, "tasks": {}}

    def _save(self):
        """保存账本"""
        try:
            with open(LEDGER_PATH, "w", encoding="utf-8") as f:
                json.dump(self._ledger, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"[CostTracker] 保存失败: {e}")

    def today_spent_cents(self) -> float:
        """今日已消费（美分）"""
        today = date.today().isoformat()
        return float(self._ledger["daily"].get(today, 0.0))

    def estimate_task_cost(self, num_scenes: int, clip_duration: int) -> float:
        """预估一次任务成本（美分）"""
        return num_scenes * clip_duration * PRICE_PER_SECOND_CENTS

    def can_start_task(self, est_cost_cents: float) -> tuple[bool, str]:
        """
        检查是否可以启动任务。
        Returns: (allowed, reason_if_not)
        """
        # 单任务上限
        if est_cost_cents > PER_TASK_LIMIT_CENTS:
            return False, (
                f"预估成本 {est_cost_cents:.1f} 美分超过单次上限 "
                f"{PER_TASK_LIMIT_CENTS:.1f} 美分"
            )

        # 每日上限
        today = self.today_spent_cents()
        if today + est_cost_cents > DAILY_LIMIT_CENTS:
            return False, (
                f"今日已消费 {today:.1f} 美分，本次需 {est_cost_cents:.1f} 美分，"
                f"超过每日上限 {DAILY_LIMIT_CENTS:.1f} 美分"
            )

        return True, ""

    def record_task_start(self, task_id: str, est_cost_cents: float):
        """记录任务开始（预扣）"""
        self._ledger["tasks"][task_id] = {
            "estimated": est_cost_cents,
            "actual": 0.0,
            "started_at": datetime.utcnow().isoformat(),
            "status": "running",
        }
        self._save()

    def record_task_done(
        self, task_id: str, actual_cost_cents: float, success: bool
    ):
        """记录任务完成，更新每日消费"""
        task = self._ledger["tasks"].get(task_id, {})
        task["actual"] = actual_cost_cents
        task["status"] = "completed" if success else "failed"
        task["done_at"] = datetime.utcnow().isoformat()
        self._ledger["tasks"][task_id] = task

        # 更新每日累计
        today = date.today().isoformat()
        current = self._ledger["daily"].get(today, 0.0)
        self._ledger["daily"][today] = current + actual_cost_cents

        self._save()

        logger.info(
            f"[CostTracker] 任务 {task_id} 完成: 实际花费 {actual_cost_cents:.1f} 美分，"
            f"今日累计 {self._ledger['daily'][today]:.1f} 美分"
        )

    def get_summary(self) -> Dict[str, Any]:
        """获取消费摘要"""
        return {
            "today_spent_cents": self.today_spent_cents(),
            "daily_limit_cents": DAILY_LIMIT_CENTS,
            "per_task_limit_cents": PER_TASK_LIMIT_CENTS,
            "price_per_second_cents": PRICE_PER_SECOND_CENTS,
            "recent_tasks": list(self._ledger["tasks"].items())[-10:],
        }


# 全局单例
cost_tracker = CostTracker()