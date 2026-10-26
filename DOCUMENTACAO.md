# Sistema de Gestão Acadêmica Integrado (Python + TXT)

## 1. Integrantes

- Milena — trabalho individual (desenvolveu os módulos das equipes ALFA e BETA e a integração).

> Para entregar: acrescentar sobrenome e RA.

## 2. Como executar

Requer Python 3.8 ou superior (a interface gráfica usa o `tkinter`, que já vem com o Python no Windows e no macOS).

```
python main.py          # menu no console
python main.py --gui    # interface gráfica (Desafio)
python testes.py        # testes automáticos
```

Na pasta `dados/` já existem registros de exemplo (nomes fictícios). Para começar do zero, apague o conteúdo dos quatro arquivos `.txt`.

## 3. Estrutura do projeto

```
sistema_academico/
├── main.py                 # ponto de entrada único (menu de console; --gui abre a interface)
├── interface_grafica.py    # Desafio: interface gráfica em tkinter
├── integracao.py           # SistemaAcademico: junta os módulos e gera o relatório
├── base.py                 # exceções, validadores e GerenciadorBase (CRUD + arquivos)
├── equipe_alfa/
│   ├── aluno.py            # Aluno + GerenciadorAlunos
│   └── curso.py            # Curso + GerenciadorCursos
├── equipe_beta/
│   ├── professor.py        # Professor + GerenciadorProfessores
│   └── disciplina.py       # Disciplina + GerenciadorDisciplinas
├── dados/                  # alunos.txt, cursos.txt, professores.txt, disciplinas.txt
└── testes.py
```

As classes de **entidade** (`Aluno`, `Curso`, `Professor`, `Disciplina`) são só modelos de dados: `__init__`, `__str__` e atributos protegidos (`_nome`) com `@property` e setters que validam. Toda a lógica de listas e arquivos fica nas classes **gerenciadoras** (`GerenciadorAlunos` etc.), que herdam de `GerenciadorBase`, onde o CRUD e a leitura/gravação dos `.txt` são escritos uma única vez.

## 4. Formato dos arquivos .txt

Uma linha por registro, campos separados por ponto e vírgula (`;`), na ordem dos atributos do enunciado. O primeiro campo é o identificador único.

| Arquivo | Campos (na ordem) | Exemplo |
|---|---|---|
| `alunos.txt` | matrícula; nome; CPF; e-mail; código do curso | `202301;João Silva;123.456.789-00;joao.silva@exemplo.com;10` |
| `cursos.txt` | código do curso; nome; modalidade | `10;Análise e Desenvolvimento de Sistemas;Presencial` |
| `professores.txt` | código do professor; nome; CPF; especialidade | `P1;Carlos Souza;111.222.333-44;Programação Orientada a Objetos` |
| `disciplinas.txt` | código da disciplina; nome; carga horária (horas); código do professor; código do curso | `D1;Programação Orientada a Objetos;80;P1;10` |

Por que esse formato:

- **Sem linha de cabeçalho**, para cada linha ser exatamente um registro e a leitura ser simples (`linha.split(";")`).
- **Ponto e vírgula** como separador, como pede o enunciado. Por isso nenhum campo pode conter `;` nem quebra de linha: o sistema recusa esses valores no cadastro.
- **Código do curso e do professor** guardados nas linhas de aluno e disciplina funcionam como "chave estrangeira" entre os arquivos.
- **Codificação UTF-8**, para acentos funcionarem em qualquer computador.

Como o sistema lê e grava:

- **Ao iniciar** (RF11), cada gerenciador lê o seu `.txt` e monta a lista de objetos em memória. Se o arquivo não existir, ele é criado vazio.
- **A cada cadastro, alteração ou exclusão** (RF12), o arquivo inteiro é regravado. A gravação é feita num arquivo temporário que depois substitui o original, para um erro no meio da escrita não corromper os dados.
- **Ao listar** (RF02), o arquivo é lido de novo, então uma edição manual no `.txt` aparece na hora.
- **Linhas inválidas** (campos faltando, dados fora do padrão ou código repetido) são ignoradas, e o sistema avisa quantas foram.

## 5. Regras de validação

| Campo | Regra |
|---|---|
| Matrícula e códigos | letras, números, `-` ou `_`, sem espaços; únicos dentro do arquivo |
| Nome, especialidade | obrigatórios |
| CPF | 11 dígitos, com ou sem pontuação; é gravado como `000.000.000-00` |
| E-mail | formato `nome@dominio.com` |
| Modalidade | `Presencial` ou `EAD` (aceita maiúsculas/minúsculas) |
| Carga horária | número inteiro maior que zero |

## 6. Integração entre os módulos

- Um **aluno** só é cadastrado se o `codigo_curso` existir (RF13).
- Uma **disciplina** só é cadastrada se o `codigo_professor` e o `codigo_curso` existirem (RF14).
- Não é possível **excluir** um curso que ainda tem alunos ou disciplinas, nem um professor que ainda tem disciplinas. Isso evita registros "órfãos".
- O **identificador** de um registro não pode ser alterado (os outros arquivos o referenciam). Para trocar, exclui-se e cadastra-se de novo.
- O **relatório integrado** (RF15) usa a frase pedida no enunciado, uma por combinação aluno × disciplina do curso dele:
  *"O Aluno [Nome] está matriculado no curso [Nome do Curso], assistindo a disciplina [Nome da Disciplina] com o professor [Nome do Professor]."*
- Os módulos de cada equipe também funcionam **sozinhos**: `GerenciadorAlunos(pasta)` sem o gerenciador de cursos simplesmente não confere o vínculo.

## 7. Dificuldades encontradas na integração

1. **O exemplo do enunciado tinha menos campos que o aluno.** O exemplo de `alunos.txt` mostra 4 campos, mas o módulo Aluno pede 5 (inclui o e-mail). Foi adotado o formato com 5 campos, na ordem do enunciado.
2. **O CPF do exemplo (`123.456.789-00`) não é um CPF válido de verdade.** Por isso o sistema valida apenas o formato (11 dígitos), sem conferir o dígito verificador, para o exemplo do enunciado funcionar.
3. **Aluno e disciplina não se ligam diretamente.** O aluno guarda só o curso; a disciplina guarda curso e professor. O relatório segue o caminho Aluno → Curso → Disciplinas do curso → Professor, e por isso um aluno aparece em uma linha para cada disciplina do seu curso.
4. **Ordem de cadastro.** Como há dependências, o cadastro precisa seguir a ordem: curso e professor, depois disciplina, depois aluno. O sistema avisa quando um vínculo aponta para um código que não existe.
5. **Consistência ao excluir e alterar.** Foi preciso bloquear exclusões que deixariam vínculos quebrados, e garantir que uma alteração inválida não deixe o registro pela metade (ou o arquivo diferente da memória): se qualquer campo novo for inválido, nada é alterado.
6. **Arquivo editado à mão.** Uma linha quebrada num `.txt` não derruba o programa: ela é ignorada e o usuário é avisado.

## 8. Requisitos atendidos

| Requisitos | Onde |
|---|---|
| RF01–RF05 (CRUD) | `GerenciadorBase`: `cadastrar`, `listar`, `pesquisar`, `alterar`, `excluir` |
| RF06–RF09 (atributos) | classes de entidade em `equipe_alfa/` e `equipe_beta/` |
| RF10–RF12 (persistência) | `GerenciadorBase`: `carregar` e `salvar` |
| RF13–RF14 (vínculos) | `_validar_vinculos` em `GerenciadorAlunos` e `GerenciadorDisciplinas` |
| RF15 (relatório) | `SistemaAcademico.relatorio_integrado` |
| RF16–RF18 (execução) | `main.py` (ponto único, menu e opção "Sair") |
| Desafio | `interface_grafica.py` (`python main.py --gui`) |

## 9. Roteiro sugerido para a demonstração

1. Abrir o sistema e mostrar os `.txt` da pasta `dados/`.
2. Cadastrar um **Curso** e um **Professor**.
3. Cadastrar uma **Disciplina** ligando os dois.
4. Cadastrar um **Aluno** no curso.
5. Abrir o **Relatório integrado** e mostrar a frase.
6. Abrir os `.txt` de novo e mostrar as linhas novas gravadas.
7. Mostrar um erro de validação (ex.: aluno em curso inexistente) e, se quiser, a interface gráfica.
