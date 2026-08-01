import pandas as pd
import plotly.graph_objects as go

def create_performance_trend_chart(df: pd.DataFrame) -> go.Figure:
    """
    Creates a line chart for Performance Score over time using Plotly.
    Designed to scale and support zoom/pan with professional theming.
    """
    if "DateTime" not in df.columns:
        df["DateTime"] = pd.to_datetime(df["Date"] + " " + df["Time"])
        
    # Sort chronologically
    df = df.sort_values(by="DateTime")

    # Create hover text
    hover_text = df.apply(
        lambda row: f"<b>Date:</b> {row['Date']} {row['Time']}<br>"
                    f"<b>Score:</b> {row['Score']}<br>"
                    f"<b>Confidence:</b> {row['Confidence']}<br>"
                    f"<b>Stroke:</b> {row['Stroke']}",
        axis=1
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['DateTime'],
        y=df['Score'],
        mode='lines+markers',
        name='Performance Score',
        line=dict(color='#1f77b4', width=3, shape='spline'), # Blue, smooth curve
        marker=dict(size=8, color='#1f77b4', line=dict(width=2, color='white')),
        text=hover_text,
        hoverinfo="text"
    ))

    # Add trendline (moving average) if we have enough points (e.g., > 5)
    if len(df) >= 5:
        ma = df['Score'].rolling(window=3, min_periods=1).mean()
        fig.add_trace(go.Scatter(
            x=df['DateTime'],
            y=ma,
            mode='lines',
            name='Trend (3-Session Avg)',
            line=dict(color='rgba(31, 119, 180, 0.3)', width=5, dash='dot'),
            hoverinfo='skip'
        ))

    fig.update_layout(
        title="Performance Score Progression",
        xaxis_title="Session Date",
        yaxis_title="Overall Score",
        yaxis=dict(range=[max(0, df['Score'].min() - 10), min(100, df['Score'].max() + 10)]),
        hovermode="closest",
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40),
        xaxis=dict(fixedrange=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

def create_cycles_trend_chart(df: pd.DataFrame) -> go.Figure:
    """
    Creates a bar chart for Completed Cycles over time.
    """
    if "DateTime" not in df.columns:
        df["DateTime"] = pd.to_datetime(df["Date"] + " " + df["Time"])
        
    df = df.sort_values(by="DateTime")

    hover_text = df.apply(
        lambda row: f"<b>Date:</b> {row['Date']} {row['Time']}<br>"
                    f"<b>Cycles:</b> {row['Cycles']}<br>"
                    f"<b>Stroke:</b> {row['Stroke']}",
        axis=1
    )

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['DateTime'],
        y=df['Cycles'],
        name='Completed Cycles',
        marker_color='#ff7f0e', # Orange for cycles/rate
        marker_line_color='white',
        marker_line_width=1,
        text=hover_text,
        hoverinfo="text"
    ))

    fig.update_layout(
        title="Completed Cycles (Endurance Trend)",
        xaxis_title="Session Date",
        yaxis_title="Cycles Completed",
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40),
        xaxis=dict(fixedrange=False),
        yaxis=dict(fixedrange=False)
    )
    
    return fig
