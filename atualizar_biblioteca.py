"""Atualiza a biblioteca offline do TaVivo com os novos manuais (Sabedorias, Saúde, Comida e Itens).

- Cria/atualiza os arquivos 0144.md a 0175.md em library.noindex/text/ptbr/
- Indexa de forma idempotente em library.noindex/index.sqlite (SQLite FTS5)
- Exporta app/static/library_offline.json para busca 100% offline no modo PWA

Uso:
  python3 atualizar_biblioteca.py

Construído por Capitain Of Cruzades.
"""

import json
import os
import sqlite3

ROOT = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.join(ROOT, "library.noindex")
DB_PATH = os.path.join(LIB_DIR, "index.sqlite")
TEXT_DIR = os.path.join(LIB_DIR, "text")
PTBR_DIR = os.path.join(TEXT_DIR, "ptbr")
PWA_LIB_PATH = os.path.join(ROOT, "app", "static", "library_offline.json")

NEW_SOURCES = [
    (
        "sabedorias-oficios",
        "Sabedorias Práticas, Ofícios, Energia Off-Grid e Defesa Passiva (PT-BR)",
        "survival-wisdom",
        "ptbr-v2",
        "Domínio Público / Conhecimento Técnico Tradicional",
    ),
    (
        "saude-campo-avancada",
        "Saúde de Campo Avançada, Pediatria, Fitoterapia RENISUS e Veterinária (PT-BR)",
        "medical",
        "ptbr-v2",
        "Domínio Público / Referência OMS, SUS (RENISUS) e Medicina de Campo",
    ),
    (
        "comida-longo-prazo",
        "Comida, PANCs do Brasil, Conservação, Fermentação e Micro-Agricultura (PT-BR)",
        "food-survival",
        "ptbr-v2",
        "Domínio Público / Extensão Rural e Segurança Alimentar",
    ),
    (
        "itens-fim-do-mundo",
        "Itens pro Fim do Mundo: Kits EDC, BOB, Bug-In, Carro, Farmácia e Faraday (PT-BR)",
        "gear-kits",
        "ptbr-v2",
        "Domínio Público / Defesa Civil e Preparação Familiar",
    ),
]

MANUALS = [
    # === 1. SABEDORIAS (0144 - 0151) ===
    (
        "0144.md",
        "sabedorias-oficios",
        "Nós e Amarrações Essenciais de Sobrevivência e Resgate",
        """# Nós e Amarrações Essenciais de Sobrevivência e Resgate

1. NÓ DIREITO (JUNÇÃO DE CORDAS IGUAIS E BANDAGENS):
   - Passe a ponta direita sobre a esquerda e por baixo (meio nó); depois passe a esquerda sobre a direita e por baixo.
   - Uso: fechar ataduras, amarrar pacotes e unir duas cordas de mesma espessura sem carga crítica. Não use em cordas escorregadias sob peso alto.

2. LAIS DE GUIA (ALÇA FIXA QUE NÃO CORRE E NÃO APERTA):
   - Faça um pequeno laço na corda firme; passe a ponta livre de baixo para cima pelo laço, dê a volta por trás da corda firme e volte por dentro do mesmo laço.
   - Uso: resgate, amarrar lona, prender carga pesada. Mesmo após tensão extrema, é fácil de desatar quebrando a "costa" do nó.

3. NÓ FIEL (PRENDER CORDA EM POSTE OU ÁRVORE):
   - Dê uma volta completa no tronco, cruze por cima formando um X, dê segunda volta e passe a ponta por baixo da última volta no centro do X.
   - Uso: iniciar amarrações de abrigo, esticar varal ou lona. Finalize com dois cotes para não soltar.

4. NÓ DE PESCADOR DUPLO (UNIR DUAS CORDAS OU LINHA DE PESCA):
   - Dê um nó simples duplo com a ponta A abraçando o corpo da corda B, e repita com a ponta B abraçando o corpo da corda A. Puxe até os dois nós encostarem.
   - Uso: emendar linhas de nylon, paracord ou cordas molhadas sem escorregar.

5. NÓ TENSOR (TAUT-LINE HITCH — ESTICAR LONA/BARRACA):
   - Dê a volta no ponto fixo, faça duas voltas internas ao redor da corda principal e uma volta externa acima delas.
   - Uso: desliza para ajustar a tensão da lona quando chove ou venta e trava sob tração.

6. AMARRA QUADRADA E AMARRA DIAGONAL (ABRIGO E MACA):
   - Amarra quadrada: une dois troncos a 90 graus. Inicie com nó fiel, dê 3 a 4 voltas alternando por cima e por baixo, faça 2 voltas de enforcamento entre os troncos e feche com nó fiel.
   - Amarra diagonal: une troncos em X (tripés de fogão ou reforço de estrutura). Comece com volta da ribeira, 3 voltas em cada eixo do X, enforcamento e nó fiel.
""",
    ),
    (
        "0145.md",
        "sabedorias-oficios",
        "Sabão Caseiro com Cinzas (Lixívia), Vinagre, Bicarbonato e Cal Virgem",
        """# Sabão Caseiro com Cinzas (Lixívia), Vinagre, Bicarbonato e Cal Virgem

1. LIXÍVIA CASEIRA COM CINZA DE MADEIRA (SEM SODA CÁUSTICA INDUSTRIAL):
   - Use apenas cinza branca de madeira dura (evite madeira tratada, pintada ou lixo).
   - Monte um balde com furos no fundo, forre com pedras pequenas, areia limpa e pano/capim seco. Encha com cinza e despeje água da chuva ou fervida lentamente.
   - O líquido marrom que escorre é hidróxido de potássio (lixívia). Teste de força: um ovo cru fresco ou uma batata pequena deve flutuar parcialmente; se afundar, passe o líquido novamente pelas cinzas ou ferva para concentrar.
   - SEGURANÇA: lixívia é cáustica e queima pele e olhos. Use luvas, recipiente de inox, vidro ou plástico grosso (NUNCA alumínio).

2. SABÃO DE EMERGÊNCIA (GORDURA + LIXÍVIA OU SODA):
   - Com lixívia de cinzas: aqueça 1 parte de gordura animal limpa ou óleo vegetal usado coado com 2 a 3 partes de lixívia concentrada em fogo baixo, mexendo sempre até engrossar (saponificação gera sabão pastoso). Adicionar sal de cozinha ajuda a separar e endurecer o sabão.
   - Com soda cáustica (NaOH 99%): proporção clássica de segurança — 1 litro de óleo coado + 140 g de soda dissolvida em 300 ml de água (SEMPRE despeje a soda na água, nunca água na soda). Misture até ponto de mingau, despeje em forma e aguarde cura de 15 a 30 dias antes de usar na pele.

3. QUÍMICA DOMÉSTICA ESSENCIAL EM CRISE:
   - Vinagre (ácido acético): desengordurante, conservação ácida de vegetais, alívio de picada de água-viva (nunca misture com água sanitária — libera gás cloro mortal!).
   - Bicarbonato de sódio: antiácido estomacal leve (meia colher de chá em 1 copo de água), pasta para picadas de inseto, higiene dental sem pasta, combate a pequenos focos de fogo em gordura.
   - Cal virgem / cal hidratada: controle de odor e moscas em latrinas secas (polvilhar fina camada após uso) e desinfecção de solo contaminado. Proteja olhos e vias aéreas ao manusear.
""",
    ),
    (
        "0146.md",
        "sabedorias-oficios",
        "Costura Manual, Remendos, Reparo de Calçados e Impermeabilização",
        """# Costura Manual, Remendos, Reparo de Calçados e Impermeabilização

1. PONTOS MANUAIS RESISTENTES:
   - Ponto atrás (backstitch): o mais forte para costuras que sofrem tração (mochilas, calças, alças). Avance um ponto, volte no furo anterior e saia um ponto à frente.
   - Ponto chuleado (whipstitch): ideal para fechar bordas desfiando ou unir dois tecidos grossos lado a lado.
   - Fio de emergência: fio dental encerado (altíssima resistência para mochilas e calçados), linha de pesca fina ou fios internos do paracord 550.

2. REMENDOS E REFORÇO DE ROUPAS:
   - Corte o remendo 2 cm maior que o rasgo em todos os lados, com cantos arredondados (cantos quadrados descolam/rasgam primeiro).
   - Dobre 0,5 cm das bordas do remendo para dentro e costure pelo lado interno em tecidos leves ou pelo externo em lonas/mochilas.

3. REPARO DE CALÇADOS E SOLADOS:
   - Solado descolando: limpe sujeira e umidade, raspe levemente, aplique cola de contato/epóxi e pressione com peso por 12 horas. Sem cola, fure a borda com sovela/prego aquecido e costure com fio dental encerado ou arame fino.
   - Bolhas e desgaste interno: forre o calcanhar com fita silver tape (superfície lisa reduz atrito na pele).

4. IMPERMEABILIZAÇÃO CASEIRA DE TECIDOS E LONAS:
   - Mistura de cera de abelha (ou parafina de vela) derretida em banho-maria com 20% a 30% de óleo vegetal ou mineral para manter flexibilidade.
   - Esfregue a barra de cera no tecido de algodão/lona seco e aqueça levemente com calor indireto (sol forte ou próximo à brasa sem queimar) para penetrar nas fibras.
""",
    ),
    (
        "0147.md",
        "sabedorias-oficios",
        "Carpintaria Sem Eletricidade, Afiação de Lâminas e Cordas Vegetais",
        """# Carpintaria Sem Eletricidade, Afiação de Lâminas e Cordas Vegetais

1. AFIAÇÃO DE FACAS, FACÕES E MACHADOS EM CAMPO:
   - Ângulo padrão: 20 graus para facas utilitárias, 25 a 30 graus para facões e machados (fio mais resistente a lascas).
   - Técnica na pedra (ou fundo de caneca de cerâmica sem esmalte / pedra lisa de rio): molhe a pedra, deslize a lâmina como se tentasse "fatiar" a superfície da pedra, mantendo o mesmo número de passadas em cada lado até sumir o brilho na borda do fio.
   - Assentamento final: passe o fio no sentido contrário (puxando) sobre um cinto de couro ou papelão grosso para alinhar rebarbas.

2. FABRICAÇÃO DE CORDAS COM FIBRAS VEGETAIS BRASILEIRAS:
   - Melhores fontes: fibra de sisal, casca interna (entrecasca) de embaúba/embira, folha de bananeira seca, bromélias resistentes, palha de milho.
   - Método da torção reversa: segure dois feixes de fibra, torça o feixe superior no sentido horário e passe-o por baixo do inferior no sentido anti-horário. Repita sempre no mesmo ritmo; para emendar, insira nova fibra 5 cm antes da anterior acabar.

3. CARPINTARIA BÁSICA E ENCAIXES SEM PREGOS:
   - Meia-madeira: entalhe metade da espessura em cada peça para cruzar vigas niveladas.
   - Furo e espiga: use brasa controlada (carvão quente soprado com canudo de bambu) para queimar e abrir furos em madeira quando não houver furadeira.
   - Proteção da madeira em contato com o solo: carbonize levemente (queime 2 a 3 mm da superfície) a ponta da estaca que vai enterrada — reduz apodrecimento e cupins.
""",
    ),
    (
        "0148.md",
        "sabedorias-oficios",
        "Energia Off-Grid Prática: Placa Solar, Bateria 12V e Carregamento Seguro",
        """# Energia Off-Grid Prática: Placa Solar, Bateria 12V e Carregamento Seguro

1. SISTEMA SOLAR MÍNIMO DE EMERGÊNCIA (12V):
   - Componentes essenciais: placa solar 12V (20W a 100W) + controlador de carga PWM ou MPPT + bateria 12V (estacionária, AGM, LiFePO4 ou automotiva em último caso).
   - ORDEM OBRIGATÓRIA DE LIGAÇÃO: 1) conecte primeiro a BATERIA ao controlador (para ele reconhecer 12V); 2) depois conecte a PLACA SOLAR; 3) por último as cargas USB/12V. Para desligar, faça a ordem inversa.

2. CUIDADOS COM BATERIAS EM APAGÕES:
   - Bateria automotiva comum (chumbo-ácido): NÃO descarregue abaixo de 12,0V (50% de carga) com frequência, senão perde vida útil rapidamente. Mantenha em local ventilado (libera gás hidrogênio inflamável ao carregar).
   - Referência de voltagem 12V em repouso: 12,6V–12,7V (100%), 12,2V (50%), abaixo de 11,8V (descarregada — recarregar imediatamente).

3. CARREGAR CELULAR, RÁDIO E PILHAS EM BATERIA DE CARRO:
   - NUNCA ligue celular direto nos 12V da bateria (queima na hora; USB é 5V).
   - Use adaptador veicular 12V→5V (tomada de acendedor com garras jacaré: centro = positivo +, lateral = negativo -) ou módulo conversor DC-DC step-down ajustado para 5V.
   - Economize energia do celular: Modo Avião sempre ligado, brilho mínimo, desligue Bluetooth/GPS/Wi-Fi quando não estiver usando e use tema escuro.

4. SEGURANÇA ELÉTRICA:
   - Use fusível próximo ao polo positivo da bateria (10A a 15A para cargas leves).
   - Nunca feche curto entre polos com chave metálica ou anéis; bateria automotiva libera centenas de ampères e derrete metal instantaneamente.
""",
    ),
    (
        "0149.md",
        "sabedorias-oficios",
        "Gestão de Comunidade, Turnos de Vigia, Racionamento e Escambo",
        """# Gestão de Comunidade, Turnos de Vigia, Racionamento e Escambo

1. ORGANIZAÇÃO DE GRUPO E TURNOS DE VIGIA:
   - Em crises prolongadas, ninguém sobrevive isolado por muito tempo: divida tarefas claras (água/fogo, saúde/higiene, comida/estoque, segurança/comunicação).
   - Turnos de vigia noturna: máximo de 2 horas por pessoa (após 2h a atenção cai drasticamente). Sempre acorde o próximo turno pessoalmente e confirme que está de pé antes de deitar.

2. RACIONAMENTO JUSTO E SUSTENTÁVEL:
   - Faça inventário escrito de toda água e comida logo no Dia 1 e divida pela estimativa conservadora de dias sem reposição.
   - Prioridade calórica e hídrica: crianças pequenas, gestantes/lactantes, feridos/doentes e quem executa trabalho físico pesado.
   - Consuma primeiro perecíveis (geladeira/freezer), depois frutas/verduras, e só por último enlatados e grãos secos.

3. ESCAMBO (TROCA SEM DINHEIRO OU PIX):
   - Itens de altíssimo valor de troca: sal, açúcar, água potável/cloro, pilhas/baterias, isqueiros, remédios básicos (analgésicos, antitérmicos, antissépticos), sabão, papel higiênico, café, sementes, ferramentas e habilidades técnicas (costura, mecânica, primeiros socorros).
   - Regra de ouro de segurança no escambo: NUNCA leve o negociador até sua casa/estoque e NUNCA revele quanto você tem guardado. Troque apenas quantidades pequenas em local neutro e acompanhado.
""",
    ),
    (
        "0150.md",
        "sabedorias-oficios",
        "Defesa Residencial Passiva, Disciplina de Luz/Fumaça e OpSec Familiar",
        """# Defesa Residencial Passiva, Disciplina de Luz/Fumaça e OpSec Familiar

1. REGRA DO PERFIL BAIXO (OPSEC — SEGURANÇA OPERACIONAL):
   - A melhor defesa em colapso social é não parecer um alvo valioso. Não exiba gerador barulhento, luz acesa quando a rua inteira está no escuro ou cheiro forte de churrasco/comida farta.
   - Combine com a família (incluindo crianças) a regra do silêncio sobre estoques, remédios, equipamentos e rotas de fuga.

2. DISCIPLINA DE LUZ, SOM E FUMAÇA:
   - Blackout nas janelas: cubra janelas internas com papelão, lona preta ou cobertores grossos antes de acender lanternas ou velas à noite.
   - Prefira lanterna de luz vermelha fraca para circular à noite (preserva visão noturna e é menos visível de longe).
   - Cozinhar com menos fumaça: use fogão foguete (rocket stove) com lenha bem seca ou panela térmica (haybox) — menos fumaça e menos cheiro circulando.

3. REFORÇO PASSIVO DE PORTAS E JANELAS:
   - Troque parafusos curtos da fechadura/batente por parafusos longos (7 a 8 cm) que alcancem a estrutura firme da parede.
   - Trancas internas adicionais (ferrolhos, calços de madeira em portas de correr) e iluminação externa com sensor solar em pontos cegos.
   - Tenha sempre um plano de saída secundária (nunca se tranque sem rota de fuga em caso de incêndio).
""",
    ),
    (
        "0151.md",
        "sabedorias-oficios",
        "Leitura do Tempo (Nuvens e Ventos) e Calendário Agrícola do Brasil",
        """# Leitura do Tempo (Nuvens e Ventos) e Calendário Agrícola do Brasil

1. PREVISÃO DO TEMPO SEM INTERNET (NUVENS E SINAIS):
   - Cirrus (finas e altas, "rabo de galo"): mudança de tempo ou frente fria em 24 a 48 horas.
   - Cumulus baixas e brancas (algodão isolado): tempo estável. Se começarem a crescer verticalmente rápido formando "bigorna" escura (Cumulonimbus): tempestade forte, raios e vendaval em menos de 1 a 2 horas — busque abrigo.
   - Halo ao redor do Sol ou da Lua: cristais de gelo em altitude anunciam chuva nas próximas 24 horas.
   - Fumaça de fogueira que sobe reta = alta pressão (tempo firme); fumaça que desce ou gira rente ao chão = baixa pressão e umidade alta (chuva próxima).

2. CALENDÁRIO AGRÍCOLA SIMPLIFICADO NO BRASIL:
   - Culturas de ciclo muito rápido (25 a 50 dias, quase o ano todo): rabanete, rúcula, alface, espinafre, coentro, cebolinha, couve.
   - Culturas de alta caloria (90 a 180 dias): batata-doce (muito rústica, tolera seca), feijão (75–90 dias), milho (90–120 dias), abóbora/moranga (90–110 dias, dura meses colhida), mandioca (8–12 meses, funciona como "geladeira viva" debaixo da terra).
   - Regiões:
     * Sul/Sudeste: plantio principal de verão (milho, feijão, abóbora, tomate) de setembro a janeiro; inverno (couve, brócolis, cenoura, ervilha, alho) de março a julho.
     * Centro-Oeste: aproveite o início das chuvas (outubro–março) para grãos e raízes; na seca (maio–setembro) priorize hortas irrigadas com cobertura morta (palha).
     * Nordeste/Norte: priorize culturas resistentes ao calor e seca (mandioca, feijão-caupi/de-corda, maxixe, quiabo, jerimum/abóbora, batata-doce, palma).
""",
    ),
    # === 2. SAÚDE (0152 - 0159) ===
    (
        "0152.md",
        "saude-campo-avancada",
        "Triagem de Múltiplas Vítimas em Crise (Método START)",
        """# Triagem de Múltiplas Vítimas em Crise (Método START)

1. QUANDO USAR:
   - Quando há várias vítimas (desabamento, acidente, enchente, explosão) e poucos socorristas. Objetivo: salvar o maior número possível de vidas em menos de 30 segundos por pessoa.

2. PASSO A PASSO DO MÉTODO START (4 CORES):
   - PASSO 1 — ANDA? Peça em voz alta: "Quem puder andar, venha até aqui!". Quem caminha sozinho = VERDE (lesões leves, aguarda atendimento).
   - PASSO 2 — RESPIRA? Para quem não anda, verifique respiração. Se NÃO respira, abra a via aérea (elevação do queixo). Se continuar sem respirar = PRETO (óbito/expectante em cenário de recursos esgotados). Se voltou a respirar = VERMELHO (imediato).
   - PASSO 3 — FREQUÊNCIA RESPIRATÓRIA: Se respira acima de 30 incursões por minuto = VERMELHO.
   - PASSO 4 — PERFUSÃO (CIRCULAÇÃO): Aperte a unha/polpa do dedo; se a cor demorar mais de 2 segundos para voltar ou não houver pulso radial no punho = VERMELHO (controle hemorragia imediata).
   - PASSO 5 — ESTADO MENTAL: Peça um comando simples ("aperte minha mão"). Se não obedece ou está confuso = VERMELHO. Se obedece bem = AMARELO (grave, mas pode aguardar logo após os vermelhos).

3. ORDEM DE ATENDIMENTO E TRANSPORTE:
   - 1º Vermelhos (risco imediato de vida: hemorragia grave, via aérea, choque).
   - 2º Amarelos (fraturas graves, queimaduras moderadas estáveis).
   - 3º Verdes (cortes leves, escoriações — podem ajudar a cuidar uns dos outros).
""",
    ),
    (
        "0153.md",
        "saude-campo-avancada",
        "Tratamento de Feridas Infectadas, Curativos em Campo e Quando Não Suturar",
        """# Tratamento de Feridas Infectadas, Curativos em Campo e Quando Não Suturar

1. LIMPEZA CORRETA (O PASSO QUE EVITA INFECÇÃO):
   - Irrigue abundantemente com soro fisiológico 0,9% ou água fervida e resfriada (use seringa sem agulha ou saco plástico furado para fazer jato firme que remova terra e resíduos).
   - Limpe ao redor com sabão neutro ou clorexidina aquosa. Evite jogar álcool ou água oxigenada dentro de ferida aberta profunda (danifica tecido saudável e atrasa cicatrização).

2. QUANDO NÃO FECHAR / NÃO SUTURAR UMA FERIDA:
   - NUNCA feche hermeticamente (com cola ou pontos): mordidas de animais ou humanos, ferimentos perfurantes profundos (prego, faca), feridas com terra/fezes/lixo, ou feridas abertas há mais de 6–8 horas.
   - Motivo: fechar bactérias dentro da ferida causa abscesso, tétano ou gangrena. Mantenha limpa, coberta com gaze estéril úmida e troque o curativo 1 a 2 vezes ao dia (cicatrização por segunda intenção).

3. PROTOCOLO DE CAMPO COM MEL PURO OU AÇÚCAR (SEM POMADA DISPONÍVEL):
   - Mel puro de abelha (não adulterado) ou açúcar cristal limpo têm alta osmolaridade que inibe crescimento bacteriano em feridas superficiais/infectadas quando não há antibiótico tópico. Aplique camada fina, cubra com gaze limpa e troque a cada 12–24h lavando bem a cada troca.

4. SINAIS DE INFECÇÃO GRAVE E SEPSE (ALERTA VERMELHO):
   - Vermelhidão se espalhando (marque a borda com caneta para acompanhar), calor local, inchaço crescente, pus com mau cheiro, listras vermelhas subindo pelo membro, febre alta, calafrios ou confusão mental. Requer antibiótico sistêmico e atendimento médico urgente.
""",
    ),
    (
        "0154.md",
        "saude-campo-avancada",
        "Imobilização Ortopédica, Talas Improvisadas e Transporte Seguro de Feridos",
        """# Imobilização Ortopédica, Talas Improvisadas e Transporte Seguro de Feridos

1. REGRAS DE OURO DA IMOBILIZAÇÃO:
   - Imobilize na posição em que o membro foi encontrado (NUNCA tente "puxar o osso para o lugar", salvo ausência total de pulso distal em isolamento extremo).
   - A tala deve travar a articulação ACIMA e a articulação ABAIXO da fratura.
   - Sempre acolchoe entre a tala rígida (madeira, papelão dobrado, revista grossa, bastão) e a pele usando panos/roupas.
   - Cheque circulação (cor, calor, sensibilidade e pulso nos dedos) ANTES e DEPOIS de amarrar. Se ficar frio, roxo ou dormente, afrouxe imediatamente.

2. TALAS POR REGIÃO:
   - Braço/Antebraço: tala rígida acolchoada + tipoia triangular (lenço/camiseta) apoiando o punho levemente acima do cotovelo.
   - Dedo quebrado: "buddy taping" — amarre o dedo lesionado ao dedo vizinho saudável com gaze no meio.
   - Perna/Fêmur: se não houver tala longa, use a outra perna saudável como tala natural, colocando pano dobrado entre os joelhos e tornozelos e amarrando acima e abaixo da fratura (nunca em cima do osso quebrado).
   - Suspeita de coluna/pescoço (queda de altura, impacto na cabeça, formigamento): NÃO movimente a vítima, exceto risco iminente de fogo/desabamento. Estabilize a cabeça manualmente alinhada com o tronco.

3. TRANSPORTE SEGURO DE FERIDOS:
   - 1 socorrista (emergência imediata): arrasto pelas roupas/ombros ou sobre cobertor/lona mantendo coluna alinhada.
   - 2 socorristas: cadeirinha de 4 mãos (vítima consciente) ou maca improvisada com 2 varas resistentes passadas por dentro de 2 jaquetas/camisas abotoadas do avesso (teste o peso antes de colocar o ferido).
""",
    ),
    (
        "0155.md",
        "saude-campo-avancada",
        "Doenças Tropicais e Parasitárias no Brasil (Malária, Chagas, Leishmaniose, Verminoses)",
        """# Doenças Tropicais e Parasitárias no Brasil (Malária, Chagas, Leishmaniose, Verminoses)

1. MALÁRIA (REGIÃO AMAZÔNICA E ÁREAS ENDÊMICAS):
   - Sintomas: febre alta em ciclos (a cada 48h ou 72h), calafrios intensos, suor profuso, dor de cabeça forte e prostração.
   - Prevenção: mosquiteiro impregnado, tela nas janelas, repelente (DEET/Icaridina) ao entardecer e amanhecer, roupas compridas.
   - Conduta: hidratação rigorosa, controle de febre (paracetamol/dipirona; evite AAS), buscar diagnóstico/antimaláricos do SUS (tratamento gratuito e específico).

2. DOENÇA DE CHAGAS (BARBEIRO E ALIMENTOS):
   - Transmissão: fezes do inseto barbeiro em frestas de paredes/palha OU ingestão de caldo de cana/açaí moído sem higiene.
   - Prevenção: não dormir encostado em paredes de barro sem reboco, usar mosquiteiro, ferver/pasteurizar sucos artesanais de risco.

3. LEISHMANIOSE (MOSQUITO-PALHA):
   - Cutânea: ferida arredondada que não cicatriza, com bordas elevadas e fundo granuloso, geralmente indolor.
   - Visceral (Calazar): febre prolongada, perda de peso, barriga inchada (baço/fígado aumentados) e palidez. Evite acúmulo de lixo orgânico/folhas úmidas perto do abrigo (criadouro do mosquito).

4. VERMINOSES, BICHO-DE-PÉ, BERNE E MICOSE:
   - Prevenção central: água fervida/clorada, lavar mãos com sabão, andar calçado (evita ancilostomose/amarelão e bicho-de-pé), cozinhar bem carne de porco e boi.
   - Berne (larva sob a pele com orifício que respira): tampe o orifício com vaselina/pomada espessa ou toucinho por algumas horas para forçar a larva a sair em busca de ar; remova com pinça limpa sem esmagar (esmagar gera infecção severa) e limpe com antisséptico.
   - Micose/frieira: manter pés secos, trocar meias, sol direto nas roupas/calçados; pomada antifúngica (miconazol/cetoconazol) se disponível.
""",
    ),
    (
        "0156.md",
        "saude-campo-avancada",
        "Saúde da Mulher, Pós-Parto e Cuidados com Recém-Nascido (Método Canguru)",
        """# Saúde da Mulher, Pós-Parto e Cuidados com Recém-Nascido (Método Canguru)

1. HIGIENE MENSTRUAL EM CRISE (SEM ABSORVENTES COMERCIAIS):
   - Use panos de algodão limpos dobrados (lavados com água e sabão e secos ao sol forte para desinfecção UV).
   - Troque a cada 4 a 6 horas para evitar infecções urinárias e vaginais. Nunca use papel higiênico desmanchando, folhas desconhecidas ou materiais sujos internamente.

2. CUIDADOS PÓS-PARTO E ALERTA DE HEMORRAGIA:
   - Após o nascimento da placenta (nunca puxe o cordão!), massageie firmemente o útero (abaixo do umbigo) em movimentos circulares para estimular a contração e reduzir sangramento.
   - Colocar o bebê para mamar imediatamente libera ocitocina natural, ajudando o útero a contrair e estancar o sangramento.
   - ALERTA VERMELHO: encharcar mais de 1 absorvente/pano grosso por hora, coágulos muito grandes, tontura, pele fria/pálida ou febre alta dias depois (infecção puerperal) — emergência médica imediata.

3. RECÉM-NASCIDO SEM INCUBADORA (MÉTODO CANGURU):
   - Bebês perdem calor muito rápido (risco fatal de hipotermia mesmo em clima ameno).
   - Seque imediatamente ao nascer, cubra a cabeça com touca/pano e coloque o bebê pele a pele no peito nu da mãe ou do pai, cobertos juntos por um cobertor/camisa (posição canguru).
   - Coto umbilical: mantenha limpo e SECO (álcool 70% se houver; nunca coloque pó de café, teia de aranha, terra ou moedas — risco de tétano neonatal).
   - Alimentação: leite materno exclusivo sob livre demanda até 6 meses (não dê água, chá ou leite de vaca puro a recém-nascidos).
""",
    ),
    (
        "0157.md",
        "saude-campo-avancada",
        "Fitoterapia Segura Baseada em Evidência (RENISUS/SUS — Doses e Contraindicações)",
        """# Fitoterapia Segura Baseada em Evidência (RENISUS/SUS — Doses e Contraindicações)

AVISO: Só use plantas cuja identificação você tenha 100% de certeza (cultivadas ou conhecidas). Nunca substitua antibiótico ou socorro médico em quadro grave.

1. GUACO (Mikania glomerata) — TOSSE E BRONCOESPASMO LEVE:
   - Uso: expectorante e broncodilatador suave (infusão de 3 a 5 folhas frescas em 150 ml de água quente, até 3x/dia).
   - Contraindicação: NÃO usar com anticoagulantes (varfarina/AAS) nem em sangramentos ativos (contém cumarina). Evitar em menores de 1 ano.

2. ESPINHEIRA-SANTA (Maytenus ilicifolia) — GASTRITE E AZIA:
   - Uso: protetor gástrico (infusão de 1 colher de sobremesa de folhas secas em 150 ml de água, antes das refeições).
   - Contraindicação: contraindicada em gestantes e lactantes (pode reduzir leite).

3. BABOSA (Aloe vera) — USO TÓPICO APENAS:
   - Uso: gel interno transparente (sem a casca verde e sem a seiva amarela/aloína, que é irritante/laxativa tóxica) para queimaduras leves de 1º grau e assaduras. NÃO ingerir.

4. CAMOMILA (Matricaria recutita) E ERVA-CIDREIRA / MELISSA:
   - Uso: cólicas abdominais leves, ansiedade leve e auxílio ao sono (infusão tampada por 5 a 10 min para não perder óleos essenciais).

5. HORTELÃ-PIMENTA (Mentha piperita) E GENGIBRE:
   - Hortelã: alívio de gases, má digestão e dor de cabeça tensional. Evitar em bebês pequenos e refluxo grave.
   - Gengibre: excelente antiemético natural (náusea/enjoo leve — 1 fatia pequena em infusão). Moderar se usar anticoagulantes.

6. AROEIRA-DA-PRAIA (Schinus terebinthifolia) — ANTISSÉPTICO TÓPICO:
   - Uso: decocção das cascas/folhas para lavagem externa de pele/mucosas em inflamações leves (pode causar alergia de contato em pessoas sensíveis — teste em pequena área primeiro).
""",
    ),
    (
        "0158.md",
        "saude-campo-avancada",
        "Tabela de Doses Pediátricas por Peso (mg/kg) em Emergências",
        """# Tabela de Doses Pediátricas por Peso (mg/kg) em Emergências

ATENÇÃO CRÍTICA: Em crianças, NUNCA estime dose apenas pela idade — calcule SEMPRE pelo PESO (kg) e confira a concentração impressa no frasco (mg/ml). Não exceda a dose máxima diária.

1. PARACETAMOL (FEBRE E DOR — MAIS SEGURO NA SUSPEITA DE DENGUE):
   - Dose usual: 10 a 15 mg/kg por dose, a cada 6 horas (máximo 5 doses em 24h; máx. 75 mg/kg/dia).
   - Gotas 200 mg/ml (padrão Brasil): aproximadamente 1 gota por kg de peso por dose (máx. 35 gotas/dose em crianças maiores).
   - RISCO: superdose causa lesão grave no fígado.

2. DIPIRONA (FEBRE ALTA E DOR — ACIMA DE 3 MESES E > 5 KG):
   - Dose usual: 10 a 20 mg/kg por dose, a cada 6 horas.
   - Gotas 500 mg/ml (padrão Brasil): cerca de 0,5 a 0,8 gota por kg por dose (ex.: criança de 10 kg = 5 a 8 gotas).
   - Contraindicação: alergia prévia, bebês < 3 meses ou < 5 kg.

3. IBUPROFENO (FEBRE/INFLAMAÇÃO — PROIBIDO SE SUSPEITA DE DENGUE OU DESIDRATAÇÃO):
   - Dose usual: 5 a 10 mg/kg por dose, a cada 6 a 8 horas (acima de 6 meses).
   - Gotas 100 mg/ml: aproximadamente 1 gota por kg (para 5 mg/kg, metade disso).

4. SORO DE REIDRATAÇÃO ORAL (OMS — DIARREIA/VÔMITO):
   - Regra prática após cada evacuação líquida: menores de 2 anos = 50 a 100 ml; de 2 a 10 anos = 100 a 200 ml, sempre em pequenos goles/colheradas frequentes (beber rápido demais provoca vômito).
   - Sinais de desidratação grave em criança (emergência): boca muito seca, choro sem lágrimas, olhos fundos, moleira afundada, mais de 6h sem urinar, sonolência extrema.
""",
    ),
    (
        "0159.md",
        "saude-campo-avancada",
        "Primeiros Socorros Veterinários Básicos (Cães, Galinhas e Animais de Criação)",
        """# Primeiros Socorros Veterinários Básicos (Cães, Galinhas e Animais de Criação)

1. SEGURANÇA AO SOCORRER UM CÃO FERIDO:
   - Mesmo um cão dócil pode morder por dor extrema. Improvise focinheira com tira de pano/atadura envolvendo o focinho (NUNCA use focinheira se o animal estiver vomitando ou com falta de ar).

2. MEDICAMENTOS HUMANOS TÓXICOS PARA CÃES E GATOS (NUNCA DAR!):
   - PARACETAMOL e IBUPROFENO: altamente tóxicos e frequentemente FATAIS para cães e gatos (especialmente gatos!).
   - Alimentos proibidos para cães: chocolate, uva/passa, cebola, alho em excesso, xilitol (adoçante) e ossos cozidos (lascam e perfuram o intestino).

3. EMERGÊNCIAS COMUNS EM CÃES:
   - Hemorragia: pressão direta com gaze/pano limpo por 5 a 10 minutos, igual em humanos.
   - Golpe de calor (hipertermia): sombra, ventilação e panos molhados com água fresca (não gelada) nas patas, barriga e virilha.
   - Ferimentos leves: lavar com soro fisiológico ou água limpa e sabão neutro; manter limpo e impedir o animal de lamber (colar improvisado com balde plástico recortado).

4. AVES E ANIMAIS DE CRIAÇÃO (GALINHAS/CABRAS):
   - Isolamento imediato (quarentena): qualquer ave apática, com penas arrepiadas ou secreção respiratória deve ser separada do restante do plantel imediatamente para evitar perda total.
   - Água limpa renovada diariamente e cama seca (maravalha/palha) previnem 80% das doenças em criações de quintal.
""",
    ),
    # === 3. COMIDA (0160 - 0167) ===
    (
        "0160.md",
        "comida-longo-prazo",
        "Guia de PANCs Brasileiras Seguras (Ora-pro-nóbis, Taioba, Beldroega, Mandioca)",
        """# Guia de PANCs Brasileiras Seguras (Ora-pro-nóbis, Taioba, Beldroega, Mandioca)

REGRA DE SEGURANÇA: Só consuma se tiver certeza absoluta da espécie e fizer o preparo correto. Nunca confie em identificação por foto para plantas silvestres desconhecidas.

1. ORA-PRO-NÓBIS (Pereskia aculeata):
   - Trepadeira rústica com espinhos nos ramos e folhas suculentas verde-brilhantes.
   - Rica em proteína vegetal (~20–25% na folha seca), ferro e fibras. Consome-se refogada, em sopas ou farinha seca.

2. TAIOBA VERDADEIRA vs TAIOBA BRAVA / INHAME-BRANCO (CUIDADO!):
   - Taioba comestível (Xanthosoma taioba): folha verde-clara uniforme, caule verde (nunca roxo/manchado) e o corte em "V" da base da folha vai ATÉ o talo (pecíolo), com linha marginal contínua na borda.
   - SEMPRE COZINHE BEM (refogada ou fervida, descartando a primeira água) para eliminar cristais de oxalato de cálcio que causam ardência severa na garganta. Se houver dúvida se é taioba verdadeira, NÃO COMA.

3. BELDROEGA (Portulaca oleracea) E DENTE-DE-LEÃO:
   - Beldroega: planta rasteira comum em quintais e calçadas, folhas gordinhas em formato de gota, talo avermelhado, sem látex branco (se soltar leite branco ao quebrar o talo, é sósia tóxica — DESCARTE!). Rica em ômega-3; coma refogada.
   - Dente-de-leão (Taraxacum): folhas recortadas em roseta rente ao chão, flor amarela única em haste oca. Folhas jovens comestíveis refogadas; raiz torrada faz substituto de café.

4. MANDIOCA MANSA (AIPIM/MACAXEIRA) vs MANDIOCA BRAVA:
   - Mandioca brava contém alto teor de ácido cianídrico (veneno mortal se apenas cozida!).
   - Para tornar mandioca brava segura: descasque, rale, esprema bem toda a água (manipueira — altamente tóxica para humanos e animais), deixe fermentar/secar e torre completamente no fogo (farinha) ou ferva a manipueira por dias (tucupi). Na dúvida, trate toda mandioca desconhecida como brava.
""",
    ),
    (
        "0161.md",
        "comida-longo-prazo",
        "Teste Universal de Comestibilidade (Último Recurso) e Sinais de Descarte Imediato",
        """# Teste Universal de Comestibilidade (Último Recurso) e Sinais de Descarte Imediato

AVISO: Só utilize este protocolo em risco real de inanição absoluta (dias sem nenhuma outra fonte alimentar). NUNCA faça este teste com cogumelos/fungos.

1. REGRAS DE DESCARTE IMEDIATO (NEM TESTE — EVITE):
   - TODOS os cogumelos e fungos silvestres (alguns destroem o fígado em 24–72h sem dar gosto ruim).
   - Plantas com seiva leitosa (látex branco) ou descolorida (exceto espécies 100% conhecidas como mamão/figo).
   - Cheiro de amêndoa amarga (sinal de cianeto).
   - Folhas em grupos de três brilhantes, vagens/feijões silvestres desconhecidos, bulbos sem cheiro de cebola/alho, frutos brancos ou amarelos desconhecidos.
   - Plantas crescendo em beira de estrada movimentada, lixo industrial ou esgoto.

2. PROTOCOLO DE TESTE UNIVERSAL (24 HORAS, 1 PARTE POR VEZ):
   - Separe a planta em partes (folha, talo, raiz, fruto) e teste APENAS UMA parte por vez. Não coma nada além de água limpa durante o teste.
   - 1) Pele (15 min): esmague e esfregue no interior do antebraço ou punho. Ardeu, coçou ou ficou vermelho? DESCARTE.
   - 2) Lábio (3 min): encoste um pedacinho cozido (cozinhar reduz muitas toxinas) na borda do lábio. Formigamento ou queimação? DESCARTE.
   - 3) Língua (15 min): coloque na língua sem mastigar; depois mastigue sem engolir por 15 min. Amargor intenso, sabor de sabão ou dormência? CUSPIR e DESCARTE.
   - 4) Pequena ingestão (8 horas): engula uma pequena porção (~1 colher de chá) e aguarde 8 horas. Se houver náusea, cólica, diarreia ou tontura, induza vômito se recente, hidrate-se e DESCARTE.
   - 5) Porção moderada (8 horas): se zero sintomas, coma 1/4 de xícara da mesma parte preparada igual e aguarde mais 8 horas. Só então considere tolerável.
""",
    ),
    (
        "0162.md",
        "comida-longo-prazo",
        "Fermentação Natural (Lactofermentação), Conservas e Defumação Sem Energia",
        """# Fermentação Natural (Lactofermentação), Conservas e Defumação Sem Energia

1. LACTOFERMENTAÇÃO DE VEGETAIS (SEM GELADEIRA E SEM VINAGRE):
   - Bactérias benéficas (Lactobacillus) produzem ácido lático que conserva repolho (chucrute), cenoura, pepino, beterraba e vagem por meses e preserva vitamina C.
   - Proporção segura de salmoura: 2% a 3% de sal (20 a 30 g de sal sem iodo, se possível, para cada 1 kg de vegetal ou 1 litro de água limpa).
   - Regra vital: os vegetais devem ficar 100% SUBMERSOS na salmoura (use peso limpo de vidro/pedra fervida). Deixe em vidro tampado frouxamente (para gás escapar) à sombra por 5 a 14 dias.
   - Cheiro agradável ácido = seguro. Mofo colorido (preto/verde/rosa) ou cheiro podre = DESCARTE TUDO.

2. CONSERVA EM VINAGRE E ÓLEO/GORDURA (CONFIT):
   - Picles em vinagre: ferva partes iguais de vinagre (mín. 4–5% acidez) e água + sal e despeje quente sobre vegetais limpos em vidro esterilizado.
   - Confit (carne na lata de banha — tradição brasileira): cozinhe carne de porco em pedaços bem salgados em banha até evaporar TODA a água da carne; guarde totalmente coberta pela banha solidificada em pote limpo e fresco. Sem água e sem oxigênio, dura semanas/meses.

3. DEFUMAÇÃO IMPROVISADA (CONSERVAÇÃO DE CARNES E PEIXES):
   - Primeiro salgue a carne em tiras finas (máx. 1 a 2 cm) por 12–24h para retirar umidade.
   - Monte um defumador com tambor, tripé coberto por lona/folhas ou buraco inclinado no solo (fogo a 1 metro de distância conectado por túnel de terra para fumaça fria).
   - Use apenas madeira dura/frutífera seca (goiabeira, laranjeira, eucalipto seco sem tinta). NUNCA use pinus resinoso ou madeira tratada/envernizada. Defume por 12 a 24h até ficar seca e firme.
""",
    ),
    (
        "0163.md",
        "comida-longo-prazo",
        "Desidratação Solar, Farinhas de Sobrevivência, Charque e Pemmican",
        """# Desidratação Solar, Farinhas de Sobrevivência, Charque e Pemmican

1. DESIDRATAÇÃO SOLAR CASEIRA:
   - Retirar a água dos alimentos impede fungos e bactérias. Corte frutas (banana, maçã, manga), tomate ou ervas em fatias finas uniformes (3 a 5 mm).
   - Disponha sobre tela limpa (sombrite/mosquiteiro) elevada do chão para circular ar por baixo e por cima, coberta com tela fina contra moscas. Recolha à noite para não pegar orvalho.
   - Ponto seco: dobra sem soltar gota de umidade (frutas) ou quebra fácil (ervas/folhas). Guarde em pote hermético.

2. CARNE DE SOL E CHARQUE (CARNE SECA):
   - Corte carne magra em mantas finas (2 cm), faça cortes rasos e esfregue sal grosso abundante em toda a superfície (cerca de 15% a 20% do peso da carne).
   - Deixe escorrer o líquido (salmoura) em local protegido de moscas por 24–48h, virando e trocando o sal se ficar encharcado; depois pendure ao sol e vento protegido com tela até secar bem. Para consumir, dessalgue em várias trocas de água.

3. PEMMICAN (RAÇÃO DE ALTÍSSIMA CALORIA QUE DURA MESES/ANOS):
   - 1) Seque carne magra em tiras muito finas até ficar quebradiça e triture até virar pó/farinha.
   - 2) Derreta gordura animal limpa (sebo bovino/banha) em fogo brando até evaporar toda água e coe.
   - 3) Misture 1 parte de pó de carne seca + 1 parte de gordura derretida (opcional: pitada de sal e fruta bem seca picada). Molde em barras e deixe esfriar. Embalado seco, fornece energia densa sem precisar cozinhar.

4. FARINHAS DE SOBREVIVÊNCIA:
   - Banana verde seca ao sol e pilada, milho torrado pilado (paçoca/fubá) e mandioca torrada rendem farinhas que duram meses e viram mingau nutritivo rapidamente com água quente.
""",
    ),
    (
        "0164.md",
        "comida-longo-prazo",
        "Armazenamento de Grãos por 1 a 10 Anos (Garrafa PET, Controle de Pragas e FIFO)",
        """# Armazenamento de Grãos por 1 a 10 Anos (Garrafa PET, Controle de Pragas e FIFO)

1. MELHORES ALIMENTOS PARA ESTOQUE DE LONGO PRAZO:
   - Arroz branco (dura 5–10+ anos; arroz integral rança rápido pelo óleo), feijão seco (2–5 anos), lentilha, milho de pipoca/grão, macarrão seco, aveia, açúcar, sal (validade infinita se seco), mel puro (validade infinita), óleo vegetal (1–2 anos — rotacionar), leite em pó e sardinha/atum enlatados.

2. TÉCNICA DA GARRAFA PET (BARATA E EFICAZ NO BRASIL):
   - Use garrafas PET de refrigerante (mais grossas que as de água), lavadas e 100% SECAS (qualquer gota de água mofa tudo!).
   - Coloque uma camada de arroz/feijão, bata a garrafa no chão para compactar e tirar o ar.
   - Controle tradicional de gorgulho/caruncho: adicione 2 a 3 dentes de alho com casca (inteiros, sem machucar) ou folhas secas de louro intercalados (ou 1 absorvedor de oxigênio de 100cc se tiver). Encha até a boca sem deixar espaço de ar e feche firmemente vedando a tampa com fita isolante ou parafina derretida.
   - Etiquete com DATA DE ENVASE e guarde em local escuro, fresco e longe do chão (evita umidade e roedores).

3. MÉTODO FIFO (PRIMEIRO QUE ENTRA, PRIMEIRO QUE SAI):
   - Sempre consuma os pacotes mais antigos na cozinha do dia a dia e reponha atrás com compras novas. Nunca estoque o que sua família não sabe comer ou preparar.
   - Se o feijão antigo ficar duro para cozinhar: deixe de molho 12h com 1 pitada de bicarbonato de sódio (enxágue antes de cozinhar) ou use panela de pressão / panela térmica.
""",
    ),
    (
        "0165.md",
        "comida-longo-prazo",
        "Micro-Agricultura Urbana, Brotos em 5 Dias, Compostagem e Sementes Crioulas",
        """# Micro-Agricultura Urbana, Brotos em 5 Dias, Compostagem e Sementes Crioulas

1. BROTOS EM POTE DE VIDRO (COMIDA FRESCA EM 4 A 6 DIAS SEM TERRA E SEM SOL):
   - Use grãos inteiros não tratados: feijão moyashi/comum, lentilha, grão-de-bico, trigo, alfafa ou girassol com casca.
   - Deixe 2 colheres de sopa de grãos de molho em água limpa por 8–12h. Escorra usando gaze/tela presa com elástico na boca do vidro.
   - Enxágue e escorra bem 2 vezes ao dia (manhã e noite), deixando o vidro inclinado de boca para baixo na sombra para não acumular água. Em 4–6 dias os brotos multiplicam volume e vitaminas (ferva rapidamente brotos de feijão comum antes de comer).

2. REBROTA E HORTA EM BALDES (APARTAMENTO OU QUINTAL):
   - Rebrota rápida: base da cebolinha, alho-poró, alface, cenoura (rama comestível) e broto de batata-doce em água/terra.
   - Baldes de 10–20L com furos de drenagem no fundo + camada de pedras + terra misturada com composto/folhas secas. Cubra o solo com palha/folha seca (reduz evaporação em 60%).

3. COMPOSTAGEM SIMPLES E SEMENTES CRIOULAS:
   - Composto: alterne 1 parte de restos vegetais crus (cascas, borra de café — sem carne/óleo) com 2 partes de material seco (folhas secas, papelão rasgado, serragem limpa). Mantenha úmido como esponja torcida e revolva semanalmente.
   - Sementes: prefira sementes crioulas/não-híbridas (híbridas F1 não reproduzem bem na geração seguinte). Seque sementes maduras à sombra ventilada sobre papel e guarde em vidro seco com sílica ou arroz torrado.
""",
    ),
    (
        "0166.md",
        "comida-longo-prazo",
        "Culinária de Apagão: Panela Térmica (Haybox) e Pão Sem Fermento Comercial (Levain)",
        """# Culinária de Apagão: Panela Térmica (Haybox) e Pão Sem Fermento Comercial (Levain)

1. PANELA TÉRMICA IMPROVISADA (HAYBOX — ECONOMIZA ATÉ 70% DE GÁS/LENHA):
   - Como fazer: forre uma caixa de papelão, caixa térmica (isopor) ou baú com cobertores grossos, jornal amassado, palha seca ou roupas velhas deixando um ninho justo para a panela.
   - Como usar: deixe arroz ou feijão (já demolhado) ferver em fogo normal por apenas 10 a 15 minutos com tampa fechada. Retire do fogo SEM abrir a tampa, envolva rápido em pano seco e feche dentro da caixa isolada por 1h (arroz) a 3–4h (feijão/sopas). O calor retido termina o cozimento sem gastar fogo.

2. PÃO DE FRIGIDEIRA SEM FORNO E SEM FERMENTO BIOLÓGICO:
   - Pão ázimo rápido (emergência): 2 xícaras de farinha de trigo + 1/2 colher de chá de sal + 2 colheres de óleo/azeite + cerca de 3/4 xícara de água morna. Sove 5 min, abra discos finos e asse em frigideira seca tampada por 2–3 min de cada lado em fogo baixo.

3. FERMENTO NATURAL (LEVAIN) SÓ COM FARINHA E ÁGUA:
   - Dia 1: misture 50 g de farinha + 50 ml de água filtrada/fervida fria em vidro tampado frouxamente em temperatura ambiente.
   - Dias 2 a 6: uma vez ao dia, descarte metade e alimente com +50 g de farinha e +50 ml de água. Quando borbulhar forte e dobrar de tamanho em 4–6h com cheiro levemente ácido/frutado, está pronto para fazer pães indefinidamente sem comprar fermento.
""",
    ),
    (
        "0167.md",
        "comida-longo-prazo",
        "Fontes Alternativas de Água (Bambu, Condensação, Chuva Urbana e Risco Químico)",
        """# Fontes Alternativas de Água (Bambu, Condensação, Chuva Urbana e Risco Químico)

1. RESERVATÓRIOS OCULTOS DENTRO DE CASA EM APAGÃO:
   - Caixa d'água (feche o registro de entrada para não voltar água contaminada da rua se a pressão cair), tubulação interna (abra a torneira mais baixa da casa e uma alta para entrar ar), caixa acoplada do vaso sanitário (APENAS o reservatório superior limpo, nunca o vaso, e somente se não tiver pastilha química), água de aquecedor/boiler e água de frutas/enlatados.

2. FONTES NATURAIS ALTERNATIVAS:
   - Orvalho matinal: amarre panos limpos nos tornozelos e caminhe por capim alto ao amanhecer, torcendo o pano em um recipiente (evite áreas com agrotóxico).
   - Bambu verde: sacuda gomos de bambu grosso; se ouvir água dentro, faça pequeno furo na base do gomo e drene (ferva/clore antes de beber).
   - Transpiração vegetal: amarre saco plástico transparente limpo em galho folhoso não-tóxico exposto ao sol com pedrinha no fundo para acumular gotas.

3. RISCO QUÍMICO E INDUSTRIAL EM ÁREAS URBANAS:
   - Fervura e cloro matam bactérias/vírus/parasitas, mas NÃO removem gasolina, óleo, metais pesados, esgoto industrial ou agrotóxicos!
   - Evite água com filme oleoso na superfície, espuma persistente, cheiro químico/solvente ou vegetação morta nas margens. Para reduzir contaminantes orgânicos leves, use filtração em carvão ativado após decantação — mas priorize sempre água da chuva descartando os primeiros 5–10 minutos de escoamento do telhado.
""",
    ),
    # === 4. ITENS PRO FIM DO MUNDO (0168 - 0175) ===
    (
        "0168.md",
        "itens-fim-do-mundo",
        "Kit EDC (Every Day Carry — Itens de Bolso Para o Dia a Dia)",
        """# Kit EDC (Every Day Carry — Itens de Bolso Para o Dia a Dia)

1. CONCEITO DO EDC:
   - É o que está com você TODOS OS DIAS no bolso ou mochila diária — porque emergências (apagão, pane no metrô, temporal, acidente) quase nunca acontecem quando você está em casa.

2. LISTA ESSENCIAL DE BOLSO / MOCHILA DIÁRIA:
   - Iluminação: mini lanterna LED resistente (pilha AA/AAA ou USB-C) — não dependa só da bateria do celular.
   - Fogo: 1 isqueiro BIC confiável (fita isolante enrolada ao redor do corpo serve de reserva e trava o botão).
   - Corte/Ferramenta: canivete dobrável ou mini alicate multifunção (respeite regras locais de transporte).
   - Sinalização e Emergência: apito de alto decibel (funciona quando a voz acaba), par de luvas descartáveis, 2 curativos e 1 analgésico pessoal.
   - Dinheiro e Documentos: dinheiro em notas trocadas (quando Pix e maquininhas caem, só papel-moeda funciona) + cópia plastificada de RG/CPF, tipo sanguíneo, alergias e telefones de emergência escritos em papel.
   - Energia: powerbank carregado (10.000 mAh) + cabo curto de qualidade.
""",
    ),
    (
        "0169.md",
        "itens-fim-do-mundo",
        "Kit BOB (Mochila 72 Horas por Perfil: Adulto, Criança, Idoso e Pet)",
        """# Kit BOB (Mochila 72 Horas por Perfil: Adulto, Criança, Idoso e Pet)

1. REGRA DE PESO DA MOCHILA DE FUGA (BOB — BUG-OUT BAG):
   - Peso máximo recomendado: 15% a 20% do peso corporal (ex.: pessoa de 75 kg = máx. 11 a 15 kg). Se você não consegue caminhar 5 km com ela, está pesada demais.

2. NÚCLEO ADULTO (72 HORAS):
   - Água: mínimo 2 a 3 litros + cantil metálico (pode ir ao fogo) + filtro portátil ou frasco de hipoclorito 2,5%.
   - Comida (sem precisar cozinhar): 6.000 kcal leves (barras de cereal/proteína, amendoim/paçoca, atum em sachê, chocolate amargo, mel em sachê).
   - Abrigo/Calor: cobertor térmico aluminizado, capa de chuva resistente (poncho), lona leve 2x3m + 10m de paracord, 1 troca completa de roupa seca em saco plástico vedado + 2 pares extras de meia.
   - Fogo/Luz/Comms: 2 isqueiros + pederneira, lanterna de cabeça + pilhas extras, rádio AM/FM/SW a pilha ou manivela, mapa físico da região.
   - Saúde/Higiene: kit trauma básico (gaze, atadura, torniquete, esparadrapo, clorexidina), álcool gel, papel higiênico em saco zip, máscaras N95/PFF2.

3. ADAPTAÇÕES POR PERFIL:
   - Criança/Bebê: fraldas para 3 dias, fórmula/papinha pronta, remédio pediátrico (antitérmico/soro), pulseira/etiqueta com nome e telefone dos pais, 1 brinquedo pequeno para acalmar.
   - Idoso: receita médica impressa + estoque de 7 a 15 dias dos remédios contínuos, óculos reserva, pilhas de aparelho auditivo.
   - Pet: coleira com identificação, guia firme, ração porcionada para 3 dias, pote dobrável e cópia da carteira de vacinação.
""",
    ),
    (
        "0170.md",
        "itens-fim-do-mundo",
        "Kit Bug-In (Abrigo Residencial de 15 a 90 Dias e Banheiro Seco em Apartamento)",
        """# Kit Bug-In (Abrigo Residencial de 15 a 90 Dias e Banheiro Seco em Apartamento)

1. POR QUE ABRIGAR-SE EM CASA É A PRIMEIRA OPÇÃO:
   - Na maioria das crises (apagões, colapso logístico, greves, epidemias, tempestades), ficar em casa é mais seguro que virar refugiado na estrada — desde que a casa esteja preparada.

2. PILARES DO ESTOQUE RESIDENCIAL (15 A 90 DIAS):
   - Água: mínimo 3 a 4 litros por pessoa/dia (beber + cozinhar + higiene mínima). Para 2 pessoas por 15 dias = 90 a 120 litros em bombonas alimentícias ou galões + filtro de barro/gravidade + hipoclorito 2,5%.
   - Alimentação: base de 2.000 kcal/pessoa/dia em grãos secos (arroz, feijão, macarrão, aveia), proteínas enlatadas/secas, óleo, sal, açúcar, leite em pó, café e multivitamínico.
   - Cozimento sem rede: 1 botijão P13 reserva (armazenado ventilado) OU fogareiro portátil com cartuchos/álcool gel + panela térmica (haybox).
   - Energia e Luz: lanternas recarregáveis, velas de 7 dias em recipientes seguros, pilhas AA/AAA em quantidade, painel solar portátil 20–50W + powerbanks.

3. BANHEIRO SECO DE EMERGÊNCIA EM APARTAMENTO (SEM ÁGUA):
   - NUNCA use o vaso sanitário normal sem descarga — entope rápido e traz risco biológico.
   - Sistema de 2 baldes (20 litros com tampa firme):
     * Balde 1 (Urina): despeje em ralo/vaso com pouca água ou dilua; separar urina das fezes elimina 90% do mau cheiro!
     * Balde 2 (Fezes): forre com 2 sacos de lixo reforçados + assento improvisado; após cada uso, cubra completamente com serragem, areia de gato, terra seca ou cinzas + fina camada de cal hidratada. Feche bem a tampa e amarre os sacos ao encher metade.
""",
    ),
    (
        "0171.md",
        "itens-fim-do-mundo",
        "Kit Carro (Get Home Bag — Sobrevivência e Pane em Estradas)",
        """# Kit Carro (Get Home Bag — Sobrevivência e Pane em Estradas)

1. REGRA DO TANQUE:
   - Nunca deixe o combustível cair abaixo de MEIO TANQUE. Em crises, filas de posto travam em menos de 2 horas ou bombas param sem energia elétrica.

2. KIT MECÂNICO E RESGATE VEICULAR:
   - Cabo de chupeta grosso (ou auxiliar de partida portátil carregado), compressor 12V, kit reparo de pneu (macarrão), fusíveis reserva, fita silver tape, abraçadeiras (enforca-gato), luvas de raspa, lanterna magnética, martelo quebra-vidro + corta-cinto ao alcance do motorista (NUNCA no porta-malas!).
   - Triângulo, colete refletivo, corda/cinta de reboque, galão homologado vazio (ou com estabilizador se seguro) e extintor válido.

3. GET HOME BAG (PARA VOLTAR A PÉ PARA CASA SE O CARRO PARAR):
   - Um par de tênis/bota confortável + meias grossas (você pode estar de sapato social/chinelo no trabalho).
   - 2 litros de água (troque a cada 3 meses pelo calor do porta-malas) + comida que NÃO derrete no calor (amendoim, castanhas, biscoito água e sal, atum em lata).
   - Cobertor térmico, capa de chuva, boné, protetor solar, mapa rodoviário de papel da sua cidade/estado e dinheiro trocado para pedágio/ônibus/ajuda.
""",
    ),
    (
        "0172.md",
        "itens-fim-do-mundo",
        "Farmácia de Guerra (Lista Real de Compras no Brasil e Controle de Validade)",
        """# Farmácia de Guerra (Lista Real de Compras no Brasil e Controle de Validade)

1. TRAUMA E CURATIVOS (CONTROLE DE HEMORRAGIA E INFECÇÃO):
   - Torniquete comercial de qualidade (CAT ou SOFTT — nunca improvisar se puder ter um real), gazes estéreis abundantes, ataduras de crepom, esparadrapo micropore e comum, soro fisiológico 0,9% (vários frascos pequenos de 100 ml abrem sem contaminar o resto), clorexidina degermante e aquosa (melhor que álcool em ferida), luvas nitrílicas, tesoura ponta romba, pinça fina, termômetro analógico (não depende de pilha!).

2. MEDICAMENTOS ISENTOS DE PRESCRIÇÃO (MIP — FARMÁCIAS DO BRASIL):
   - Febre e dor: Paracetamol e Dipirona (comprimido e gotas se houver crianças).
   - Anti-inflamatório (evitar na dengue): Ibuprofeno.
   - Alergia / Picada: Loratadina ou Dexclorfeniramina (Polaramine).
   - Estômago / Vômito / Diarreia: Sais de Reidratação Oral (SRO — muitos envelopes!), Simeticona, antiácido/Omeprazol, Loperamida (uso pontual só se sem febre/sangue nas fezes).
   - Pele/Olhos: pomada antibiótica tópica (neomicina+bacitracina), antifúngica (miconazol), colírio lubrificante, pomada para queimadura leve/assadura.

3. MEDICAMENTOS CONTROLADOS / CONTÍNUOS:
   - Converse com seu médico para manter margem de segurança (15 a 30 dias extras) de remédios de uso contínuo (pressão, diabetes, tireoide, coração, epilepsia, asma). Guarde receitas atualizadas impressas.
   - Armazene tudo em caixa opaca, seca, fresca (longe do banheiro úmido!) e revise validades a cada 6 meses.
""",
    ),
    (
        "0173.md",
        "itens-fim-do-mundo",
        "Kit Ferramentas, Manutenção e Reparos de Emergência Sem Energia",
        """# Kit Ferramentas, Manutenção e Reparos de Emergência Sem Energia

1. FERRAMENTAS MANUAIS QUE NÃO DEPENDEM DE ELETRICIDADE:
   - Alicate multifunção + alicate universal e de corte, jogo de chaves de fenda/Philips/canhão, chave inglesa ajustável, martelo/pé-de-cabra pequeno (útil também para resgate em portas travadas), serra manual dobrável (poda/lenha), facão ou machadinha + pedra de amolar dupla face.

2. CONSUMÍVEIS QUE RESOLVEM 90% DOS REPAROS:
   - Fita silver tape (lona/telhado/vedação), fita isolante, fita veda-rosca (encanamento), arame recozido (amarração estrutural que não queima no fogo), abraçadeiras plásticas (enforca-gato) de vários tamanhos, corda paracord 550 (30 m), cola epóxi bicomponente (Durepoxi/Araldite), pregos e parafusos sortidos, lona plástica grossa (mín. 4x4m).

3. MANUTENÇÃO PREVENTIVA DE EQUIPAMENTOS:
   - Guarde pilhas FORA das lanternas e rádios de reserva (evita vazamento ácido que destrói os contatos).
   - Passe fina camada de óleo mineral/vaselina em lâminas e ferramentas de aço carbono para evitar ferrugem.
   - Teste lanternas, filtros de água e fogareiros antes da crise — equipamento nunca testado na caixa pode falhar na hora H.
""",
    ),
    (
        "0174.md",
        "itens-fim-do-mundo",
        "Kit Documentos, Backup Criptografado e Gaiola de Faraday Caseira (EMP)",
        """# Kit Documentos, Backup Criptografado e Gaiola de Faraday Caseira (EMP)

1. DOCUMENTOS FÍSICOS E DIGITAIS (PASTA À PROVA D'ÁGUA):
   - Cópias físicas em saco zip duplo: RG, CPF, CNH, certidões (nascimento/casamento), carteira de vacinação, receitas médicas, escritura/contrato do imóvel, apólices, contatos escritos à mão (ninguém decora números hoje!).
   - Backup digital: pendrive metálico (preferência) com PDFs dos documentos + cópia do TaVivo, criptografado com senha forte (ex.: VeraCrypt ou 7-Zip AES-256) que a família conheça.

2. GAIOLA DE FARADAY CASEIRA (PROTEÇÃO BÁSICA CONTRA EMP / TEMPESTADE SOLAR):
   - O que proteger: rádio AM/FM/SW reserva, celular antigo com TaVivo/mapas offline, pendrive com documentos, 1 powerbank pequeno e lanterna LED simples (com pilhas embaladas separadas).
   - Como montar:
     1) Use um recipiente metálico condutor com tampa que feche com contato metal-com-metal em toda a volta (lata de tinta nova limpa, caixa de munição metálica com borracha removida ou lixeira metálica galvanizada com tampa justa).
     2) ISOLAMENTO INTERNO OBRIGATÓRIO: forre todo o interior com papelão grosso, plástico bolha ou tecido seco — nenhum aparelho pode encostar diretamente na parede de metal!
     3) Vede a junção da tampa com fita de alumínio condutiva ou múltiplas camadas de papel alumínio bem pressionadas.
   - Teste simples: coloque um celular tocando música/rádio FM dentro e feche — o sinal de rádio/rede deve cair drasticamente ou zerar (não é garantia absoluta contra EMP militar extremo, mas aumenta muito a proteção contra surtos e tempestades geomagnéticas).
""",
    ),
    (
        "0175.md",
        "itens-fim-do-mundo",
        "Rotação de Estoque, Manutenção de Equipamentos e Simulado Familiar Semestral",
        """# Rotação de Estoque, Manutenção de Equipamentos e Simulado Familiar Semestral

1. ROTINA DE REVISÃO A CADA 6 MESES (EX.: MARÇO E SETEMBRO):
   - Água: troque a água de garrafas/galões armazenados (use a antiga para regar plantas ou limpeza) e verifique validade do hipoclorito (perde força após 6–12 meses aberto!).
   - Alimentos: mova itens próximos de vencer para a despensa diária e reponha novos no fundo (FIFO).
   - Remédios: descarte vencidos que perderam eficácia crítica (insulina, adrenalina, antibióticos líquidos) e atualize doses das crianças conforme o peso atual.
   - Energia: recarregue powerbanks até 80%, teste o rádio de emergência, confira pilhas e teste o carregador solar.

2. SIMULADO FAMILIAR DE 24 HORAS SEM LUZ/INTERNET:
   - Uma vez por ano, passe um fim de semana ou 12–24 horas simulando apagão: disjuntor desligado (ou sem usar tomada/Wi-Fi), cozinhando no fogareiro, usando lanternas e consultando apenas o TaVivo offline.
   - Esse teste revela imediatamente o que falta (um abridor de latas, um adaptador, uma pilha do tamanho errado, um remédio esquecido) sem estresse real.

3. PLANO DE ENCONTRO FAMILIAR (SEM CELULAR):
   - Defina 2 pontos de encontro combinados previamente:
     * Ponto A (Local): praça, igreja ou casa de parente a até 1–2 km de casa (caso o prédio/casa fique inacessível).
     * Ponto B (Regional): cidade vizinha ou sítio de referência caso haja evacuação da área urbana.
   - Defina 1 contato fora do estado (quando redes locais congestionam, ligações/SMS interurbanos às vezes passam primeiro).
""",
    ),
]


def ensure_sources(db):
    source_ids = {}
    for key, label, topic, origin, lic in NEW_SOURCES:
        row = db.execute("SELECT id FROM sources WHERE key=?", (key,)).fetchone()
        if row:
            sid = row[0]
            db.execute(
                "UPDATE sources SET label=?, topic=?, origin=?, license=?, done=1 WHERE id=?",
                (label, topic, origin, lic, sid),
            )
        else:
            cur = db.execute(
                "INSERT INTO sources(key, label, topic, origin, docs, done, license) VALUES (?, ?, ?, ?, 0, 1, ?)",
                (key, label, topic, origin, lic),
            )
            sid = cur.lastrowid
        source_ids[key] = sid
    return source_ids


def upsert_manual(db, source_id, rel_path, title, content):
    full_path = os.path.join(TEXT_DIR, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    raw_bytes = content.strip().encode("utf-8") + b"\n"
    with open(full_path, "wb") as f:
        f.write(raw_bytes)
    byte_len = len(raw_bytes)

    row_f = db.execute("SELECT id FROM files WHERE path=?", (rel_path,)).fetchone()
    if row_f:
        file_id = row_f[0]
    else:
        file_id = db.execute("INSERT INTO files(path) VALUES (?)", (rel_path,)).lastrowid

    existing_docs = db.execute("SELECT id FROM docs WHERE file_id=?", (file_id,)).fetchall()
    for (doc_id,) in existing_docs:
        db.execute("DELETE FROM passages WHERE doc_id=?", (doc_id,))
        db.execute("DELETE FROM docs WHERE id=?", (doc_id,))

    doc_id = db.execute(
        "INSERT INTO docs(source_id, title, url, file_id, offset, length) VALUES (?, ?, '', ?, 0, ?)",
        (source_id, title, file_id, byte_len),
    ).lastrowid

    pid = db.execute(
        "INSERT INTO passages(doc_id, offset, length) VALUES (?, 0, ?)",
        (doc_id, byte_len),
    ).lastrowid
    return doc_id, pid


def rebuild_fts(db):
    """Reconstrói a tabela FTS5 (content='') de forma limpa e livre de corrupção."""
    db.execute("DROP TABLE IF EXISTS fts")
    db.execute(
        "CREATE VIRTUAL TABLE fts USING fts5("
        "title, body, content='', tokenize='porter unicode61 remove_diacritics 2')"
    )
    rows = db.execute(
        """
        SELECT p.id, d.title, f.path, p.offset, p.length
        FROM passages p
        JOIN docs d ON d.id = p.doc_id
        JOIN files f ON f.id = d.file_id
        ORDER BY p.id
        """
    ).fetchall()
    file_cache = {}
    for pid, title, rel_path, offset, length in rows:
        raw = file_cache.get(rel_path)
        if raw is None:
            fpath = os.path.join(TEXT_DIR, rel_path)
            raw = open(fpath, "rb").read() if os.path.isfile(fpath) else b""
            file_cache[rel_path] = raw
        body = raw[offset : offset + length].decode("utf-8", "replace")
        db.execute("INSERT INTO fts(rowid, title, body) VALUES (?, ?, ?)", (pid, title, body))
    db.execute("INSERT INTO fts(fts) VALUES('optimize')")


def export_pwa_library(db):
    """Exporta todos os manuais PT-BR (exceto os 73 capítulos extensos da Bíblia) para busca offline no PWA."""
    rows = db.execute(
        """
        SELECT p.id, d.title, s.label, s.topic, s.license, f.path, p.offset, p.length, s.key
        FROM passages p
        JOIN docs d ON d.id = p.doc_id
        JOIN sources s ON s.id = d.source_id
        JOIN files f ON f.id = d.file_id
        WHERE s.key != 'biblia-catolica-completa'
        ORDER BY s.id, d.id, p.id
        """
    ).fetchall()

    articles = []
    seen_docs = set()
    for pid, title, label, topic, lic, rel_path, offset, length, skey in rows:
        if (title, skey) in seen_docs:
            continue
        seen_docs.add((title, skey))
        fpath = os.path.join(TEXT_DIR, rel_path)
        if not os.path.isfile(fpath):
            continue
        with open(fpath, "rb") as f:
            f.seek(offset)
            text = f.read(length).decode("utf-8", "replace")
        articles.append(
            {
                "id": pid,
                "title": title,
                "source": label,
                "topic": topic,
                "license": lic or "",
                "text": text,
            }
        )

    payload = {
        "version": "2.0",
        "count": len(articles),
        "articles": articles,
    }
    os.makedirs(os.path.dirname(PWA_LIB_PATH), exist_ok=True)
    with open(PWA_LIB_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    size_kb = os.path.getsize(PWA_LIB_PATH) / 1024.0
    print(f"Exportado PWA offline: {PWA_LIB_PATH} ({len(articles)} artigos, {size_kb:.1f} KB)")


def main():
    os.makedirs(PTBR_DIR, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    try:
        source_ids = ensure_sources(db)
        for fname, skey, title, content in MANUALS:
            rel_path = f"ptbr/{fname}"
            upsert_manual(db, source_ids[skey], rel_path, title, content)

        # Recalcula contagem de docs por fonte e reconstrói FTS5 limpo
        for key, sid in source_ids.items():
            cnt = db.execute("SELECT COUNT(*) FROM docs WHERE source_id=?", (sid,)).fetchone()[0]
            db.execute("UPDATE sources SET docs=?, done=1 WHERE id=?", (cnt, sid))

        rebuild_fts(db)
        db.commit()
        total_docs = db.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
        total_sources = db.execute("SELECT COUNT(*) FROM sources WHERE done=1").fetchone()[0]
        print(f"Biblioteca atualizada com sucesso: {total_docs} documentos em {total_sources} fontes.")
        export_pwa_library(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
