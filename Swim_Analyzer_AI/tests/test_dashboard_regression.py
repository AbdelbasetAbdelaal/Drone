import pytest
from unittest.mock import patch, MagicMock
from app.ui.dashboard import render_dashboard_page

def test_dashboard_invokes_get_all_sessions_with_principal():
    with patch('app.ui.dashboard.st') as mock_st, \
         patch('app.ui.dashboard.AthleteService') as MockAthleteService, \
         patch('app.ui.dashboard.AnalysisHistoryService') as MockHistoryService:
        
        # Setup mock principal
        mock_coach = MagicMock()
        mock_coach.coach_id = "test_coach_id"
        mock_st.session_state.get.return_value = mock_coach
        
        # Setup mock services
        mock_athlete_instance = MockAthleteService.return_value
        mock_athlete_instance.get_all_profiles.return_value = []
        
        mock_history_instance = MockHistoryService.return_value
        mock_history_instance.get_all_sessions.return_value = []
        
        render_dashboard_page()
        
        # Verify get_all_profiles was called with coach_id
        mock_athlete_instance.get_all_profiles.assert_called_once_with(coach_id="test_coach_id")
        
        # Verify get_all_sessions was called with principal
        mock_history_instance.get_all_sessions.assert_called_once_with(principal=mock_coach)
