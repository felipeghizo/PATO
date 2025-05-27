import pandas as pd
import re
from functools import lru_cache

@lru_cache(maxsize=1)
def carregar_categorias_excel(file_path):
    """Carrega e cacheia as categorias do Excel"""
    try:
        df = pd.read_excel(file_path, header=0, dtype=str)
        categorias = df.columns[1:]
        
        base_url = "https://wwws.suframa.gov.br/servicos/estrangeiro/consultas/ListagemInsumos/EST_PoloProdutoTipo.asp?produto="
        
        return {
            cat: [base_url + val if not val.startswith(('http', 'www')) else val 
                 for val in df[cat].dropna().tolist()]
            for cat in categorias
        }
    except Exception as e:
        print(f"Erro ao carregar Excel: {e}")
        return {}

def parse_keywords(keyword_string):
    """Otimização da criação de regex para palavras-chave"""
    words = [w for w in keyword_string.strip().split() if w]
    return [re.compile(rf'(?=.*\b{re.escape(w)}\b)', re.I) for w in words] if words else []

def parse_excluded_keywords(excluded_keyword_string):
    """Otimização da criação de regex para exclusões"""
    words = [w for w in excluded_keyword_string.strip().split() if w]
    return [re.compile(rf'\b{re.escape(w)}\b', re.I) for w in words] if words else []