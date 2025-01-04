from bin import Bin
from box import Box 

import plotly.graph_objects as go

def add_cuboid(fig, x, y, z, width, depth, height, color, opacity=0.6, name="", show_top=True):
    """
    Add a 3D cuboid to the Plotly figure with an optional top surface.
    """
    # Define the 8 corner points of the cuboid
    x_vals = [x, x + width, x + width, x, x, x + width, x + width, x]
    y_vals = [y, y, y + depth, y + depth, y, y, y + depth, y + depth]
    z_vals = [z, z, z, z, z + height, z + height, z + height, z + height]

    # Define faces (remove the top face if show_top is False)
    faces = [
        (0, 1, 5), (0, 5, 4),  # Bottom
        (1, 2, 6), (1, 6, 5),  # Right
        (2, 3, 7), (2, 7, 6),  # Top (disabled if `show_top=False`)
        (3, 0, 4), (3, 4, 7),  # Left
        (0, 1, 2), (0, 2, 3),  # Front
        (4, 5, 6), (4, 6, 7)   # Back
    ]

    if not show_top:
        faces = faces[:-2]  # Remove the top face for bins

    i_faces = [f[0] for f in faces]
    j_faces = [f[1] for f in faces]
    k_faces = [f[2] for f in faces]

    fig.add_trace(go.Mesh3d(
        x=x_vals,
        y=y_vals,
        z=z_vals,
        i=i_faces,
        j=j_faces,
        k=k_faces,
        color=color,
        opacity=opacity,
        name=name
    ))

def plot_bins(bins: Bin):
    """
    Plot bins without a top surface and boxes with a top surface in 3D using Plotly.
    """
    fig = go.Figure()

    # Define colors for boxes
    colors = [
        "#636EFA", "#EF553B", "#00CC96", "#AB63FA",
        "#FFA15A", "#19D3F3", "#FF6692", "#B6E880"
    ]

    # Offset for separating bins
    bin_offset = 1

    for bin_idx, bin in enumerate(bins):
        # Calculate the offset for this bin
        bin_x_offset = bin_idx * (bin.width + bin_offset)
        bin_y_offset = 0

        # Add the bin as a black wireframe cuboid without a top surface
        add_cuboid(
            fig,
            bin_x_offset,
            bin_y_offset,
            0,
            bin.width,
            bin.depth,
            bin.height,
            color="black",
            opacity=0.4,
            name=f"Bin {bin_idx + 1}",
            show_top=False  # Skip top surface for bins
        )

        for box_idx, box in enumerate(bin.boxes):
            x, y, z = box.position

            # Apply the offset to the box position
            x_offset = x + bin_x_offset
            y_offset = y + bin_y_offset

            # Add the box as a colored cuboid with a top surface
            add_cuboid(
                fig,
                x_offset,
                y_offset,
                z,
                box.width,
                box.depth,
                box.height,
                color=colors[box_idx % len(colors)],
                opacity=1,
                name=f"Bin {bin_idx + 1}, Box {box_idx + 1}",
                show_top=True  # Show top surface for boxes
            )

    # Set axis labels and layout
    fig.update_layout(
        scene=dict(
            xaxis_title="Width",
            yaxis_title="Depth",
            zaxis_title="Height",
        ),
        title="3D Bin Packing Visualization with Bins and Boxes",
        showlegend=True,
    )
    fig.show()
