# evaluate-methods

Corpora sendo comparados:

* Bosque-UD

Sistema: bosqueud-2.5-test_udpipe.conllu (modelo: pré-treinado (portuguese-bosque-ud-2.5-191206.udpipe))

Sistema_guia: bosqueud-2.5-test_stanza.conllu (modelo: pré-treinado (Bosque-UD 2.5))

Golden: bosqueud-2.5-test.conllu

* Petrolês 1

Sistema: Petroles_1_udpipe.conllu (modelo: pré-treinado (portuguese-bosque-ud-2.5-191206.udpipe))

Sistema_guia: Petroles_1_stanza.conllu (modelo: pré-treinado (Bosque-UD 2.5))

Golden: Petroles_1.conllu

* Petrolês 2

Sistema: Petroles_2_udpipe.conllu (modelo: Bosque-train2.6+Petroles_1.udpipe)

Sistema_guia: Petroles_2_stanza.conllu (modelo: Bosque-train2.6+Petroles_1.stanza => ICA)

Golden: Petroles_2.conllu

## Procedimentos

Tokenizar os corpora golden:

```
python3 tokenizar_conllu.py bosqueud-2.5-test.conllu bosqueud-2.5-test_tokenizado.txt
python3 tokenizar_conllu.py Petroles_1.conllu Petroles_1_tokenizado.txt
python3 tokenizar_conllu.py Petroles_2.conllu Petroles_2_tokenizado.txt
```

Anotar com UDPipe:

```
python3 udpipe_vertical.py portuguese-bosque-ud-2.5-191206.udpipe bosqueud-2.5-test_tokenizado.txt bosqueud-2.5-test_udpipe.conllu
python3 udpipe_vertical.py portuguese-bosque-ud-2.5-191206.udpipe Petroles_1_tokenizado.txt Petroles_1_udpipe.conllu
python3 udpipe_vertical.py Bosque-train2.6+Petroles_1.udpipe Petroles_2_tokenizado.txt Petroles_2_udpipe.conllu
```

Anotar com Stanza:

```
python3 stanza_tokenized.py bosqueud-2.5-test_tokenizado.txt bosqueud-2.5-test_stanza.conllu
python3 stanza_tokenized.py Petroles_1_tokenizado.txt Petroles_1_stanza.conllu
<modelo_ICA Petroles_2_tokenizado.txt Petroles_2_B.conllu>
```

evaluate_methods:

```
python3 evaluate_methods_Passiva.py bosqueud-2.5-test_udpipe.conllu bosqueud-2.5-test_stanza.conllu bosqueud-2.5-test.conllu
python3 evaluate_methods_Passiva.py Petroles_1_udpipe.conllu Petroles_1_stanza.conllu Petroles_1.conllu
python3 evaluate_methods_Passiva.py Petroles_2_udpipe.conllu Petroles_2_B.conllu Petroles_2.conllu
```

<< renomear Petroles_2_B para Petroles_2_stanza? >>

conll18_metrics:

```
python3 conll18_ud_eval.py -v bosqueud-2.5-test.conllu bosqueud-2.5-test_stanza.conllu > bosqueud-2.5_stanza.metrics
python3 conll18_ud_eval.py -v Petroles_1.conllu Petroles_1_stanza.conllu > Petroles_1_stanza.metrics
python3 conll18_ud_eval.py -v Petroles_2.conllu Petroles_2_B.conllu > Petroles_2_stanza.metrics
```

```
python3 conll18_ud_eval.py -v bosqueud-2.5-test.conllu bosqueud-2.5-test_udpipe.conllu > bosqueud-2.5_udpipe.metrics
python3 conll18_ud_eval.py -v Petroles_1.conllu Petroles_1_udpipe.conllu > Petroles_1_udpipe.metrics
python3 conll18_ud_eval.py -v Petroles_2.conllu Petroles_2_udpipe.conllu > Petroles_2_udpipe.metrics
```


