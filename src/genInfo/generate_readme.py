import os
import yaml
import json
import logging

from pathlib import Path
from omegaconf import OmegaConf
from typing import Dict, Any, List

from utils.json_handler import JsonHandler
from utils.common_utils import merge_settings

# Requires pybtex-apa7-style plugins.
from pybtex.plugin import find_plugin
from pybtex.database import parse_file
APA = find_plugin('pybtex.style.formatting', 'apa7')()
PLAINTEXT = find_plugin('pybtex.backends', 'plaintext')()

# Depricated
# For BibTeX to APA conversion
from pybtex.database import parse_string
# For latex-to-unicode conversion
#from pylatexenc.latex2text import LatexNodes2Text


class ReadmeGeneratorManager:
    def __init__(
        self,
        config: OmegaConf,
        target_datasets: List[str],
        default_dataset_settings: Dict[str, Any],
        mapping: Dict[str, Any],
    ):
        self.config = config
        self.target_datasets = target_datasets
        self.default_dataset_settings = default_dataset_settings
        self.mapping = mapping
        self.logger = logging.getLogger(__name__)
        
        
    def initiate_readme_generation(self):
        for dataset_name in self.target_datasets:
            self.logger.info(f"Readme Generator - Generating readme.md for dataset: {dataset_name}")

            # Merging Default Settings with Dataset Settings.
            dataset_path = Path(self.config.pathDataset) / dataset_name
            dataset_settings = JsonHandler(dataset_path / self.config.datasetSettingsJson)
            final_settings = merge_settings(
                defaults=self.default_dataset_settings,
                overrides=dataset_settings.get_data()
            )

            # Acquiring the Mapping
            dataset_mapping = self.mapping[dataset_name]

            # Initialize and run the readme generator
            readme_generator = ReadmeGenerator(
                dataset_settings=final_settings,
                dataset_path=dataset_path,
                mapping=dataset_mapping,
                config=self.config,
            )

            success = readme_generator.run()
            if success:
                self.logger.info(f"Readme generation completed for dataset '{dataset_name}'.")
            else:
                self.logger.error(f"Readme generation failed for dataset '{dataset_name}'.")


class ReadmeGenerator:
    plugin_name = "readme_generator"

    @classmethod
    def get_name(cls) -> str:
        return cls.plugin_name

    def __init__(self, dataset_settings: dict, dataset_path: Path, mapping: List[Dict[str, Any]], config: OmegaConf):
        self.logger = logging.getLogger(__name__)
        self.dataset_settings = dataset_settings
        self.dataset_path = dataset_path
        self.mapping = mapping
        self.config = config

        # Paths
        self.readme_file = self.dataset_path / self.config.datasetReadMe
        self.info_yaml_file = self.dataset_path / self.config.datasetInfoYaml
        
        
    def run(self) -> bool:
        
        # Check if Info File is present, Else Skip.
        if not self.info_yaml_file.exists():
            self.logger.warning(f"-ReadmeGenerator - info.yaml file Missing for Dataset:{self.dataset_path.name}")
            return False
        
        
        try:
            # Load info.yaml
            with open(self.info_yaml_file, 'r', encoding='utf-8') as f:
                info = yaml.safe_load(f)

            # Extract data from info.yaml
            note = info.get('note', '')
            title = info.get('title', '')
            description = info.get('description', '')
            usage_agreement = info.get('usage_agreement', '')
            license_info = info.get('license', '')
            citation_bibtex = info.get('citation', '')
            download_url = info.get('download','')

            # Convert BibTeX to APA style
            if citation_bibtex:
                apa_citation = self.bibtex_to_apa_new(citation_bibtex)
            else:
                apa_citation = ""
                
            # Generate dataset statistics from mapping
            stats_table = self.generate_stats_table()

            # Prepare markdown content
            readme_content = f"{note}\n\n"
            readme_content += f"# {title}\n\n"
            if description:
                readme_content += f"## Description\n\n{description}\n\n"
            if usage_agreement:
                readme_content += f"## Usage Agreement\n\n{usage_agreement}\n\n"
            if license_info:
                readme_content += f"## License\n\n{license_info}\n\n"
            if citation_bibtex:
                readme_content += f"## Citation\n\n{apa_citation}\n\n"
            if download_url:
                readme_content += f"## Download\n\n{download_url}\n\n"
                
            readme_content += f"## Dataset Statistics\n\n{stats_table}\n\n"

            # Write to readme.md
            with open(self.readme_file, 'w') as f:
                f.write(readme_content)

            self.logger.info(f"Readme file generated at {self.readme_file}")
            return True

        except Exception as e:
            self.logger.error(f"An error occurred during readme generation: {e}")
            return False

    def bibtex_to_apa_new(self, bibtex_str):
        bibliography = parse_string(bibtex_str, 'bibtex')
        formatted_bib = APA.format_bibliography(bibliography)
        if len(formatted_bib.entries) != 1:
            self.logger.error(f"The Number of bibliography Entries must be equal to 1, Dataset:{self.dataset_path.name}")
            return ""
        else:
            return formatted_bib.entries[0].text.render(PLAINTEXT)
            

    # The following Function is Obsolete/depricated. Using pybtex-apa7-style now
    # from: https://github.com/yasinzaii/pybtex-apa7-style.git
    def bibtex_to_apa(self, bibtex_str):
        """
        Convert a BibTeX string to APA style citation using manubot.
        """
        try:
            
            # Parse the BibTeX string
            bib_data = parse_string(bibtex_str, 'bibtex')

            # Assuming there's only one entry in the BibTeX string
            entry = next(iter(bib_data.entries.values()))
            
            # Extract and format authors
            authors = entry.persons.get('author', [])
            formatted_authors = self.format_authors(authors)
            
            # Extract other necessary fields
            year = entry.fields.get('year', 'n.d.')
            title = entry.fields.get('title', '').rstrip('.')
            journal = entry.fields.get('journal', '')
            volume = entry.fields.get('volume', '')
            number = entry.fields.get('number', '')
            pages = entry.fields.get('pages', '')
            doi = entry.fields.get('doi', '')
            
            # Construct the APA citation
            citation = f"{formatted_authors} ({year}). {title}. {journal}"
            
            if volume:
                citation += f", {volume}"
                if number:
                    citation += f"({number})"
            if pages:
                citation += f", {pages}"
            citation += "."
            
            # Append DOI if available
            if doi:
                citation += f" https://doi.org/{doi}"
            
            return citation
            
        except Exception as e:
            self.logger.error(f"Error converting BibTeX to APA style with manubot: {e}")
            return ""

    # Depricated
    def format_authors(self, authors):
        """
        Format a list of pybtex Person objects into APA-style authors string.
        
        Args:
            authors (list): List of pybtex.database.Person objects.
            
        Returns:
            str: Formatted authors string.
        """
        formatted = []
        for author in authors:
            # Combine last names
            last_names = ' '.join(author.last_names)
            last_names = LatexNodes2Text().latex_to_text(last_names)

            # Combine initials
            initials = ''.join([f"{name[0]}." for name in author.first_names])
            
            formatted.append(f"{last_names}, {initials}")
        
        # APA style formatting for multiple authors
        if len(formatted) <= 20:
            if len(formatted) == 1:
                return formatted[0]
            else:
                return ', '.join(formatted[:-1]) + f", & {formatted[-1]}"
        else:
            # For 21 or more authors, list the first 19, then ellipsis, then the last author
            first_nineteen = ', '.join(formatted[:19])
            last_author = formatted[-1]
            return f"{first_nineteen}, ... & {last_author}"
    
    
    
    def generate_stats_table(self):
        """
        Generate a markdown table of dataset statistics from the mapping.
        """
        # Collect stats
        num_subjects = len(set(entry['subject'] for entry in self.mapping))
        num_sessions = len(set((entry['subject'], entry.get('session', '')) for entry in self.mapping))
        
        modalities = set()
        for entry in self.mapping:
            modalities.update(entry.get('mris', {}).keys())

        # Count MRIs per modality
        modality_counts = {modality: 0 for modality in modalities}
        for entry in self.mapping:
            for modality in entry.get('mris', {}).keys():
                modality_counts[modality] += 1

        # Calculate the total number of MRIs
        num_mris = sum(modality_counts.values())
        
        # Create a table
        stats_data = [
            {'Statistic': 'Number of Subjects', 'Value': num_subjects},
            {'Statistic': 'Number of Sessions', 'Value': num_sessions},
            {'Statistic': 'Total Number of MRIs', 'Value': num_mris},
        ]

        for modality, count in modality_counts.items():
            stats_data.append({'Statistic': f'Number of {modality.upper()} MRIs', 'Value': count})

        table_md = self.generate_markdown_table(stats_data)
        return table_md

    def generate_markdown_table(self, data):
        """
        Generate a markdown table from a list of dictionaries.
        """
        if not data:
            return ''
        headers = data[0].keys()
        header_row = '| ' + ' | '.join(headers) + ' |'
        separator_row = '| ' + ' | '.join(['---'] * len(headers)) + ' |'
        data_rows = []
        for item in data:
            row = '| ' + ' | '.join(str(item[h]) for h in headers) + ' |'
            data_rows.append(row)
        table = '\n'.join([header_row, separator_row] + data_rows)
        return table