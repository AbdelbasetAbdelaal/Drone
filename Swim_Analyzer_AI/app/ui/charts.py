import pandas as pd
import plotly.graph_objects as go

# Premium Neon/Dark Theme Colors
BACKGROUND_COLOR = "rgba(0,0,0,0)" # Transparent to fit Streamlit dark mode
GRID_COLOR = "#333333"
TEXT_COLOR = "#E0E0E0"
PRIMARY_CYAN = "#00F0FF"
SECONDARY_BLUE = "#0055FF"
ACCENT_PINK = "#FF007F"
ACCENT_ORANGE = "#FF8C00"

def apply_premium_layout(fig: go.Figure, title: str):
    """Applies a consistent, premium dark theme to a Plotly figure."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color=TEXT_COLOR, family="Inter, sans-serif")),
        plot_bgcolor=BACKGROUND_COLOR,
        paper_bgcolor=BACKGROUND_COLOR,
        font=dict(color=TEXT_COLOR, family="Inter, sans-serif"),
        margin=dict(l=40, r=40, t=60, b=40),
        xaxis=dict(showgrid=True, gridcolor=GRID_COLOR, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor=GRID_COLOR, zeroline=False),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def create_performance_trend_chart(df: pd.DataFrame) -> go.Figure:
    """
    Creates a premium line chart for Performance Score over time using Plotly.
    """
    if "DateTime" not in df.columns:
        df["DateTime"] = pd.to_datetime(df["Date"] + " " + df["Time"])
        
    df = df.sort_values(by="DateTime")

    hover_text = df.apply(
        lambda row: f"<b>Date:</b> {row['Date']} {row['Time']}<br>"
                    f"<b>Score:</b> {row['Score']}<br>"
                    f"<b>Confidence:</b> {row['Confidence']}<br>"
                    f"<b>Stroke:</b> {row['Stroke']}",
        axis=1
    )

    fig = go.Figure()
    
    # Glowing filled area under the line
    fig.add_trace(go.Scatter(
        x=df['DateTime'],
        y=df['Score'],
        mode='lines+markers',
        name='Performance Score',
        line=dict(color=PRIMARY_CYAN, width=4, shape='spline'),
        marker=dict(size=8, color=TEXT_COLOR, line=dict(color=PRIMARY_CYAN, width=2)),
        fill='tozeroy',
        fillcolor='rgba(0, 240, 255, 0.1)', # Faint cyan glow
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
            line=dict(color='rgba(0, 240, 255, 0.3)', width=5, dash='dot'),
            hoverinfo='skip'
        ))

    fig = apply_premium_layout(fig, "Performance Score Progression")
    fig.update_yaxes(title="Overall Score", range=[max(0, df['Score'].min() - 10), min(100, df['Score'].max() + 10)])
    fig.update_xaxes(title="Session Date", fixedrange=False)
    return fig

def create_cycles_trend_chart(df: pd.DataFrame) -> go.Figure:
    """
    Creates a premium bar chart for Completed Cycles over time.
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
        marker_color=ACCENT_PINK, 
        marker_line_color=TEXT_COLOR,
        marker_line_width=1,
        text=hover_text,
        hoverinfo="text"
    ))

    fig = apply_premium_layout(fig, "Completed Cycles (Endurance Trend)")
    fig.update_yaxes(title="Cycles Completed", fixedrange=False)
    fig.update_xaxes(title="Session Date", fixedrange=False)
    
    return fig

