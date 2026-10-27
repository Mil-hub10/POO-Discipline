"""
base.py - Núcleo compartilhado pelas duas equipes (ALFA e BETA).

Contém:
  * as exceções do sistema;
  * os validadores usados pelos setters das entidades;
  * a classe GerenciadorBase, que implementa o CRUD e a persistência em .txt
    uma única vez. Cada gerenciador (alunos, cursos, ...) só informa qual é
    a sua classe de entidade, o seu arquivo e os seus campos.

Formato dos arquivos .txt: uma linha por registro, campos separados por ";".
"""

import copy
import os
import re
import unicodedata


# --------------------------------------------------------------------------
# Exceções
# --------------------------------------------------------------------------
class ErroSistema(Exception):
    """Erro geral do sistema (registro não encontrado, falha ao gravar...)."""


class ErroValidacao(ErroSistema):
    """Dado inválido. Guarda o nome do campo para a interface poder
    perguntar novamente só aquele campo."""

    def __init__(self, mensagem, campo=None):
        super().__init__(mensagem)
        self.campo = campo


# --------------------------------------------------------------------------
# Validadores (usados pelos setters das classes de entidade)
# --------------------------------------------------------------------------
def validar_texto(valor, campo, rotulo):
    """Texto obrigatório, sem ';' (separador do arquivo) nem quebra de linha."""
    valor = "" if valor is None else str(valor).strip()
    if not valor:
        raise ErroValidacao(f"{rotulo} é obrigatório.", campo)
    if ";" in valor or "\n" in valor or "\r" in valor:
        raise ErroValidacao(
            f"{rotulo} não pode conter ponto e vírgula (;) nem quebra de linha.",
            campo,
        )
    return valor


def validar_codigo(valor, campo, rotulo):
    """Identificador: letras, números, '-' ou '_' (sem espaços)."""
    valor = validar_texto(valor, campo, rotulo)
    if not re.fullmatch(r"[A-Za-z0-9_-]+", valor):
        raise ErroValidacao(
            f"{rotulo} deve ter apenas letras, números, '-' ou '_' (sem espaços).",
            campo,
        )
    return valor


def validar_cpf(valor, campo, rotulo="CPF"):
    """Aceita 11 dígitos com ou sem pontuação e grava como 000.000.000-00.

    Valida só o formato: o dígito verificador não é conferido, porque o
    próprio exemplo do enunciado (123.456.789-00) não é um CPF real.
    """
    valor = validar_texto(valor, campo, rotulo)
    if not re.fullmatch(r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}", valor):
        raise ErroValidacao(
            f"{rotulo} inválido. Use 11 dígitos (ex.: 123.456.789-00).", campo
        )
    d = re.sub(r"\D", "", valor)
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"


def validar_email(valor, campo, rotulo="E-mail"):
    valor = validar_texto(valor, campo, rotulo)
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", valor):
        raise ErroValidacao(f"{rotulo} inválido (ex.: nome@dominio.com).", campo)
    return valor


def validar_modalidade(valor, campo, rotulo="Modalidade"):
    valor = validar_texto(valor, campo, rotulo)
    opcoes = {"presencial": "Presencial", "ead": "EAD"}
    if valor.casefold() not in opcoes:
        raise ErroValidacao(f"{rotulo} deve ser Presencial ou EAD.", campo)
    return opcoes[valor.casefold()]


def validar_carga_horaria(valor, campo, rotulo="Carga horária"):
    texto = validar_texto(valor, campo, rotulo)
    try:
        horas = int(texto)
    except ValueError:
        raise ErroValidacao(f"{rotulo} deve ser um número inteiro de horas.", campo)
    if horas <= 0:
        raise ErroValidacao(f"{rotulo} deve ser maior que zero.", campo)
    return horas


def normalizar(texto):
    """Minúsculas e sem acentos, para a pesquisa por nome."""
    sem_acento = unicodedata.normalize("NFKD", str(texto))
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return sem_acento.casefold()


# --------------------------------------------------------------------------
# Gerenciador genérico (CRUD + persistência)
# --------------------------------------------------------------------------
class GerenciadorBase:
    """Lógica de manipulação de listas e arquivos .txt.

    As subclasses definem:
      CLASSE         - classe da entidade (só modelo de dados);
      NOME_ARQUIVO   - ex.: "alunos.txt";
      ROTULO         - nome da entidade no singular, ex.: "Aluno";
      CAMPOS         - lista de (atributo, rótulo) NA ORDEM das colunas do
                       arquivo. O primeiro campo é o identificador único.
    """

    CLASSE = None
    NOME_ARQUIVO = ""
    ROTULO = ""
    ROTULO_PLURAL = ""
    GENERO_FEMININO = False  # só para o contador: "encontrado" x "encontrada"
    CAMPOS = []

    def __init__(self, pasta_dados):
        self._caminho = os.path.join(pasta_dados, self.NOME_ARQUIVO)
        self._itens = []
        self._dependentes = []  # quem referencia os registros daqui
        self._avisos = []       # mensagens amigáveis sobre o arquivo (RF31)
        self._leitura_ok = True
        self.linhas_ignoradas = 0
        try:
            os.makedirs(pasta_dados, exist_ok=True)
        except OSError:
            pass  # carregar() informa o problema de forma amigável
        self.carregar()  # RF11: carregamento inicial

    # ---- propriedades auxiliares ----------------------------------------
    @property
    def caminho(self):
        return self._caminho

    @property
    def itens(self):
        """Cópia da lista em memória (sem reler o arquivo)."""
        return list(self._itens)

    @property
    def atributo_id(self):
        return self.CAMPOS[0][0]

    @property
    def rotulo_id(self):
        return self.CAMPOS[0][1]

    def _codigo(self, item):
        return getattr(item, self.atributo_id)

    def pegar_avisos(self):
        """Devolve (e esvazia) os avisos sobre o arquivo, para a interface
        mostrar ao usuário em vez de o programa fechar com erro (RF31)."""
        avisos, self._avisos = self._avisos, []
        return avisos

    def texto_total(self, quantidade):
        """Texto do rodapé das listagens (RF28): 'Total: 15 alunos encontrados'."""
        nome = self.ROTULO if quantidade == 1 else self.ROTULO_PLURAL
        encontrado = "encontrada" if self.GENERO_FEMININO else "encontrado"
        if quantidade != 1:
            encontrado += "s"
        return f"Total: {quantidade} {nome.lower()} {encontrado}"

    # ---- persistência ---------------------------------------------------
    def carregar(self):
        """Lê o .txt e converte cada linha em objeto (RF02 / RF11).

        Nunca derruba o programa (RF31):
          * arquivo apagado -> é recriado vazio e o usuário é avisado;
          * arquivo ilegível ou corrompido -> o usuário é avisado e o arquivo
            NÃO é sobrescrito (para não perder o que ainda der para recuperar);
          * linhas em branco são ignoradas; linhas com número errado de
            campos, dados inválidos ou código repetido são ignoradas e
            contadas em `linhas_ignoradas`.
        """
        self._itens = []
        self.linhas_ignoradas = 0
        self._leitura_ok = True
        if not os.path.exists(self._caminho):
            try:
                open(self._caminho, "w", encoding="utf-8").close()
            except OSError as erro:
                self._leitura_ok = False
                self._avisos.append(
                    f"O arquivo {self.NOME_ARQUIVO} não existe e não pôde ser "
                    f"criado ({erro.strerror or erro}). Os dados de "
                    f"{self.ROTULO_PLURAL.lower()} estão inacessíveis."
                )
                return
            self._avisos.append(
                f"O arquivo {self.NOME_ARQUIVO} não foi encontrado e foi "
                "recriado vazio."
            )
            return
        try:
            with open(self._caminho, "r", encoding="utf-8-sig") as arq:
                linhas = arq.read().splitlines()
        except (OSError, UnicodeDecodeError):
            self._leitura_ok = False
            self._avisos.append(
                f"O arquivo {self.NOME_ARQUIVO} está inacessível ou corrompido "
                "e não pôde ser lido. Ele não será alterado. Para recomeçar, "
                "apague o arquivo (ele será recriado vazio); para recuperar, "
                "abra-o e salve como UTF-8."
            )
            return
        codigos = set()
        for linha in linhas:
            linha = linha.strip()
            if not linha:
                continue
            try:
                item = self.CLASSE(*linha.split(";"))
            except (ErroValidacao, TypeError):
                self.linhas_ignoradas += 1
                continue
            if self._codigo(item) in codigos:
                self.linhas_ignoradas += 1
                continue
            codigos.add(self._codigo(item))
            self._itens.append(item)
        if self.linhas_ignoradas:
            self._avisos.append(
                f"{self.linhas_ignoradas} linha(s) inválida(s) em "
                f"{self.NOME_ARQUIVO} foram ignoradas."
            )

    def salvar(self):
        """Regrava o arquivo inteiro (RF12). Escreve num arquivo temporário e
        só então substitui o original, para não corromper os dados se algo
        falhar no meio da escrita."""
        temporario = self._caminho + ".tmp"
        with open(temporario, "w", encoding="utf-8", newline="\n") as arq:
            for item in self._itens:
                campos = [str(getattr(item, a)) for a, _ in self.CAMPOS]
                arq.write(";".join(campos) + "\n")
        os.replace(temporario, self._caminho)

    def _gravar_ou_desfazer(self, desfazer):
        if not self._leitura_ok:
            desfazer()
            raise ErroSistema(
                f"{self.NOME_ARQUIVO} está inacessível ou corrompido; nada foi "
                "gravado para não perder dados. Veja o aviso na listagem."
            )
        try:
            self.salvar()
        except OSError as erro:
            desfazer()
            raise ErroSistema(f"Não foi possível gravar {self.NOME_ARQUIVO}: {erro}")

    # ---- gancho para validar vínculos entre entidades -------------------
    def _validar_vinculos(self, item):
        """Sobrescrito por quem tem chave estrangeira (Aluno, Disciplina)."""

    def registrar_dependente(self, gerenciador, atributo, descricao):
        """Informa que `gerenciador` guarda, em `atributo`, o código dos
        registros daqui. Usado para impedir exclusões que deixariam
        vínculos órfãos."""
        self._dependentes.append((gerenciador, atributo, descricao))

    # ---- CRUD -----------------------------------------------------------
    def cadastrar(self, **dados):  # RF01
        try:
            item = self.CLASSE(**dados)
        except TypeError as erro:
            raise ErroSistema(f"Dados incompletos para cadastrar {self.ROTULO}: {erro}")
        if self.buscar_por_codigo(self._codigo(item)) is not None:
            raise ErroValidacao(
                f"Já existe {self.ROTULO} com {self.rotulo_id} "
                f"'{self._codigo(item)}'.",
                self.atributo_id,
            )
        self._validar_vinculos(item)
        self._itens.append(item)
        self._gravar_ou_desfazer(lambda: self._itens.remove(item))
        return item

    def listar(self):  # RF02
        """Relê o arquivo e devolve a lista de objetos."""
        self.carregar()
        return list(self._itens)

    def buscar_por_codigo(self, codigo):
        codigo = str(codigo).strip()
        for item in self._itens:
            if self._codigo(item) == codigo:
                return item
        return None

    def pesquisar(self, termo):  # RF03
        """Busca pelo código exato OU por parte do nome (sem diferenciar
        maiúsculas/minúsculas nem acentos)."""
        termo = normalizar(termo.strip())
        if not termo:
            return []
        return [
            item
            for item in self._itens
            if normalizar(self._codigo(item)) == termo
            or termo in normalizar(item.nome)
        ]

    def alterar(self, codigo, **novos):  # RF04
        """Atualiza atributos do registro e regrava o arquivo.

        O identificador não pode ser alterado (os outros arquivos referenciam
        esse código). Se algum valor novo for inválido, nada é alterado.
        """
        item = self.buscar_por_codigo(codigo)
        if item is None:
            raise ErroSistema(f"{self.ROTULO} com {self.rotulo_id} '{codigo}' não encontrado.")
        if not novos:
            raise ErroSistema("Nenhuma alteração informada.")
        validos = {a for a, _ in self.CAMPOS}
        if self.atributo_id in novos:
            raise ErroValidacao(
                f"{self.rotulo_id} não pode ser alterado. Exclua e cadastre de novo.",
                self.atributo_id,
            )
        desconhecidos = set(novos) - validos
        if desconhecidos:
            raise ErroSistema(f"Campo(s) inexistente(s): {', '.join(sorted(desconhecidos))}")

        antigo = copy.copy(item).__dict__.copy()
        try:
            for atributo, valor in novos.items():
                setattr(item, atributo, valor)  # o setter valida
            self._validar_vinculos(item)
        except ErroSistema:
            item.__dict__.update(antigo)
            raise
        self._gravar_ou_desfazer(lambda: item.__dict__.update(antigo))
        return item

    def excluir(self, codigo):  # RF05
        item = self.buscar_por_codigo(codigo)
        if item is None:
            raise ErroSistema(f"{self.ROTULO} com {self.rotulo_id} '{codigo}' não encontrado.")
        for gerenciador, atributo, descricao in self._dependentes:
            qtd = sum(1 for i in gerenciador.itens if getattr(i, atributo) == self._codigo(item))
            if qtd:
                raise ErroSistema(
                    f"Não é possível excluir {self.ROTULO} '{item.nome}': "
                    f"há {qtd} {descricao} vinculado(s). Remova ou altere esses "
                    "registros antes."
                )
        posicao = self._itens.index(item)
        self._itens.remove(item)
        self._gravar_ou_desfazer(lambda: self._itens.insert(posicao, item))
        return item
