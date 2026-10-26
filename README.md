# Sistema de Gestão Acadêmica Integrado

Projeto prático da disciplina de **Programação Orientada a Objetos (POO)**, em Python.

Sistema de cadastro acadêmico que gerencia **Alunos, Cursos, Professores e Disciplinas**, guarda os dados em arquivos `.txt` e relaciona as quatro entidades em um relatório integrado.

**Autora:** Milena Santana De Jesus — RA 202647035

## O que o sistema faz

- **CRUD completo** para as quatro entidades: cadastrar, listar, pesquisar (por código ou parte do nome), alterar e excluir.
- **Persistência em arquivos `.txt`**, um por entidade, com campos separados por ponto e vírgula (`;`). Os dados são carregados ao iniciar e o arquivo é atualizado a cada cadastro, alteração ou exclusão.
- **Vínculos entre entidades:** o aluno pertence a um curso; a disciplina pertence a um curso e a um professor. O sistema recusa vínculos com códigos que não existem e impede excluir um curso ou professor ainda em uso.
- **Validação dos dados:** CPF, e-mail, modalidade (Presencial ou EAD), carga horária e códigos únicos.
- **Relatório integrado:** uma frase por aluno e disciplina do curso dele, no formato *"O Aluno [Nome] está matriculado no curso [Curso], assistindo a disciplina [Disciplina] com o professor [Professor]."*
- **Duas interfaces:** menu no console e interface gráfica (desafio), ambas em um único ponto de entrada, o `main.py`.

## Como executar

Requer **Python 3.8 ou superior**. A interface gráfica usa o `tkinter`, que já acompanha o Python no Windows e no macOS.

```
python main.py            # menu no console
python main.py --gui      # interface gráfica (desafio)
python testes.py          # testes automáticos
```

Na pasta `dados/` já existem registros de exemplo, com nomes fictícios. Para começar do zero, apague o conteúdo dos quatro arquivos `.txt`.

> Ordem de cadastro: **curso** e **professor** primeiro, depois **disciplina**, depois **aluno**.

## Estrutura do projeto

```
├── main.py                 # ponto de entrada único (console; --gui abre a interface)
├── interface_grafica.py    # desafio: interface gráfica em tkinter
├── integracao.py           # SistemaAcademico: junta os módulos e gera o relatório
├── base.py                 # exceções, validadores e GerenciadorBase (CRUD + arquivos)
├── equipe_alfa/
│   ├── aluno.py            # Aluno + GerenciadorAlunos
│   └── curso.py            # Curso + GerenciadorCursos
├── equipe_beta/
│   ├── professor.py        # Professor + GerenciadorProfessores
│   └── disciplina.py       # Disciplina + GerenciadorDisciplinas
├── dados/                  # alunos.txt, cursos.txt, professores.txt, disciplinas.txt
├── testes.py               # testes automáticos
└── DOCUMENTACAO.md         # documentação completa
```

## Conceitos de POO aplicados

- **Encapsulamento:** atributos protegidos (`_nome`) com `@property` e setters que validam os dados.
- **Separação de responsabilidades:** as classes de entidade são só modelos de dados (`__init__` e `__str__`); a lógica de listas e arquivos fica nas classes gerenciadoras.
- **Herança:** todos os gerenciadores herdam de `GerenciadorBase`, onde o CRUD e a leitura/gravação dos arquivos são escritos uma única vez.
- **Tratamento de erros:** exceções próprias (`ErroSistema` e `ErroValidacao`) mostram mensagens claras, sem derrubar o programa.

## Formato dos arquivos de dados

| Arquivo | Campos (na ordem) |
|---|---|
| `alunos.txt` | matrícula; nome; CPF; e-mail; código do curso |
| `cursos.txt` | código do curso; nome; modalidade |
| `professores.txt` | código do professor; nome; CPF; especialidade |
| `disciplinas.txt` | código da disciplina; nome; carga horária; código do professor; código do curso |

Exemplo de linha em `alunos.txt`:

```
202301;João Silva;123.456.789-00;joao.silva@exemplo.com;10
```

## Documentação

Formato dos arquivos, regras de validação, dificuldades encontradas na integração e roteiro de demonstração estão em [`DOCUMENTACAO.md`](DOCUMENTACAO.md).
