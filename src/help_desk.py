import sys
import collections
from dotenv import load_dotenv
import os
import numpy as np 
from src.evaluate import get_cosine_distance, get_euclidian_distance, get_levenshtein_distance
from src.SourcesOrganizer import SourceOrganizer
from .load_db import DataLoader
from collections import Counter, defaultdict
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from project_config import (
    OPENAI_API_KEY
)

class HelpDesk():
    """Create the necessary objects to create a QARetrieval chain"""
    def __init__(self, new_db=True): 
        self.new_db = new_db
        self.template = self.get_template()
        self.embeddings = self.get_embeddings()
        self.llm = self.get_llm()
        self.prompt = self.get_prompt()
      #  self.OPENAI_API_KEY = CONFLUENCE_API_KEY
        if self.new_db:
            self.db = DataLoader().set_db(self.embeddings)
        else:
            self.db = DataLoader().get_db(self.embeddings)

        self.retriever = self.db.as_retriever()
        self.retrieval_qa_chain = self.get_retrieval_qa()


    def get_template(self):
        template = """
        Tu es un professeur spécialisé en **marketing**. En te basant uniquement sur les sources suivantes :
        -----
        {context}
        -----
        et en suivant le fil de la discussion. 
        Réponds de manière détaillée et précise à la question suivante : {question}. Mais ne t'éloigne pas trop du sujet de la question.

        ### Consignes : 
        - Si tu connais le chapitre, la section, mentionne le. 
        - Si tu n'as pas assez d'informations pour répondre, écris uniquement : **"Je n'ai pas assez d'informations pour répondre. 🤔" 
        - Si la question est **imprécise**, réponds uniquement : **"Pourrais-tu préciser ta question ? 🧐"**.
        - Si la question n'est pas claire ou pas précise, réponds uniquement : **"Pourrais-tu préciser ta question ? 🧐"**.
        - Si la question est **hors contexte** et n'a rien avoir avec le, réponds uniquement : **"Ta question est hors de mon champs de compétences. 🤷‍♂️"**.
        - Si la question est **inappropriée**, réponds uniquement : **"Ta question est hors de mon champs de compétences. 🤷‍♂️"**.
        - Mets en **gras** les mots clés.
        - Structure ta réponse avec des **listes** ou des **sections** si cela est pertinent.
        """
        return template

    def get_prompt(self) -> PromptTemplate:
        prompt = PromptTemplate(
            template=self.template,
            input_variables=["context","question"]
        )
        return prompt
    
    def get_embeddings(self) -> OpenAIEmbeddings:
        """Retourne les embeddings d'OpenAI"""
        embeddings = OpenAIEmbeddings(
              model="text-embedding-ada-002",  
              openai_api_key= OPENAI_API_KEY 
        )
        return embeddings

    def get_llm(self):
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.3,
            openai_api_key= OPENAI_API_KEY 
        )
        return llm
    
    def get_retrieval_qa(self):
        chain_type_kwargs = {"prompt": self.prompt}
        qa = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.retriever,
            return_source_documents=True,
            chain_type_kwargs=chain_type_kwargs
        )
        return qa

    def format_sources_with_ranges(sources):
        """
        Organize and format sources by document and group consecutive pages into ranges.
        
        :param sources: List of sources in the format 
                        "Document_Name.pdf (Page : X)"
        :return: Formatted string where sources are grouped by document, 
                with consecutive pages shown as ranges.
        """
        def group_pages_into_ranges(pages):
            """Group consecutive pages into ranges (e.g., 23-27)."""
            pages = sorted(pages)
            ranges = []
            start = pages[0]
            for i in range(1, len(pages)):
                if pages[i] != pages[i - 1] + 1:  # Break in continuity
                    if start == pages[i - 1]:
                        ranges.append(f"{start}")
                    else:
                        ranges.append(f"{start}-{pages[i - 1]}")
                    start = pages[i]
            # Handle the last range
            if start == pages[-1]:
                ranges.append(f"{start}")
            else:
                ranges.append(f"{start}-{pages[-1]}")
            return ranges

        # Group pages by document
        document_pages = defaultdict(list)
        for source in sources:
            # Extract document name and page number
            if " (Page : " in source:
                doc, page = source.split(" (Page : ")
                page_number = int(page.strip("Page : ").strip(")"))
                document_pages[doc].append(page_number)

        # Format output with grouped pages
        formatted_sources = []
        for doc, pages in document_pages.items():
            ranges = group_pages_into_ranges(pages)
            formatted_sources.append(f"{doc} (Pages : {', '.join(ranges)})")

        return "\n".join(formatted_sources)
    
    def retrieval_qa_inference(self, question: str, verbose: bool = True) -> str:
        
        """
        Interroge le modèle pour récupérer des documents et générer une réponse.
        """
        try:
            # Exécution de la chaîne pour obtenir la réponse et les documents sources
            result = self.retrieval_qa_chain({"query": question})

            # Vérifier si une réponse a été générée
            answer = result.get("result", "").strip()
            if not answer:
                return "Aucune réponse pertinente n'a été générée pour votre question."

            # Récupérer les documents sources
            source_documents = result.get("source_documents", [])
            if not source_documents:
                return f"{answer}\n\nSources:\nAucune source pertinente trouvée."

            # Construire la liste des sources en éliminant les doublons
            unique_sources = list(
                dict.fromkeys(
                    f"{doc.metadata.get('source', 'Source inconnue')} (Page : {doc.metadata.get('page', 'Page inconnue')})"
                    for doc in source_documents
                )
            )
            sources = "\n".join(unique_sources).strip()
            sourcesOrg = SourceOrganizer(sources)
            sources = sourcesOrg.to_string()
            if not sources:
                sources = "Aucune source fournie."

            # Affichage pour débogage si nécessaire
            if verbose:
                print(f"Question: {question}")
                print(f"Generated Answer: {answer}")
                print(f"Sources: {sources}")

            tab =np.array([get_cosine_distance(answer,"Je n'ai pas assez d'informations pour répondre. 🤔")['score'],
                   get_cosine_distance(answer, "Pourrais-tu préciser ta question ? 🧐")['score'], 
                   get_cosine_distance(answer,"Ta question est hors de mon champs de compétences. 🤷‍♂️")['score'],
                   get_cosine_distance(answer,"Bonjour! En tant que professeur spécialisé en marketing, je suis là pour répondre à ta question. Que puis-je faire pour t'aider aujourd'hui ?")['score']
                   ]
                   )
            
            dist = np.min(tab)
            Afficher = True 
            if dist > 0.1 : 
                Sources = f"\n\nSources:\n{sources}"
            else : 
                Sources = ""
            # Retourner la réponse avec les sources
            return f"{answer}" + Sources, sourcesOrg, Sources

        except KeyError as e:
            # Gestion des erreurs liées à des clés manquantes
            error_message = f"Erreur lors de l'inférence : clé manquante dans les résultats - {e}"
            print(error_message)
            return "Une erreur est survenue lors de la génération de la réponse."

        except Exception as e:
            # Gestion d'erreurs générales
            error_message = f"Erreur générale lors de l'inférence : {e}"
            print(error_message)
            return "Une erreur inattendue est survenue lors de la génération de la réponse."


    def list_top_k_sources(self, answer, k=3):
        # Extraire les sources en évitant les doublons et en gérant les clés manquantes
        sources = [
            [doc.metadata.get('source', 'Source inconnue'), doc.page_content]
            for doc in answer["source_documents"]
        ]
        #print(answer["source_documents"])
        
        # Élimine les doublons tout en préservant l'ordre
        unique_sources = list(dict.fromkeys(tuple(source) for source in sources))

        if not unique_sources:
            return "Désolé, je n'ai trouvé aucune ressource pour répondre à votre question."

        # Limiter le nombre de sources à afficher
        k = min(k, len(unique_sources))
        top_sources = unique_sources[:k]

        # Construire le texte affiché
        sources_display = "\n- ".join(f"{source[0]}: {source[1]}" for source in top_sources)
        
        if len(top_sources) == 1:
            return f"Voici la source qui pourrait t'être utile :\n- {sources_display}"
        else:
            return f"Voici {len(top_sources)} sources qui pourraient t'être utiles :\n- {sources_display}"

