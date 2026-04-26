import json
import os
from elasticsearch import Elasticsearch

def indexar_noticias():
    # 1. Ligar ao Elastic
    es = Elasticsearch("http://localhost:9200")
    
    # 2. Caminho para a pasta de dados
    pasta_data = "../data"
    nome_indice = "noticias_tecnologia"

    # 3. Listar todos os ficheiros .json na pasta
    ficheiros = [f for f in os.listdir(pasta_data) if f.endswith('.json')]
    
    if not ficheiros:
        print("Nenhum ficheiro JSON encontrado para indexar.")
        return

    for nome_f in ficheiros:
        caminho_completo = os.path.join(pasta_data, nome_f)
        with open(caminho_completo, 'r', encoding='utf-8') as f:
            noticias = json.load(f)
            
            print(f"A indexar {len(noticias)} notícias do ficheiro {nome_f}...")
            for noticia in noticias:
                # O Elastic usa o URL como ID para evitar duplicados se correres o script 2 vezes
                es.index(index=nome_indice, id=noticia['url'], document=noticia)
        
    print("\nIndexação concluída com sucesso!")

if __name__ == "__main__":
    indexar_noticias()