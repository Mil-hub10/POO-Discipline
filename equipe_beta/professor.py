"""Módulo Professor (Equipe BETA): entidade + gerenciador."""

from base import GerenciadorBase, validar_codigo, validar_cpf, validar_texto


class Professor:
    """Modelo de dados do Professor (sem lógica de arquivo)."""

    def __init__(self, codigo_professor, nome, cpf, especialidade):
        self.codigo_professor = codigo_professor
        self.nome = nome
        self.cpf = cpf
        self.especialidade = especialidade

    @property
    def codigo_professor(self):
        return self._codigo_professor

    @codigo_professor.setter
    def codigo_professor(self, valor):
        self._codigo_professor = validar_codigo(
            valor, "codigo_professor", "Código do Professor"
        )

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
    def especialidade(self):
        return self._especialidade

    @especialidade.setter
    def especialidade(self, valor):
        self._especialidade = validar_texto(valor, "especialidade", "Especialidade")

    def __str__(self):
        return (
            f"Professor {self.codigo_professor} | {self.nome} | CPF: {self.cpf} | "
            f"Especialidade: {self.especialidade}"
        )


class GerenciadorProfessores(GerenciadorBase):
    CLASSE = Professor
    NOME_ARQUIVO = "professores.txt"
    ROTULO = "Professor"
    ROTULO_PLURAL = "Professores"
    CAMPOS = [
        ("codigo_professor", "Código do Professor"),
        ("nome", "Nome"),
        ("cpf", "CPF"),
        ("especialidade", "Especialidade"),
    ]
