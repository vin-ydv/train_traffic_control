"""3D Visualization of train traffic control network.

Provides interactive 3D visualization of:
  - Railway network topology (stations and blocks in 3D space)
  - Train positions and movements along tracks
  - Real-time conflict detection with visual indicators
  - Block occupancy and direction of travel
"""

from __future__ import annotations
from typing import Optional
import plotly.graph_objects as go
import numpy as np
from engine.simulation import Simulation
from ui.theme import BG, TEXT, ACCENT, RED, GREEN, AMBER


# ==================== 3D Scene Colors ====================
COLOR_DOUBLE_LINE = GREEN  # Green
COLOR_SINGLE_LINE = AMBER  # Orange
COLOR_STATION = ACCENT      # Blue
COLOR_TRAIN_DOWN = "#E91E63"   # Pink (downbound)
COLOR_TRAIN_UP = "#00BCD4"     # Cyan (upbound)
COLOR_CONFLICT = RED     # Red (conflict)
COLOR_TRACK_BG = "#1e293b"     # Dark gray
COLOR_BLOCK_OCCUPIED = "#FFEB3B"  # Yellow


def draw_3d_network(sim: Simulation, height: int = 700) -> go.Figure:
    """Create interactive 3D visualization of the entire rail network.
    
    Args:
        sim: Simulation instance with network topology
        height: Height of the figure in pixels
        
    Returns:
        Plotly Figure object with 3D scatter and line traces
    """
    fig = go.Figure()
    
    # ========== Draw Stations (3D nodes) ==========
    stations = sim.net.stations
    station_x, station_y, station_z = [], [], []
    station_names = []
    
    for sid, station in stations.items():
        station_x.append(station.x)
        station_y.append(station.y)
        station_z.append(0)  # Base level
        station_names.append(f"{sid}<br>{station.name}<br>Loops: {station.loops}")
    
    fig.add_trace(
        go.Scatter3d(
            x=station_x,
            y=station_y,
            z=station_z,
            mode="markers+text",
            marker=dict(
                size=12,
                color=COLOR_STATION,
                opacity=0.9,
                line=dict(color="white", width=2),
            ),
            text=[sid for sid in stations.keys()],
            textposition="top center",
            textfont=dict(size=11, color="white", family="Arial Black"),
            hovertext=station_names,
            hoverinfo="text",
            name="Stations",
        )
    )
    
    # ========== Draw Blocks (3D track segments) ==========
    for block in sim.net.blocks:
        from_station = stations.get(block.from_id)
        to_station = stations.get(block.to_id)
        
        if not from_station or not to_station:
            continue
        
        # Determine color based on block type
        block_color = COLOR_DOUBLE_LINE if block.double_line else COLOR_SINGLE_LINE
        
        # Create elevation profile (slight curve for visualization)
        t = np.linspace(0, 1, 50)
        x_curve = from_station.x + (to_station.x - from_station.x) * t
        y_curve = from_station.y + (to_station.y - from_station.y) * t
        z_curve = np.sin(t * np.pi) * 5  # Slight elevation
        
        # Determine opacity based on occupancy
        occupancy = "occupied" if (block.occupant_up or block.occupant_down) else "free"
        line_color = COLOR_BLOCK_OCCUPIED if occupancy == "occupied" else block_color
        line_width = 4 if occupancy == "occupied" else 2
        
        block_type = "Double-line" if block.double_line else "Single-line"
        hover_text = f"{block.id}<br>{block_type}<br>{block.length_km} km<br>Status: {occupancy}"
        
        fig.add_trace(
            go.Scatter3d(
                x=x_curve,
                y=y_curve,
                z=z_curve,
                mode="lines",
                line=dict(color=line_color, width=line_width),
                name=f"Block {block.id}",
                hovertext=[hover_text] * len(x_curve),
                hoverinfo="text",
                showlegend=False,
            )
        )
    
    # ========== Draw Trains (3D moving objects) ==========
    train_x, train_y, train_z = [], [], []
    train_colors = []
    train_names = []
    train_hover = []
    
    for train in sim.trains:
        if train.finished or not train.entered_section:
            continue
        
        x, y = sim.train_position(train)
        train_x.append(x)
        train_y.append(y)
        
        # Elevation based on priority (visual hierarchy)
        z = train.priority * 2
        train_z.append(z)
        
        # Color by direction
        color = COLOR_TRAIN_DOWN if train.direction == "down" else COLOR_TRAIN_UP
        train_colors.append(color)
        
        # Status text
        status = (
            f"At {train.at_station}" if train.at_station
            else f"On {train.on_block}" if train.on_block
            else "Waiting"
        )
        
        train_hover.append(
            f"<b>{train.number}</b><br>"
            f"{train.name}<br>"
            f"Type: {train.type}<br>"
            f"Priority: {train.priority}<br>"
            f"Passengers: {train.pax}<br>"
            f"Status: {status}<br>"
            f"Delay: {max(0, sim.time - train.planned_dep)}m"
        )
        train_names.append(train.number)
    
    if train_x:
        fig.add_trace(
            go.Scatter3d(
                x=train_x,
                y=train_y,
                z=train_z,
                mode="markers+text",
                marker=dict(
                    size=10,
                    color=train_colors,
                    opacity=0.95,
                    line=dict(color="white", width=1),
                    symbol="diamond",
                ),
                text=train_names,
                textposition="top center",
                textfont=dict(size=9, color="white"),
                hovertext=train_hover,
                hoverinfo="text",
                name="Trains",
            )
        )
    
    # ========== Highlight Conflicts ==========
    conflict_x, conflict_y, conflict_z = [], [], []
    conflict_labels = []
    
    for block in sim.net.blocks:
        if block.occupant_up and block.occupant_down and block.occupant_up != block.occupant_down:
            # Safety violation: two different trains on single-line block
            from_station = stations.get(block.from_id)
            to_station = stations.get(block.to_id)
            if from_station and to_station:
                conflict_x.append((from_station.x + to_station.x) / 2)
                conflict_y.append((from_station.y + to_station.y) / 2)
                conflict_z.append(8)
                conflict_labels.append(f"⚠️ CONFLICT<br>Block: {block.id}")
    
    if conflict_x:
        fig.add_trace(
            go.Scatter3d(
                x=conflict_x,
                y=conflict_y,
                z=conflict_z,
                mode="markers+text",
                marker=dict(
                    size=18,
                    color=COLOR_CONFLICT,
                    opacity=0.85,
                    symbol="x",
                    line=dict(color="white", width=2),
                ),
                text=["⚠️"] * len(conflict_x),
                textfont=dict(size=14),
                name="🚨 Conflicts",
                hovertext=conflict_labels,
                hoverinfo="text",
            )
        )
    
    # ========== Layout Configuration ==========
    fig.update_layout(
        title=dict(
            text=f"<b>🚆 RailMind 3D Network Visualization (T+{sim.time}m)</b>",
            font=dict(size=18, color=TEXT),
        ),
        scene=dict(
            xaxis=dict(
                title="<b>Distance (km)</b>",
                backgroundcolor=COLOR_TRACK_BG,
                gridcolor="#334155",
                showbackground=True,
                titlefont=dict(color=TEXT),
            ),
            yaxis=dict(
                title="<b>Lateral offset</b>",
                backgroundcolor=COLOR_TRACK_BG,
                gridcolor="#334155",
                showbackground=True,
                titlefont=dict(color=TEXT),
            ),
            zaxis=dict(
                title="<b>Elevation / Priority</b>",
                backgroundcolor=COLOR_TRACK_BG,
                gridcolor="#334155",
                showbackground=True,
                titlefont=dict(color=TEXT),
            ),
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.3),
            ),
        ),
        hovermode="closest",
        margin=dict(l=0, r=0, t=60, b=0),
        paper_bgcolor=BG,
        font=dict(color=TEXT, family="Arial"),
        height=height,
        showlegend=True,
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor="rgba(15, 23, 42, 0.8)",
            bordercolor=TEXT,
            borderwidth=1,
        ),
    )
    
    return fig


def draw_3d_timeline(sim: Simulation, height: int = 500) -> go.Figure:
    """Create 3D visualization showing train progress over time.
    
    Each train is a trajectory: X=distance, Y=time, Z=passenger load.
    
    Args:
        sim: Simulation instance
        height: Figure height
        
    Returns:
        Plotly Figure with train trajectories
    """
    fig = go.Figure()
    
    finished_trains = [t for t in sim.trains if t.finished]
    
    for train in finished_trains:
        # Reconstruct approximate trajectory
        route = (sim.net.down_route if train.direction == "down"
                else sim.net.up_route)
        
        stations = sim.net.stations
        idx_o = route.index(train.origin) if train.origin in route else 0
        idx_d = route.index(train.dest) if train.dest in route else len(route) - 1
        
        traj_x = []
        traj_y = []
        traj_z = []
        
        cumulative_dist = 0
        for i in range(min(idx_o, idx_d), max(idx_o, idx_d)):
            from_st = stations.get(route[i])
            to_st = stations.get(route[i + 1])
            if from_st and to_st:
                dist = np.sqrt((to_st.x - from_st.x)**2 + (to_st.y - from_st.y)**2)
                traj_x.append(cumulative_dist)
                traj_y.append(train.finish_time if train.finished else sim.time)
                traj_z.append(train.pax)
                cumulative_dist += dist
        
        if traj_x:
            color = COLOR_TRAIN_DOWN if train.direction == "down" else COLOR_TRAIN_UP
            fig.add_trace(
                go.Scatter3d(
                    x=traj_x,
                    y=traj_y,
                    z=traj_z,
                    mode="lines+markers",
                    line=dict(color=color, width=3),
                    marker=dict(size=5, opacity=0.7),
                    name=f"{train.number} ({train.type})",
                    hovertext=[f"{train.number}<br>Passengers: {train.pax}"] * len(traj_x),
                    hoverinfo="text",
                )
            )
    
    if not finished_trains:
        fig.add_annotation(
            text="No finished trains yet. Simulation in progress...",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color=TEXT),
        )
    
    fig.update_layout(
        title=dict(
            text="<b>🚆 Train Journey Timeline (Distance vs Time vs Passengers)</b>",
            font=dict(size=18, color=TEXT),
        ),
        scene=dict(
            xaxis_title="<b>Distance along section (km)</b>",
            yaxis_title="<b>Time (minutes)</b>",
            zaxis_title="<b>Passengers</b>",
            camera=dict(eye=dict(x=1.5, y=1.2, z=1.2)),
            xaxis=dict(backgroundcolor=COLOR_TRACK_BG, gridcolor="#334155"),
            yaxis=dict(backgroundcolor=COLOR_TRACK_BG, gridcolor="#334155"),
            zaxis=dict(backgroundcolor=COLOR_TRACK_BG, gridcolor="#334155"),
        ),
        hovermode="closest",
        paper_bgcolor=BG,
        font=dict(color=TEXT, family="Arial"),
        height=height,
        showlegend=True,
        margin=dict(l=0, r=0, t=60, b=0),
    )
    
    return fig


def draw_3d_conflict_heatmap(sim: Simulation, height: int = 500) -> go.Figure:
    """Create heatmap showing conflict intensity across blocks.
    
    Args:
        sim: Simulation instance
        height: Figure height
        
    Returns:
        Plotly Figure with conflict heatmap
    """
    blocks = sim.net.blocks
    block_ids = [b.id for b in blocks]
    
    # Build conflict matrix
    conflict_data = []
    for block in blocks:
        occupancy = 0
        if block.occupant_up:
            occupancy += 1
        if block.occupant_down:
            occupancy += 1
        conflict_data.append(occupancy)
    
    fig = go.Figure(
        data=go.Heatmap(
            z=[conflict_data],
            x=block_ids,
            y=["Block Occupancy"],
            colorscale="Reds",
            colorbar=dict(
                title="Occupancy<br>(trains)",
                titlefont=dict(color=TEXT),
                tickfont=dict(color=TEXT),
            ),
            hovertemplate="<b>%{x}</b><br>Trains: %{z}<extra></extra>",
        )
    )
    
    fig.update_layout(
        title=dict(
            text=f"<b>Block Occupancy Heatmap (T+{sim.time}m)</b>",
            font=dict(size=18, color=TEXT),
        ),
        xaxis_title="<b>Block ID</b>",
        yaxis_title="",
        paper_bgcolor=BG,
        font=dict(color=TEXT, family="Arial"),
        height=height,
        margin=dict(l=50, r=50, t=80, b=50),
        xaxis=dict(side="bottom", tickfont=dict(size=11)),
        yaxis=dict(tickfont=dict(size=11)),
    )
    
    return fig


def draw_3d_block_status(sim: Simulation, height: int = 500) -> go.Figure:
    """Create 3D bar chart showing block occupancy and conflict status.
    
    Args:
        sim: Simulation instance
        height: Figure height
        
    Returns:
        Plotly Figure with 3D bars
    """
    blocks = sim.net.blocks
    block_ids = [b.id for b in blocks]
    occupancy = []
    colors = []
    
    for block in blocks:
        occ = 0
        if block.occupant_up:
            occ += 1
        if block.occupant_down:
            occ += 1
        occupancy.append(occ)
        
        # Color based on status
        if occ == 0:
            colors.append(GREEN)
        elif occ == 1:
            colors.append(AMBER)
        else:
            colors.append(RED)  # Safety violation
    
    fig = go.Figure(
        data=[go.Bar(
            x=block_ids,
            y=occupancy,
            marker=dict(
                color=colors,
                line=dict(color=TEXT, width=1),
            ),
            text=occupancy,
            textposition="auto",
            textfont=dict(size=12, color="white", family="Arial Black"),
            hovertemplate="<b>%{x}</b><br>Trains: %{y}<extra></extra>",
        )]
    )
    
    fig.update_layout(
        title=dict(
            text=f"<b>Block Status Dashboard (T+{sim.time}m)</b>",
            font=dict(size=18, color=TEXT),
        ),
        xaxis_title="<b>Block ID</b>",
        yaxis_title="<b>Number of Trains</b>",
        paper_bgcolor=BG,
        plot_bgcolor=COLOR_TRACK_BG,
        font=dict(color=TEXT, family="Arial"),
        height=height,
        margin=dict(l=60, r=30, t=80, b=60),
        xaxis=dict(tickfont=dict(size=11)),
        yaxis=dict(tickfont=dict(size=11), dtick=1),
        showlegend=False,
    )
    
    return fig
