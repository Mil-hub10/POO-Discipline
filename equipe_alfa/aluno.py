"""Módulo Aluno (Equipe ALFA): entidade + gerenciador."""

from base import (
    ErroValidacao,
    GerenciadorBase,
    validar_codigo,
    validar_cpf,
    validar_email,
    validar_texto,
)


class Aluno:
    """Modelo de dados do Aluno (sem lógica de arquivo)."""

    def __init__(self, matricula, nome, cpf, email, codigo_curso):
        self.matricula = matricula
        self.nome = nome
        self.cpf = cpf
        self.email = email
        self.codigo_curso = codigo_curso

    @property
    def matricula(self):
        return self._matricula

    @matricula.setter
    def matricula(self, valor):
        self._matricula = validar_codigo(valor, "matricula", "Matrícula")

    @property
    def nome(self):
        return self._nome

    @nome.setter
    def nome(self, valor):
        self._nome = validar_texto(valor, "nome", "Nome")

    @property
    def cpf(self):
        return self._cpf

    @cpf.setter
    def cpf(self, valor):
        self._cpf = validar_cpf(valor, "cpf")

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, valor):
        self._email = validar_email(valor, "email")

    @property
    def codigo_curso(self):
        return self._codigo_curso

    @codigo_curso.setter
    def codigo_curso(self, valor):
        self._codigo_curso = validar_codigo(valor, "codigo_curso", "Código do Curso")

    def __str__(self):
        return (
            f"Matrícula {self.matricula} | {self.nome} | CPF: {self.cpf} | "
            f"E-mail: {self.email} | Curso: {self.codigo_curso}"
        )


class GerenciadorAlunos(GerenciadorBase):
    CLASSE = Aluno
    NOME_ARQUIVO = "alunos.txt"
    ROTULO = "Aluno"
    ROTULO_PLURAL = "Alunos"
    CAMPOS = [
        ("matricula", "Matrícula"),
        ("nome", "Nome"),
        ("cpf", "CPF"),
        ("email", "E-mail"),
        ("codigo_curso", "Código do Curso"),
    ]

    def __init__(self, pasta_dados, gerenciador_cursos=None):
        # Sem gerenciador de cursos o módulo funciona isolado (Equipe ALFA
        # sozinha); com ele, o vínculo é conferido (RF13).
        self._cursos = gerenciador_cursos
        super().__init__(pasta_dados)

    def _validar_vinculos(self, aluno):
        if self._cursos is not None and self._cursos.buscar_por_codigo(aluno.codigo_curso) is None:
            raise ErroValidacao(
                f"O Curso '{aluno.codigo_curso}' não existe. Cadastre o curso primeiro.",
                "codigo_curso",
            )
