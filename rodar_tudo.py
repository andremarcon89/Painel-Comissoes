"""
Script principal: executa os dois passos em sequência.

Uso:
  python3 rodar_tudo.py             # Roda download + tratamento
  python3 rodar_tudo.py --so-tratar # Só roda o tratamento (CSV brutos já existem)
  python3 rodar_tudo.py --inspecionar # Só inspeciona a página
"""

import sys
import subprocess


def rodar(script):
    print(f"\n{'='*60}")
    print(f"Executando: {script}")
    print(f"{'='*60}")
    resultado = subprocess.run(["python3", script], check=False)
    return resultado.returncode == 0


def main():
    args = sys.argv[1:]

    if "--inspecionar" in args:
        rodar("inspecionar_pagina.py")
        return

    sucesso = True

    if "--so-tratar" not in args:
        print("PASSO 1: Download dos relatórios brutos")
        sucesso = rodar("download_relatorios.py")
        if not sucesso:
            print("\nPasso 1 encerrou com erros. Verifique antes de continuar.")
            resposta = input("Continuar com o tratamento mesmo assim? (s/N): ").strip().lower()
            if resposta != "s":
                return

    print("\nPASSO 2: Tratamento dos relatórios")
    rodar("tratar_relatorios.py")

    print("\n=== CONCLUÍDO ===")
    print("Arquivos gerados em relatorios_tratados/:")
    import os
    for arq in sorted(os.listdir("relatorios_tratados")):
        tamanho = os.path.getsize(os.path.join("relatorios_tratados", arq))
        print(f"  {arq}  ({tamanho:,} bytes)")


if __name__ == "__main__":
    main()
