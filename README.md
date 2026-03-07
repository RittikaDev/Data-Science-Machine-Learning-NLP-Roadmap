# Project Setup Guide

This project can be set up using **Conda**, **Python built-in venv**, or **virtualenv**.  
Choose the method that best fits your system.

---

# Option 1: Using Conda (Recommended)

## Prerequisites

Before getting started, make sure you have:

- [Anaconda](https://www.anaconda.com/products/distribution) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html) installed.
- Basic familiarity with the terminal/command line.

---

## Setup Instructions

### 1. Create a Virtual Environment

Run the following command to create a new Conda environment with Python 3.10:

```bash
conda create -p venv python=3.10 -y
```

venv is the folder where the environment will be stored. You can rename it if desired.

### 2. Activate the Environment

Activate the environment with:

```bash
conda activate venv/
```

After activation, your terminal should display (venv) indicating the environment is active.

### 3. Install Dependencies

Install all required packages from the requirement.txt file:

```bash
pip install -r requirement.txt
```

This ensures your environment has all the necessary libraries to run the project.

### Verify Installation

Check that Python 3.10 is active:

```bash
python --version
```

Expected output:

```bash
Python 3.10.x
```

### Notes

    * Always activate the environment before running scripts.
    * If you face issues activating in PowerShell, run:

```bash
    conda init powershell
```

    * Then restart your terminal.

# Option 2: Using Python Built-in venv (No Anaconda Required)

This method uses the Python version installed on your system.

### 1. Create Virtual Environment

```bash
python -m venv myenv
```

### 2. Activate the Environment

```bash
myenv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirement.txt
```

### 4. Deactivate Environment

```bash
deactivate
```

### Notes

    * This environment will use the Python version already installed on your system.

# Option 3: Using virtualenv

### 1. Install virtualenv

```bash
pip install virtualenv
```

### 2. Create Virtual Environment

```bash
virtualenv -p python3 virtual_env
```

### 3. Activate Environment (Windows)

```bash
virtual_env\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirement.txt
```

### 5. Deactivate Environment

```bash
deactivate
```

## Ready to Go!

Your environment is now set up. You can start developing and running the project using:

```bash
python your_script.py
```
