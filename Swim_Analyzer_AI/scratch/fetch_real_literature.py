import json
import urllib.request
import xml.etree.ElementTree as ET

pmids = [
    "448780",    # Craig & Pendergast 1979
    "3995828",   # Craig et al. 1985
    "26236319",  # Dormehl et al. 2015 (Adolescent freestyle)
    "18274945",  # Seifert et al. 2008 (Butterfly skill & gender)
    "18978622",  # Hellard et al. 2008 (Elite all 4 strokes)
    "32679803",  # Cortesi et al. 2020 (Backstroke youth 11-13)
    "20544485",  # Psycharakis et al. 2010 (Front crawl & backstroke)
    "9546059",   # Capelli et al. 1998 (Breaststroke & Butterfly)
    "15616894",  # Zamparo et al. 2005 (Masters 35-75 yrs kinematics)
    "23486330"   # Barbosa et al. 2010 (Age-group youth kinematics)
]

url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={','.join(pmids)}&retmode=xml"
import ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request(url, headers={'User-Agent': 'SwimAnalyzerAI/1.0'})
with urllib.request.urlopen(req, context=ctx) as resp:
    xml_data = resp.read()

root = ET.fromstring(xml_data)
articles = []

for article in root.findall('.//PubmedArticle'):
    pmid = article.findtext('.//PMID')
    title = article.findtext('.//ArticleTitle')
    journal = article.findtext('.//Journal/Title')
    year = article.findtext('.//JournalIssue/PubDate/Year') or article.findtext('.//JournalIssue/PubDate/MedlineDate')
    
    # DOI
    doi = None
    for el in article.findall('.//ArticleId'):
        if el.attrib.get('IdType') == 'doi':
            doi = el.text

    authors = []
    for author in article.findall('.//Author'):
        last = author.findtext('LastName') or ''
        initials = author.findtext('Initials') or ''
        if last:
            authors.append(f"{last}, {initials}".strip())

    abstract = article.findtext('.//AbstractText') or ''
    articles.append({
        "pmid": pmid,
        "title": title,
        "authors": authors,
        "year": year,
        "journal": journal,
        "doi": doi,
        "abstract": abstract[:300] + "..." if abstract else ""
    })

print(json.dumps(articles, indent=2))
