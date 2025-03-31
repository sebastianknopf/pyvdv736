import logging

from vdv736.sirixml import get_value as sirixml_get_value

from abc import ABC, abstractmethod
from datetime import datetime
from datetime import timezone


class BaseSituationHandler(ABC):

    @abstractmethod
    def handle_situation(cls, pts, chaining_result=True) -> bool:
        """Returns whether the situation object can be discarded or not."""
        pass

class SituationProgressHandler(BaseSituationHandler):

    @classmethod
    def handle_situation(cls, pts, chaining_result=True) -> bool:
        situation_id = sirixml_get_value(pts, 'SituationNumber')
        situation_progress = sirixml_get_value(pts, 'Progress', None)

        if situation_progress is None:
            logging.warning(f"Situation {situation_id} has not set Progress attribute!")
        
        if situation_progress == 'closed':
            return False
        elif situation_progress == 'closing':
            situation_versioned_at = sirixml_get_value(pts, 'VersionedAtTime', None)
            if situation_versioned_at is not None:
                situation_versioned_at = datetime.fromisoformat(situation_versioned_at.replace('Z', '+00:00'))
                situation_deprecation_difference_minutes = int((datetime.now(timezone.utc) - situation_versioned_at).total_seconds() // 60)

                if situation_deprecation_difference_minutes >= 5:
                    return False
                else:
                    return chaining_result
            else:
                return chaining_result
        else:
            return chaining_result