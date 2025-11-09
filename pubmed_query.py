from Bio import Entrez
import time

# Configure NCBI API
# Entrez.email = ""
# Entrez.api_key = ""  # Optional but recommended for higher rate limits


def search_pubmed_with_boolean(query, retmax=10, sleep_time=0.35):
    """
    Search PubMed using a Boolean operator query string.

    Args:
        query (str): Boolean search string (e.g., 'deep learning[Title/Abstract] AND hypothesis[Title/Abstract]')
        retmax (int): Maximum number of results to retrieve (default: 10)
        sleep_time (float): Time to sleep between API calls to comply with NCBI rate limiting

    Returns:
        list: List of PubMed IDs matching the search criteria
    """
    try:
        print(f"Searching PubMed with query: {query}")

        # Perform search
        search_handle = Entrez.esearch(db="pubmed", term=query, retmax=retmax)
        search_record = Entrez.read(search_handle)
        search_handle.close()

        id_list = search_record.get("IdList", [])
        count = search_record.get("Count", "0")

        print(f"Found {count} articles; retrieving {len(id_list)} records\n")

        if not id_list:
            print("No results found.")
            return []

        # Respect NCBI rate limiting
        time.sleep(sleep_time)

        return id_list

    except Exception as e:
        print(f"Error during search: {e}")
        return []


def fetch_article_details(pmid_list):
    """
    Fetch article metadata, abstract, and title from PubMed using XML format.

    Args:
        pmid_list (list): List of PubMed IDs

    Returns:
        list: List of dictionaries containing article details
    """
    if not pmid_list:
        print("No PubMed IDs provided.")
        return []

    try:
        # Use retmode="xml" for proper parsing with Bio.Entrez.read()
        fetch_handle = Entrez.efetch(
            db="pubmed",
            id=",".join(pmid_list),
            retmode="xml"
        )
        records = Entrez.read(fetch_handle)
        fetch_handle.close()

        articles = []

        for article in records.get("PubmedArticle", []):
            try:
                medline_citation = article.get("MedlineCitation", {})
                article_info = medline_citation.get("Article", {})

                # Extract title
                title = article_info.get("ArticleTitle", "N/A")

                # Extract abstract (AbstractText is a list)
                abstract_text = article_info.get("Abstract", {})
                abstract_content = ""
                if abstract_text:
                    abstract_list = abstract_text.get("AbstractText", [])
                    # AbstractText can be a list or a string
                    if isinstance(abstract_list, list):
                        abstract_content = " ".join(str(text) for text in abstract_list)
                    else:
                        abstract_content = str(abstract_list)
                else:
                    abstract_content = "No abstract available"

                # Extract authors
                author_list = article_info.get("AuthorList", [])
                authors = []
                for author in author_list:
                    last_name = author.get("LastName", "")
                    first_name = author.get("ForeName", "")
                    if last_name and first_name:
                        authors.append(f"{first_name} {last_name}")

                # Extract publication date
                pub_date = article_info.get("Journal", {}).get("JournalIssue", {}).get("PubDate", {})
                year = pub_date.get("Year", "N/A")

                # Extract PMID
                pmid = medline_citation.get("PMID", "N/A")

                articles.append({
                    "PMID": pmid,
                    "Title": title,
                    "Abstract": abstract_content,
                    "Authors": ", ".join(authors[:5]),  # First 5 authors
                    "Year": year
                })

            except Exception as e:
                print(f"Error parsing article: {e}")
                continue

        return articles

    except Exception as e:
        print(f"Error during fetch: {e}")
        return []


def print_articles(articles):
    """
    Pretty print article details.

    Args:
        articles (list): List of article dictionaries
    """
    for idx, article in enumerate(articles, 1):
        print(f"\n{'=' * 80}")
        print(f"Article {idx}")
        print(f"{'=' * 80}")
        print(f"PMID: {article['PMID']}")
        print(f"Title: {article['Title']}")
        print(f"Authors: {article['Authors']}")
        print(f"Year: {article['Year']}")
        print(f"Abstract: {article['Abstract'][:500]}...")  # Print first 500 chars
        print()


# Main workflow
if __name__ == "__main__":
    # Example 1: Search with Boolean operators
    # search_query = 'deep learning[Title/Abstract] AND hypothesis[Title/Abstract]'
    search_query = '(metformin) and (cancer)'
    pmid_list = search_pubmed_with_boolean(search_query, retmax=5)

    if pmid_list:
        # Fetch detailed information
        articles = fetch_article_details(pmid_list)

        # Display results
        print_articles(articles)
