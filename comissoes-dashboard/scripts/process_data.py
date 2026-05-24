import pandas as pd
import json
import sys
import re
import logging
import csv
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def detect_separator(filepath):
    """Detecta automaticamente o separador do arquivo CSV."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            sample = f.read(4096)
        dialect = csv.Sniffer().sniff(sample)
        return dialect.delimiter
    except Exception as e:
        logger.warning(f"Erro ao detectar separador: {e}. Usando ';' como padrão.")
        return ';'


def extract_processo_info(processo_str):
    """Extrai Tipo, Número e Ano da coluna Processo."""
    if pd.isna(processo_str):
        return None, None, None

    try:
        # Padrão: "PL 1234/2026"
        match = re.match(r'^([A-Z]+)\s+(\d+)/(\d+)$', str(processo_str).strip())
        if match:
            tipo, numero, ano = match.groups()
            return tipo, numero, ano
        else:
            logger.warning(f"Processo não segue padrão esperado: {processo_str}")
            return None, None, None
    except Exception as e:
        logger.warning(f"Erro ao extrair Processo: {e} para '{processo_str}'")
        return None, None, None


def extract_tramitacao(tramitacao_str):
    """Extrai Data, Local e Origem da coluna Tramitação."""
    if pd.isna(tramitacao_str):
        return None, None, None

    try:
        tramitacao_str = str(tramitacao_str).strip()
        # Padrão: "16/04/2026 21:40:00 - FIN  (Recebido de SGP22)"
        match = re.match(
            r'^(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})\s+-\s+([A-Z0-9]+)\s+\(([^)]+)\)$',
            tramitacao_str
        )
        if match:
            data, local, origem = match.groups()
            return data.strip(), local.strip(), origem.strip()
        else:
            logger.warning(f"Tramitação não segue padrão esperado: {tramitacao_str}")
            return None, None, None
    except Exception as e:
        logger.warning(f"Erro ao extrair Tramitação: {e} para '{tramitacao_str}'")
        return None, None, None


def extract_tramitacao_interna(tramitacao_interna_str):
    """Extrai Data, Local e Estado da coluna Tramitacao Interna."""
    if pd.isna(tramitacao_interna_str):
        return None, None, None

    try:
        tramitacao_interna_str = str(tramitacao_interna_str).strip()
        # Padrão: "20/05/2026 02:46 - Secretaria (SGP12) / Aguardando Notas Taquigráficas"
        match = re.match(
            r'^(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2})\s+-\s+(.+?)\s+/\s+(.+)$',
            tramitacao_interna_str
        )
        if match:
            data, local, estado = match.groups()
            return data.strip(), local.strip(), estado.strip()
        else:
            logger.warning(f"Tramitação Interna não segue padrão esperado: {tramitacao_interna_str}")
            return None, None, None
    except Exception as e:
        logger.warning(f"Erro ao extrair Tramitação Interna: {e} para '{tramitacao_interna_str}'")
        return None, None, None


def process_csv(input_file, comissao):
    """Processa o arquivo CSV com os tratamentos especificados."""
    logger.info(f"Iniciando processamento: {input_file}")

    # Detectar separador
    separator = detect_separator(input_file)
    logger.info(f"Separador detectado: '{separator}'")

    # Ler CSV
    try:
        df = pd.read_csv(input_file, encoding='utf-8', sep=separator)
        logger.info(f"Arquivo carregado com sucesso. {len(df)} linhas encontradas.")
    except Exception as e:
        logger.error(f"Erro ao ler CSV: {e}")
        raise

    # 2. Extrair Tipo, Número e Ano
    logger.info("Extraindo Tipo, Número e Ano de Processo...")
    processo_data = df['Processo'].apply(lambda x: pd.Series(extract_processo_info(x)))
    df['Tipo'] = processo_data[0]
    df['Numero'] = processo_data[1]
    df['Ano'] = processo_data[2]

    # 3. Fragmentar Tramitação
    logger.info("Extraindo dados de Tramitação...")
    tramitacao_data = df['Tramitação'].apply(lambda x: pd.Series(extract_tramitacao(x)))
    df['Data_Tramitação'] = tramitacao_data[0]
    df['Local_Tramitação'] = tramitacao_data[1]
    df['Origem_Tramitação'] = tramitacao_data[2]

    # 4. Fragmentar Tramitacao Interna
    logger.info("Extraindo dados de Tramitação Interna...")
    tramitacao_interna_data = df['Tramitacao Interna'].apply(lambda x: pd.Series(extract_tramitacao_interna(x)))
    df['Data_TI'] = tramitacao_interna_data[0]
    df['Local_TI'] = tramitacao_interna_data[1]
    df['Estado'] = tramitacao_interna_data[2]

    # 5. Preencher Relator nulo
    logger.info("Preenchendo Relator nulo...")
    df['Relator'] = df['Relator'].fillna('Sem Relator Designado')

    # 6. Remover colunas originais
    logger.info("Removendo colunas compostas originais...")
    df = df.drop(columns=['Tramitação', 'Tramitacao Interna'])

    # 7. Reordenar colunas
    logger.info("Reordenando colunas...")
    colunas_ordenadas = [
        'Processo', 'Tipo', 'Numero', 'Ano', 'Ementa', 'Autor', 'Relator',
        'Data_Tramitação', 'Local_Tramitação', 'Origem_Tramitação',
        'Data_TI', 'Local_TI', 'Estado',
        'Dias na Comissão', 'Dias no Estado Atual'
    ]
    df = df[colunas_ordenadas]

    logger.info(f"Processamento concluído. {len(df)} registros processados.")
    return df


def save_csv(df, comissao):
    """Salva o DataFrame processado como CSV."""
    output_path = Path('data/processed') / f'{comissao}_tratado.csv'
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        df.to_csv(output_path, index=False, encoding='utf-8', sep=';')
        logger.info(f"CSV salvo em: {output_path}")
    except Exception as e:
        logger.error(f"Erro ao salvar CSV: {e}")
        raise


def save_json(df, comissao):
    """Salva os dados processados como JSON com estatísticas."""
    output_path = Path('data/processed') / f'{comissao}.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Calcular estatísticas
        por_relator = df['Relator'].value_counts().to_dict()
        por_estado = df['Estado'].value_counts().to_dict()

        # Preparar JSON
        json_data = {
            'comissao': comissao,
            'ultima_atualizacao': datetime.now().isoformat(),
            'total': len(df),
            'por_relator': por_relator,
            'por_estado': por_estado,
            'registros': df.to_dict('records')
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        logger.info(f"JSON salvo em: {output_path}")
    except Exception as e:
        logger.error(f"Erro ao salvar JSON: {e}")
        raise


def main():
    """Função principal."""
    if len(sys.argv) < 3:
        logger.error("Uso: python process_data.py <input_csv> <comissao>")
        logger.error("Exemplo: python process_data.py data/raw/FIN.csv FIN")
        sys.exit(1)

    input_file = sys.argv[1]
    comissao = sys.argv[2]

    try:
        # Processar CSV
        df = process_csv(input_file, comissao)

        # Salvar resultados
        save_csv(df, comissao)
        save_json(df, comissao)

        logger.info(f"Processamento de {comissao} finalizado com sucesso!")
    except Exception as e:
        logger.error(f"Erro durante o processamento: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
