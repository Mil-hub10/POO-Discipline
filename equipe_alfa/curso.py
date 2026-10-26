"""Módulo Curso (Equipe ALFA): entidade + gerenciador."""

from base import (
    GerenciadorBase,
    validar_codigo,
    validar_modalidade,
    validar_texto,
)


class Curso:
    """Modelo de dados do Curso (sem lógica de arquivo)."""

    def __init__(self, codigo_curso, nome, modalidade):
        self.codigo_curso = codigo_curso
        self.nome = nome
        self.modalidade = modalidade

    @property
    def codigo_curso(self):
        return self._codigo_curso

    @codigo_curso.setter
    def codigo_curso(self, valor):
        self._codigo_curso = validar_codigo(valor, "codigo_curso", "Código do Curso")

    @property
    def nome(self):
        return self._nome

    @nome.setter
    def nome(self, valor):
        self._nome = validar_texto(valor, "nome", "Nome do Curso")

    @property
    def modalidade(self):
        return self._modalidade

    @modalidade.setter
    def modalidade(self, valor):
        self._modalidade = validar_modalidade(valor, "modalidade")

    def __str__(self):
        return (
            f"Curso {self.codigo_curso} | {self.nome} | "
            f"Modalidade: {self.modalidade}"
        )


class GerenciadorCursos(GerenciadorBase):
    CLASSE = Curso
    NOME_ARQUIVO = "cursos.txt"
    ROTULO = "Curso"
    ROTULO_PLURAL = "Cursos"
    CAMPOS = [
        ("codigo_curso", "Código do Curso"),
        ("nome", "Nome"),
        ("modalidade", "Modalidade (Presencial/EAD)"),
    ]
