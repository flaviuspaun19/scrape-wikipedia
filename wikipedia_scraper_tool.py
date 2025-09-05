import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
import os
import io

def scrape_wiki_tables(url):
    print(f"Attempting to scrape tables from: {url}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers)
        response.raise_for_status() 

        tables = pd.read_html(io.StringIO(response.text))
        print(f"Successfully found {len(tables)} table(s) on the page.")
    
        for table in tables:
            table.columns = table.columns.str.strip()
            if 'Population' in table.columns:
                print("Found the correct table with the 'Population' column.")
                return table 
        
        print("Could not find a table with the 'Population' column.")
        return pd.DataFrame()

    except requests.exceptions.RequestException as e:
        print(f"Error accessing the URL: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"Error scraping tables: {e}")
        return pd.DataFrame()

def clean_and_analyze_population_data(df):
    if not isinstance(df, pd.DataFrame) or 'Population' not in df.columns:
        print("Data is not a valid DataFrame or 'Population' column is missing.")
        return None

    try:
        df['Population'] = df['Population'].astype(str)
        df['Population'] = df['Population'].str.replace(',', '', regex=True)
        df['Population'] = df['Population'].str.replace(r'\[\d+\]', '', regex=True)
        df['Population'] = pd.to_numeric(df['Population'], errors='coerce')
        df.dropna(subset=['Population'], inplace=True)

        print("Data successfully cleaned and converted to numeric.")

        top_10 = df.nlargest(10, 'Population')
        
        average_population = df['Population'].mean()
        print(f"The average population is: {average_population:,.2f}")
        return top_10

    except Exception as e:
        print(f"Error during data cleaning or analysis: {e}")
        return None

def create_population_chart(df):
    if df is None or df.empty:
        print("No data to plot.")
        return

    try:
    
        country_col_name = None
        for col in df.columns:
            if 'Country' in col or 'Dependency' in col:
                country_col_name = col
                break

        if country_col_name is None:
            for col in df.columns:
                if df[col].dtype == 'object' and 'Population' not in col and 'Region' not in col and 'Date' not in col:
                    country_col_name = col
                    break

        if country_col_name is None:
            print("Error creating chart: Could not find a suitable column for countries.")
            return

        plt.style.use('ggplot')
        plt.figure(figsize=(12, 8))
        
        plt.bar(df[country_col_name], df['Population'], color='skyblue')
        
        plt.title('Top 10 Most Populous Countries in the World', fontsize=16)
        plt.xlabel('Country / Dependency', fontsize=12)
        plt.ylabel('Population (in Billions)', fontsize=12)
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
     
        script_dir = os.path.dirname(os.path.abspath(__file__))
     
        charts_dir = os.path.join(script_dir, 'charts')
        if not os.path.exists(charts_dir):
            os.makedirs(charts_dir)

        file_path = os.path.join(charts_dir, 'top_10_population.png')
        
        plt.savefig(file_path)
        print(f"Chart saved to: {file_path}")
        
        plt.show()
    except Exception as e:
        print(f"Error creating chart: {e}")

def analyze_page_content(url):
    print(f"Analyzing page content for: {url}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html5lib')

        section_headers = soup.find_all('span', {'class': 'mw-headline'})
        
        if not section_headers:
            print("No main sections found. Analyzing the entire page.")
            body_content = soup.find('div', {'id': 'mw-content-text'})
            if body_content:
                count_attributes_in_section("Main Content", body_content)
            return

        for i, header_span in enumerate(section_headers):
            section_name = header_span.text
            content_div = header_span.parent.find_next_sibling('div')

            if content_div:
                count_attributes_in_section(section_name, content_div)
            else:
                print(f"Could not find content for section: {section_name}")

    except requests.exceptions.RequestException as e:
        print(f"Error accessing the URL: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def count_attributes_in_section(section_name, content_soup):
    paragraphs = content_soup.find_all('p')
    paragraph_count = len(paragraphs)
    hyperlink_count = sum(len(p.find_all('a')) for p in paragraphs)
    picture_count = sum(len(p.find_all('img')) for p in paragraphs)
    word_count = sum(len(re.findall(r'\w+', p.text)) for p in paragraphs)

    print("-" * 20)
    print("Section:", section_name)
    print("Paragraphs:", paragraph_count)
    print("Hyperlinks:", hyperlink_count)
    print("Pictures:", picture_count)
    print("Words:", word_count)
    print("-" * 20)

if __name__ == "__main__":
    population_url = "https://en.wikipedia.org/wiki/List_of_countries_and_dependencies_by_population"
    
    population_df = scrape_wiki_tables(population_url)
    
    if not population_df.empty:
        top_10_countries = clean_and_analyze_population_data(population_df)
        
        if top_10_countries is not None:
            create_population_chart(top_10_countries)

    decision = 'y'
    while decision.lower() == 'y':
        url = input("\nInsert the URL of the Wikipedia page you want to analyze: ")
        analyze_page_content(url)
        decision = input("Do you want to analyze another URL? (y/n): ")
    
    print("Program terminated.")
