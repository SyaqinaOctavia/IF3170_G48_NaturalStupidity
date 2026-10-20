# Tubes 3 Strategi Algoritma 2025/2026 — Local Search untuk Optimasi Pengemasan Truk

## Identitas Pembuat
| Nama | NIM |
|------|-----|
| Billie Bhaskara Wibawa | 13524024 |
| Josh Reinhart Zidik | 13524048 |
| Syaqina Octavia Rizha | 13524088 |

## Deskripsi Singkat Repository
Program ini mengimplementasikan algoritma **Local Search** dan **Genetic Algorithm** untuk memecahkan masalah **optimasi pengemasan truk 3D (3D Bin Packing dengan constraints)**. Tujuannya adalah memaksimalkan total nilai (value) paket yang dimuat ke dalam truk dengan mematuhi berbagai kendala realistis:

- **Kapasitas berat** truk tidak boleh terlampaui
- **Tidak ada tumpang tindih (overlap)** antar paket
- **Dukungan gravitasi** — paket tidak boleh melayang (harus ada penopang di bawahnya)
- **Paket pecah belah (fragile)** — tidak boleh ditindih paket lain
- **Batas dimensi truk** — paket harus sepenuhnya di dalam volume truk

Algoritma yang diimplementasikan:
| Algoritma | Kategori | Deskripsi Singkat |
|-----------|----------|-------------------|
| **Simulated Annealing** | Metaheuristik | Menerima solusi lebih buruk dengan probabilitas yang menurun seiring waktu (suhu T) untuk menghindari local optima |
| **Steepest Ascent Hill Climbing** | Local Search | Selalu bergerak ke tetangga terbaik; berhenti saat tidak ada tetangga yang lebih baik |
| **Stochastic Hill Climbing** | Local Search | Memilih tetangga acak; pindah hanya jika lebih baik, dengan batas iterasi stagnan |
| **Hill Climbing with Sideways Move** | Local Search | Memperbolehkan perpindahan ke tetangga dengan nilai sama (sideways) hingga batas tertentu |
| **Random Restart Hill Climbing** | Local Search | Menjalankan steepest ascent berulang dari titik awal acak; mengembalikan solusi terbaik global |
| **Genetic Algorithm** | Evolutionary | Populasi kromosom (state truk) berevolusi via seleksi roulette wheel, crossover, dan mutasi |

Aplikasi dibangun dengan **Streamlit** untuk antarmuka web interaktif, mendukung visualisasi 3D (Matplotlib & Plotly), kurva konvergensi 2D, eksperimen batch, dan ekspor log JSON/CSV.

## Requirements
- **Python 3.11+**
- **pip** (termasuk di Python)
- **Docker** (opsional, untuk containerization)

Referensi instalasi:
- **Python**: [python.org/downloads](https://www.python.org/downloads/)
- **Docker**: [docker.com/get-started](https://www.docker.com/get-started/)

## Cara Setup dan Menjalankan Program

### Opsi 1: Menjalankan Lokal (Development)
Jalankan dari direktori **root** project.

#### 1. Buat virtual environment & install dependency (sekali saja)
```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows (PowerShell)

pip install --upgrade pip
pip install -r requirements.txt
```

#### 2. Jalankan aplikasi Streamlit
```bash
streamlit run src/app.py
```

Setelah jalan, akses di browser: `http://localhost:8501`

---

### Opsi 2: Menjalankan dengan Docker (Production/Deployment)
Pastikan Docker Engine berjalan.

#### 1. Build & jalankan via Docker Compose
```bash
docker compose up --build -d
```

#### 2. Akses aplikasi
Buka browser: `http://localhost:8501`

#### 3. Hentikan container
```bash
docker compose down
```

> **Catatan:** `docker-compose.yml` mem-mount `./src` ke `/app` di container, sehingga perubahan kode pada `src/` langsung terefleksi tanpa rebuild (hot-reload via `streamlit --server.fileWatcherType=poll`).

## Struktur Proyek
```
IF3170_G48_NaturalStupidity
├── README.md
├── requirements.txt
├── dockerfile
├── docker-compose.yml
├── .dockerignore
├── src/
│   ├── app.py                    # Entry point Streamlit (UI, parameter, orchestrasi eksperimen)
│   ├── utils.py                  # Model data: Position, Dimension, Package, TruckState, neighbor generation
│   ├── state.py                  # Generator state acak: random_state, randomize_pack, generate_population
│   ├── search_result.py          # Dataclass SearchResult (initial, final, history, duration, metrics)
│   ├── hill_climbing.py          # 4 varian Hill Climbing + Random Restart
│   ├── simmulated_annealing.py   # Simulated Annealing dengan scheduling eksponensial
│   ├── genetic_algorithm.py      # GA: seleksi, crossover, mutasi, elitism, populasi awal
│   └── visualizer.py             # Visualisasi 3D (matplotlib/plotly), kurva 2D, komparasi GA
└── test/
    └── (file uji coba / dataset)
```

## Pembagian Tugas Anggota Kelompok

| Nama | NIM | Tugas Utama |
|------|-----|-------------|
| **Billie Bhaskara Wibawa** | 13524024 | **Simulated Annealing & Visualisasi**: `simmulated_annealing.py` (scheduling, acceptance probability, stuck tracking), `visualizer.py` (3D matplotlib/plotly, kurva konvergensi 2D, komparasi GA) |
| **Josh Reinhart Zidik** | 13524048 | **Semua Algoritma Hill Climbing, Testing, Laporan**: `hill_climbing.py` (Steepest Ascent, Stochastic, Sideways Move, Random Restart), testing & validasi algoritma, penyusunan laporan |
| **Syaqina Octavia Rizha** | 13524088 | **Genetic Algorithm & Laporan**: `genetic_algorithm.py` (seleksi, crossover, mutasi, elitism, populasi awal), `app.py` (Streamlit UI, parameter panel, batch run, export JSON/CSV), penyusunan laporan |

---

## Panduan Singkat Penggunaan Aplikasi

### 1. Panel Samping (Sidebar) — Input & Parameter
- **Dimensi Truk** (Width, Height, Length) & **Kapasitas Berat (cap)**
- **Input Package Manual** — tambah paket satu per satu (dimensi, value, weight, ETA, fragile)
- **Generate State Acak** — buat state awal acak dengan `n_packs` dan probabilitas fragile
- **Load / Simpan State (JSON)** — upload/download state truk untuk reproduktibilitas
- **Pilihan Algoritma & Parameter** — 6 algoritma dengan parameter spesifik masing-masing
- **Mode Eksekusi** — Single Run (1×) atau Batch Run (3× eksperimen, opsi randomize tiap run)

### 2. Area Utama — Hasil & Visualisasi
- **Preview Initial State** — ringkasan metrik + visualisasi 3D sebelum dijalankan
- **Log Eksperimen** — tabel ringkasan per run (Objective awal/akhir, delta, durasi, iterasi, metrik spesifik algo)
- **Download Log** — ekspor hasil ke `.json` atau `.csv`
- **Tab per Run** — detail visualisasi 3D (Initial vs Final), kurva konvergensi 2D, detail paket final state, download final state JSON

### 3. Format JSON State (Contoh)
```json
{
  "truck": { "dim": { "width": 6, "height": 6, "length": 6 }, "cap": 150 },
  "packs": [
    { "id": 0, "dim": { "width": 2, "height": 2, "length": 2 }, "pos": { "x": 0, "y": 0, "z": 0 }, "orientation": { "w": "x", "h": "y", "l": "z" }, "value": 10, "weight": 5, "isFragile": false, "eta": 1, "isInside": true }
  ]
}
```

---

*Proyek ini dibuat untuk memenuhi Tugas Besar 3 Mata Kuliah Strategi Algoritma 2025/2026 — Institut Teknologi Bandung*