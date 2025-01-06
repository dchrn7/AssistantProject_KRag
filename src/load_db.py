import os
import logging
import shutil
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document
from PyPDF2 import PdfReader
import re

#import datetime

class DataLoader:
    """Load, process, and save documents from local PDF files."""
    def __init__(self, pdf_directory="/Users/drisschraibi/Desktop/RAG-Chatbot-with-Confluence/Cours_Marketing_Maths", persist_directory="./db"):
        self.pdf_directory = pdf_directory
        self.persist_directory = persist_directory

    def load_from_local_pdfs(self):
        """Load documents from local PDF files."""
        if not os.path.exists(self.pdf_directory):
            logging.error("Le répertoire PDF n'existe pas : %s", self.pdf_directory)
            return []
        
        fichiers_pdf = [f for f in os.listdir(self.pdf_directory) if f.endswith(".pdf")]
        if not fichiers_pdf:
            logging.warning("Aucun fichier PDF trouvé dans le répertoire : %s", self.pdf_directory)
            return []

        docs = []
        for filename in os.listdir(self.pdf_directory):
            if filename.endswith(".pdf"):
                filepath = os.path.join(self.pdf_directory, filename)
                print("filepath", filepath)
                try:
                    doc_extrait = self._extract_text_from_pdf(filepath)
                    docs.extend(doc_extrait)  # On ajoute chaque page extraite
                except Exception as e:
                    logging.error("Erreur lors du traitement du fichier PDF %s : %s", self.pdf_directory, e)
                
        logging.info("Chargement terminé : %d pages extraites.", len(docs))
        return docs

    
    def _extract_text_from_pdf(self, filepath):
        """
        Extract text from a PDF file and return a list of Document objects.
        :param filepath: Path to the PDF file.
        :return: List of Document objects, each containing page content and metadata.
        """
        if not os.path.exists(filepath):
            logging.error("File not found: %s", filepath)
            return []

        try:
            reader = PdfReader(filepath)
            documents = []  # List to store the extracted Document objects

            for i, page in enumerate(reader.pages):
                try:
                    # Extract and validate text
                    raw_text = page.extract_text() or ""
                    text = str(raw_text).strip()  # Convert to string and strip whitespace

                    if not isinstance(text, str):
                        logging.error("Invalid content type on page %d: %s", i + 1, type(text))
                        continue

                    if text:  # Only process non-empty text
                        metadata = {
                            "source": os.path.basename(filepath),
                            "page": i + 1,
                        }
                        # Create Document object
                        documents.append(Document(page_content=text, metadata=metadata))
                    else:
                        logging.warning("Page %d of %s skipped (empty or irrelevant text)", i + 1, filepath)
                except Exception as page_error:
                    logging.error("Error processing page %d of file %s: %s", i + 1, filepath, page_error)
            if not documents:
                logging.warning("No valid pages extracted from %s", filepath)
            else:
                logging.info("Successfully extracted %d pages from %s", len(documents), filepath)
            return documents
        except Exception as e:
            logging.error("Error reading PDF file %s: %s", filepath, e)
            return []
    
    
        
    def split_docs(self, docs, chunk_size=2048, chunk_overlap=30, separators=None):
        """
        Split documents into smaller chunks.
        
        :param docs: List of Document objects to split. Each Document should have `page_content` and `metadata` attributes.
        :param chunk_size: Maximum size of each chunk.
        :param chunk_overlap: Overlap between chunks to maintain context.
        :param separators: List of custom separators to split text. Defaults to ["\n\n", "\n", "(?<=\\. )", " ", ""].
        :return: List of split Document objects.
        """
        if not docs:
            logging.warning("Aucun document à diviser.")
            return []

        if separators is None:
            separators = ["\n\n", "\n", "(?<=\\. )", " ", ""]

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators
        )
        
        splitted_docs = []
        for doc in docs:
            if not hasattr(doc, 'page_content') or not hasattr(doc, 'metadata'):
                logging.error("Document mal formé, attributs manquants.")
                continue

            # Vérification et conversion de la liste en texte
            if isinstance(doc.page_content, list):
                doc.page_content = "\n".join(doc.page_content)

            # Vérifie si le contenu est vide après conversion
            if not doc.page_content or not doc.page_content.strip():
                logging.warning("Document vide ignoré : %s", doc.metadata.get("source", "Source inconnue"))
                continue

            try:
                chunks = splitter.split_text(doc.page_content)
                for chunk in chunks:
                    #page_number = doc.metadata.get("page", "Page inconnue")
                    
                    # Logique de validation de la page
                  #  if page_number == "Page inconnue":
                   #     logging.warning("Le document %s a une page inconnue lors du fractionnement.", doc.metadata.get("source"))

                    splitted_docs.append(
                        Document(
                            page_content=chunk,
                            metadata={
                                "source": doc.metadata.get("source", "Source inconnue"),
                                "page": doc.metadata.get('page', "Page inconnue"),
                            }
                        )
                    )
            except Exception as e:
                print('a')
                #logging.error("Erreur lors du fractionnement du document (%s) : %s", 
                           # doc.metadata.get("source", "Source inconnue"), e)
            
       # logging.info("Documents fractionnés en %d morceaux.", len(splitted_docs))

        # Optionnel : Vérification finale des pages dans les métadonnées
        #for doc in splitted_docs:
            #if "page" not in doc.metadata or doc.metadata["page"] == "Page inconnue":
                #logging.warning("Document fractionné sans information de page : %s", doc.metadata.get("source"))

        return splitted_docs


    def save_to_db(self, splitted_docs, embeddings):
        """Save chunks to Chroma DB."""
        try:
            logging.info("Enregistrement des documents dans la base de données Chroma...")
            db = Chroma.from_documents(splitted_docs, embeddings, persist_directory=self.persist_directory)
            #db.persist()
            logging.info("Base de données Chroma enregistrée avec succès.")
            return db
        except Exception as e:
            logging.error("Erreur lors de l'enregistrement dans la base de données : %s", e)
            print("err")
            return None

    def load_from_db(self, embeddings):
        """Load chunks from Chroma DB."""
        try:
            logging.info("Chargement de la base de données Chroma...")
            db = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=embeddings
            )
            logging.info("Base de données Chroma chargée avec succès.")
            return db
        except Exception as e:
            logging.error("Erreur lors du chargement de la base de données : %s", e)
            return None

    def set_db(self, embeddings):
        """Create, save, and load db."""
        if os.path.exists(self.persist_directory):
            try:
                shutil.rmtree(self.persist_directory)
                logging.info("Répertoire de base de données réinitialisé : %s", self.persist_directory)
            except Exception as e:
                logging.warning("Impossible de réinitialiser le répertoire : %s", e)
        else : 
                logging.info("Le répertoire n'existe pas encore, rien à réinitialiser : %s", self.persist_directory)
        # Load docs
        docs = self.load_from_local_pdfs()
        if not docs:
            logging.error("Aucun document chargé. Base de données non créée.")
            return None

        # Split Docs
        splitted_docs = self.split_docs(docs)

        # Save to DB
        return self.save_to_db(splitted_docs, embeddings)

    def get_db(self, embeddings):
        """Load existing db."""
        return self.load_from_db(embeddings)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Exemple d'utilisation
    data_loader = DataLoader(
        pdf_directory="/Users/drisschraibi/Desktop/RAG-Chatbot-with-Confluence/Cours_Marketing_Maths",  # Répertoire contenant vos fichiers PDF locaux
        persist_directory="./db"
    )

    # Exemple : Charger les documents et créer la base de données
    from langchain.embeddings.openai import OpenAIEmbeddings
    embeddings = OpenAIEmbeddings()

    db = data_loader.set_db(embeddings)
    if db:
        logging.info("Base de données créée et prête à l'emploi.")
