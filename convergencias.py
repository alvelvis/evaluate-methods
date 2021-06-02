import estrutura_ud
import sys
import datetime
import os

if any(not os.path.isfile(x) for x in [sys.argv[1], sys.argv[2], sys.argv[3]]):
    raise Exception("File not found.")

sistema = estrutura_ud.Corpus()
sistema.load(sys.argv[1])
sistema_guia = estrutura_ud.Corpus()
sistema_guia.load(sys.argv[2])
golden = estrutura_ud.Corpus()
golden.load(sys.argv[3])

sentences = 0
tokens = 0
attributes = ["lemma", "upos", "feats", "dephead", "deprel"]
cols = "id word lemma upos xpos feats dephead deprel deps misc".split()
convergencias = {x: [] for x in attributes}
convergencias_incorretas = {x: [] for x in attributes}
for sentid, sentence in golden.sentences.items():
    if all(sentid in x.sentences for x in [sistema, sistema_guia, golden]):
        if all(len(sentence.tokens) == len(x.sentences[sentid].tokens) for x in [sistema, sistema_guia, golden]):
            sentences += 1
            for t, token in enumerate(sentence.tokens):
                if not '-' in token.id:
                    tokens += 1
                    for attribute in attributes:
                        if (sistema.sentences[sentid].tokens[t].__dict__[attribute] == 
                        sistema_guia.sentences[sentid].tokens[t].__dict__[attribute]):
                            convergencias[attribute].append([sentid, t])
                            if (sistema.sentences[sentid].tokens[t].__dict__[attribute] !=
                            golden.sentences[sentid].tokens[t].__dict__[attribute]):
                                convergencias_incorretas[attribute].append([sentid, t])

text = "{}\n\nSistema: {}\nSistema_guia: {}\nGolden: {}\n\nSentenças: {}\nTokens: {}".format(
    datetime.datetime.now(),
    sys.argv[1],
    sys.argv[2],
    sys.argv[3],
    sentences,
    tokens,
)

for attribute in attributes:
    text += "\nConvergências de {0}: {1}\nConvergências incorretas de {0}: {2} ({3:.2f}%)".format(
        attribute,
        len(convergencias[attribute]),
        len(convergencias_incorretas[attribute]),
        len(convergencias_incorretas[attribute])*100 / len(convergencias[attribute])
    )

for attribute in attributes:
    text += "\n\n===== Convergências incorretas de {} =====".format(
        attribute.upper()
    )
    for convergencia in convergencias_incorretas[attribute]:
        text += "\n\n"
        text += golden.sentences[convergencia[0]].metadados_to_str()
        for t, token in enumerate(golden.sentences[convergencia[0]].tokens):
            text += "\n{}".format(">> " if t == convergencia[1] else "") + "\t".join(["{}>{}".format(
                sistema_guia.sentences[convergencia[0]].tokens[convergencia[1]].__dict__[x], 
                token.__dict__[x]
                ) if t == convergencia[1] and x == attribute else token.__dict__[x] for x in cols])

with open("convergencias_{}_{}_{}.txt".format(
    os.path.basename(os.path.splitext(sys.argv[1])[0]),
    os.path.basename(os.path.splitext(sys.argv[2])[0]),
    os.path.basename(os.path.splitext(sys.argv[3])[0])
), "w") as f:
    f.write(text)