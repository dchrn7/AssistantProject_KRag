from src.help_desk import HelpDesk
# src/__main__.py
import subprocess
import sys

if __name__ == "__main__":
    #Lancer Streamlit avec subprocess
    subprocess.run([sys.executable, "-m", "streamlit", "run", "src/streamlit.py"])


    #model = HelpDesk(new_db=True)

    #print(model.db._collection.count())

    #prompt = "le football américain ?"
    #result = model.retrieval_qa_inference(prompt)
    #print(result)
