"""
main.py - Ponto de entrada único do Sistema de Gestão Acadêmica (RF16).

    python main.py          -> menu no console (RF17)
    python main.py --gui    -> interface gráfica (Desafio)
    python main.py --dados PASTA   -> usa outra pasta para os .txt
"""

import argparse
import os
import sys
from functools import partial

from base import ErroSistema, ErroValidacao
from integracao import SistemaAcademico

CANCELAR = "cancelar"


# --------------------------------------------------------------------------
# Utilidades de entrada/saída
# --------------------------------------------------------------------------
class Cancelado(Exception):
    """O usuário digitou 'cancelar' durante uma operação."""


def limpar_tela():  # RF30
    """Limpa o console a cada transição de menu (só num terminal de verdade)."""
    if sys.stdout.isatty():
        os.system("cls" if os.name == "nt" else "clear")


def pausar():
    """Deixa o usuário ler o resultado antes de a tela ser limpa."""
    input("\nPressione Enter para continuar...")


def exibir_avisos(avisos):  # RF31
    for aviso in avisos:
        print(f"  [Aviso] {aviso}")


def pedir(rotulo, atual=None):
    """Lê um valor. Com `atual`, Enter mantém o valor (retorna None)."""
    sufixo = f" [{atual}]" if atual is not None else ""
    valor = input(f"  {rotulo}{sufixo}: ").strip()
    if valor.casefold() == CANCELAR:
        raise Cancelado()
    if atual is not None and valor == "":
        return None
    return valor


def mostrar(itens, ger, vazio="  Nenhum registro encontrado."):
    """Mostra os itens e, no rodapé, o total encontrado (RF28)."""
    if not itens:
        print(vazio)
    for item in itens:
        print(f"  {item}")
    print(f"\n  {ger.texto_total(len(itens))}")


def escolher_opcao(titulo, opcoes, avisos=()):
    """Limpa a tela, mostra um menu numerado e devolve o que foi digitado."""
    limpar_tela()
    exibir_avisos(avisos)
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
    itens = ger.listar()
    exibir_avisos(ger.pegar_avisos())  # arquivo recriado/corrompido (RF31)
    mostrar(itens, ger)


def pesquisar(ger):
    print(f"\n-- Pesquisar {ger.ROTULO} --")
    termo = pedir(f"{ger.rotulo_id} ou parte do nome")
    mostrar(ger.pesquisar(termo), ger)


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
    if input("  Tem certeza que deseja excluir? (s/n): ").strip().casefold() != "s":  # RF29
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


# --------------------------------------------------------------------------
# Consultas extras (precisam cruzar mais de uma entidade)
# --------------------------------------------------------------------------
def alunos_por_curso(sistema):  # RF26
    print("\n-- Alunos de um curso --")
    for curso in sistema.cursos.listar():
        print(f"  {curso}")
    codigo = pedir("Código do Curso")
    curso, alunos = sistema.alunos_do_curso(codigo)
    print(f"\n  Curso: {curso.nome}")
    mostrar(alunos, sistema.alunos)


def alunos_por_disciplina(sistema):  # RF27
    print("\n-- Alunos de uma disciplina --")
    for disciplina in sistema.disciplinas.listar():
        print(f"  {disciplina}")
    codigo = pedir("Código da Disciplina")
    disciplina, curso, alunos = sistema.alunos_da_disciplina(codigo)
    nome_curso = curso.nome if curso else f"(curso {disciplina.codigo_curso} não encontrado)"
    print(f"\n  Disciplina: {disciplina.nome} | Curso: {nome_curso}")
    mostrar(alunos, sistema.alunos)


# --------------------------------------------------------------------------
# Menus
# --------------------------------------------------------------------------
def menu_entidade(ger, extras=()):
    """extras: lista de (numero, texto, funcao_sem_argumentos)."""
    opcoes = [
        ("1", "Cadastrar"),
        ("2", "Listar"),
        ("3", "Pesquisar"),
        ("4", "Alterar"),
        ("5", "Excluir"),
    ]
    operacoes = {numero: partial(funcao, ger) for numero, funcao in OPERACOES.items()}
    for numero, texto, funcao in extras:
        opcoes.append((numero, texto))
        operacoes[numero] = funcao
    opcoes.append(("0", "Voltar"))

    while True:
        escolha = escolher_opcao(ger.ROTULO_PLURAL.upper(), opcoes, ger.pegar_avisos())
        if escolha == "0":
            return
        operacao = operacoes.get(escolha)
        if operacao is None:
            print("  Opção inválida.")
        else:
            try:
                operacao()
            except Cancelado:
                print("  Operação cancelada.")
            except ErroSistema as erro:
                print(f"  Erro: {erro}")
        pausar()


def mostrar_relatorio(sistema):  # RF15
    print("\n=== RELATÓRIO INTEGRADO ===")
    linhas = sistema.relatorio_integrado()
    exibir_avisos(sistema.coletar_avisos())
    if not linhas:
        print("  Nenhum aluno cadastrado ainda.")
    for linha in linhas:
        print(f"  {linha}")


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
        "1": (sistema.cursos, []),
        "2": (sistema.professores, []),
        "3": (
            sistema.disciplinas,
            [("6", "Alunos de uma disciplina", partial(alunos_por_disciplina, sistema))],
        ),
        "4": (
            sistema.alunos,
            [("6", "Filtrar alunos por curso", partial(alunos_por_curso, sistema))],
        ),
    }
    while True:
        escolha = escolher_opcao(
            "SISTEMA DE GESTÃO ACADÊMICA", opcoes, sistema.coletar_avisos()
        )
        if escolha == "0":  # RF18: encerramento controlado
            print("\nEncerrando o sistema. Os dados já estão salvos nos arquivos .txt. Até logo!")
            return
        if escolha == "5":
            try:
                mostrar_relatorio(sistema)
            except ErroSistema as erro:
                print(f"  Erro: {erro}")
        elif escolha in destinos:
            ger, extras = destinos[escolha]
            menu_entidade(ger, extras)
            continue
        else:
            print("  Opção inválida.")
        pausar()


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
