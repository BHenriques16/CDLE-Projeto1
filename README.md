# Usage guide to run the project locally

### Requirements

Make sure to have the following installed:
* **Git**
* **Docker**
* **Python 3.12+**


### Step by step

**Clone the repository**
Open your terminal and clone this project to your local machine and enter the project's folder
```bash
git clone https://github.com/BHenriques16/CDLE-Projeto1
cd CDLE-Projeto1
```

### Setting up the Infrastructure (Database)

To ensure the code works perfectly, start the Redis container in the background:
```bash
docker compose up -d
```
* **Redis:** Will be avaliable in port 6379

### Configure python enviroment
```bash
# Create virtual enviroment
python3 -m venv venv  # if you are testing on Windows, use: python -m venv venv 

# Activate the venv 
source venv/bin/activate    # if you are testing on Windows, use: venv\Scripts\activate

# Install required libraries
pip install -r requirements.txt
```

### Execute jupyter notebook

With the venv activated and the data base running, start Jupyter
```bash
jupyter notebook
```
This will open a window in your browser. After that you can just open the file ```Projeto1_grupo2.ipynb```.
