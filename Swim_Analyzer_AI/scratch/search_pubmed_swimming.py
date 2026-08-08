import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

queries = [
    ("SRC-FREE-CRAIG-1979", "Craig Pendergast stroke rate distance velocity swimming"),
    ("SRC-FREE-DORMEHL-2015", "Dormehl age sex adolescent freestyle swimming"),
    ("SRC-FLY-SEIFERT-2008", "Seifert butterfly spatial temporal parameters gender swimming"),
    ("SRC-ALL-HELLARD-2008", "Hellard elite female swimmers velocity stroke rate"),
    ("SRC-BACK-CORTESI-2020", "Cortesi backstroke kinematics 11-13 year-old swimmers"),
    ("SRC-FREE-PSYCHARAKIS-2010", "Psycharakis front crawl kinematics swimming"),
    ("SRC-MASTERS-ZAMPARO-2005", "Zamparo masters swimming kinematics age"),
    ("SRC-YOUTH-BARBOSA-2010", "Barbosa age group swimming kinematics youth")
]

results = []

for sid, q in queries:
    encoded_q = urllib.parse.quote(q)
    search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={encoded_q}&retmode=json&retmax=3"
    
    req = urllib.request.Request(search_url, headers={'User-Agent': 'SwimAnalyzerAI/1.0'})
    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            data = json.loads(resp.read().decode())
            pmids = data.get("esearchresult", {}).get("idlist", [])
            
            if pmids:
                fetch_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmids[0]}&retmode=xml"
                freq = urllib.request.Request(fetch_url, headers={'User-Agent': 'SwimAnalyzerAI/1.0'})
                with urllib.request.urlopen(freq, context=ctx) as fresp:
                    xml_data = fresp.read()
                    root = ET.fromstring(xml_data)
                    art = root.find('.//PubmedArticle')
                    if art is not None:
                        pmid = art.findtext('.//PMID')
                        title = art.findtext('.//ArticleTitle')
                        journal = art.findtext('.//Journal/Title')
                        year = art.findtext('.//JournalIssue/PubDate/Year') or art.findtext('.//JournalIssue/PubDate/MedlineDate')
                        doi = None
                        for el in art.findall('.//ArticleId'):
                            if el.attrib.get('IdType') == 'doi':
                                doi = el.text
                        authors = []
                        for author in art.findall('.//Author'):
                            last = author.findtext('LastName') or ''
                            initials = author.findtext('Initials') or ''
                            if last:
                                authors.append(f"{last}, {initials}".strip())
                        abstract = art.findtext('.//AbstractText') or ''
                        results.append({
                            "query_id": sid,
                            "pmid": pmid,
                            "title": title,
                            "authors": authors[:4],
                            "year": year,
                            "journal": journal,
                            "doi": doi,
                            "abstract": abstract[:400]
                        })
    except Exception as e:
        print(f"Error searching for {sid}: {e}")

print(json.dumps(results, indent=2))
