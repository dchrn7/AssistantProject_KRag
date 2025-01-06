import re
import os 
from collections import defaultdict
from pdf2image import convert_from_path

class SourceOrganizer:
    def __init__(self, sources_string):
        """
        Initialize the organizer with a string of sources, each on a new line.
        :param sources_string: String containing sources in the format:
                               "Document.pdf (Page : X)\nDocument.pdf (Page : Y)"
        """
        self.sources_string = sources_string
        self.organized_sources = defaultdict(list)
        self._process_sources()

    def get_organized_sources(self): 
        return self.organized_sources
    
    def _process_sources(self):
        """Parse the sources string and organize it by document and pages."""
        # Match all occurrences of "Document_Name.pdf (Page : X)"
        pattern = r"([^\(]+\.pdf) \(Pages? : (\d+)\)"
        matches = re.findall(pattern, self.sources_string)

        for doc, page in matches:
            self.organized_sources[doc.strip()].append(int(page))

        # Group pages into ranges for each document
        for doc, pages in self.organized_sources.items():
            self.organized_sources[doc] = self._group_pages_into_ranges(sorted(pages))

    @staticmethod
    def _group_pages_into_ranges(pages):
        """
        Group consecutive pages into ranges (e.g., [1, 2, 3, 9] -> ["1-3", "9"])
        :param pages: List of integers representing page numbers.
        :return: List of strings with grouped pages.
        """
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

    def to_string(self):
        """Return the organized sources as a formatted string."""
        formatted_sources = []
        for doc, ranges in self.organized_sources.items():
            formatted_sources.append(f"{doc} (Pages : {', '.join(ranges)})")
        return "\n".join(formatted_sources)
    
    def generate_file_paths(self, folder_path):
        """
        Génère un dictionnaire mappant les noms de fichiers PDF aux chemins réels.
        :param folder_path: Chemin du dossier contenant les fichiers PDF.
        :return: Dictionnaire {nom_fichier: chemin_complet}.
        """
        file_paths = {}
        for file_name in os.listdir(folder_path):
            if file_name.endswith(".pdf") and file_name in self.organized_sources:
                file_paths[file_name] = os.path.join(folder_path, file_name)
        return file_paths
    

if __name__ == "__main__":
    # Exemple d'utilisation
    sources = "ENT-Maketing_operationnel.pdf (Page : 1) ENT-Maketing_operationnel.pdf (Page : 2) Marketing stratégique et opérationnel.pdf (Page : 9) COURS_DE_MARKETING.pdf (Page : 102)"

    organizer = SourceOrganizer(sources)
    print(organizer.get_organized_sources())

    pdf_directory="/Users/drisschraibi/Desktop/RAG-Chatbot-with-Confluence/Cours_Marketing_Maths" # Répertoire contenant vos fichiers PDF locaux