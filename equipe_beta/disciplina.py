"""Módulo Disciplina (Equipe BETA): entidade + gerenciador."""

from base import (
    ErroValidacao,
    GerenciadorBase,
    validar_carga_horaria,
    validar_codigo,
    validar_texto,
)


class Disciplina:
    """Modelo de dados da Disciplina (sem lógica de arquivo)."""

    def __init__(self, codigo_disciplina, nome, carga_horaria, codigo_professor, codigo_curso):
        self.codigo_disciplina = codigo_disciplina
        self.nome = nome
        self.carga_horaria = carga_horaria
        self.codigo_professor = codigo_professor
        self.codigo_curso = codigo_curso

    @property
    def codigo_disciplina(self):
        return self._codigo_disciplina

    @codigo_disciplina.setter
    def codigo_disciplina(self, valor):
        self._codigo_disciplina = validar_codigo(
            valor, "codigo_disciplina", "Código da Disciplina"
        )

    @property
    def nome(self):
        return self._nome

    @nome.setter
    def nome(self, valor):
        self._nome = validar_texto(valor, "nome", "Nome da Disciplina")

    @property
    def carga_horaria(self):
        return self._carga_horaria

    @carga_horaria.setter
    def carga_horaria(self, valor):
        self._carga_horaria = validar_carga_horaria(valor, "carga_horaria")

    @property
    def codigo_professor(self):
        return self._codigo_professor

    @codigo_professor.setter
    def codigo_professor(self, valor):
        self._codigo_professor = validar_codigo(
            valor, "codigo_professor", "Código do Professor"
        )

    @property
    def codigo_curso(self):
        return self._codigo_curso

    @codigo_curso.setter
    def codigo_curso(self, valor):
        self._codigo_curso = validar_codigo(valor, "codigo_curso", "Código do Curso")

    def __str__(self):
        return (
            f"Disciplina {self.codigo_disciplina} | {self.nome} | "
            f"{self.carga_horaria}h | Professor: {self.codigo_professor} | "
            f"Curso: {self.codigo_curso}"
        )


class GerenciadorDisciplinas(GerenciadorBase):
    CLASSE = Disciplina
    NOME_ARQUIVO = "disciplinas.txt"
    ROTULO = "Disciplina"
    ROTULO_PLURAL = "Disciplinas"
    CAMPOS = [
        ("codigo_disciplina", "Código da Disciplina"),
        ("nome", "Nome"),
        ("carga_horaria", "Carga Horária (horas)"),
        ("codigo_professor", "Código do Professor"),
        ("codigo_curso", "Código do Curso"),
    ]

    def __init__(self, pasta_dados, gerenciador_professores=None, gerenciador_cursos=None):
        # Sem os outros gerenciadores o módulo funciona isolado (Equipe BETA
        # sozinha); com eles, os dois vínculos são conferidos (RF14).
        self._professores = gerenciador_professores
        self._cursos = gerenciador_cursos
        super().__init__(pasta_dados)

    def _validar_vinculos(self, disciplina):
        if (
            self._professores is not None
            and self._professores.buscar_por_codigo(disciplina.codigo_professor) is None
        ):
            raise ErroValidacao(
                f"O Professor '{disciplina.codigo_professor}' não existe. "
                "Cadastre o professor primeiro.",
                "codigo_professor",
            )
        if (
            self._cursos is not None
            and self._cursos.buscar_por_codigo(disciplina.codigo_curso) is None
        ):
            raise ErroValidacao(
                f"O Curso '{disciplina.codigo_curso}' não existe. Cadastre o curso primeiro.",
                "codigo_curso",
            )
