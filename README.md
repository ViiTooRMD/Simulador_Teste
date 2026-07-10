Simulador de Custos e Fretes - MVP
Esta versão inclui:
cálculo de custo;
cálculo de frete por faixa de peso;
peso tarifado como maior entre peso real e cubado;
ad valorem;
cálculo manual;
cálculo em lote;
exportação em Excel.
Arquivos de referência
Coloque na pasta `data/`:
`CIDADES.csv`
`CUSTOS.csv`
`TABELA_PADRAO.csv`
Regra do frete
BUSCA_DESTINO = UF + CIDADE DESTINO.
BUSCA retorna REF no arquivo de cidades.
ROTA_FRETE = ORIGEM + REF.
PESO_TARIFADO = maior entre PESO REAL e PESO CUBADO.
Até 100 kg, usa o valor fixo da faixa.
Acima de 100 kg, multiplica o peso tarifado pela tarifa/kg.
AD_VALOREM = VALOR MERCADORIA x percentual.
FRETE_PARCIAL = FRETE_PESO + AD_VALOREM.
