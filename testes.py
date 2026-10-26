"""
testes.py - Testes automáticos do sistema.

Rode com:  python testes.py
Usam uma pasta temporária; não mexem nos arquivos da pasta dados/.
"""

import os
import shutil
import tempfile
import unittest

from base import ErroSistema, ErroValidacao
from integracao import SistemaAcademico


def ler(pasta, arquivo):
    with open(os.path.join(pasta, arquivo), encoding="utf-8") as f:
        return f.read().splitlines()


class BaseTeste(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp()
        self.s = SistemaAcademico(self.pasta)

    def tearDown(self):
        shutil.rmtree(self.pasta, ignore_errors=True)

    def popular(self):
        self.s.cursos.cadastrar(codigo_curso="10", nome="Análise e Desenvolvimento de Sistemas", modalidade="Presencial")
        self.s.professores.cadastrar(codigo_professor="P1", nome="Carlos Souza", cpf="111.222.333-44", especialidade="Python")
        self.s.disciplinas.cadastrar(codigo_disciplina="D1", nome="Programação Orientada a Objetos", carga_horaria="80", codigo_professor="P1", codigo_curso="10")
        self.s.alunos.cadastrar(matricula="202301", nome="João Silva", cpf="123.456.789-00", email="joao@exemplo.com", codigo_curso="10")


class TestPersistencia(BaseTeste):
    def test_cadastro_grava_linha_com_ponto_e_virgula(self):
        self.popular()
        self.assertEqual(ler(self.pasta, "alunos.txt"), ["202301;João Silva;123.456.789-00;joao@exemplo.com;10"])
        self.assertEqual(ler(self.pasta, "cursos.txt"), ["10;Análise e Desenvolvimento de Sistemas;Presencial"])
        self.assertEqual(ler(self.pasta, "disciplinas.txt"), ["D1;Programação Orientada a Objetos;80;P1;10"])
        self.assertEqual(ler(self.pasta, "professores.txt"), ["P1;Carlos Souza;111.222.333-44;Python"])

    def test_carregamento_inicial(self):
        self.popular()
        novo = SistemaAcademico(self.pasta)  # simula reabrir o programa
        self.assertEqual(len(novo.alunos.itens), 1)
        self.assertEqual(novo.alunos.itens[0].nome, "João Silva")
        self.assertEqual(novo.disciplinas.itens[0].carga_horaria, 80)

    def test_listar_le_o_arquivo(self):
        self.popular()
        with open(os.path.join(self.pasta, "cursos.txt"), "a", encoding="utf-8") as f:
            f.write("20;Medicina;Presencial\n")  # edição manual do arquivo
        self.assertEqual([c.codigo_curso for c in self.s.cursos.listar()], ["10", "20"])

    def test_linhas_invalidas_sao_ignoradas(self):
        with open(os.path.join(self.pasta, "cursos.txt"), "w", encoding="utf-8") as f:
            f.write("10;ADS;EAD\n\nquebrada\n20;Direito;Hibrido\n10;Duplicado;EAD\n")
        cursos = self.s.cursos.listar()
        self.assertEqual([c.codigo_curso for c in cursos], ["10"])
        self.assertEqual(self.s.cursos.linhas_ignoradas, 3)

    def test_arquivos_criados_vazios_na_primeira_execucao(self):
        for nome in ("alunos.txt", "cursos.txt", "professores.txt", "disciplinas.txt"):
            self.assertTrue(os.path.exists(os.path.join(self.pasta, nome)))


class TestCrud(BaseTeste):
    def test_pesquisar_por_codigo_e_por_nome_sem_acento(self):
        self.popular()
        self.assertEqual(len(self.s.alunos.pesquisar("202301")), 1)
        self.assertEqual(len(self.s.alunos.pesquisar("joao")), 1)
        self.assertEqual(len(self.s.alunos.pesquisar("JOÃO sil")), 1)
        self.assertEqual(len(self.s.disciplinas.pesquisar("orientada")), 1)
        self.assertEqual(self.s.alunos.pesquisar("inexistente"), [])
        self.assertEqual(self.s.alunos.pesquisar("   "), [])

    def test_alterar_atualiza_arquivo(self):
        self.popular()
        self.s.alunos.alterar("202301", nome="João Pedro Silva", email="jp@exemplo.com")
        self.assertEqual(ler(self.pasta, "alunos.txt"), ["202301;João Pedro Silva;123.456.789-00;jp@exemplo.com;10"])

    def test_alterar_invalido_nao_muda_nada(self):
        self.popular()
        with self.assertRaises(ErroValidacao):
            self.s.alunos.alterar("202301", nome="Novo Nome", email="emailinvalido")
        aluno = self.s.alunos.buscar_por_codigo("202301")
        self.assertEqual(aluno.nome, "João Silva")  # o nome válido também foi revertido
        self.assertEqual(ler(self.pasta, "alunos.txt")[0].split(";")[1], "João Silva")

    def test_nao_altera_identificador(self):
        self.popular()
        with self.assertRaises(ErroValidacao):
            self.s.alunos.alterar("202301", matricula="999")

    def test_alterar_e_excluir_inexistente(self):
        with self.assertRaises(ErroSistema):
            self.s.alunos.alterar("nada", nome="X")
        with self.assertRaises(ErroSistema):
            self.s.alunos.excluir("nada")

    def test_excluir_remove_do_arquivo(self):
        self.popular()
        self.s.alunos.excluir("202301")
        self.assertEqual(ler(self.pasta, "alunos.txt"), [])
        self.assertEqual(self.s.alunos.itens, [])

    def test_codigo_duplicado(self):
        self.popular()
        with self.assertRaises(ErroValidacao) as ctx:
            self.s.cursos.cadastrar(codigo_curso="10", nome="Outro", modalidade="EAD")
        self.assertEqual(ctx.exception.campo, "codigo_curso")
        self.assertEqual(len(ler(self.pasta, "cursos.txt")), 1)


class TestValidacoes(BaseTeste):
    def _cadastrar_aluno(self, **ruins):
        base = dict(matricula="1", nome="Ana", cpf="12345678900", email="ana@x.com", codigo_curso="10")
        base.update(ruins)
        self.s.cursos.cadastrar(codigo_curso="10", nome="ADS", modalidade="EAD")
        return self.s.alunos.cadastrar(**base)

    def test_cpf_sem_pontuacao_e_normalizado(self):
        self.assertEqual(self._cadastrar_aluno().cpf, "123.456.789-00")

    def test_rejeita_dados_invalidos(self):
        for ruim in (
            dict(cpf="123"), dict(cpf="abc.def.ghi-jk"), dict(email="sem-arroba"),
            dict(nome="   "), dict(nome="Ana;Maria"), dict(matricula="com espaço"),
        ):
            with self.subTest(ruim=ruim):
                with self.assertRaises(ErroValidacao):
                    self._cadastrar_aluno(**ruim)

    def test_modalidade_e_carga_horaria(self):
        self.assertEqual(self.s.cursos.cadastrar(codigo_curso="1", nome="A", modalidade="ead").modalidade, "EAD")
        with self.assertRaises(ErroValidacao):
            self.s.cursos.cadastrar(codigo_curso="2", nome="B", modalidade="Híbrido")
        self.popular_para_disciplina()
        for horas in ("0", "-5", "abc", "8.5", ""):
            with self.subTest(horas=horas):
                with self.assertRaises(ErroValidacao):
                    self.s.disciplinas.cadastrar(codigo_disciplina="X", nome="N", carga_horaria=horas, codigo_professor="P1", codigo_curso="1")

    def popular_para_disciplina(self):
        self.s.professores.cadastrar(codigo_professor="P1", nome="Prof", cpf="11122233344", especialidade="TI")


class TestIntegracao(BaseTeste):
    def test_vinculos_inexistentes_sao_recusados(self):
        with self.assertRaises(ErroValidacao) as ctx:
            self.s.alunos.cadastrar(matricula="1", nome="Ana", cpf="12345678900", email="a@x.com", codigo_curso="99")
        self.assertEqual(ctx.exception.campo, "codigo_curso")
        self.popular()
        with self.assertRaises(ErroValidacao) as ctx:
            self.s.disciplinas.cadastrar(codigo_disciplina="D2", nome="X", carga_horaria="40", codigo_professor="ZZ", codigo_curso="10")
        self.assertEqual(ctx.exception.campo, "codigo_professor")
        with self.assertRaises(ErroValidacao):
            self.s.alunos.alterar("202301", codigo_curso="99")
        self.assertEqual(self.s.alunos.buscar_por_codigo("202301").codigo_curso, "10")

    def test_nao_exclui_curso_ou_professor_em_uso(self):
        self.popular()
        with self.assertRaises(ErroSistema):
            self.s.cursos.excluir("10")
        with self.assertRaises(ErroSistema):
            self.s.professores.excluir("P1")
        self.s.alunos.excluir("202301")
        self.s.disciplinas.excluir("D1")
        self.s.cursos.excluir("10")
        self.s.professores.excluir("P1")

    def test_relatorio_frase(self):
        self.popular()
        self.assertEqual(
            self.s.relatorio_integrado(),
            ["O Aluno João Silva está matriculado no curso Análise e Desenvolvimento de Sistemas, "
             "assistindo a disciplina Programação Orientada a Objetos com o professor Carlos Souza."],
        )

    def test_relatorio_varias_disciplinas_e_curso_sem_disciplina(self):
        self.popular()
        self.s.professores.cadastrar(codigo_professor="P2", nome="Marina Lopes", cpf="55566677788", especialidade="Banco de Dados")
        self.s.disciplinas.cadastrar(codigo_disciplina="D2", nome="Banco de Dados", carga_horaria="60", codigo_professor="P2", codigo_curso="10")
        self.s.cursos.cadastrar(codigo_curso="20", nome="Redes", modalidade="EAD")
        self.s.alunos.cadastrar(matricula="2", nome="Bia", cpf="99988877766", email="bia@x.com", codigo_curso="20")
        linhas = self.s.relatorio_integrado()
        self.assertEqual(len(linhas), 3)
        self.assertIn("professor Marina Lopes", linhas[1])
        self.assertIn("que ainda não tem disciplinas", linhas[2])

    def test_modulos_funcionam_isolados(self):
        """Cada equipe consegue usar o seu módulo sem o da outra."""
        from equipe_alfa.aluno import GerenciadorAlunos
        pasta = tempfile.mkdtemp()
        try:
            alunos = GerenciadorAlunos(pasta)
            alunos.cadastrar(matricula="1", nome="Ana", cpf="12345678900", email="a@x.com", codigo_curso="10")
            self.assertEqual(len(alunos.listar()), 1)
        finally:
            shutil.rmtree(pasta, ignore_errors=True)


class TestEncapsulamento(BaseTeste):
    def test_atributos_protegidos_e_str(self):
        self.popular()
        aluno = self.s.alunos.itens[0]
        self.assertEqual(aluno._nome, "João Silva")
        with self.assertRaises(ErroValidacao):
            aluno.nome = ""
        self.assertIn("João Silva", str(aluno))


if __name__ == "__main__":
    unittest.main(verbosity=2)
