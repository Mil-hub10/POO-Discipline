"""
integracao.py - Junta os módulos das equipes ALFA e BETA.

SistemaAcademico cria os quatro gerenciadores, liga um ao outro (vínculos
por codigo_curso e codigo_professor) e gera o relatório integrado.
"""

import os

from equipe_alfa.aluno import GerenciadorAlunos
from equipe_alfa.curso import GerenciadorCursos
from equipe_beta.disciplina import GerenciadorDisciplinas
from equipe_beta.professor import GerenciadorProfessores

PASTA_PADRAO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados")


class SistemaAcademico:
    def __init__(self, pasta_dados=None):
        pasta = pasta_dados or PASTA_PADRAO
        # RF11: cada gerenciador já carrega o seu .txt ao ser criado.
        self.cursos = GerenciadorCursos(pasta)
        self.professores = GerenciadorProfessores(pasta)
        self.alunos = GerenciadorAlunos(pasta, self.cursos)
        self.disciplinas = GerenciadorDisciplinas(pasta, self.professores, self.cursos)

        # Integridade: não permite excluir um curso/professor que ainda é
        # referenciado por alunos ou disciplinas.
        self.cursos.registrar_dependente(self.alunos, "codigo_curso", "aluno(s)")
        self.cursos.registrar_dependente(self.disciplinas, "codigo_curso", "disciplina(s)")
        self.professores.registrar_dependente(
            self.disciplinas, "codigo_professor", "disciplina(s)"
        )

    @property
    def gerenciadores(self):
        """Na ordem em que fazem sentido cadastrar (curso/professor antes)."""
        return {
            "cursos": self.cursos,
            "professores": self.professores,
            "disciplinas": self.disciplinas,
            "alunos": self.alunos,
        }

    def relatorio_integrado(self):  # RF15
        """Uma frase por aluno x disciplina do curso dele.

        O aluno guarda só o codigo_curso, e a disciplina guarda codigo_curso e
        codigo_professor. Então: Aluno -> Curso -> Disciplinas do curso ->
        Professor de cada disciplina.
        """
        alunos = self.alunos.listar()
        cursos = {c.codigo_curso: c for c in self.cursos.listar()}
        professores = {p.codigo_professor: p for p in self.professores.listar()}
        disciplinas = self.disciplinas.listar()

        linhas = []
        for aluno in alunos:
            curso = cursos.get(aluno.codigo_curso)
            nome_curso = curso.nome if curso else f"(curso {aluno.codigo_curso} não encontrado)"
            do_curso = [d for d in disciplinas if d.codigo_curso == aluno.codigo_curso]
            if not do_curso:
                linhas.append(
                    f"O Aluno {aluno.nome} está matriculado no curso {nome_curso}, "
                    "que ainda não tem disciplinas cadastradas."
                )
            for disc in do_curso:
                prof = professores.get(disc.codigo_professor)
                nome_prof = prof.nome if prof else f"(professor {disc.codigo_professor} não encontrado)"
                linhas.append(
                    f"O Aluno {aluno.nome} está matriculado no curso {nome_curso}, "
                    f"assistindo a disciplina {disc.nome} com o professor {nome_prof}."
                )
        return linhas
