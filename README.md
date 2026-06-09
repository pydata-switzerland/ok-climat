# OK Climat

This project aims to support [OK CLIMAT](https://www.ok-klima.ch/fr) by addressing data-related challenges. Specifically, we are developing tools and workflows to make it faster and easier to retrieve and analyse data on climate policies and initiatives at the cantonal and municipal levels in Switzerland.

We are collaborating with the [OK CLIMAT team](https://www.ok-klima.ch/fr/a-propos-de-nous), a partnership initiated following [Yvonne](https://www.linkedin.com/in/yvonne-winteler-b2b27426/)'s presentation at PyData Lausanne in November 2025.

## Setup

### Clone the Repository

First, download the project to your computer. Open a terminal and run:

```
git clone [github.com](https://github.com/pydata-switzerland/ok-climat.git)
cd ok-climat
```

If you want to work on a specific branch, e.g. ```explore-webscraping-#7``` that contains all code developed at GovTech in Bern, run:

```
git checkout explore-webscraping-#7 
```

Then you can find the code in the directory ```hackathon_govtech```

### Environment 

To set up the environment you can do it with pixi or with conda.

### Setting up environment with pixi

If you don't have Pixi installed, run:

```
curl -fsSL [pixi.sh](https://pixi.sh/install.sh) | bash
```

On Windows, use instead:

```
powershell -ExecutionPolicy ByPass -c "irm [pixi.sh](https://pixi.sh/install.ps1) | iex"
```

From the project folder you install pixi with the settings specified in pixi.toml by running:

```
pixi install
```

To activate the environment, run:

```
pixi shell
```

Now you should be able to run the scripts in this project.

To deactivate the environment, run:

```
exit
```

### Setting up environment with conda

Run in terminal:

```bash
conda env create -f environment.yml
```

This will automatically create a virtual environment called `ok_climat_env` with all required libraries defined in the `environment.yml` file.

To activate the environment, run:

```bash
conda activate ok_env
```
To deactive, run:

```
conda deactivate
```

## Running the hackathon prototype

To run the prototype developed during the GovTech hackathon May 28 & 29, 2026:

1. From the project root, change into the prototype folder:
```
cd hackathon_govtech
```

2. Follow the instructions in that directory (check hackathon_govtech/README.md). It contains the exact commands to run the prototype.