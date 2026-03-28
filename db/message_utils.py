import json
import os
from typing import List, Optional, Tuple


def get_messages_around(file_path: str, message_id: str, above: int = 50, below: int = 50) -> Tuple[Optional[List[dict]], Optional[int], Optional[int]]:
    """
    Get messages centered around a specific message ID.
    
    Args:
        file_path: Path to the JSON Lines file
        message_id: The message ID to center around
        above: Number of messages to include above (after) the target
        below: Number of messages to include below (before) the target
    
    Returns:
        Tuple of (messages, start_idx, end_idx) or (None, None, None) if message not found
    """
    if not os.path.exists(file_path):
        return None, None, None
    
    above = max(0, min(above, 200))
    below = max(0, min(below, 200))
    
    target_idx = None
    total_lines = 0
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            total_lines = idx + 1
            if target_idx is None and f'"id":"{message_id}"' in line:
                target_idx = idx
    
    if target_idx is None:
        return None, None, None
    
    start_line = max(0, target_idx - below)
    end_line = min(total_lines, target_idx + above + 1)
    
    messages = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            if idx >= start_line and idx < end_line:
                try:
                    messages.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
            elif idx >= end_line:
                break
    
    return messages, start_line, end_line
