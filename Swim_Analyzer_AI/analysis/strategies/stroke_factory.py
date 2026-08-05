from models.data_models import StrokeType
from analysis.strategies.base_strategy import BaseStrokeStrategy
from analysis.strategies.freestyle_strategy import FreestyleStrategy
from analysis.strategies.backstroke_strategy import BackstrokeStrategy

class StrokeStrategyFactory:
    """Creates the appropriate Stroke Strategy based on the identified stroke type."""
    
    @staticmethod
    def get_strategy(stroke_type: StrokeType) -> BaseStrokeStrategy:
        if stroke_type == StrokeType.FREESTYLE or stroke_type == StrokeType.AUTO_DETECT:
            return FreestyleStrategy()
        elif stroke_type == StrokeType.BACKSTROKE:
            return BackstrokeStrategy()
        # For now, if other strokes are selected but not implemented, fallback to Freestyle or raise NotImplementedError.
        import logging
        logging.getLogger(__name__).warning(f"Strategy for {stroke_type.value} not fully implemented. Falling back to Freestyle strategy skeleton.")
        return FreestyleStrategy()
