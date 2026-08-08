import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

queries = [
    ("Capelli breaststroke energy cost stroke mechanics 1998", "Capelli 1998"),
    ("Barbosa kinematic changes 400-m front crawl young swimmers 2010", "Barbosa 2010"),
    ("Seifert breaststroke inter-limb coordination 2011", "Seifert 2011"),
    ("Psycharakis backstroke shoulder hip roll 2008", "Psycharakis 2008")
]

for q, label in queries:
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={urllib.parse.quote(q)}&retmode=json"
    req = urllib.request.Request(url, headers={'User-Agent': 'SwimAnalyzerAI/1.0'})
    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            data = json.loads(resp.read().decode())
            ids = data.get("esearchresult", {}).get("idlist", [])
            print(f"{label} -> PMIDs: {ids}")
            if ids:
                fetch_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={ids[0]}&retmode=xml"
                freq = urllib.request.Request(fetch_url, headers={'User-Agent': 'SwimAnalyzerAI/1.0'})
                with urllib.request.urlopen(freq, context=ctx) as fresp:
                    root = ET.fromstring(fresp.read())
                    art = root.find('.//PubmedArticle')
                    if art is not None:
                        title = art.findtext('.//ArticleTitle')
                        doi = None
                        for el in art.findall('.//ArticleId'):
                            if el.attrib.get('IdType') == 'doi':
                                doi = el.text
                        print(f"  Title: {title}\n  DOI: {doi}")
    except Exception as e:
        print(f"Error searching {label}: {e}")
