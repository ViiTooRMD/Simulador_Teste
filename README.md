# Simulador de Custos - MVP

Estrutura inicial do simulador interno de custos e fretes.

## Responsabilidades

- `app.py`: interface Streamlit.
- `repositories/`: leitura e preparação dos arquivos.
- `services/`: regras de negócio e cálculo.
- `utils/`: funções reutilizáveis.
- `data/`: arquivos CSV de referência.

## Arquivos esperados

Coloque na pasta `data/`:

- `CIDADES.csv`
- `CUSTOS.csv`

## Execução local

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Regra atual

- Rota = origem + filial Jamef de destino.
- Peso de custeio = maior entre peso real e PM.
- Custo por peso = peso de custeio x custo/kg.
- Custo variável = valor da mercadoria x percentual.
- Custo total = custo por peso + custo variável.
