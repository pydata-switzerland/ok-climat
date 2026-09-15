# OK Climat

This repository contains tools and experiments developed to support OK Climat's work on climate policy monitoring in Switzerland.

The goal of the project is to make it easier to collect, organise, and analyse information about climate policies and initiatives at the cantonal and municipal levels in Switzerland.

The core pipeline started as a prototype developed during the GovTech Hackathon in Bern (May 2026).

## About OK Climat

* https://www.ok-klima.ch/fr
* https://www.ok-klima.ch/fr/a-propos-de-nous

---

# Before You Start

To run the code, you will need:

* Git
* A terminal (Terminal, PowerShell, Command Prompt, etc.)
* A Python environment manager

This repository supports two environment managers:

1. **Pixi (recommended)**
2. **Conda**

If you are unsure which one to use, use **Pixi**.

---

# Getting the Code

Open a terminal and run:

```bash
git clone https://github.com/pydata-switzerland/ok-climat.git
cd ok-climat
```

The core pipeline can then be found in:

```text
pipeline/
```

---

# Setting Up the Environment

You only need **one** of the following options.

## Option 1: Pixi (Recommended)

### Install Pixi

macOS / Linux:

```bash
curl -fsSL https://pixi.sh/install.sh | bash
```

Windows (PowerShell):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://pixi.sh/install.ps1 | iex"
```

### Install Project Dependencies

From the project root directory:

```bash
pixi install
```

### Activate the Environment

```bash
pixi shell
```

You should now be able to run the project code.

### Leave the Environment

```bash
exit
```

---

## Option 2: Conda

Create the environment:

```bash
conda env create -f environment.yml
```

Activate it:

```bash
conda activate ok_climat_env
```

Deactivate it:

```bash
conda deactivate
```

---

# Running the Pipeline

Once your environment is activated:

```bash
cd pipeline
```

Detailed instructions for running the pipeline are available in:

```text
pipeline/README.md
```

Follow the instructions in that README to run the pipeline.

---

# Exploration Scripts

The `exploration/` folder contains early prototyping/exploration scripts written before the GovTech Hackathon while getting familiar with the project and investigating what was possible. This code is **not maintained** and is **not part of the documented pipeline** — it's kept for reference only. See `exploration/README.md` for details.

---

# Repository Structure

```text
ok-climat/
│
├── pipeline/              # Core webscraping + LLM analysis pipeline
├── exploration/           # Early prototype/exploration scripts (not maintained)
├── pixi.toml             # Pixi environment definition
├── environment.yml       # Conda environment definition
└── README.md             # This file
```
