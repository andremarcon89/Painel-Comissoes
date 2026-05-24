import json
import sys
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ValidationReport:
    """Classe para gerar relatório de validação."""

    def __init__(self):
        self.checks = []
        self.passed = 0
        self.failed = 0

    def add_check(self, name, passed, details=''):
        """Adiciona um resultado de validação."""
        status = '✓ PASS' if passed else '✗ FAIL'
        self.checks.append({
            'name': name,
            'passed': passed,
            'details': details,
            'status': status
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1

    def print_report(self):
        """Imprime o relatório formatado."""
        print("\n" + "=" * 70)
        print("RELATÓRIO DE VALIDAÇÃO DO PIPELINE")
        print("=" * 70)
        print()

        for check in self.checks:
            status_color = '\033[92m' if check['passed'] else '\033[91m'
            reset_color = '\033[0m'
            print(f"{status_color}{check['status']}{reset_color} {check['name']}")
            if check['details']:
                print(f"      {check['details']}")

        print()
        print("=" * 70)
        print(f"Resultados: {self.passed} PASS / {self.failed} FAIL")
        print("=" * 70)
        print()

        return self.failed == 0


def validate_csv_exists():
    """Valida se o arquivo de teste CSV existe."""
    csv_path = Path('data/raw/FIN.csv')

    if csv_path.exists():
        return True, f"Arquivo encontrado em {csv_path}"
    else:
        return False, f"Arquivo não encontrado: {csv_path}"


def validate_process_data():
    """Valida se o process_data.py pode ser importado e executado."""
    try:
        # Importar módulo de processamento
        sys.path.insert(0, str(Path('scripts')))
        import process_data

        # Verificar se as funções principais existem
        required_functions = [
            'detect_separator',
            'extract_processo_info',
            'extract_tramitacao',
            'extract_tramitacao_interna',
            'process_csv',
            'save_csv',
            'save_json'
        ]

        missing = [f for f in required_functions if not hasattr(process_data, f)]

        if missing:
            return False, f"Funções faltantes: {', '.join(missing)}"

        return True, "Módulo importado com sucesso"
    except Exception as e:
        return False, f"Erro ao importar: {e}"


def process_test_data():
    """Processa o arquivo de teste FIN.csv."""
    try:
        sys.path.insert(0, str(Path('scripts')))
        import process_data

        logger.info("Processando arquivo de teste: data/raw/FIN.csv")

        # Processar CSV
        df = process_data.process_csv('data/raw/FIN.csv', 'FIN')

        # Salvar saídas
        process_data.save_csv(df, 'FIN')
        process_data.save_json(df, 'FIN')

        logger.info("Arquivo de teste processado com sucesso")
        return True, "Processamento concluído"

    except Exception as e:
        logger.error(f"Erro ao processar arquivo de teste: {e}")
        return False, str(e)


def validate_json_structure():
    """Valida a estrutura do JSON gerado."""
    json_path = Path('data/processed/FIN.json')
    checks = []

    if not json_path.exists():
        return False, "Arquivo FIN.json não encontrado", checks

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        return False, f"Erro ao ler JSON: {e}", checks

    # Verificação 1: Comissão
    passed = data.get('comissao') == 'FIN'
    checks.append(('Chave "comissao" = "FIN"', passed))

    # Verificação 2: Total
    total = data.get('total', 0)
    passed = total > 0
    checks.append(('Campo "total" > 0', passed, f"Total: {total}"))

    # Verificação 3: Última atualização
    passed = 'ultima_atualizacao' in data and isinstance(data['ultima_atualizacao'], str)
    checks.append(('Campo "ultima_atualizacao" existe', passed))

    # Verificação 4: por_relator
    por_relator = data.get('por_relator', {})
    passed = len(por_relator) > 0
    checks.append(('Campo "por_relator" não vazio', passed, f"Entradas: {len(por_relator)}"))

    # Verificação 5: por_estado
    por_estado = data.get('por_estado', {})
    passed = len(por_estado) > 0
    checks.append(('Campo "por_estado" não vazio', passed, f"Entradas: {len(por_estado)}"))

    # Verificação 6: registros
    registros = data.get('registros', [])
    passed = isinstance(registros, list) and len(registros) > 0
    checks.append(('Campo "registros" é lista não vazia', passed, f"Registros: {len(registros)}"))

    return True, "Estrutura válida", checks, registros


def validate_removed_columns(registros):
    """Valida que colunas compostas foram removidas."""
    checks = []

    if not registros:
        return False, "Lista de registros vazia", checks

    first_record = registros[0]

    # Verificação 1: Tramitação foi removida
    passed = 'Tramitação' not in first_record
    checks.append(('Coluna "Tramitação" foi removida', passed))

    # Verificação 2: Tramitacao Interna foi removida
    passed = 'Tramitacao Interna' not in first_record
    checks.append(('Coluna "Tramitacao Interna" foi removida', passed))

    return True, "Colunas validadas", checks


def validate_new_columns(registros):
    """Valida que as colunas foram criadas corretamente."""
    checks = []

    if not registros:
        return False, "Lista de registros vazia", checks

    first_record = registros[0]

    # Colunas esperadas
    required_columns = [
        'Data_Tramitação',
        'Local_Tramitação',
        'Origem_Tramitação',
        'Data_TI',
        'Local_TI',
        'Estado'
    ]

    all_exist = True
    missing_columns = []

    for col in required_columns:
        if col not in first_record:
            all_exist = False
            missing_columns.append(col)
        else:
            checks.append((f'Coluna "{col}" existe', True))

    if missing_columns:
        checks.append((f'Colunas faltantes: {", ".join(missing_columns)}', False))
        return False, "Algumas colunas estão faltando", checks

    return True, "Todas as colunas foram criadas", checks


def validate_data_quality(registros):
    """Valida a qualidade dos dados processados."""
    checks = []

    if not registros:
        return False, "Lista de registros vazia", checks

    # Verificação 1: Nenhum registro tem Tramitação
    has_tramitacao = any('Tramitação' in reg for reg in registros)
    checks.append(('Nenhum registro tem coluna "Tramitação"', not has_tramitacao))

    # Verificação 2: Nenhum registro tem Tramitacao Interna
    has_tramitacao_interna = any('Tramitacao Interna' in reg for reg in registros)
    checks.append(('Nenhum registro tem coluna "Tramitacao Interna"', not has_tramitacao_interna))

    # Verificação 3: Campos Processo, Tipo, Numero, Ano estão presentes
    sample_record = registros[0]
    processo_fields = ['Processo', 'Tipo', 'Numero', 'Ano']
    all_present = all(field in sample_record for field in processo_fields)
    checks.append((f'Campos de Processo ({", ".join(processo_fields)}) existem', all_present))

    # Verificação 4: Relator foi preenchido (sem valores nulos para "Sem Relator Designado")
    relators_check = all(
        reg.get('Relator') and reg.get('Relator') != ''
        for reg in registros
    )
    checks.append(('Todos os registros têm Relator preenchido', relators_check))

    return True, "Validação de qualidade concluída", checks


def main():
    """Função principal de validação."""
    report = ValidationReport()

    print("\n" + "=" * 70)
    print("INICIANDO VALIDAÇÃO DO PIPELINE")
    print("=" * 70 + "\n")

    # Etapa 1: Validar CSV de teste
    logger.info("Etapa 1: Validando arquivo CSV de teste...")
    passed, details = validate_csv_exists()
    report.add_check("CSV de teste existe (data/raw/FIN.csv)", passed, details)

    if not passed:
        report.print_report()
        return 1

    # Etapa 2: Validar importação do módulo
    logger.info("Etapa 2: Validando módulo process_data...")
    passed, details = validate_process_data()
    report.add_check("Módulo process_data.py importável", passed, details)

    if not passed:
        report.print_report()
        return 1

    # Etapa 3: Processar dados de teste
    logger.info("Etapa 3: Processando dados de teste...")
    passed, details = process_test_data()
    report.add_check("Processamento dos dados de teste", passed, details)

    if not passed:
        report.print_report()
        return 1

    # Etapa 4: Validar estrutura JSON
    logger.info("Etapa 4: Validando estrutura do JSON...")
    passed, details, checks, registros = validate_json_structure()

    if not passed:
        report.add_check("Estrutura JSON válida", False, details)
        report.print_report()
        return 1

    for check_name, check_passed, *check_details in checks:
        detail = check_details[0] if check_details else ''
        report.add_check(check_name, check_passed, detail)

    # Etapa 5: Validar remoção de colunas
    logger.info("Etapa 5: Validando remoção de colunas compostas...")
    passed, details, checks = validate_removed_columns(registros)

    for check_name, check_passed in checks:
        report.add_check(check_name, check_passed)

    # Etapa 6: Validar criação de novas colunas
    logger.info("Etapa 6: Validando criação de novas colunas...")
    passed, details, checks = validate_new_columns(registros)

    for check_name, check_passed in checks:
        report.add_check(check_name, check_passed)

    # Etapa 7: Validar qualidade dos dados
    logger.info("Etapa 7: Validando qualidade dos dados...")
    passed, details, checks = validate_data_quality(registros)

    for check_name, check_passed in checks:
        report.add_check(check_name, check_passed)

    # Imprimir relatório final
    all_passed = report.print_report()

    return 0 if all_passed else 1


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Erro fatal na validação: {e}")
        sys.exit(1)
