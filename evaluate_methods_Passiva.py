import os
import sys
sys.path.append("../ACDC-UD")
import estrutura_ud
import Cristian_Marneffe_Passiva as Cristian_Marneffe
import validar_UD
from pprint import pprint
from collections import defaultdict
from datetime import datetime
import itertools

if len(sys.argv) != 4:
    print("usage: evaluate_methods.py system.conllu sistema_guiamodifications.conllu goldenmodifications.conllu")
    exit()

if not os.path.isdir("EM"):
    os.mkdir("EM")

sistema = estrutura_ud.Corpus(recursivo=True)
sistema_guia = estrutura_ud.Corpus(recursivo=True)
golden = estrutura_ud.Corpus(recursivo=True)
sistema.load(sys.argv[1])
sistema_guia.load(sys.argv[2])
golden.load(sys.argv[3])

for sentid, sentence in sistema.sentences.items():
    if all(sentid in x.sentences and 
    len(x.sentences[sentid].tokens) == len(sistema.sentences[sentid].tokens) for 
    x in [sistema, sistema_guia, golden]):
        for t, token in enumerate(sentence.tokens):
            sistema.sentences[sentid].tokens[t].misc = "_"
            sistema_guia.sentences[sentid].tokens[t].misc = "_"
            golden.sentences[sentid].tokens[t].misc = "_"

#DICIONÁRIO COM TODAS AS MODIFICAÇÕES REALIZADAS
all_modifications = set()
all_modifications_lemma = set()
for sentid, sentence in golden.sentences.items():
    if (all(sentid in x.sentences for x in [sistema_guia, sistema]) and 
    all(len(sentence.tokens) == len(x.sentences[sentid].tokens) for 
    x in [sistema_guia, sistema])):
        for t, token in enumerate(sentence.tokens):
            if any(token.__dict__[x] != sistema_guia.sentences[sentid].tokens[t].__dict__[x] for 
            x in ["lemma", "upos", "feats", "deprel", "dephead"]):
                all_modifications.add(f"{sentid}<tok>{t}")
            if token.__dict__['lemma'] != sistema_guia.sentences[sentid].tokens[t].__dict__['lemma']:
                all_modifications_lemma.add(f"{sentid}<tok>{t}")

#DICIONÁRIOS COM OS ERROS APONTADOS
errors_validar_UD = set()
erros = validar_UD.validate(sistema_guia, errorList = "../ACDC-UD/validar_UD.txt").values()
#sys.stderr.write(str(erros))
for assunto in erros:
    for error in assunto:
        if error['sentence']:
            if (all(error['sentence'].sent_id in x.sentences for 
            x in [sistema, sistema_guia, golden]) and 
            all(len(error['sentence'].tokens) == len(x.sentences[error['sentence'].sent_id].tokens) for 
            x in [sistema, sistema_guia, golden])):
                errors_validar_UD.add(f"{error['sentence'].sent_id}<tok>{error['t']}")

confusion_matrix = defaultdict(set)
confusion_matrix_errors = defaultdict(set)
confusion_matrix_hit = defaultdict(lambda: defaultdict(set))
convergence = defaultdict(set)
good_convergence = defaultdict(set)
bad_convergence = defaultdict(set)

for sentid, sentence in sistema_guia.sentences.items():
    if (all(sentid in x.sentences for 
    x in [sistema_guia, sistema, golden]) and 
    all(len(sentence.tokens) == len(x.sentences[sentid].tokens) for 
    x in [sistema_guia, sistema, golden])):
        for t, token in enumerate(sentence.tokens):
            for coluna in ['deprel', 'dephead', 'upos']:
                if token.__dict__[coluna] == sistema.sentences[sentid].tokens[t].__dict__[coluna]:
                    convergence[coluna].add(f"{sentid}<tok>{t}")
                    if token.__dict__[coluna] == golden.sentences[sentid].tokens[t].__dict__[coluna]:
                        good_convergence[coluna].add(f"{sentid}<tok>{t}")
                    else:
                        bad_convergence[coluna].add(f"{sentid}<tok>{t}")
                elif token.__dict__[coluna] != sistema.sentences[sentid].tokens[t].__dict__[coluna]:
                    confusion_matrix[coluna].add(f"{sentid}<tok>{t}")
                    if golden.sentences[sentid].tokens[t].__dict__[coluna] == sistema_guia.sentences[sentid].tokens[t].__dict__[coluna]:
                        confusion_matrix_hit[coluna]['sistema_guia'].add(f"{sentid}<tok>{t}")
                    elif golden.sentences[sentid].tokens[t].__dict__[coluna] == sistema.sentences[sentid].tokens[t].__dict__[coluna]:
                        confusion_matrix_hit[coluna]['sistema'].add(f"{sentid}<tok>{t}")
                        confusion_matrix_errors[coluna].add(f"{sentid}<tok>{t}")
                    else:
                        confusion_matrix_hit[coluna]['none'].add(f"{sentid}<tok>{t}")
                        confusion_matrix_errors[coluna].add(f"{sentid}<tok>{t}")

cristian_marneffe_lexicais = []
cristian_marneffe_lexicais_dependency = []
lexical_pairs = 0
lexical_pairs_hit = 0
lexical_governor = 0
lexical_governor_hit = 0
for exemplo in Cristian_Marneffe.main(sys.argv[2], 'lexicais'):
    lexical_pairs += 1
    example_found_error = False
    deprel_groups = defaultdict(list)
    for error in exemplo['frases']:
        if (all(error['sent_id'] in x.sentences for 
        x in [sistema, sistema_guia, golden]) and 
        all(len(x.sentences[error['sent_id']].tokens) == len(x.sentences[error['sent_id']].tokens) for 
        x in [sistema, sistema_guia, golden])):
            cristian_marneffe_lexicais.append(f"{error['sent_id']}<tok>{sistema_guia.sentences[error['sent_id']].map_token_id[str(error['id1'])]}") #realmente ID1 ou ID2?
            deprel_groups[sistema_guia.sentences[error['sent_id']].tokens[sistema_guia.sentences[error['sent_id']].map_token_id[str(error['id2'])]].deprel].append(f"{error['sent_id']}<tok>{sistema_guia.sentences[error['sent_id']].map_token_id[str(error['id1'])]}")
            if (f"{error['sent_id']}<tok>{sistema_guia.sentences[error['sent_id']].map_token_id[str(error['id1'])]}" in all_modifications and 
            not example_found_error):
                example_found_error = True
                lexical_pairs_hit += 1
    deprel_groups = {
        deprel: list_of_tokens for 
        deprel, list_of_tokens in deprel_groups.items() if 
        len(deprel_groups[deprel]) > 1
        }
    lexical_governor += len(deprel_groups) - 1
    for deprel in deprel_groups:
        example_found_error = False
        for token in deprel_groups[deprel]:
            cristian_marneffe_lexicais_dependency.append(token)
            if (token in all_modifications and 
            not example_found_error):
                example_found_error = True
                lexical_governor_hit += 1
lexical_governor += lexical_pairs

cristian_marneffe_gramaticais = []
cristian_marneffe_gramaticais_dependency = []
grammatical_pairs = 0
grammatical_pairs_hit = 0
grammatical_governor = 0
grammatical_governor_hit = 0
for exemplo in Cristian_Marneffe.main(sys.argv[2], 'gramaticais'):
    grammatical_pairs += 1
    example_found_error = False
    deprel_groups = defaultdict(list)
    for error in exemplo['frases']:
        if (all(error['sent_id'] in x.sentences for 
        x in [sistema, sistema_guia, golden]) and 
        all(len(x.sentences[error['sent_id']].tokens) == len(x.sentences[error['sent_id']].tokens) for 
        x in [sistema, sistema_guia, golden])):
            cristian_marneffe_gramaticais.append(f"{error['sent_id']}<tok>{sistema_guia.sentences[error['sent_id']].map_token_id[str(error['id1'])]}") #realmente ID1 ou ID2?
            deprel_groups[sistema_guia.sentences[error['sent_id']].tokens[sistema_guia.sentences[error['sent_id']].map_token_id[str(error['id2'])]].deprel].append(f"{error['sent_id']}<tok>{sistema_guia.sentences[error['sent_id']].map_token_id[str(error['id1'])]}")
            if (f"{error['sent_id']}<tok>{sistema_guia.sentences[error['sent_id']].map_token_id[str(error['id1'])]}" in all_modifications and 
            not example_found_error):
                example_found_error = True
                grammatical_pairs_hit += 1
    deprel_groups = {deprel: list_of_tokens for deprel, list_of_tokens in deprel_groups.items() if len(deprel_groups[deprel]) > 1}
    grammatical_governor += len(deprel_groups) - 1
    for deprel in deprel_groups:
        example_found_error = False
        for token in deprel_groups[deprel]:
            cristian_marneffe_gramaticais_dependency.append(token)
            if (token in all_modifications and 
            not example_found_error):
                example_found_error = True
                grammatical_governor_hit += 1
grammatical_governor += grammatical_pairs

#PRINT das frases dos n-grams inconsistentes
def print_token(i, length, token):
    sent_id = token.split("<tok>")[0]
    t = int(token.split("<tok>")[1])
    head = sistema_guia.sentences[sent_id].tokens[t].head_token.lemma + "_" + sistema_guia.sentences[sent_id].tokens[t].head_token.deprel
    child = sistema_guia.sentences[sent_id].tokens[t].lemma + "_" + sistema_guia.sentences[sent_id].tokens[t].deprel
    head_t = int(sistema_guia.sentences[sent_id].map_token_id[sistema_guia.sentences[sent_id].tokens[t].head_token.id])
    return "{}/{} - <span style='color:red'>{}</span> <- <span style='color:blue'>{}</span>: {}<hr>".format(
        i+1,
        length,
        head,
        child,
        " ".join([
            "<span style='color:{};'>".format("red"*(x_t==head_t)+"blue"*(x_t==t)) + x.word + "</span>" for 
            x_t, x in enumerate(sistema_guia.sentences[sent_id].tokens) if not '-' in x.id
            ])
    )

with open("EM/{}_{}_{}_Passiva_n-grams-lexicais.html".format(
    sys.argv[1].rsplit('/', 1)[1].rsplit('.', 1)[0] if '/' in sys.argv[1] else sys.argv[1].rsplit('.', 1)[0],
    sys.argv[2].rsplit('/', 1)[1].rsplit('.', 1)[0] if '/' in sys.argv[2] else sys.argv[2].rsplit('.', 1)[0],
    sys.argv[3].rsplit('/', 1)[1].rsplit('.', 1)[0] if '/' in sys.argv[3] else sys.argv[3].rsplit('.', 1)[0],
), "w+") as f:
    f.write("<html><meta charset='utf-8'/><body>")
    for i, token in enumerate(cristian_marneffe_lexicais):
        f.write(print_token(i, len(cristian_marneffe_lexicais), token))
    f.write("</body></html>")

with open("EM/{}_{}_{}_Passiva_n-grams-gramaticais.html".format(
    sys.argv[1].rsplit('/', 1)[1].rsplit('.', 1)[0] if '/' in sys.argv[1] else sys.argv[1].rsplit('.', 1)[0],
    sys.argv[2].rsplit('/', 1)[1].rsplit('.', 1)[0] if '/' in sys.argv[2] else sys.argv[2].rsplit('.', 1)[0],
    sys.argv[3].rsplit('/', 1)[1].rsplit('.', 1)[0] if '/' in sys.argv[3] else sys.argv[3].rsplit('.', 1)[0]
), "w+") as f:
    f.write("<html><meta charset='utf-8'/><body>")
    for i, token in enumerate(cristian_marneffe_gramaticais):
        f.write(print_token(i, len(cristian_marneffe_gramaticais), token))
    f.write("</body></html>")

with open("EM/{}_{}_{}_Passiva_n-grams-lexicais-dependency.html".format(
    sys.argv[1].rsplit('/', 1)[1].rsplit('.', 1)[0] if '/' in sys.argv[1] else sys.argv[1].rsplit('.', 1)[0],
    sys.argv[2].rsplit('/', 1)[1].rsplit('.', 1)[0] if '/' in sys.argv[2] else sys.argv[2].rsplit('.', 1)[0],
    sys.argv[3].rsplit('/', 1)[1].rsplit('.', 1)[0] if '/' in sys.argv[3] else sys.argv[3].rsplit('.', 1)[0]
), "w+") as f:
    f.write("<html><meta charset='utf-8'/><body>")
    for i, token in enumerate(cristian_marneffe_lexicais_dependency):
        f.write(print_token(i, len(cristian_marneffe_lexicais_dependency), token))
    f.write("</body></html>")

with open("EM/{}_{}_{}_Passiva_n-grams-gramaticais-dependency.html".format(
    sys.argv[1].rsplit('/', 1)[1].rsplit('.', 1)[0] if '/' in sys.argv[1] else sys.argv[1].rsplit('.', 1)[0],
    sys.argv[2].rsplit('/', 1)[1].rsplit('.', 1)[0] if '/' in sys.argv[2] else sys.argv[2].rsplit('.', 1)[0],
    sys.argv[3].rsplit('/', 1)[1].rsplit('.', 1)[0] if '/' in sys.argv[3] else sys.argv[3].rsplit('.', 1)[0]
), "w+") as f:
    f.write("<html><meta charset='utf-8'/><body>")
    for i, token in enumerate(cristian_marneffe_gramaticais_dependency):
        f.write(print_token(i, len(cristian_marneffe_gramaticais_dependency), token))
    f.write("</body></html>")

#combinações
metodos = {
    'Erros de validação': errors_validar_UD,
    'Matriz de confusão UPOS': confusion_matrix['upos'],
    'Matriz de confusão DEPHEAD': confusion_matrix['dephead'],
    'Matriz de confusão DEPREL': confusion_matrix['deprel'],
    'N-grams gramaticais': cristian_marneffe_gramaticais,
    'N-grams lexicais': cristian_marneffe_lexicais
    }
for metodo in metodos:
    metodos[metodo] = set(metodos[metodo])
combinatoria = []
somas = defaultdict()
for i in range(len(metodos)+1):
    combinatoria.extend(list(itertools.combinations(metodos.keys(), i)))
pprint(combinatoria)

#COMEÇA A MONTAGEM DOS HTML
html = "<html><meta charset='utf-8'/><body style='width:60%; padding-bottom:100px; margin:auto; margin-top:20px;'>"
html += "<h1>Avaliação dos métodos de correção do Julgamento</h1>"
html += "Relatório gerado: {}<hr>".format(datetime.now().strftime("%d/%m/%Y, %H:%M:%S"))
html += "<h3>Sistema: {}</h3>".format(
    sys.argv[1]
    )
html += "<h3>Sistema guia (pré-correções): {}</h3>".format(
    sys.argv[2]
    )
html += "<h3>Golden (pós-correções): {}</h3>".format(
    sys.argv[3]
    )

html += "<h2>Características do corpus</h2><hr>"
html += "<table border='1'>"
html += "<tr><th>Arquivos</th><th>Sentenças</th><th>Tokens</th></tr>"
html += "<tr><td>Sistema</td><td>{}</td><td>{}</td></tr>".format(
    len(sistema.sentences),
    len([x for sentence in sistema.sentences.values() for 
        x in sentence.tokens if not '-' in x.id])
)
html += "<tr><td>Sistema guia</td><td>{}</td><td>{}</td></tr>".format(
    len(sistema_guia.sentences),
    len([x for sentence in sistema_guia.sentences.values() for 
        x in sentence.tokens if not '-' in x.id])
)
html += "<tr><td>Golden</td><td>{}</td><td>{}</td></tr>".format(
    len(golden.sentences),
    len([x for sentence in golden.sentences.values() for 
        x in sentence.tokens if not '-' in x.id])
)
html += "</table>"

html += "<hr><table border='1'>"
html += "<tr><td>Sentenças comparáveis</td><td colspan='2'>{}</td></tr>".format(
    len([x for x in golden.sentences if all(x in y for 
        y in [sistema.sentences, sistema_guia.sentences])])
)
html += "<tr><td>Tokens corrigidos</td><td colspan='2'>{}</td></tr>".format(
    len(all_modifications)
)
html += "</table><hr>"

html += "<h2>Avaliação dos métodos</h2><hr>"
html += "<table border='1'>"
html += "<tr><th>Método</th><th>Erros detectados (por token)</th><th>Verdadeiro Positivo</th><th>Falso Positivo</th><th>Precisão</th><th>Abrangência</th><th title='Erros detectados por todos os métodos DESSA linha'>Erros repetidos</th><th>Repetidos VP</th></tr>"

html += "<tr><td>Nenhum método</td><td colspan='42'>{}</td></tr>".format(
    len(all_modifications - set.union(*metodos.values()))
)

html += "<tr><td>Nenhum método (com erro de lema)</td><td colspan='42'>{}</td></tr>".format(
    len(all_modifications_lemma - set.union(*metodos.values()))
)

for combination in sorted([x for x in list(combinatoria) if x], key=lambda x: x[0]):
    html += "<tr><td>{}{}{}</td><td>{}</td><td>{}</td><td>{}</td><td>{:.2f}%</td><td>{:.2f}%</td><td>{}</td><td>{}</td></tr>".format(
        '<b>' if len(combination) == 1 else '',
        ' + '.join(combination),
        '</b>' if len(combination) == 1 else '',
        len(set.union(*[
            metodos[metodo] for metodo in combination
            ])),
        len(all_modifications.intersection(set.union(*[
            metodos[metodo] for metodo in combination
            ]))),
        len(set.union(*[
            metodos[metodo] for metodo in combination
            ]) - all_modifications),
        len(all_modifications.intersection(set.union(*[
            metodos[metodo] for metodo in combination
            ])))*100 / 
            len(set.union(*[
                metodos[metodo] for metodo in combination
                ])) if len(set.union(*[
                    metodos[metodo] for metodo in combination
                    ])) > 0 else 0,
        len(all_modifications.intersection(set.union(*[
            metodos[metodo] for metodo in combination
            ])))*100 / 
            len(all_modifications),
        len(set.intersection(*[
            metodos[metodo] for metodo in combination
            ])) if len(combination) > 1 else 'Não se aplica',
        len(all_modifications.intersection(set.intersection(*[
            metodos[metodo] for metodo in combination
            ]))) if len(combination) > 1 else 'Não se aplica'
    )

html += "</table><hr>"

for coluna in ['upos', 'deprel', 'dephead']:
    if sys.argv[1] != sys.argv[2]:
        html += "<h2>Detalhe: matriz de confusão de {}</h2><hr>".format(coluna.upper())
        html += "<table border='1'>"
        html += "<tr><th>Coluna</th><th>Divergências</th><th>sistema_guia estava correto (não é erro)</th><th>Não é erro %</th><th>sistema estava correto (erro de fato)</th><th>Ninguém estava correto (erro de fato)</th><th>Erro de fato %</th><th>sistema estava correto %</th><th>Precisa de correção cuidadosa (ninguém estava correto)</th></tr>"
        html += "<tr><td>{}</td><td>{}</td><td>{}</td><td>{:.2f}%</td><td>{}</td><td>{}</td><td>{:.2f}%</td><td>{:.2f}%</td><td>{:.2f}%</td></tr>".format(
            coluna,
            len(confusion_matrix[coluna]),
            len(confusion_matrix_hit[coluna]['sistema_guia']),
            len(confusion_matrix_hit[coluna]['sistema_guia'])*100 / 
                len(confusion_matrix[coluna]),
            len(confusion_matrix_hit[coluna]['sistema']),
            len(confusion_matrix_hit[coluna]['none']),
            (len(confusion_matrix_hit[coluna]['sistema']) + 
                len(confusion_matrix_hit[coluna]['none']))*100 / 
                len(confusion_matrix[coluna]),
            (len(confusion_matrix_hit[coluna]['sistema']))*100 / 
                len(confusion_matrix[coluna]),
            (len(confusion_matrix_hit[coluna]['none']))*100 / 
                len(confusion_matrix[coluna])
        )
        html += "</table><br>"

        html += "<table border='1'>"
        html += "<tr><th>Coluna</th><th>Convergências</th><th>Convergência correta</th><th>Convergência incorreta</th><th>Confiança das convergências</th></tr>"
        html += "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{:.2f}%</td></tr>".format(
            coluna,
            len(convergence[coluna]),
            len(good_convergence[coluna]),
            len(bad_convergence[coluna]),
            len(good_convergence[coluna])*100 / len(convergence[coluna])
        )
        html += "</table><br>"

        html += "<table border='1'>"
        html += "<tr><th></th><th>Dos {} tokens com erros de fato, o método X encontrou:</th><th>Dos {} tokens com convergência incorreta, o método X encontrou:</th></tr>".format(
            len(confusion_matrix_errors[coluna]),
            len(bad_convergence[coluna])
        )
        html += "<tr><td>Apenas a matriz de {}</td><td>{} ({:.2f}%)</td><td>{} ({:.2f}%)</td></tr>".format(
            coluna.upper(),
            len(confusion_matrix_errors[coluna] - set.union(*[
                metodos[metodo] for metodo in metodos if metodo != "Matriz de confusão {}".format(coluna.upper())
                ])),
            len(confusion_matrix_errors[coluna] - set.union(*[
                metodos[metodo] for metodo in metodos if metodo != "Matriz de confusão {}".format(coluna.upper())
                ]))*100 / len(confusion_matrix_errors[coluna]),
            len(bad_convergence[coluna].intersection(confusion_matrix_errors[coluna]) - set.union(*[
                metodos[metodo] for metodo in metodos if metodo != "Matriz de confusão {}".format(coluna.upper())
                ])),
            len(bad_convergence[coluna].intersection(confusion_matrix_errors[coluna]) - set.union(*[
                metodos[metodo] for metodo in metodos if metodo != "Matriz de confusão {}".format(coluna.upper())
                ]))*100 / len(bad_convergence[coluna])
        )
        html += "<tr><td>Apenas qualquer matriz</td><td>{} ({:.2f}%)</td><td>{} ({:.2f}%)</td></tr>".format(
            len(confusion_matrix_errors[coluna] - set.union(*[
                metodos[metodo] for metodo in metodos if not metodo.startswith("Matriz de confusão")
                ])),
            len(confusion_matrix_errors[coluna] - set.union(*[
                metodos[metodo] for metodo in metodos if not metodo.startswith("Matriz de confusão")
                ]))*100 / len(confusion_matrix_errors[coluna]),
            len(bad_convergence[coluna].intersection(confusion_matrix_errors[coluna]) - set.union(*[
                metodos[metodo] for metodo in metodos if not metodo.startswith("Matriz de confusão")
                ])),
            len(bad_convergence[coluna].intersection(confusion_matrix_errors[coluna]) - set.union(*[
                metodos[metodo] for metodo in metodos if not metodo.startswith("Matriz de confusão")
                ]))*100 / len(bad_convergence[coluna])
        )
        html += "<tr><td>Nenhum método</td><td>{} ({:.2f}%)</td><td>{} ({:.2f}%)</td></tr>".format(
            len(confusion_matrix_errors[coluna] - set.union(*[
                metodos[metodo] for metodo in metodos
                ])),
            len(confusion_matrix_errors[coluna] - set.union(*[
                metodos[metodo] for metodo in metodos
                ]))*100 / len(confusion_matrix_errors[coluna]),
            len(bad_convergence[coluna] - set.union(*[
                metodos[metodo] for metodo in metodos
                ])),
            len(bad_convergence[coluna] - set.union(*[
                metodos[metodo] for metodo in metodos
                ]))*100 / len(bad_convergence[coluna])
        )
        for metodo in [x for x in metodos]:
            html += "<tr><td>{}</td><td>{} ({:.2f}%)</td><td>{} ({:.2f}%)</td></tr>".format(
                metodo,
                len(set.intersection(confusion_matrix_errors[coluna], metodos[metodo])),
                len(set.intersection(confusion_matrix_errors[coluna], metodos[metodo]))*100 / 
                    len(confusion_matrix_errors[coluna]),
                len(set.intersection(bad_convergence[coluna], metodos[metodo])),
                len(set.intersection(bad_convergence[coluna], metodos[metodo]))*100 / 
                    len(bad_convergence[coluna])
            )
        html += "</table><hr>"

html += "<h2>Detalhe: n-grams inconsistentes</h2><hr>"
html += "<table border='1'>"
html += "<tr><th>Tipo</th><th>Pares</th><th>Pares com pelo menos 1 token corrigido</th><th>Precisão</th><th>Pares em que o pai tem mesmo deprel (dependency context)</th><th>Pares com pelo menos 1 token corrigido quando pai tem mesmo deprel</th><th>Precisão quando o pai nos pares tem mesmo deprel</th><th>Abrangência do \"dependency context\" (comparando com os pares sem restrição de deprel no pai)</th></tr>"
html += "<tr><td>N-grams gramaticais</td><td>{}</td><td>{}</td><td>{:.2f}%</td><td>{}</td><td>{}</td><td>{:.2f}%</td><td>{:.2f}%</td></tr>".format(
    grammatical_pairs,
    grammatical_pairs_hit,
    (grammatical_pairs_hit/grammatical_pairs)*100 if grammatical_pairs > 0 else 0,
    grammatical_governor,
    grammatical_governor_hit,
    (grammatical_governor_hit/grammatical_governor)*100 if grammatical_governor > 0 else 0,
    (grammatical_governor_hit/grammatical_pairs)*100 if grammatical_pairs > 0 else 0
)
html += "<tr><td>N-grams lexicais</td><td>{}</td><td>{}</td><td>{:.2f}%</td><td>{}</td><td>{}</td><td>{:.2f}%</td><td>{:.2f}%</td></tr>".format(
    lexical_pairs,
    lexical_pairs_hit,
    (lexical_pairs_hit/lexical_pairs)*100 if lexical_pairs > 0 else 0,
    lexical_governor,
    lexical_governor_hit,
    (lexical_governor_hit/lexical_governor)*100 if lexical_governor > 0 else 0,
    (lexical_governor_hit/lexical_pairs)*100 if lexical_pairs > 0 else 0
)
html += "</table><br>"

html += '</body></html>'

with open("EM/{}_{}_{}_Passiva.html".format(
    sys.argv[1].rsplit('/', 1)[1].rsplit('.', 1)[0] if '/' in sys.argv[1] else sys.argv[1].rsplit('.', 1)[0],
    sys.argv[2].rsplit('/', 1)[1].rsplit('.', 1)[0] if '/' in sys.argv[2] else sys.argv[2].rsplit('.', 1)[0],
    sys.argv[3].rsplit('/', 1)[1].rsplit('.', 1)[0] if '/' in sys.argv[3] else sys.argv[3].rsplit('.', 1)[0]
), "w") as f:
    f.write(html)


