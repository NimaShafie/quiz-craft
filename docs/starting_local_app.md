# Instructions
Follow these instructions to start the application locally on your computer

1. Install Python 3.12.7

2. Create a virtual enviornment for this application by performing the command
```
python -m venv .venv
```
Linux
```
python3 -m venv --without-pip foo
```

3. Activate the virutal enviornment by running the following command
Windows command prompt
```
.venv\Scripts\activate.bat
```
Windows PowerShell
```
.venv\Scripts\Activate.ps1
```
macOS and Linux
```
source .venv/bin/activate
```

**Exit the virtual environment by running the command ```deactivate``` at anytime**

4. Download all prerequsite pip packages by running the following command
```
pip install -r requirements.txt
```

5. Start the local server by running the following command
```
streamlit run src/QuizCraft.py
```
