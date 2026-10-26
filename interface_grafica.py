"""
interface_grafica.py - Desafio: interface gráfica (tkinter) do sistema.

Abre com:  python main.py --gui

Uma aba por entidade (tabela + formulário + busca) e uma aba de relatório.
Toda a regra de negócio continua nos gerenciadores; aqui só há telas.
"""

import tkinter as tk
from tkinter import messagebox, ttk

from base import ErroSistema, ErroValidacao

MODALIDADES = ["Presencial", "EAD"]


class AbaEntidade(ttk.Frame):
    """Aba com tabela, busca e formulário de uma entidade."""

    def __init__(self, mestre, sistema, gerenciador):
        super().__init__(mestre, padding=10)
        self.sistema = sistema
        self.ger = gerenciador
        self.campos = {}        # atributo -> widget de entrada
        self.selecionado = None  # código do registro em edição

        self._montar_tabela()
        self._montar_formulario()
        self.atualizar()

    # ---- montagem das telas ---------------------------------------------
    def _montar_tabela(self):
        esquerda = ttk.Frame(self)
        esquerda.pack(side="left", fill="both", expand=True)

        busca = ttk.Frame(esquerda)
        busca.pack(fill="x", pady=(0, 8))
        ttk.Label(busca, text=f"Pesquisar ({self.ger.rotulo_id} ou nome):").pack(side="left")
        self.var_busca = tk.StringVar()
        entrada = ttk.Entry(busca, textvariable=self.var_busca, width=24)
        entrada.pack(side="left", padx=6)
        entrada.bind("<Return>", lambda _e: self.pesquisar())
        ttk.Button(busca, text="Pesquisar", command=self.pesquisar).pack(side="left")
        ttk.Button(busca, text="Mostrar todos", command=self.mostrar_todos).pack(side="left", padx=6)

        colunas = [a for a, _ in self.ger.CAMPOS]
        self.tabela = ttk.Treeview(esquerda, columns=colunas, show="headings", height=14)
        for atributo, rotulo in self.ger.CAMPOS:
            self.tabela.heading(atributo, text=rotulo.split(" (")[0])
            self.tabela.column(atributo, width=110, anchor="w")
        self.tabela.pack(fill="both", expand=True)
        self.tabela.bind("<<TreeviewSelect>>", self._ao_selecionar)

    def _montar_formulario(self):
        direita = ttk.LabelFrame(self, text=f" {self.ger.ROTULO} ", padding=10)
        direita.pack(side="right", fill="y", padx=(12, 0))

        for linha, (atributo, rotulo) in enumerate(self.ger.CAMPOS):
            ttk.Label(direita, text=rotulo).grid(row=linha * 2, column=0, sticky="w")
            if atributo == "modalidade":
                widget = ttk.Combobox(direita, values=MODALIDADES, width=28)
            elif atributo in ("codigo_curso", "codigo_professor"):
                widget = ttk.Combobox(direita, width=28)
            else:
                widget = ttk.Entry(direita, width=31)
            widget.grid(row=linha * 2 + 1, column=0, pady=(0, 6), sticky="w")
            self.campos[atributo] = widget

        botoes = ttk.Frame(direita)
        botoes.grid(row=len(self.ger.CAMPOS) * 2, column=0, pady=(10, 0), sticky="w")
        ttk.Button(botoes, text="Cadastrar", command=self.cadastrar).grid(row=0, column=0, padx=2, pady=2)
        ttk.Button(botoes, text="Alterar", command=self.alterar).grid(row=0, column=1, padx=2, pady=2)
        ttk.Button(botoes, text="Excluir", command=self.excluir).grid(row=1, column=0, padx=2, pady=2)
        ttk.Button(botoes, text="Limpar", command=self.limpar).grid(row=1, column=1, padx=2, pady=2)

    # ---- dados dos campos -----------------------------------------------
    def _ler_formulario(self):
        dados = {}
        for atributo, widget in self.campos.items():
            texto = widget.get().strip()
            if atributo in ("codigo_curso", "codigo_professor"):
                texto = texto.split(" - ")[0].strip()  # "10 - ADS" -> "10"
            dados[atributo] = texto
        return dados

    def _preencher(self, item):
        for atributo, widget in self.campos.items():
            widget.delete(0, "end")
            widget.insert(0, str(getattr(item, atributo)))

    def _atualizar_opcoes(self):
        """Mantém as listas de códigos (curso/professor) sempre atuais."""
        opcoes = {
            "codigo_curso": [f"{c.codigo_curso} - {c.nome}" for c in self.sistema.cursos.itens],
            "codigo_professor": [
                f"{p.codigo_professor} - {p.nome}" for p in self.sistema.professores.itens
            ],
        }
        for atributo, valores in opcoes.items():
            if atributo in self.campos:
                self.campos[atributo]["values"] = valores

    # ---- tabela ---------------------------------------------------------
    def _preencher_tabela(self, itens):
        self.tabela.delete(*self.tabela.get_children())
        for item in itens:
            valores = [getattr(item, a) for a, _ in self.ger.CAMPOS]
            self.tabela.insert("", "end", iid=getattr(item, self.ger.atributo_id), values=valores)

    def atualizar(self):
        self._atualizar_opcoes()
        self._preencher_tabela(self.ger.listar())

    def mostrar_todos(self):
        self.var_busca.set("")
        self.atualizar()

    def pesquisar(self):
        termo = self.var_busca.get()
        achados = self.ger.pesquisar(termo)
        self._preencher_tabela(achados)
        if not achados:
            messagebox.showinfo("Pesquisar", "Nenhum registro encontrado.")

    def _ao_selecionar(self, _evento):
        escolhido = self.tabela.selection()
        if not escolhido:
            return
        item = self.ger.buscar_por_codigo(escolhido[0])
        if item is not None:
            self.selecionado = escolhido[0]
            self._preencher(item)

    # ---- ações ----------------------------------------------------------
    def limpar(self):
        self.selecionado = None
        for widget in self.campos.values():
            widget.delete(0, "end")
        self.tabela.selection_remove(*self.tabela.selection())

    def _executar(self, acao, sucesso):
        """Roda a ação; mostra o erro (e devolve False) ou o sucesso (True)."""
        try:
            acao()
        except ErroSistema as erro:
            messagebox.showerror("Atenção", str(erro))
            return False
        self.atualizar()
        messagebox.showinfo("Pronto", sucesso)
        return True

    def cadastrar(self):
        dados = self._ler_formulario()

        def acao():
            self.ger.cadastrar(**dados)

        if self._executar(acao, f"{self.ger.ROTULO} cadastrado(a) com sucesso."):
            self.limpar()

    def alterar(self):
        if self.selecionado is None:
            messagebox.showwarning("Alterar", "Selecione um registro na tabela primeiro.")
            return
        dados = self._ler_formulario()
        dados.pop(self.ger.atributo_id)  # o identificador não muda

        def acao():
            self.ger.alterar(self.selecionado, **dados)

        self._executar(acao, "Registro alterado com sucesso.")

    def excluir(self):
        if self.selecionado is None:
            messagebox.showwarning("Excluir", "Selecione um registro na tabela primeiro.")
            return
        if not messagebox.askyesno("Excluir", "Confirma a exclusão deste registro?"):
            return

        def acao():
            self.ger.excluir(self.selecionado)

        if self._executar(acao, "Registro excluído com sucesso."):
            self.limpar()


class AbaRelatorio(ttk.Frame):
    def __init__(self, mestre, sistema):
        super().__init__(mestre, padding=10)
        self.sistema = sistema
        ttk.Button(self, text="Gerar relatório integrado", command=self.gerar).pack(anchor="w")
        self.texto = tk.Text(self, wrap="word", height=20, state="disabled")
        self.texto.pack(fill="both", expand=True, pady=(8, 0))

    def gerar(self):
        linhas = self.sistema.relatorio_integrado() or ["Nenhum aluno cadastrado ainda."]
        self.texto.configure(state="normal")
        self.texto.delete("1.0", "end")
        self.texto.insert("1.0", "\n\n".join(linhas))
        self.texto.configure(state="disabled")


class Aplicacao(tk.Tk):
    def __init__(self, sistema):
        super().__init__()
        self.title("Sistema de Gestão Acadêmica")
        self.geometry("1000x560")
        self.minsize(900, 480)
        ttk.Style(self).theme_use("clam")

        self.sistema = sistema
        self.abas = []
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        for ger in (sistema.cursos, sistema.professores, sistema.disciplinas, sistema.alunos):
            aba = AbaEntidade(notebook, sistema, ger)
            notebook.add(aba, text=ger.ROTULO_PLURAL)
            self.abas.append(aba)
        self.aba_relatorio = AbaRelatorio(notebook, sistema)
        notebook.add(self.aba_relatorio, text="Relatório integrado")

        # Ao trocar de aba, recarrega os dados (um curso novo, por exemplo,
        # precisa aparecer na lista de cursos da aba de alunos).
        notebook.bind("<<NotebookTabChanged>>", self._ao_trocar_aba)

        ttk.Button(self, text="Encerrar", command=self.encerrar).pack(anchor="e", padx=8, pady=(0, 8))
        self.protocol("WM_DELETE_WINDOW", self.encerrar)

    def _ao_trocar_aba(self, _evento):
        for aba in self.abas:
            aba.atualizar()

    def encerrar(self):  # RF18
        if messagebox.askyesno("Encerrar", "Deseja encerrar o sistema?"):
            self.destroy()


def iniciar(sistema):
    Aplicacao(sistema).mainloop()
