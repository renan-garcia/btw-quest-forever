# BtWQuests no WoW Forever

O BtWQuests de retail foi adaptado para o WoW Forever (Interface 16001). O diário abre a expansão Forever, id 160, e as zonas de level são geradas a partir do Wowhead, não desenhadas à mão.

## Instalação

Copie as pastas `BTWQuests` e `BtWQuestsForever` para a pasta `Interface/AddOns` do cliente WoW Forever. As duas devem ficar diretamente em `AddOns`, sem uma pasta intermediária com o nome do repositório. Ative o BtWQuests na seleção de personagens; o módulo Forever é carregado sob demanda pelo núcleo.

Os dados Lua já estão incluídos. Python só é necessário para executar as ferramentas de geração. Reinicie o cliente após instalar ou alterar um arquivo TOC; para alterações apenas em Lua, use `/reload`.

## Pastas

`BTWQuests` é o núcleo. É o fork que carrega no cliente. O arquivo que o Forever usa é `BTWQuests_Camelot.toc`. Essa lista existe uma vez só. Ela não é gerada pelo tooling.

`BtWQuestsForever` é o módulo de dados, carregado sob demanda. Depende de `BTWQuests`. A expansão, as categorias e as cadeias ficam em `Defines.lua` e `General.lua`. Cada zona de level vira um arquivo em `Zones/`. Missões, NPCs e a busca ficam em `Database/`. `ZoneBuilder.lua` monta a cadeia em coluna. `Bindings.xml` existe vazio porque o cliente sempre abre esse arquivo.

`Tooling` fica ao lado do addon, não dentro dele. `atualizar.ps1` é o comando do dia a dia. `reset.ps1` zera as zonas geradas e o progresso, e mantém o catálogo e o cache. `run.py` é o programa. `lib/` tem o download, o estado, as cadeias e a gravação do Lua. `state/progress.json` diz o que já entrou e o que falta. `cache/` guarda as páginas já baixadas.

`tmp` contém cópias oficiais usadas como referência local. O cliente não carrega essa pasta, e ela não é incluída no repositório nem necessária para instalar o addon ou executar os testes.

O repositório inclui `Tooling/state/progress.json` para preservar o catálogo, os dados coletados e o progresso de geração. O cache de downloads, os backups, os arquivos compilados do Python e as configurações locais do editor ficam no disco, mas são ignorados pelo Git.

## Requisitos das ferramentas

Use Python 3.10 ou mais recente, disponível como `python` no PATH. As ferramentas usam apenas a biblioteca padrão do Python, sem pacotes adicionais. Os scripts `.ps1` exigem PowerShell. Comandos que baixam dados também precisam de acesso à internet.

## Comandos

Na pasta `Tooling`:

```powershell
.\atualizar.ps1
.\atualizar.ps1 list
.\atualizar.ps1 seed eastern-kingdoms/elwynn-forest
.\atualizar.ps1 seed eastern-kingdoms/westfall --refresh
.\atualizar.ps1 seed classes/paladin --delay=3
.\reset.ps1
```

`list` mostra o slug. `seed` baixa, grava o Lua e regrava a partir do estado. `--refresh` ignora o cache e pode vir antes ou depois do comando. `--delay` espera esses segundos entre páginas novas do Wowhead. Sem esses dois, o comportamento antigo continua. Depois de mudar o addon, use `/reload`. Mudança de TOC pede fechar o cliente.

## O que o gerador faz

Só zona de level vira categoria: Reinos do Leste e Kalimdor, sem capital. Classe, masmorra, raide e campo de batalha não ganham página própria.

A página do diário usa a primeira categoria de região válida na série completa do Wowhead (`category`), na ordem dos capítulos. O gerador baixa também as missões da série que não aparecem na lista inicial. A cadeia permanece nessa região mesmo quando seus últimos capítulos vão para outras zonas ou capitais. O pino do NPC só marca o mapa. Um id positivo que não está no catálogo, como a Ilha de Zefras, vira a categoria `new/{id}`, com o nome em português do Wowhead e sem mapa até existir um UiMapID.

Se faltarem dados de algum capítulo, a classificação fica pendente e a série não vira uma cadeia parcial. `--limit` limita também o download desses capítulos adicionais; use sem limite para completar a série. Se nenhuma categoria da série for uma região, a origem do NPC só é usada quando todas as origens conhecidas apontam para uma única área. Missões com origens diferentes ficam pendentes, evitando escolher uma zona pela ordem dos NPCs na página. As variantes de Aliança e Horda permanecem separadas.

Os testes de regressão do gerador podem ser executados da pasta AddOns com `python -m unittest discover -s Tooling/tests -v`. Eles verificam séries completas, capítulos ausentes, variantes de facção, origens ambíguas, migrações entre categorias e pinos sem mapa conhecido, usando dados em memória.

Facção trava a categoria quando todas as cadeias com facção são do mesmo lado. Raça e classe escondem a missão. O Celonato da Alta Ordem é a raça `Skyborne`: id 95 na Aliança e 96 na Horda. O bit do Wowhead `4294967296` vira essa raça.

O fundo do retângulo é um id de textura do cliente em `Tooling/lib/uimap.py`, obtido do BtWQuests Cataclysm e do catálogo wowdev/wow-listfile. Elwynn, Dun Morogh, Durotar, Mulgore, Teldrassil, Tirisfal Glades e Silverpine Forest também têm fundo mapeado. Alterac Mountains, Deadwind Pass e Moonglade ainda ficam sem fundo.

## Enviar para o GitHub

Crie um repositório vazio no GitHub, sem inicializar README, licença ou `.gitignore`. Na raiz desta pasta, substitua a URL do exemplo pela URL do repositório criado:

```powershell
git remote add origin https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git
git push -u origin main
```

O commit inicial já contém os addons, as ferramentas, os testes e o estado dos dados. Antes dos próximos commits, confira `git status` para verificar os arquivos que serão incluídos.
