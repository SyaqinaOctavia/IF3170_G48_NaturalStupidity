import streamlit as st
import pandas as pd
from utils import Dimension, TruckState
from state import random_state, randomize_pack
from simmulated_annealing import simmulate_annealing
from hill_climbing import *
from visualizer import plot_comparison_3d, plot_comparison_3d_interactive, plot_metrics_2d, get_truck_summary

st.set_page_config(
    page_title="Dashboard",
    layout="wide"
)

st.title("Eksperimen Local Search")
st.caption("Visualisasi State 3D, Kurva Konvergensi 2D, dan Pencatatan Log Eksperimen")

# PANEL SAMPING (PARAMETER)
with st.sidebar:
    st.header("1. Konfigurasi Kontainer & Paket")
    col_w, col_h, col_l = st.columns(3)
    with col_w:
        truck_w = st.number_input("Width (X)", min_value=2, max_value=30, value=6)
    with col_h:
        truck_h = st.number_input("Height (Y)", min_value=2, max_value=30, value=6)
    with col_l:
        truck_l = st.number_input("Length (Z)", min_value=2, max_value=30, value=6)

    truck_cap = st.number_input("Kapasitas Berat (cap)", min_value=10, max_value=5000, value=150, step=10)
    n_packs = st.number_input("Jumlah Paket (n_packs)", min_value=1, max_value=100, value=15)
    fragile_prob = st.slider("Probabilitas Fragile", min_value=0.0, max_value=1.0, value=0.25, step=0.05)
    use_seed = st.checkbox("Gunakan Seed Tetap", value=False)
    seed_val = st.number_input("Nilai Seed", value=42, step=1) if use_seed else None

    if st.button("Initial State Baru", use_container_width=True):
        dim = Dimension(int(truck_w), int(truck_h), int(truck_l))
        st.session_state["base_state"] = random_state(
            truck_dim=dim,
            cap=int(truck_cap),
            n_packs=int(n_packs),
            fragile_prob=float(fragile_prob),
            seed=int(seed_val) if seed_val is not None else None
        )
        st.session_state.pop("experiment_runs", None)

    st.divider()
    st.header("2. Pilihan Algoritma & Parameter")
    algo_choice = st.selectbox(
        "Pilih Algoritma",
        [
            "Simulated Annealing",
            "Steepest Ascent Hill Climbing",
            "Stochastic Hill Climbing",
            "Hill Climbing with Sideways Move",
            "Random Restart Hill Climbing",
            "Genetic Algorithm"
        ]
    )

    # Parameter spesifik per algoritma
    algo_params = {}
    if algo_choice == "Simulated Annealing":
        algo_params["T0"] = st.number_input("Suhu Awal (T0)", min_value=1.0, max_value=10000.0, value=200.0, step=10.0)
        algo_params["alpha"] = st.number_input("Faktor Pendinginan (alpha)", min_value=0.800, max_value=0.9999, value=0.995, step=0.001, format="%.4f")

    elif algo_choice == "Hill Climbing with Sideways Move":
        algo_params["max_sideways_move"] = st.number_input("Batas Maksimum Sideways Move", min_value=1, max_value=1000, value=50)

    elif algo_choice == "Random Restart Hill Climbing":
        algo_params["max_restart"] = st.number_input("Batas Maksimum Restart", min_value=1, max_value=100, value=10)

    elif algo_choice == "Genetic Algorithm":
        ga_mode = st.radio(
            "Mode Eksperimen GA",
            [
                "Single Konfigurasi",
                "Kontrol Populasi (3 Variasi Iterasi)",
                "Kontrol Iterasi (3 Variasi Populasi)"
            ]
        )
        algo_params["ga_mode"] = ga_mode
        if ga_mode == "Single Konfigurasi":
            algo_params["pop_size"] = st.number_input("Jumlah Populasi", min_value=2, max_value=500, value=30)
            algo_params["max_iter"] = st.number_input("Banyak Iterasi", min_value=1, max_value=2000, value=100)
        elif ga_mode == "Kontrol Populasi (3 Variasi Iterasi)":
            algo_params["pop_size"] = st.number_input("Jumlah Populasi (Tetap)", min_value=2, max_value=500, value=30)
            algo_params["iter_vars"] = st.text_input("3 Variasi Iterasi (pisahkan koma)", value="50, 100, 200")
        else:
            algo_params["max_iter"] = st.number_input("Banyak Iterasi (Tetap)", min_value=1, max_value=2000, value=100)
            algo_params["pop_vars"] = st.text_input("3 Variasi Populasi (pisahkan koma)", value="20, 50, 100")

    st.divider()
    st.header("3. Mode Eksekusi")
    run_mode = st.radio("Jumlah Eksekusi", ["Single Run (1x)", "Batch Run (3x Eksperimen)"])
    randomize_each_run = st.checkbox(
        "Acak ulang posisi paket (randomize_pack) tiap Run pada Batch",
        value=True,
        help="Jika dicentang, setiap run menggunakan daftar paket yang sama namun dengan posisi awal yang diacak ulang."
    )

    run_btn = st.button("Jalankan Eksperimen", type="primary", use_container_width=True)

# Inisialisasi state awal jika belum ada di session_state
if "base_state" not in st.session_state:
    init_dim = Dimension(int(truck_w), int(truck_h), int(truck_l))
    st.session_state["base_state"] = random_state(
        truck_dim=init_dim,
        cap=int(truck_cap),
        n_packs=int(n_packs),
        fragile_prob=float(fragile_prob),
        seed=int(seed_val) if seed_val is not None else None
    )

# Helper untuk mengosongkan truk lalu mengacak ulang posisi paket yang sama
def re_randomize_existing_packs(base_truck: TruckState) -> TruckState:
    empty_truck = base_truck.copy()
    for p in empty_truck.packs:
        p.isInside = False
        p.pos.move(0, 0, 0)
    return randomize_pack(empty_truck)

# Run algorithm
if run_btn:
    num_runs = 3 if "Batch" in run_mode else 1

    if algo_choice == "Simulated Annealing":
        runs_output = []
        progress = st.progress(0, text="Menjalankan Simulated Annealing...")
        for i in range(num_runs):
            if i == 0 or not randomize_each_run:
                start_state = st.session_state["base_state"].copy()
            else:
                start_state = re_randomize_existing_packs(st.session_state["base_state"])

            res = simmulate_annealing(
                start_state,
                T0=algo_params["T0"],
                alpha=algo_params["alpha"]
            )
            runs_output.append((f"Run #{i + 1}", res))
            progress.progress((i + 1) / num_runs, text=f"Selesai Run #{i + 1} dari {num_runs}")

        progress.empty()
        st.session_state["experiment_runs"] = {
            "algo": algo_choice,
            "runs": runs_output
        }
    elif algo_choice == "Steepest Ascent Hill Climbing":
        runs_output = []
        progress = st.progress(0, text="Menjalankan Steepest Ascent Hill Climbing...")
        for i in range(num_runs):
            if i == 0 or not randomize_each_run:
                start_state = st.session_state["base_state"].copy()
            else:
                start_state = re_randomize_existing_packs(st.session_state["base_state"])

            res = steepest_ascent(start_state)
            runs_output.append((f"Run #{i + 1}", res))
            progress.progress((i + 1) / num_runs, text=f"Selesai Run #{i + 1} dari {num_runs}")

        progress.empty()
        st.session_state["experiment_runs"] = {
            "algo": algo_choice,
            "runs": runs_output
        }
    elif algo_choice == "Stochastic Hill Climbing":
        runs_output = []
        progress = st.progress(0, text="Menjalankan Stochastic Hill Climbing...")
        for i in range(num_runs):
            if i == 0 or not randomize_each_run:
                start_state = st.session_state["base_state"].copy()
            else:
                start_state = re_randomize_existing_packs(st.session_state["base_state"])

            res = stochastic(start_state)
            runs_output.append((f"Run #{i + 1}", res))
            progress.progress((i + 1) / num_runs, text=f"Selesai Run #{i + 1} dari {num_runs}")

        progress.empty()
        st.session_state["experiment_runs"] = {
            "algo": algo_choice,
            "runs": runs_output
        }
    elif algo_choice == "Hill Climbing with Sideways Move":
        runs_output = []
        progress = st.progress(0, text="Menjalankan Hill Climbing with Sideways Move...")
        for i in range(num_runs):
            if i == 0 or not randomize_each_run:
                start_state = st.session_state["base_state"].copy()
            else:
                start_state = re_randomize_existing_packs(st.session_state["base_state"])

            res = sideways_move(
                start_state,
                max_sideways=algo_params["max_sideways_move"]
            )
            runs_output.append((f"Run #{i + 1}", res))
            progress.progress((i + 1) / num_runs, text=f"Selesai Run #{i + 1} dari {num_runs}")

        progress.empty()
        st.session_state["experiment_runs"] = {
            "algo": algo_choice,
            "runs": runs_output
        }
    elif algo_choice == "Random Restart Hill Climbing":
        runs_output = []
        progress = st.progress(0, text="Menjalankan Random Restart Hill Climbing...")
        for i in range(num_runs):
            if i == 0 or not randomize_each_run:
                start_state = st.session_state["base_state"].copy()
            else:
                start_state = re_randomize_existing_packs(st.session_state["base_state"])

            res = random_restart(
                start_state,
                max_restart=algo_params["max_restart"]
            )
            runs_output.append((f"Run #{i + 1}", res))
            progress.progress((i + 1) / num_runs, text=f"Selesai Run #{i + 1} dari {num_runs}")

        progress.empty()
        st.session_state["experiment_runs"] = {
            "algo": algo_choice,
            "runs": runs_output
        }
    else:
        st.warning(
            f"Modul **{algo_choice}** belum diimplementasikan oleh anggota tim. "
            f"Setelah fungsi tersedia, cukup panggil fungsi tersebut di blok eksekusi `app.py` "
            f"dan kembalikan objek `SearchResult`."
        )

# TAMPILAN STATE AWAL (SEBELUM RUN)
if "experiment_runs" not in st.session_state:
    st.subheader("Preview Initial State Saat Ini")
    base_summary = get_truck_summary(st.session_state["base_state"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Nilai Objective Awal", base_summary["total_value"])
    c2.metric("Paket Terangkut", f"{base_summary['inside_count']} / {base_summary['total_packs']}")
    c3.metric("Total Berat / Kapasitas", f"{base_summary['total_weight']} / {base_summary['capacity']}")
    c4.metric("Paket Pecah Belah (Fragile)", base_summary["fragile_count"])

    interactive = st.toggle("Interaktif", value=False)
    if interactive:
        st.plotly_chart(plot_comparison_3d_interactive(st.session_state["base_state"], st.session_state["base_state"]),
                        use_container_width=True)
    else:
        fig = plot_comparison_3d(st.session_state["base_state"], st.session_state["base_state"])
        st.pyplot(fig)

# TAMPILAN HASIL DAN PANEL LOG
else:
    exp_data = st.session_state["experiment_runs"]
    algo_used = exp_data["algo"]
    runs_list = exp_data["runs"]

    st.subheader(f"Log Eksperimen - {algo_used}")

    # Membangun tabel 
    summary_rows = []
    for run_label, res in runs_list:
        init_sum = get_truck_summary(res.initial_state)
        final_sum = get_truck_summary(res.final_state)

        row = {
            "Run": run_label,
            "Objective Awal": init_sum["total_value"],
            "Objective Akhir (Best)": final_sum["total_value"],
            "Peningkatan (Delta)": final_sum["total_value"] - init_sum["total_value"],
            "Paket Masuk (Awal -> Akhir)": f"{init_sum['inside_count']} -> {final_sum['inside_count']}",
            "Berat Akhir / Cap": f"{final_sum['total_weight']} / {final_sum['capacity']}",
            "Durasi (detik)": round(res.duration, 4),
            "Total Iterasi": res.metrics.get("iterations", len(res.obj_history) - 1),
        }

        if algo_used == "Simulated Annealing":
            row["Frekuensi Stuck Local Optima"] = res.metrics.get("stuck_count", 0)
            row["Nilai Akhir Current State"] = res.metrics.get("final_current_value", "-")
        elif algo_used == "Hill Climbing with Sideways Move":
            row["Jumlah Sideways Move"] = res.metrics.get("sideways_count", 0)
        elif algo_used == "Random Restart Hill Climbing":
            row["Banyak Restart"] = res.metrics.get("restarts", 0)
            row["Iterasi per Restart"] = str(res.metrics.get("iter_per_restart", []))
        elif algo_used == "Genetic Algorithm":
            row["Jumlah Populasi"] = res.metrics.get("pop_size", "-")
            row["Banyak Iterasi"] = res.metrics.get("max_iter", "-")

        summary_rows.append(row)

    df_summary = pd.DataFrame(summary_rows)
    st.dataframe(df_summary, use_container_width=True, hide_index=True)

    # Tabs untuk melihat detail visualisasi 3D dan plot 2D pada masing-masing run
    tab_labels = [label for label, _ in runs_list]
    tabs = st.tabs(tab_labels)

    for idx, (tab, (run_label, res)) in enumerate(zip(tabs, runs_list)):
        with tab:
            init_sum = get_truck_summary(res.initial_state)
            final_sum = get_truck_summary(res.final_state)

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Objective Awal", init_sum["total_value"])
            m2.metric(
                "Objective Akhir",
                final_sum["total_value"],
                delta=final_sum["total_value"] - init_sum["total_value"]
            )
            m3.metric("Durasi Eksekusi", f"{res.duration:.4f} s")
            m4.metric("Total Iterasi", res.metrics.get("iterations", 0))

            if algo_used == "Simulated Annealing":
                m5.metric("Frekuensi Stuck", res.metrics.get("stuck_count", 0))
            elif algo_used == "Hill Climbing with Sideways Move":
                m5.metric("Sideways Move", res.metrics.get("sideways_count", 0))
            elif algo_used == "Random Restart Hill Climbing":
                m5.metric("Jumlah Restart", res.metrics.get("restarts", 0))
            elif algo_used == "Genetic Algorithm":
                m5.metric("Populasi", res.metrics.get("pop_size", "-"))

            st.markdown("#### 1. Komparasi Visualisasi 3D (Initial State vs Final State)")
            interactive = st.toggle("Interaktif", value=False)
            if interactive:
                fig_3d = plot_comparison_3d_interactive(res.initial_state, res.final_state)
                st.plotly_chart(fig_3d, use_container_width=True, key=f"3d_{idx}")
            else:
                fig = plot_comparison_3d(res.initial_state, res.final_state)
                st.pyplot(fig)

            st.markdown("#### 2. Grafik Kurva Eksperimen 2D")
            fig_2d = plot_metrics_2d(res, algo_used)
            st.pyplot(fig_2d)

            with st.expander("Lihat Detail Paket pada Final State"):
                pack_rows = []
                for p in res.final_state.packs:
                    pack_rows.append({
                        "ID Paket": f"P{p.id}",
                        "Status": "Di Dalam Truk" if p.isInside else "Di Luar",
                        "Fragile": "Ya" if p.isFragile else "Tidak",
                        "Value": p.value,
                        "Weight": p.weight,
                        "Posisi (x, y, z)": f"({p.pos.x}, {p.pos.y}, {p.pos.z})" if p.isInside else "-",
                        "Dimensi (W x H x L)": f"{p.dim.width} x {p.dim.height} x {p.dim.length}",
                        "ETA": p.eta
                    })
                st.dataframe(pd.DataFrame(pack_rows), use_container_width=True, hide_index=True)