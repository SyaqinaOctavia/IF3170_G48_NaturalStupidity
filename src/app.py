import streamlit as st
import pandas as pd
import json
from utils import Dimension, TruckState
from state import random_state, randomize_pack
from simmulated_annealing import simmulate_annealing
from hill_climbing import *
from genetic_algorithm import genetic_algorithm # Import fungsi Genetic Algorithm
from visualizer import plot_comparison_3d, plot_comparison_3d_interactive, plot_metrics_2d, plot_ga_comparison_2d, get_truck_summary

st.set_page_config(
    page_title="Dashboard",
    layout="wide"
)

st.title("Dashboard Local Search")
# st.caption("Visualisasi State 3D, Kurva Konvergensi 2D, dan Pencatatan Log Eksperimen")

def truck_state_to_json(truck_state: TruckState) -> str:
    data = {
        "truck": {
            "dim": {
                "width": int(truck_state.dim.width),
                "height": int(truck_state.dim.height),
                "length": int(truck_state.dim.length)
            },
            "cap": int(truck_state.cap)
        },
        "packs": [
            {
                "id": int(p.id),
                "dim": {
                    "width": int(p.dim.width),
                    "height": int(p.dim.height),
                    "length": int(p.dim.length)
                },
                "pos": {
                    "x": int(p.pos.x),
                    "y": int(p.pos.y),
                    "z": int(p.pos.z)
                },
                "orientation":{
                    "w":"x",
                    "h":"y",
                    "l":"z"
                },
                "value": int(p.value),
                "weight": int(p.weight),
                "isFragile": bool(p.isFragile),
                "eta": int(p.eta),
                "isInside": bool(p.isInside)
            }
            for p in truck_state.packs
        ]
    }
    return json.dumps(data, indent=2)

def check_state(state: TruckState) -> str:
    inside = [p for p in state.packs if p.isInside]
    total_weight = sum(p.weight for p in inside)
    if total_weight > state.cap:
        return f"Total berat paket di dalam truk ({total_weight}) melebihi kapasitas truk ({state.cap})."
    for i, pack in enumerate(inside):
        if not pack.is_valid():
            return f"Paket P{pack.id} memiliki posisi atau dimensi tidak valid (harus >= 0 untuk posisi dan > 0 untuk dimensi)."
        if state.is_outside(pack):
            return f"Paket P{pack.id} pada posisi ({pack.pos.x}, {pack.pos.y}, {pack.pos.z}) dengan dimensi ({pack.dim.width}x{pack.dim.height}x{pack.dim.length}) keluar dari batas dimensi truk ({state.dim.width}x{state.dim.height}x{state.dim.length})."
        for other in inside[i + 1:]:
            if pack.is_overlap(other):
                return f"Paket P{pack.id} dan P{other.id} saling tumpang tindih (overlap)."
    for pack in inside:
        floating, under = state.is_floating(pack)
        if floating:
            return f"Paket P{pack.id} melayang di udara (pos.y={pack.pos.y} tanpa penopang di bawahnya)."
        if any(u.isFragile for u in under):
            frag_ids = [f"P{u.id}" for u in under if u.isFragile]
            return f"Paket P{pack.id} menindih paket pecah belah (Fragile): {', '.join(frag_ids)}."
    return "Konfigurasi state tidak memenuhi aturan validasi truk."

def load_truck_state_from_json(raw_json: str):
    try:
        data = json.loads(raw_json)
    except Exception as e:
        return None, f"Format JSON tidak valid: {e}"

    if not isinstance(data, dict):
        return None, "Root JSON harus berupa objek (dictionary)."

    truck_info = data.get("truck", data)
    dim_info = truck_info.get("dim", truck_info)
    try:
        t_w = int(dim_info["width"])
        t_h = int(dim_info["height"])
        t_l = int(dim_info["length"])
        t_cap = int(truck_info["cap"])
    except (KeyError, TypeError, ValueError) as e:
        return None, f"Atribut dimensi/kapasitas truk ('width', 'height', 'length', 'cap') tidak lengkap atau bukan angka: {e}"

    if t_w <= 0 or t_h <= 0 or t_l <= 0 or t_cap <= 0:
        return None, "Dimensi truk dan kapasitas berat (cap) harus bernilai lebih dari 0."

    packs_data = data.get("packs", [])
    if not isinstance(packs_data, list):
        return None, "Atribut 'packs' harus berupa list/array."

    parsed_packs = []
    seen_ids = set()
    for idx, item in enumerate(packs_data):
        if not isinstance(item, dict):
            return None, f"Elemen paket ke-{idx} harus berupa objek JSON."
        try:
            pid = int(item.get("id", idx))
            if pid in seen_ids:
                return None, f"Terdapat duplikasi ID paket: P{pid}."
            seen_ids.add(pid)

            p_dim = item.get("dim", item)
            pw = int(p_dim["width"])
            ph = int(p_dim["height"])
            pl = int(p_dim["length"])

            orient = next((v for k, v in item.items() if str(k).lower() == "orientation"), None)
            if orient is not None:
                src = {"x": pw, "y": pl, "z": ph}
                o = {str(k).lower()[0]: v for k, v in orient.items()}
                vals = {k: src[o[k].lower()] if isinstance(o[k], str) else int(o[k]) for k in "wlh"}
                if sorted(vals.values()) != sorted((pw, ph, pl)):
                    return None, f"Orientation paket P{pid} bukan permutasi dari dimensinya."
                pw, pl, ph = vals["w"], vals["l"], vals["h"]

            has_pos = "pos" in item or all(k in item for k in ("x", "y", "z"))
            p_pos = item.get("pos", item)
            px = int(p_pos.get("x", 0))
            py = int(p_pos.get("y", 0))
            pz = int(p_pos.get("z", 0))

            pval = int(item["value"])
            pweight = int(item["weight"])
            pfrag = bool(item.get("isFragile", False))
            peta = int(item.get("eta", 1))
            pinside = bool(item.get("isInside", True if has_pos else False))
        except (KeyError, TypeError, ValueError, AttributeError) as e:
            return None, f"Atribut paket ke-{idx} tidak lengkap atau tidak valid: {e}"

        if pw <= 0 or ph <= 0 or pl <= 0 or pval <= 0 or pweight <= 0 or peta <= 0:
            return None, f"Paket P{pid} memiliki dimensi, value, weight, atau ETA <= 0."

        parsed_packs.append(
            Package(
                ident=pid,
                pos=Position(px, py, pz) if pinside else Position(0, 0, 0),
                dim=Dimension(pw, ph, pl),
                value=pval,
                weight=pweight,
                isFragile=pfrag,
                eta=peta,
                isInside=pinside
            )
        )

    candidate_state = TruckState(Dimension(t_w, t_h, t_l), t_cap, parsed_packs)
    if not candidate_state.validate_state():
        reason = check_state(candidate_state)
        return None, f"State ditolak karena tidak valid: {reason}"

    return candidate_state, f"State valid berhasil dimuat ({len(parsed_packs)} paket, {sum(1 for p in parsed_packs if p.isInside)} di dalam truk)."

def export_experiment_log_to_json(algo_name: str, summary_rows: list) -> str:
    output_payload = {
        "algorithm": algo_name,
        "total_runs": len(summary_rows),
        "experiment_logs": summary_rows
    }
    return json.dumps(output_payload, indent=2)


# PANEL SAMPING (PARAMETER)
if "manual_packs" not in st.session_state:
    st.session_state["manual_packs"] = []

with st.sidebar:
    st.markdown("""
        <style>
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            gap: 0.5rem;
        }
        </style>
    """, unsafe_allow_html=True)
    st.header("Input Package Manual")
    col_w, col_h, col_l = st.columns(3)
    with col_w:
        truck_w = st.number_input("Width Truk", min_value=1, max_value=50, value=6)
    with col_h:
        truck_h = st.number_input("Height Truk", min_value=1, max_value=50, value=6)
    with col_l:
        truck_l = st.number_input("Length Truk", min_value=1, max_value=50, value=6)
    
    truck_cap = st.number_input("Kapasitas Berat (cap)", min_value=10, max_value=5000, value=150, step=10)
    
    manual_packs = st.session_state["manual_packs"]
    st.subheader("Tambah Package")
    with st.form("add_pack_form", clear_on_submit=False):
        st.caption(f"ID otomatis: {len(manual_packs)}")
        in_w, in_h, in_l = st.columns(3)
        with in_w:
            pack_w = st.number_input("Width (X)", min_value=1, max_value=50, value=2, key="in_w")
        with in_h:
            pack_h = st.number_input("Height (Y)", min_value=1, max_value=50, value=2, key="in_h")
        with in_l:
            pack_l = st.number_input("Length (Z)", min_value=1, max_value=50, value=2, key="in_l")
        in_val, in_weight, in_eta = st.columns(3)
        with in_val:
            field_val = st.number_input("Value", min_value=1, max_value=1000, value=10, key="in_val")
        with in_weight:
            field_weight = st.number_input("Weight", min_value=1, max_value=1000, value=10, key="in_weight")
        with in_eta:
            field_eta = st.number_input("ETA", min_value=1, max_value=50, value=1, key="in_eta")
        
    in_frag = st.toggle("Fragile", value=False, key="in_frag")
    if st.button("Input Pack", use_container_width=True, key="pack_in"):
        pack = Package(
                ident=len(manual_packs), 
                dim=Dimension(pack_w, pack_h, pack_l), 
                value=field_val,
                weight=field_weight,
                eta=field_eta,
                isFragile=st.session_state.in_frag,
                isInside=False,
                pos=Position(0, 0, 0)
            )
        manual_packs.append(pack)
        st.session_state["base_state"].add_pack(pack)
        st.session_state.pop("experiment_runs", None)
        st.rerun()

    if st.button("Acak pack yang sudah ditambahkan", use_container_width=True, key="manual_in"):
        dim = Dimension(int(truck_w), int(truck_h), int(truck_l))
        st.session_state["base_state"] = randomize_pack(TruckState(dim, truck_cap, manual_packs))
        st.session_state.pop("experiment_runs", None)
        st.rerun()

    if st.button("Hapus pack", use_container_width=True, key="hapus_pack"):
        manual_packs.clear()
        dim = Dimension(int(truck_w), int(truck_h), int(truck_l))
        st.session_state["base_state"] = randomize_pack(TruckState(dim, truck_cap, manual_packs))
        st.rerun()
        
    st.subheader("Generate State Acak")
    st.caption("Generate state dari 0 secara acak, state sebelumnya akan ditimpa")
    n_packs = st.number_input("Jumlah Paket (n_packs)", min_value=1, max_value=100, value=15)
    fragile_prob = st.slider("Probabilitas Fragile", min_value=0.0, max_value=1.0, value=0.25, step=0.05)
    use_seed = st.checkbox("Gunakan Seed Tetap", value=False)
    seed_val = st.number_input("Nilai Seed", value=42, step=1) if use_seed else None

    if st.button("Generate Initial State", use_container_width=True):
        dim = Dimension(int(truck_w), int(truck_h), int(truck_l))
        st.session_state["base_state"] = random_state(
            truck_dim=dim,
            cap=int(truck_cap),
            n_packs=int(n_packs),
            fragile_prob=float(fragile_prob),
            seed=int(seed_val) if seed_val is not None else None
        )
        st.session_state.pop("experiment_runs", None)

    #Json button
    st.divider()
    st.subheader("Load / Simpan State (JSON)")
    uploaded_json = st.file_uploader("Upload File Input State (.json)", type=["json"], key="upload_state_json")
    if st.button("Load State JSON", use_container_width=True, key="btn_load_json"):
        if uploaded_json is None:
            st.warning("Silakan pilih file .json terlebih dahulu.")
        else:
            raw_content = uploaded_json.getvalue().decode("utf-8")
            loaded_state, msg = load_truck_state_from_json(raw_content)
            if loaded_state is not None:
                st.session_state["base_state"] = loaded_state
                st.session_state["manual_packs"] = [p.copy() for p in loaded_state.packs]
                st.session_state.pop("experiment_runs", None)
                st.success(msg)
            else:
                st.error(msg)

    if "base_state" in st.session_state:
        st.download_button(
            label="Download Initial State Saat Ini (.json)",
            data=truck_state_to_json(st.session_state["base_state"]),
            file_name="truck_state_input.json",
            mime="application/json",
            use_container_width=True,
            key="dl_current_base_state"
        )

    st.divider()
    st.header("Pilihan Algoritma & Parameter")
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

    elif algo_choice == "Stochastic Hill Climbing":
        algo_params["max_iter"] = st.number_input("Batas Maksimum Iterasi", min_value=1.0, max_value=10000.0, value=200.0, step=10.0)

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
        algo_params["mutation_rate"] = st.slider("Probabilitas Mutasi (mutation_rate)", min_value=0.0, max_value=1.0, value=0.20, step=0.05) # Input probabilitas mutasi GA

    st.divider()
    st.header("Mode Eksekusi")
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
    st.session_state["base_state"] = randomize_pack(TruckState(init_dim, truck_cap, []))

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

            res = stochastic(start_state, algo_params["max_iter"])
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
    elif algo_choice == "Genetic Algorithm":
        # Eksekusi Genetic Algorithm sesuai mode konfigurasi dan jumlah run
        ga_mode = algo_params["ga_mode"]
        mutation_rate = float(algo_params.get("mutation_rate", 0.20))
        configs = []
        valid_input = True

        try:
            if ga_mode == "Single Konfigurasi":
                configs.append((int(algo_params["pop_size"]), int(algo_params["max_iter"]), None))
            elif ga_mode == "Kontrol Populasi (3 Variasi Iterasi)":
                p_fixed = int(algo_params["pop_size"])
                iter_list = [max(1, int(x.strip())) for x in algo_params["iter_vars"].split(",") if x.strip()]
                if not iter_list:
                    raise ValueError("Daftar iterasi kosong.")
                for it_val in iter_list:
                    configs.append((p_fixed, it_val, f"Pop={p_fixed}, Iter={it_val}"))
            else:
                it_fixed = int(algo_params["max_iter"])
                pop_list = [max(2, int(x.strip())) for x in algo_params["pop_vars"].split(",") if x.strip()]
                if not pop_list:
                    raise ValueError("Daftar populasi kosong.")
                for p_val in pop_list:
                    configs.append((p_val, it_fixed, f"Pop={p_val}, Iter={it_fixed}"))
        except ValueError:
            valid_input = False
            st.error("Input variasi populasi/iterasi tidak valid. Gunakan angka bulat yang dipisahkan koma (contoh: 50, 100, 200).")

        if valid_input:
            runs_output = []
            total_steps = len(configs) * num_runs
            step_idx = 0
            progress = st.progress(0, text="Menjalankan Genetic Algorithm...")
            base_seed = int(seed_val) if seed_val is not None else 21

            for p_size, m_iter, cfg_label in configs:
                for i in range(num_runs):
                    step_idx += 1
                    run_seed = base_seed if (i == 0 or not randomize_each_run) else (base_seed + i)
                    start_state = st.session_state["base_state"].copy()
                    res = genetic_algorithm(
                        start_state,
                        pop_size=p_size,
                        iterations=m_iter,
                        mutation_rate=mutation_rate,
                        seed=run_seed
                    )
                    if cfg_label is None:
                        run_name = f"Run #{i + 1}"
                    elif num_runs == 1:
                        run_name = cfg_label
                    else:
                        run_name = f"{cfg_label} (Run #{i + 1})"
                    runs_output.append((run_name, res))
                    progress.progress(step_idx / total_steps, text=f"Selesai {run_name} ({step_idx}/{total_steps})")

            progress.empty()
            st.session_state["experiment_runs"] = {
                "algo": algo_choice,
                "runs": runs_output
            }

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
    with st.expander("Lihat Detail Paket pada Initial State"):
        pack_rows = []
        for p in st.session_state["base_state"].packs:
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
            row["Banyak Iterasi"] = res.metrics.get("max_iter", res.metrics.get("iterations", "-")) # Fallback ke iterations
            avg_hist = res.metrics.get("avg_fitness", []) # Ambil histori rata-rata fitness populasi
            row["Rata-rata Fitness Akhir"] = round(avg_hist[-1], 2) if avg_hist else "-"
            row["Mutation Rate"] = res.metrics.get("mutation_rate", "-")

        summary_rows.append(row)

    df_summary = pd.DataFrame(summary_rows)
    st.dataframe(df_summary, use_container_width=True, hide_index=True)


    dl_col1, dl_col2 = st.columns(2)
    safe_algo_slug = algo_used.lower().replace(" ", "_")
    with dl_col1:
        st.download_button(
            label="Download Output Log Eksperimen (.json)",
            data=export_experiment_log_to_json(algo_used, summary_rows),
            file_name=f"output_log_{safe_algo_slug}.json",
            mime="application/json",
            use_container_width=True,
            key="dl_log_json"
        )
    with dl_col2:
        st.download_button(
            label="Download Output Log Eksperimen (.csv)",
            data=df_summary.to_csv(index=False).encode("utf-8"),
            file_name=f"output_log_{safe_algo_slug}.csv",
            mime="text/csv",
            use_container_width=True,
            key="dl_log_csv"
        )

    # Tampilkan plot komparasi kurva GA jika terdapat lebih dari 1 run/variasi
    if algo_used == "Genetic Algorithm" and len(runs_list) > 1:
        with st.expander("Komparasi Kurva Konvergensi Antar Run / Variasi GA", expanded=True):
            fig_ga_comp = plot_ga_comparison_2d(runs_list)
            st.pyplot(fig_ga_comp)

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
            interactive = st.toggle("Interaktif", value=False, key=f"toggle_{idx}")
            if interactive:
                fig_3d = plot_comparison_3d_interactive(res.initial_state, res.final_state)
                st.plotly_chart(fig_3d, use_container_width=True, key=f"3d_{idx}")
            else:
                fig = plot_comparison_3d(res.initial_state, res.final_state)
                st.pyplot(fig)

            st.markdown("#### 2. Grafik Kurva Eksperimen 2D")
            fig_2d = plot_metrics_2d(res, algo_used)
            st.pyplot(fig_2d)

            # Visualisasi tambahan: melihat perkembangan Best State per Generasi pada GA
            if algo_used == "Genetic Algorithm" and res.metrics.get("best_state_per_gen"):
                with st.expander("Lihat Perkembangan Best State per Generasi (3D)"):
                    gen_states = res.metrics["best_state_per_gen"]
                    gen_idx = st.slider(
                        "Pilih Generasi",
                        min_value=1,
                        max_value=len(gen_states),
                        value=len(gen_states),
                        key=f"gen_slider_{idx}"
                    ) if len(gen_states) > 1 else 1
                    selected_gen_state = gen_states[gen_idx - 1]
                    if interactive:
                        st.plotly_chart(
                            plot_comparison_3d_interactive(res.initial_state, selected_gen_state),
                            use_container_width=True,
                            key=f"gen_3d_{idx}"
                        )
                    else:
                        st.pyplot(plot_comparison_3d(res.initial_state, selected_gen_state))

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
                st.download_button(
                    label=f"Download Final State ({run_label}) (.json)",
                    data=truck_state_to_json(res.final_state),
                    file_name=f"final_state_{safe_algo_slug}_run_{idx + 1}.json",
                    mime="application/json",
                    use_container_width=True,
                    key=f"dl_final_state_{idx}"
                )