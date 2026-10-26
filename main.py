"""
main.py - Ponto de entrada único do Sistema de Gestão Acadêmica (RF16).

    python main.py          -> menu no console (RF17)
    python main.py --gui    -> interface gráfica (Desafio)
    python main.py --dados PASTA   -> usa outra pasta para os .txt
"""

import argparse
import sys

from base import ErroSistema, ErroValidacao
from integracao import SistemaAcademico

CANCELAR = "cancelar"


# --------------------------------------------------------------------------
# Utilidades de entrada/saída
# --------------------------------------------------------------------------
class Cancelado(Exception):
    """O usuário digitou 'cancelar' durante uma operação."""


def pedir(rotulo, atual=None):
    """Lê um valor. Com `atual`, Enter mantém o valor (retorna None)."""
    sufixo = f" [{atual}]" if atual is not None else ""
    valor = input(f"  {rotulo}{sufixo}: ").strip()
    if valor.casefold() == CANCELAR:
        raise Cancelado()
    if atual is not None and valor == "":
        return None
    return valor


def mostrar(itens, vazio="  Nenhum registro encontrado."):
    if not itens:
        print(vazio)
        return
    for item in itens:
        print(f"  {item}")
    print(f"  ({len(itens)} registro(s))")


def escolher_opcao(titulo, opcoes):
    """Mostra um menu numerado e devolve o número digitado (ou None)."""
    print(f"\n=== {titulo} ===")
    for numero, texto in opcoes:
        print(f"  {numero} - {texto}")
    return input("Escolha uma opção: ").strip()


# --------------------------------------------------------------------------
# Operações de CRUD (genéricas: servem para as quatro entidades)
# --------------------------------------------------------------------------
def cadastrar(ger):
    print(f"\n-- Cadastrar {ger.ROTULO} (digite '{CANCELAR}' para desistir) --")
    dados = {}
    for atributo, rotulo in ger.CAMPOS:
        dados[atributo] = pedir(rotulo)
    while True:
        try:
            item = ger.cadastrar(**dados)
            print(f"  {ger.ROTULO} cadastrado(a) com sucesso:\n  {item}")
            return
        except ErroValidacao as erro:
            print(f"  Erro: {erro}")
            if erro.campo not in dados:
                return
            rotulo = dict(ger.CAMPOS)[erro.campo]
            dados[erro.campo] = pedir(f"{rotulo} (corrigir)")


def listar(ger):
    print(f"\n-- {ger.ROTULO_PLURAL} cadastrados(as) --")
    mostrar(ger.listar())
    if ger.linhas_ignoradas:
        print(f"  Aviso: {ger.linhas_ignoradas} linha(s) inválida(s) em "
              f"{ger.NOME_ARQUIVO} foram ignoradas.")


def pesquisar(ger):
    print(f"\n-- Pesquisar {ger.ROTULO} --")
    termo = pedir(f"{ger.rotulo_id} ou parte do nome")
    mostrar(ger.pesquisar(termo))


def alterar(ger):
    print(f"\n-- Alterar {ger.ROTULO} --")
    codigo = pedir(f"{ger.rotulo_id} do registro")
    item = ger.buscar_por_codigo(codigo)
    if item is None:
        print(f"  {ger.ROTULO} não encontrado(a).")
        return
    print(f"  Atual: {item}")
    print("  Pressione Enter para manter o valor atual.")
    novos = {}
    for atributo, rotulo in ger.CAMPOS[1:]:  # o identificador não muda
        valor = pedir(rotulo, getattr(item, atributo))
        if valor is not None:
            novos[atributo] = valor
    if not novos:
        print("  Nada foi alterado.")
        return
    while True:
        try:
            item = ger.alterar(codigo, **novos)
            print(f"  Alterado com sucesso:\n  {item}")
            return
        except ErroValidacao as erro:
            print(f"  Erro: {erro}")
            if erro.campo not in novos:
                return
            rotulo = dict(ger.CAMPOS)[erro.campo]
            novos[erro.campo] = pedir(f"{rotulo} (corrigir)")


def excluir(ger):
    print(f"\n-- Excluir {ger.ROTULO} --")
    codigo = pedir(f"{ger.rotulo_id} do registro")
    item = ger.buscar_por_codigo(codigo)
    if item is None:
        print(f"  {ger.ROTULO} não encontrado(a).")
        return
    print(f"  {item}")
    if input("  Confirma a exclusão? (s/n): ").strip().casefold() != "s":
        print("  Exclusão cancelada.")
        return
    ger.excluir(codigo)
    print("  Excluído(a) com sucesso.")


OPERACOES = {
    "1": cadastrar,
    "2": listar,
    "3": pesquisar,
    "4": alterar,
    "5": excluir,
}


def menu_entidade(ger):
    opcoes = [
        ("1", "Cadastrar"),
        ("2", "Listar"),
        ("3", "Pesquisar"),
        ("4", "Alterar"),
        ("5", "Excluir"),
        ("0", "Voltar"),
    ]
    while True:
        escolha = escolher_opcao(f"{ger.ROTULO_PLURAL.upper()}", opcoes)
        if escolha == "0":
            return
        operacao = OPERACOES.get(escolha)
        if operacao is None:
            print("  Opção inválida.")
            continue
        try:
            operacao(ger)
        except Cancelado:
            print("  Operação cancelada.")
        except ErroSistema as erro:
            print(f"  Erro: {erro}")


# --------------------------------------------------------------------------
# Relatório integrado (RF15)
# --------------------------------------------------------------------------
def mostrar_relatorio(sistema):
    print("\n=== RELATÓRIO INTEGRADO ===")
    linhas = sistema.relatorio_integrado()
    if not linhas:
        print("  Nenhum aluno cadastrado ainda.")
    for linha in linhas:
        print(f"  {linha}")


# --------------------------------------------------------------------------
# Menu principal
# --------------------------------------------------------------------------
def menu_principal(sistema):
    opcoes = [
        ("1", "Cursos"),
        ("2", "Professores"),
        ("3", "Disciplinas"),
        ("4", "Alunos"),
        ("5", "Relatório integrado"),
        ("0", "Sair"),
    ]
    destinos = {
        "1": sistema.cursos,
        "2": sistema.professores,
        "3": sistema.disciplinas,
        "4": sistema.alunos,
    }
    while True:
        escolha = escolher_opcao("SISTEMA DE GESTÃO ACADÊMICA", opcoes)
        if escolha == "0":  # RF18: encerramento controlado
            print("\nEncerrando o sistema. Os dados já estão salvos nos arquivos .txt. Até logo!")
            return
        if escolha == "5":
            mostrar_relatorio(sistema)
        elif escolha in destinos:
            menu_entidade(destinos[escolha])
        else:
            print("  Opção inválida.")


def main():
    parser = argparse.ArgumentParser(description="Sistema de Gestão Acadêmica")
    parser.add_argument("--gui", action="store_true", help="abre a interface gráfica")
    parser.add_argument("--dados", help="pasta onde ficam os arquivos .txt")
    args = parser.parse_args()

    sistema = SistemaAcademico(args.dados)

    if args.gui:
        try:
            from interface_grafica import iniciar
        except ImportError:
            print("Não foi possível abrir a interface gráfica: o tkinter não está "
                  "instalado neste Python. Use o menu de console (python main.py).")
            return 1
        iniciar(sistema)
        return 0

    try:
        menu_principal(sistema)
    except (KeyboardInterrupt, EOFError):
        print("\nEncerrado pelo usuário. Os dados já gravados continuam nos arquivos .txt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
