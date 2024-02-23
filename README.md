# Desafio de Data Engineering
 
## Tabela de Conteúdos
- [Disclaimer](#disclaimer)
- [Overview](#overview)
- [Preparando o Ambiente](#preparando-o-ambiente)
  - [Criação do Diretório e Configuração Inicial](#criação-do-diretório-e-configuração-inicial)
  - [Configuração do Docker](#configuração-do-docker)
- [Instalação do Airflow](#instalação-do-airflow)
- [Instalação do Meltano](#instalação-do-meltano)
- [Instalação dos Plugins com Meltano](#instalação-dos-plugins-com-meltano)
- [Configuração e Testes](#configuração-e-testes)
  - [Meltano](#meltano)
  - [Criação da DAG](#criação-da-dag)
  - [Descrição da DAG](#descrição-da-dag)
  - [Considerações Finais](#considerações-finais)
 
## Disclaimer
Este repositório documenta o processo seguido para completar o desafio de Data Engineering. Todos os passos, desde a configuração do ambiente até a execução final do projeto, são detalhados abaixo.
O projeto foi realizado em ambiente Linux. Para execução do mesmo em outros ambientes, podem ser necessárias adaptações.
 
## Overview
Este projeto envolve a configuração de um ambiente de Data Engineering utilizando ferramentas como Docker, Airflow, e Meltano para extrair, carregar e transformar dados (ELT). O objetivo é demonstrar habilidades em configurar e utilizar essas ferramentas para manipular dados de diferentes fontes.
 
## Preparando o Ambiente
### Criação do Diretório e Configuração Inicial:
- Criação do diretório de trabalho e clonagem no GitHub.
- Criação e configuração do .gitignore, excluindo a pasta .venv e .meltanovenv.
 
### Configuração do Docker:
- Instalação do Docker Engine.
- Uso do `sudo docker compose up -d` para iniciar o Docker.
 
## Instalação do Airflow
- Criação do diretório `airflow` dentro da pasta do desafio.
- Exportação da Home do Airflow para o diretório: `export AIRFLOW_HOME=/<seu_diretorio_raiz>/airflow`.
- Criação do virtual environment para rodar o Airflow: `python3 -m venv .venv`.
- Acesso à .venv: `source .venv/bin/activate`.
- Instalação do Airflow dentro do virtual environment: `pip install "apache-airflow[celery]==2.8.1" --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.8.1/constraints-3.8.txt"`.
- Inicialização do Airflow: `airflow standalone`.
- Acesso ao Airflow através do navegador com `localhost:8080`.
- Para o funcionamento da DAG, é necessário definir uma variável do Airflow `base_path`, contendo o caminho até a pasta raiz do desafio.
 
## Instalação do Meltano
> Devido a incompatibilidades de dependências do Airflow 2.8.1 e do Meltano 3.3.1, foi necessário criar um ambiente virtual separado para o Meltano.
- Criação de Ambiente Virtual para o Meltano: `python3 -m venv .meltanovenv`.
- Instalação do Meltano: `pip install meltano`.
- Criação do projeto Meltano: `meltano init elt-desafio`.
 
## Instalação dos Plugins com Meltano
> É importante definir as senhas do banco de dados para `tap-postgres` e `target-postgres`
- `meltano add extractor tap-csv` para extrair dados de arquivos CSV.
- `meltano add extractor tap-postgres` para extrair dados do PostgreSQL.
- `meltano add loader target-csv` para carregar os dados para o localhost
- `meltano add loader target-postgres` para carregar os dados para o localhost.
- `meltano add mapper meltano-map-transformer` para transformações de dados.
 
## Configuração e Testes

### Meltano
- Acesso ao `meltano.yml` usando Vim para realizar configurações diretamente no arquivo, como a configuração do extractor CSV e a adição de filtros e configurações para o extractor PostgreSQL.
- Especificação de entidades, caminhos de arquivos, chaves, e configurações de filtros dentro do `meltano.yml` como por exemplo, há um item na tabela Orders que por definição, é um float, que pode ser interpretado normalmente na extração, porém o loader não interpretava perfeitamente, então usei um Meltano Map Transformer para converter os valores dessa coluna para string.

### Criação da DAG
Inicialmente, ao definir minhas funções na DAG, escolhi um caminho distinto da solução final do meu código. A intenção era criar diretórios e adicioná-los a uma lista, que seria então retornada ao final da função de criação dos diretórios. Planejava utilizar o XCOM para transferir as informações à próxima tarefa. Contudo, enfrentei problemas ao seguir essa abordagem porque, ao criar as tarefas da minha DAG, não consegui encontrar uma maneira de importar os dados para um BashOperator, de modo a iterar pela lista de nomes de diretórios criados. Tentei criar as tarefas dinamicamente com o BashOperator, utilizando Jinja Templates, mas essa estratégia também não resolveu o problema. Apesar de ter explorado diversas alternativas, não encontrei uma solução satisfatória. Após muitas horas sem progresso, decidi adotar uma abordagem mais simples para essa etapa, permitindo-me assim prosseguir com o restante do desafio.

### Descrição da DAG
A DAG começa com algumas funções principais:
- `create_folder_for_today` cria diretórios diários para armazenar dados do PostgreSQL e CSV, facilitando a gestão de dados. Utiliza o caminho base do Airflow, organiza os dados por data, e registra os caminhos criados.
- `get_source_names` identifica fontes de dados dentro da estrutura de diretórios, gerando uma lista de caminhos para as fontes. Isso permite a configuração dinâmica dos plugins do Meltano, otimizando a execução da pipeline.
- `write_config_file` automatiza a preparação de um arquivo de configuração JSON, que especifica os caminhos de arquivos a serem utilizados pelo loader na pipeline. Ela ajusta os caminhos fornecidos, remove referências a diretórios vazios para assegurar a relevância dos dados, e finaliza escrevendo a configuração ajustada em um arquivo config.json, o que facilita a gestão dinâmica dos caminhos de dados.
  
Utilizando as funções descritas anteriormente, foram criadas as tasks de criação de diretórios, e extração de dados para o local filesystem. Para a execução da segunda etapa, é realizada a criação de um arquivo de configuração JSON que detalha as fontes de dados extraídas, incluindo o caminho e as chaves primárias, que é necessário para a configuração do extrator final. Após a extração final, é executado o loader de dados final para transferir os dados extraídos e configurados para o banco de dados. Cada task é configurada para executar sequencialmente dentro da DAG, com base nas dependências especificadas, assegurando que os diretórios estejam prontos antes da extração de dados, que todos os dados sejam extraídos e configurados corretamente antes da criação do arquivo de configuração, e que a configuração final esteja pronta antes da execução do extrator de dados final.


### Considerações Finais
Há alguns meses, comecei a me interessar por engenharia de dados. Li alguns artigos, comecei a ler um livro sobre o assunto, fiz diversas pesquisas e explorei algumas das muitas coisas novas que essa área tem para oferecer. E foi nesse meio tempo que fiquei sabendo sobre o programa Lighthouse, e decidi me inscrever. Até participar deste desafio, não havia encontrado uma oportunidade que realmente testasse minha capacidade e me levasse ao meu limite. A experiência de enfrentar este desafio foi extraordinariamente gratificante. Encontrar-me em uma situação onde não dominava completamente todas as ferramentas necessárias me obrigou a realizar uma imersão profunda em pesquisa e aprendizado. Este processo não apenas expandiu significativamente meu conhecimento, mas também alimentou minha paixão pela área de engenharia de dados. Através deste desafio, minha convicção de seguir e me especializar em engenharia de dados se fortaleceu, reafirmando meu compromisso em concentrar meus estudos e desenvolver minha carreira nesse caminho empolgante e em constante evolução.
