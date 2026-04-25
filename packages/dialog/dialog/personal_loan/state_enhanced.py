"""Enhanced DialogState with memory and sentiment support.

This extends the base DialogState with Tier 1 improvements.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

# Import base state
from .state import DialogState as BaseDialogState, SlotSet, TurnRecord, DialogNode


class EnhancedSlotSet(SlotSet):
    """Extended slots with sentiment tracking."""
    # Existing slots from base
    # ... inherited ...

    # NEW: Current sentiment state
    sentiment_valence: Optional[float] = None  # -1 to +1
    sentiment_arousal: Optional[float] = None  # 0 to 1
    frustration_level: Optional[float] = None  # 0 to 1
    detected_emotion: Optional[str] = None  # "frustrated", "interested", etc.


class DialogStateEnhanced(BaseDialogState):
    """Enhanced dialog state with memory and sentiment.

    Adds:
    - Conversation memory (runtime only, not persisted)
    - Sentiment tracking
    - Memory-aware context
    """

    # Override slots with enhanced version
    slots: EnhancedSlotSet = Field(default_factory=EnhancedSlotSet)

    # NEW: Memory context (retrieved from long-term memory)
    memory_context: str = ""

    # NEW: Key facts extracted
    key_facts: dict[str, str] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True
