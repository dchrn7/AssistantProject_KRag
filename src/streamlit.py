import streamlit as st
from src.help_desk import HelpDesk
from pdf2image import convert_from_path
import src.PdfViewer
from src.PdfViewer import PDFViewer
import os

# Bannière et titre
st.set_page_config(page_title="Mr.Skill", page_icon="🤖", layout="centered")
st.image("/Users/drisschraibi/Desktop/RAG-Chatbot-with-Confluence/robot_ban.webp", use_container_width=True)  # Remplacez par le chemin d'une image de bannière
st.title("Bienvenue chez Mr.Skill 🤖")
st.markdown("**Votre professeur personnalisé pour répondre à toutes vos questions.**")

# Caching du modèle
@st.cache_resource
def get_model():
    model = HelpDesk(new_db=True)
    return model

if "model" not in st.session_state:
    st.session_state["model"] = get_model()

model = st.session_state["model"]

# Gestion de l'état des messages
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Bonjour ! Je suis Mr.Skill. Comment puis-je vous aider aujourd'hui ?"}]

# Affichage des messages dans l'interface
for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        st.chat_message(msg["role"]).write(f"{msg['content']}")
    else:
        st.chat_message(msg["role"]).write(msg["content"])

# Saisie utilisateur
if prompt := st.chat_input("Posez votre question à Mr.Skill !"):
    # Ajouter la question de l'utilisateur
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # Obtenir la réponse
    response, s_organizer, sources = model.retrieval_qa_inference(prompt)

    # Ajouter la réponse
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.chat_message("assistant").write(f"{response}")

    # Bouton pour afficher les sources
    pdf_directory = "/Users/drisschraibi/Desktop/RAG-Chatbot-with-Confluence/Cours_Marketing_Maths"  # Répertoire contenant vos fichiers PDF locaux
    if sources:
        if st.button("📂 Afficher les sources"):
            viewer = PDFViewer(s_organizer.get_organized_sources(), s_organizer.generate_file_paths(pdf_directory))
            viewer.display()

# Footer sympa
st.markdown("---")
st.markdown("🤓 **Même Mr. Skill n'est pas infaillible... Consultez les sources si vous avez un doute !**")
