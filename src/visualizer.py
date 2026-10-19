import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.patches import Patch
from utils import TruckState
from search_result import SearchResult
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def get_truck_summary(truck_state: TruckState):
    inside_packs = [p for p in truck_state.packs if p.isInside]
    total_weight = sum(p.weight for p in inside_packs)
    total_value = truck_state.count_value()
    fragile_count = sum(1 for p in inside_packs if p.isFragile)
    return {
        "inside_count": len(inside_packs),
        "total_packs": len(truck_state.packs),
        "total_weight": total_weight,
        "capacity": truck_state.cap,
        "total_value": total_value,
        "fragile_count": fragile_count
    }

def plot_truck_3d(ax, truck_state: TruckState, title: str):
    W = truck_state.dim.width
    H = truck_state.dim.height
    L = truck_state.dim.length

    # di Matplotlib 3D, sumbu vertikal itu Z, urutan jadi (X=Width, Y_plot=Length, Z_plot=Height)
    ax.set_xlim(0, W)
    ax.set_ylim(0, L)
    ax.set_zlim(0, H)

    ax.set_xlabel("X - Width")
    ax.set_ylabel("Z - Length")
    ax.set_zlabel("Y - Height (Vertikal)")

    ax.set_box_aspect((W, L, H))

    inside_packs = [p for p in truck_state.packs if p.isInside]
    for pack in inside_packs:
        x = pack.pos.x
        y_vert = pack.pos.y
        z_depth = pack.pos.z

        dx = pack.dim.width
        dy_vert = pack.dim.height
        dz_depth = pack.dim.length

        color = "#e63946" if pack.isFragile else "#457b9d"
        ax.bar3d(
            x, z_depth, y_vert,
            dx, dz_depth, dy_vert,
            color=color,
            alpha=0.82,
            edgecolor="#1d3557",
            linewidth=0.8
        )

        cx = x + dx / 2.0
        cz = z_depth + dz_depth / 2.0
        cy = y_vert + dy_vert / 2.0
        ax.text(cx, cz, cy, f"P{pack.id}", color="white", fontsize=8,
                ha="center", va="center", weight="bold")

    summary = get_truck_summary(truck_state)
    subtitle = (
        f"{title}\n"
        f"Value: {summary['total_value']} | "
        f"Paket: {summary['inside_count']}/{summary['total_packs']} | "
        f"Berat: {summary['total_weight']}/{summary['capacity']}"
    )
    ax.set_title(subtitle, fontsize=10, fontweight="bold", pad=12)

def plot_comparison_3d(init_state: TruckState, final_state: TruckState):
    fig = plt.figure(figsize=(14, 6))

    ax1 = fig.add_subplot(1, 2, 1, projection="3d")
    plot_truck_3d(ax1, init_state, "Initial State")

    ax2 = fig.add_subplot(1, 2, 2, projection="3d")
    plot_truck_3d(ax2, final_state, "Final State")

    legend_elements = [
        Patch(facecolor="#457b9d", edgecolor="#1d3557", label="Paket Reguler (isFragile=False)"),
        Patch(facecolor="#e63946", edgecolor="#1d3557", label="Paket Pecah Belah (isFragile=True)")
    ]
    fig.legend(handles=legend_elements, loc="lower center", ncol=2, frameon=True, fontsize=9)
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    return fig

def plot_metrics_2d(result: SearchResult, algo_name: str):
    algo_lower = algo_name.lower()

    # khusus Simulated Annealing: Objective Function + Plot e^(Delta E / T)
    if "annealing" in algo_lower:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 4.5))

        iterations = range(len(result.obj_history))
        ax1.plot(iterations, result.obj_history, color="#1d3557", linewidth=1.8, label="Current State Value")
        ax1.axhline(
            y=result.final_state.count_value(),
            color="#e63946",
            linestyle="--",
            linewidth=1.2,
            label=f"Best Value ({result.final_state.count_value()})"
        )
        ax1.set_title("Objective Function (count_value) vs Iterasi", fontweight="bold")
        ax1.set_xlabel("Iterasi")
        ax1.set_ylabel("Nilai Objective Function")
        ax1.grid(True, linestyle="--", alpha=0.5)
        ax1.legend()

        e_hist = result.metrics.get("e_delta_t_history", [])
        ax2.plot(range(1, len(e_hist) + 1), e_hist, color="#f4a261", linewidth=1.0, alpha=0.85)
        ax2.set_title(r"Probabilitas Penerimaan ($e^{\Delta E / T}$) vs Iterasi", fontweight="bold")
        ax2.set_xlabel("Iterasi")
        ax2.set_ylabel(r"$e^{\Delta E / T}$")
        ax2.set_ylim(-0.05, 1.05)
        ax2.grid(True, linestyle="--", alpha=0.5)

        fig.tight_layout()
        return fig

    # khusus Genetic Algorithm: Maksimum & Rata-rata Populasi
    elif "genetic" in algo_lower:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        iterations = range(len(result.obj_history))

        ax.plot(
            iterations,
            result.obj_history,
            color="#1948C2",
            linestyle="-",
            linewidth=2.2,
            label="Max Objective Function"
        )

        avg_hist = result.metrics.get("avg_obj_history", [])
        if avg_hist:
            ax.plot(
                range(len(avg_hist)),
                avg_hist,
                color="#1948C2",
                linestyle="--",
                linewidth=1.8,
                alpha=0.65,
                label="Rata-rata Objective Function"
            )

        ax.set_title(f"Kurva Eksperimen {algo_name}", fontweight="bold")
        ax.set_xlabel("Generasi / Iterasi")
        ax.set_ylabel("Nilai Objective Function")
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend()
        fig.tight_layout()
        return fig

    # plot standar untuk seluruh variasi Hill Climbing
    else:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        iterations = range(len(result.obj_history))
        ax.plot(iterations, result.obj_history, color="#2a9d8f", linewidth=2.0, label="Objective Value")
        ax.set_title(f"Objective Function vs Iterasi ({algo_name})", fontweight="bold")
        ax.set_xlabel("Iterasi")
        ax.set_ylabel("Nilai Objective Function")
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend()
        fig.tight_layout()
        return fig

def box_edges(x, y, z, dx, dy, dz):
    c = [(x, y, z), (x+dx, y, z), (x+dx, y+dy, z), (x, y+dy, z),
         (x, y, z+dz), (x+dx, y, z+dz), (x+dx, y+dy, z+dz), (x, y+dy, z+dz)]
    ex, ey, ez = [], [], []
    for a, b in [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]:
        ex += [c[a][0], c[b][0], None]   # None breaks the line between segments
        ey += [c[a][1], c[b][1], None]
        ez += [c[a][2], c[b][2], None]
    return ex, ey, ez

def box_vertices(x, y, z, dx, dy, dz):
    xs = [x, x, x + dx, x + dx, x, x, x + dx, x + dx]
    ys = [y, y + dy, y + dy, y, y, y + dy, y + dy, y]
    zs = [z, z, z, z, z + dz, z + dz, z + dz, z + dz]
    return xs, ys, zs

def plot_truck_3d_movable(fig, truck, title, scene):
    width, height, length = truck.dim.width, truck.dim.height, truck.dim.length
    col = scene
    scene_name = f"scene{scene}"

    cx = [0, width, width, 0, 0, None, 0, width, width, 0, 0, None, 0, 0, None, width, width, None, width, width, None, 0, 0]
    cy = [0, 0, length, length, 0, None, 0, 0, length, length, 0, None, 0, 0, None, 0, 0, None, length, length, None, length, length]
    cz = [0, 0, 0, 0, 0, None, height, height, height, height, height, None, 0, height, None, 0, height, None, 0, height, None, 0, height]
    fig.add_trace(go.Scatter3d(x=cx, y=cy, z=cz, mode="lines",
                               line=dict(color="black", width=3),
                               showlegend=False, hoverinfo="skip"),
                  row=1, col=col)
    label_x, label_y, label_z, label_t = [], [], [], []
    for p in truck.packs:
        if not p.isInside:
            continue
        x, y, z = p.pos.x, p.pos.z, p.pos.y
        dx, dy, dz = p.dim.width, p.dim.length, p.dim.height
        vx, vy, vz = box_vertices(x, y, z, dx, dy, dz)
        color = "#e63946" if p.isFragile else "#457b9d"
        ex, ey, ez = box_edges(x, y, z, dx, dy, dz)
        fig.add_trace(go.Mesh3d(
            x=vx, y=vy, z=vz, 
            i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], 
            j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], 
            k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
            color=color, 
            opacity=1.0, 
            flatshading=True,
            lighting=dict(ambient=0.6, diffuse=0.8, specular=0.1),
            hovertext=(f"P{p.id}<br>value={p.value}<br>weight={p.weight}"
                       f"<br>fragile={p.isFragile}<br>pos=({p.pos.x}, {p.pos.y}, {p.pos.z})"
                       f"<br>size=({p.dim.width}, {p.dim.height}, {p.dim.length})"),
            hoverinfo="text", showlegend=False
        ), row=1, col=col)
        fig.add_trace(go.Scatter3d(
            x=ex, y=ey, z=ez,
            mode="lines",
            line=dict(color="black", width=2),
            showlegend=False
        ))
        label_x.append(x + dx / 2); label_y.append(y + dy / 2)
        label_z.append(z + dz / 2); label_t.append(f"P{p.id}")

    fig.add_trace(go.Scatter3d(x=label_x, y=label_y, z=label_z, text=label_t,
                               mode="text", textfont=dict(color="white", size=11),
                               showlegend=False, hoverinfo="skip"),
                  row=1, col=col)

    fig.update_layout(**{scene_name: dict(
        xaxis=dict(title="X - Width", range=[0, width]),
        yaxis=dict(title="Z - Length", range=[0, length]),
        zaxis=dict(title="Y - Height", range=[0, height]),
        aspectmode="manual", aspectratio=dict(x=width, y=length, z=height),
    )})

def plot_comparison_3d_interactive(init_state: TruckState, final_state: TruckState):
    si, sf = get_truck_summary(init_state), get_truck_summary(final_state)
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "scene"}, {"type": "scene"}]],
        subplot_titles=(
            f"Initial State<br>Value: {si['total_value']} | Paket: {si['inside_count']}/{si['total_packs']} | Berat: {si['total_weight']}/{si['capacity']}",
            f"Final State<br>Value: {sf['total_value']} | Paket: {sf['inside_count']}/{sf['total_packs']} | Berat: {sf['total_weight']}/{sf['capacity']}",
        ),
    )
    plot_truck_3d_movable(fig, init_state, "Initial State", 1)
    plot_truck_3d_movable(fig, final_state, "Final State", 2)
    fig.update_layout(height=600, margin=dict(l=0, r=0, t=80, b=0))
    return fig