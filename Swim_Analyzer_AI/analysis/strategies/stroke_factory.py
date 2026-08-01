from models.data_models import StrokeType
from analysis.strategies.base_strategy import BaseStrokeStrategy
from analysis.strategies.freestyle_strategy import FreestyleStrategy

class StrokeStrategyFactory:
    """Creates the appropriate Stroke Strategy based on the identified stroke type."""
    
    @staticmethod
    def get_strategy(stroke_type: StrokeType) -> BaseStrokeStrategy:
        if stroke_type == StrokeType.FREESTYLE or stroke_type == StrokeType.AUTO_DETECT:
            return FreestyleStrategy()
        # For now, if other strokes are selected but not implemented, fallback to Freestyle or raise NotImplementedError.
        # But we want to allow users to select it and test UI, so let's fallback to Freestyle but log a warning.
        # In a real scenario we'd raise NotImplementedError or return a specific strategy.
        import logging
        logging.getLogger(__name__).warning(f"Strategy for {stroke_type.value} not fully implemented. Falling back to Freestyle strategy skeleton.")
        return FreestyleStrategy()
