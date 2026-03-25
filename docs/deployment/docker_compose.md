# 🧬 Running CensuScope with Docker Compose

This guide walks you through pulling and running the `ghcr.io/gw-hive/censuscope:2.1.0` Docker image using Docker Compose.

---

## ✅ Prerequisites

- Docker Desktop installed (macOS/Windows/Linux)
- Docker Compose available via `docker compose` command
- A FASTQ file and BLAST database available locally

---

## 📂 Local Directory Structure (Example)

Your directory should look like this:

```bash
your-project/
├── docker-compose.yml
├── temp_dirs/                # (output files will be saved here)
└── your-data/
    ├── query.fastq
    └── blast_db/
        ├── HumanGutDB.nin
        ├── HumanGutDB.nsq
        ├── HumanGutDB.nhr
        └── HumanGutDB.fasta
```

---

## 🐳 Example `docker-compose.yml`

```yaml
version: "3.8"

services:
  censuscope:
    image: ghcr.io/gw-hive/censuscope:2.1.0
    container_name: censuscope_localtest
    command: >
      python lib/censuscope.py
      -i 5
      -s 10
      -t family
      -q /app/data/query.fastq
      -d /app/data/blast_db/HumanGutDB-v2.6.fasta
    volumes:
      - /absolute/path/to/your-data:/app/data
      - ./temp_dirs:/app/temp_dirs
    stdin_open: true
    tty: true
```

---

## 🔧 What to Modify

| Field                           | Description                                                                 |
|--------------------------------|-----------------------------------------------------------------------------|
| `/absolute/path/to/your-data`  | Full absolute path to your local directory with `query.fastq` and `blast_db/` |
| `query.fastq`                  | Name of your FASTQ file (must exist inside the mounted `your-data` folder) |
| `blast_db/HumanGutDB-v2.6.fasta` | Path to your BLAST database FASTA file (used to generate the BLAST DB index) |

💡 **Make sure your BLAST database is built before running:**

```bash
makeblastdb -in HumanGutDB-v2.6.fasta -dbtype nucl -out HumanGutDB-v2.6
```

This creates the `.nin`, `.nsq`, and `.nhr` index files required for BLAST.

---

## ▶️ Run the Container

From the same directory as your `docker-compose.yml`, run:

```bash
docker compose up
```

---

## 📁 Output Location

CensuScope writes all output to `/app/temp_dirs` in the container. This is mapped to the `./temp_dirs` folder on your local machine.

---

## 🧼 Stop and Clean Up

```bash
docker compose down
```

To remove volumes too (including contents of `temp_dirs`):

```bash
docker compose down -v
```

---

## 🐛 Troubleshooting (macOS)

If you see a `Mounts denied` error on macOS:

1. Open **Docker Desktop**
2. Go to **Settings > Resources > File Sharing**
3. Add the parent directory of `/your/data` (e.g., `/Users/yourname/GitHub/GW_HIVE`)
4. Click **Apply & Restart**

---

