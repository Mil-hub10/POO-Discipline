"""
interface_grafica.py - Desafio: interface gráfica (tkinter) do sistema.

Abre com:  python main.py --gui

Uma aba por entidade (tabela + formulário + busca) e uma aba de relatórios.
Toda a regra de negócio continua nos gerenciadores; aqui só há telas.
"""

import tkinter as tk
from tkinter import messagebox, ttk

from base import ErroSistema

MODALIDADES = ["Presencial", "EAD"]


def codigo_da_escolha(texto):
    """'10 - Análise e Desenvolvimento' -> '10'."""
    return texto.split(" - ")[0].strip()


class AbaEntidade(ttk.Frame):
    """Aba com tabela, busca e formulário de uma entidade (RF32 / RF33)."""

    def __init__(self, mestre, sistema, gerenciador):
        super().__init__(mestre, padding=10)
        self.sistema = sistema
        self.ger = gerenciador
        self.campos = {}         # atributo -> widget de entrada
        self.selecionado = None  # código do registro em edição
        self.combo_filtro = None
        self.var_total = tk.StringVar()  # rodapé com o total (RF28)
        self.var_aviso = tk.StringVar()  # aviso sobre o arquivo (RF31)

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

        if self.ger is self.sistema.alunos:  # RF26: filtro por curso
            filtro = ttk.Frame(esquerda)
            filtro.pack(fill="x", pady=(0, 8))
            ttk.Label(filtro, text="Filtrar por curso:").pack(side="left")
            self.combo_filtro = ttk.Combobox(filtro, width=34, state="readonly")
            self.combo_filtro.pack(side="left", padx=6)
            ttk.Button(filtro, text="Filtrar", command=self.filtrar_por_curso).pack(side="left")

        colunas = [a for a, _ in self.ger.CAMPOS]
        self.tabela = ttk.Treeview(esquerda, columns=colunas, show="headings", height=13)
        for atributo, rotulo in self.ger.CAMPOS:
            self.tabela.heading(atributo, text=rotulo.split(" (")[0])
            self.tabela.column(atributo, width=110, anchor="w")
        self.tabela.pack(fill="both", expand=True)
        self.tabela.bind("<<TreeviewSelect>>", self._ao_selecionar)

        ttk.Label(esquerda, textvariable=self.var_total).pack(anchor="w", pady=(6, 0))
        ttk.Label(
            esquerda, textvariable=self.var_aviso, foreground="#b45309", wraplength=520
        ).pack(anchor="w")

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
                texto = codigo_da_escolha(texto)  # "10 - ADS" -> "10"
            dados[atributo] = texto
        return dados

    def _preencher(self, item):
        for atributo, widget in self.campos.items():
            widget.delete(0, "end")
            widget.insert(0, str(getattr(item, atributo)))

    def _atualizar_opcoes(self):
        """Mantém as listas de códigos (curso/professor) sempre atuais."""
        cursos = [f"{c.codigo_curso} - {c.nome}" for c in self.sistema.cursos.itens]
        opcoes = {
            "codigo_curso": cursos,
            "codigo_professor": [
                f"{p.codigo_professor} - {p.nome}" for p in self.sistema.professores.itens
            ],
        }
        for atributo, valores in opcoes.items():
            if atributo in self.campos:
                self.campos[atributo]["values"] = valores
        if self.combo_filtro is not None:
            self.combo_filtro["values"] = cursos

    # ---- tabela ---------------------------------------------------------
    def _preencher_tabela(self, itens):
        self.tabela.delete(*self.tabela.get_children())
        for item in itens:
            valores = [getattr(item, a) for a, _ in self.ger.CAMPOS]
            self.tabela.insert("", "end", iid=getattr(item, self.ger.atributo_id), values=valores)
        self.var_total.set(self.ger.texto_total(len(itens)))  # RF28

    def atualizar(self):
        itens = self.ger.listar()
        avisos = self.ger.pegar_avisos()  # RF31: arquivo recriado/corrompido
        self.var_aviso.set("Aviso: " + " ".join(avisos) if avisos else "")
        self._atualizar_opcoes()
        self._preencher_tabela(itens)

    def mostrar_todos(self):
        self.var_busca.set("")
        if self.combo_filtro is not None:
            self.combo_filtro.set("")
        self.atualizar()

    def pesquisar(self):
        termo = self.var_busca.get()
        achados = self.ger.pesquisar(termo)
        self._preencher_tabela(achados)
        if not achados:
            messagebox.showinfo("Pesquisar", "Nenhum registro encontrado.")

    def filtrar_por_curso(self):  # RF26
        escolha = self.combo_filtro.get().strip()
        if not escolha:
            messagebox.showwarning("Filtrar", "Escolha um curso na lista.")
            return
        try:
            _curso, alunos = self.sistema.alunos_do_curso(codigo_da_escolha(escolha))
        except ErroSistema as erro:
            messagebox.showerror("Atenção", str(erro))
            return
        self._preencher_tabela(alunos)

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
        if not messagebox.askyesno("Excluir", "Tem certeza que deseja excluir?"):  # RF29
            return

        def acao():
            self.ger.excluir(self.selecionado)

        if self._executar(acao, "Registro excluído com sucesso."):
            self.limpar()


class AbaRelatorio(ttk.Frame):
    """Relatório integrado (RF15) e alunos por disciplina (RF27)."""

    def __init__(self, mestre, sistema):
        super().__init__(mestre, padding=10)
        self.sistema = sistema

        topo = ttk.Frame(self)
        topo.pack(fill="x")
        ttk.Button(topo, text="Gerar relatório integrado", command=self.gerar).pack(side="left")
        ttk.Label(topo, text="    Alunos da disciplina:").pack(side="left")
        self.combo = ttk.Combobox(topo, width=34, state="readonly")
        self.combo.pack(side="left", padx=6)
        ttk.Button(topo, text="Ver alunos", command=self.alunos_da_disciplina).pack(side="left")

        self.texto = tk.Text(self, wrap="word", height=20, state="disabled")
        self.texto.pack(fill="both", expand=True, pady=(8, 0))
        self.atualizar()

    def atualizar(self):
        self.combo["values"] = [
            f"{d.codigo_disciplina} - {d.nome}" for d in self.sistema.disciplinas.itens
        ]
        self.combo.set("")
        self._escrever([])  # tela limpa a cada transição (RF30)

    def _escrever(self, linhas):
        self.texto.configure(state="normal")
        self.texto.delete("1.0", "end")
        self.texto.insert("1.0", "\n\n".join(linhas) if linhas else "")
        self.texto.configure(state="disabled")

    def gerar(self):
        try:
            linhas = self.sistema.relatorio_integrado() or ["Nenhum aluno cadastrado ainda."]
        except ErroSistema as erro:
            messagebox.showerror("Atenção", str(erro))
            return
        linhas += [f"Aviso: {a}" for a in self.sistema.coletar_avisos()]
        self._escrever(linhas)

    def alunos_da_disciplina(self):  # RF27
        escolha = self.combo.get().strip()
        if not escolha:
            messagebox.showwarning("Alunos da disciplina", "Escolha uma disciplina na lista.")
            return
        try:
            disciplina, curso, alunos = self.sistema.alunos_da_disciplina(
                codigo_da_escolha(escolha)
            )
        except ErroSistema as erro:
            messagebox.showerror("Atenção", str(erro))
            return
        nome_curso = curso.nome if curso else f"(curso {disciplina.codigo_curso} não encontrado)"
        linhas = [f"Disciplina: {disciplina.nome} | Curso: {nome_curso}"]
        linhas += [f"{a.nome} (matrícula {a.matricula})" for a in alunos]
        linhas.append(self.sistema.alunos.texto_total(len(alunos)))
        linhas += [f"Aviso: {a}" for a in self.sistema.coletar_avisos()]
        self._escrever(linhas)


class Aplicacao(tk.Tk):
    def __init__(self, sistema):
        super().__init__()
        self.title("Sistema de Gestão Acadêmica")
        self.geometry("1050x580")
        self.minsize(950, 500)
        ttk.Style(self).theme_use("clam")

        self.sistema = sistema
        self.abas = []
        notebook = ttk.Notebook(self)  # RF32: um módulo por aba
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        for ger in (sistema.cursos, sistema.professores, sistema.disciplinas, sistema.alunos):
            aba = AbaEntidade(notebook, sistema, ger)
            notebook.add(aba, text=ger.ROTULO_PLURAL)
            self.abas.append(aba)
        self.aba_relatorio = AbaRelatorio(notebook, sistema)
        notebook.add(self.aba_relatorio, text="Relatórios")

        # Ao trocar de aba, a tela é atualizada e limpa (RF30): um curso novo,
        # por exemplo, precisa aparecer na lista de cursos da aba de alunos.
        notebook.bind("<<NotebookTabChanged>>", self._ao_trocar_aba)

        ttk.Button(self, text="Encerrar", command=self.encerrar).pack(anchor="e", padx=8, pady=(0, 8))
        self.protocol("WM_DELETE_WINDOW", self.encerrar)

    def _ao_trocar_aba(self, _evento):
        for aba in self.abas:
            aba.atualizar()
            aba.limpar()
        self.aba_relatorio.atualizar()

    def encerrar(self):  # RF18
        if messagebox.askyesno("Encerrar", "Deseja encerrar o sistema?"):
            self.destroy()


def iniciar(sistema):
    Aplicacao(sistema).mainloop()
