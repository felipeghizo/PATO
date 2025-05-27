from flask import Blueprint, render_template, request, send_file
import requests
import json
import pandas as pd
from io import BytesIO
from bs4 import BeautifulSoup
import os
from .NCM_utils import carregar_categorias_excel, parse_keywords, parse_excluded_keywords

ncm_bp = Blueprint('ncm', __name__, template_folder='templates/ncm_finder',
                  static_folder='static', static_url_path='/static/ncm_finder')

# Configurações
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCEL_FILE = os.path.join(BASE_DIR, 'NCM_Finder', 'Projetos.xlsx')

# Carrega as categorias
try:
    CATEGORIAS = carregar_categorias_excel(EXCEL_FILE)
except Exception as e:
    print(f"Erro ao carregar categorias: {e}")
    CATEGORIAS = {}

# Cache da tabela de NCMs
try:
    NCM_FILE = os.path.join(BASE_DIR, 'NCM_Finder', 'NCMs.xlsx')
    _df_ncm_cache = pd.read_excel(NCM_FILE)
    _df_ncm_cache["Código"] = _df_ncm_cache.iloc[:, 0].astype(str).str.strip()
    _df_ncm_cache["NCM"] = _df_ncm_cache.iloc[:, 2].astype(str).str.strip() if _df_ncm_cache.shape[1] > 2 else ""
except Exception as e:
    print(f"Erro ao carregar cache do NCMs.xlsx: {e}")
    _df_ncm_cache = pd.DataFrame(columns=["Código", "NCM"])

@ncm_bp.route('/')
def ncm_home():
    return render_template('ncm_finder/ncmFinder.html',
                        categorias=CATEGORIAS,
                        resultados=None,
                        resultados_codigos=None,
                        active_tab='palavras',  # Definindo valor padrão
                        title="NCM Finder - Portal Intelbras")

@ncm_bp.route('/buscar_palavraChave', methods=['POST'])
def buscar_palavraChave():
    selected_categories = request.form.getlist("categorias")
    keyword_input = request.form.get("keywords", "")
    excluded_keyword_input = request.form.get("exclude", "")

    if not selected_categories or not keyword_input:
        erro_message = "Por favor, selecione pelo menos uma categoria e digite uma palavra-chave."
        return render_template('ncm_finder/ncmFinder.html', 
                            categorias=CATEGORIAS, 
                            erro_message=erro_message,
                            active_tab='palavras')

    keyword_patterns = parse_keywords(keyword_input)
    excluded_patterns = parse_excluded_keywords(excluded_keyword_input)
    resultados = []

    for categoria in selected_categories:
        urls = CATEGORIAS.get(categoria, [])
        for url in urls:
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                rows = soup.find_all("tr", class_="ft1")
                projeto_codigo = url.split("=")[-1]

                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) >= 5:
                        ncm = cols[0].get_text(strip=True)
                        destaque = cols[1].get_text(strip=True)
                        descricao = cols[2].get_text(strip=True)
                        item_controlado = cols[3].get_text(strip=True)
                        comentario = cols[4].get_text(strip=True)

                        if descricao and all(pattern.search(descricao) for pattern in keyword_patterns):
                            if not any(pattern.search(descricao) for pattern in excluded_patterns):
                                resultados.append([categoria, projeto_codigo, ncm, destaque, descricao, item_controlado, comentario])

    if not resultados:
        erro_message = "Nenhum resultado encontrado para os filtros selecionados."
        return render_template('ncm_finder/ncmFinder.html', 
                            categorias=CATEGORIAS, 
                            erro_message=erro_message,
                            active_tab='palavras')
    
    return render_template('ncm_finder/ncmFinder.html', 
                        categorias=CATEGORIAS, 
                        resultados=resultados,
                        active_tab='palavras')

@ncm_bp.route('/buscar_codigos', methods=['POST'])
def buscar_codigos():
    if request.form.get('action') == 'Exportar para Excel':
        dados_json = request.form.get("codigos_para_exportar")
        try:
            dados = json.loads(dados_json)
            # Converte lista de listas em lista de dicionários
            dados_dicts = [{"Código": linha[0], "NCM": linha[1]} for linha in dados]
            df_export = pd.DataFrame(dados_dicts)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_export.to_excel(writer, index=False, sheet_name="Codigos")
            output.seek(0)
            return send_file(output, as_attachment=True,
                           download_name="Resultados_Codigos.xlsx",
                           mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except Exception as e:
            erro_message = f"Erro ao exportar os dados: {e}"
            return render_template('ncm_finder/ncmFinder.html', 
                                categorias=CATEGORIAS, 
                                erro_message=erro_message,
                                active_tab='codigos')
    else:
        codigos_input = request.form.get("codigos", "")
        codigos_lista = [codigo.strip() for codigo in codigos_input.splitlines() if codigo.strip()]

        if not codigos_lista:
            erro_message = "Por favor, insira ao menos um código."
            return render_template('ncm_finder/ncmFinder.html', 
                                categorias=CATEGORIAS, 
                                erro_message=erro_message,
                                active_tab='codigos')

        if _df_ncm_cache.empty:
            erro_message = "Arquivo NCMs.xlsx não pôde ser carregado corretamente."
            return render_template('ncm_finder/ncmFinder.html', 
                                categorias=CATEGORIAS, 
                                erro_message=erro_message,
                                active_tab='codigos')

        df_filtrado = _df_ncm_cache[_df_ncm_cache["Código"].isin(codigos_lista)]

        if df_filtrado.empty:
            erro_message = "Nenhum código encontrado no arquivo."
            return render_template('ncm_finder/ncmFinder.html', 
                                categorias=CATEGORIAS, 
                                erro_message=erro_message,
                                active_tab='codigos')

        resultados_codigos = df_filtrado[["Código", "NCM"]].values.tolist()
        return render_template('ncm_finder/ncmFinder.html', 
                            categorias=CATEGORIAS, 
                            resultados_codigos=resultados_codigos,
                            active_tab='codigos')