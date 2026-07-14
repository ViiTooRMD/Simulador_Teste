# Arquitetura de login, políticas e alçadas

## Regra funcional

- `Frete Peso` e `FV / Ad Valorem` são componentes independentes.
- A alçada é flat: cada desconto solicitado é comparado diretamente ao limite do perfil.
- O desconto ponderado é apenas um indicador da proposta e não substitui as duas validações.
- A política por região, UF e faixa define o desconto a solicitar quando o lote não informa descontos.
- A política não amplia nem reduz a alçada do usuário.
- Quando qualquer componente excede o limite, a proposta fica `BLOQUEADO`, mantém os cálculos para análise e informa o primeiro perfil superior capaz de aprová-la.
- Margens e indicadores usam `FRETE_SIMULADO`; `FRETE_TABELA` permanece disponível para auditoria.

## Ciclo da simulação

1. **Parâmetros:** origem, regra de cubagem, densidade, prazo, horizonte e excedente.
2. **Fluxo:** cotação individual ou upload da volumetria.
3. **Tabela e descontos:** matriz da tabela padrão por rota/UF/faixa, aplicação em massa ou por célula e validação de alçada.
4. **Decisão:** resultado do cenário simulado, custos, margens, impacto financeiro e segmentações analíticas.

Cada ação “salvar e avançar” registra a próxima etapa e executa um novo ciclo do Streamlit. Isso evita a alteração direta do estado do menu depois que o componente já foi renderizado.

Na etapa comercial, as condições são apresentadas em seções visíveis por UF, com uma linha por destino. As faixas exibem diretamente o valor efetivo usado no cálculo, e as células de desconto de Frete Peso e FV ficam na própria linha. A faixa acima de 100 kg é apresentada em `R$/kg` e o FV em `% da NF`.

## Cubagem

- Cliente paga cubagem: `PESO CUBADO = M³ × DENSIDADE PARAMETRIZADA`, substituindo o peso cubado recebido.
- Cliente não paga cubagem: preserva o peso cubado informado.
- Sem peso cubado: utiliza `M³ × 300 kg/m³`.
- Sem peso cubado e sem M³: bloqueia o fluxo para correção.

## Prazo de pagamento

A taxa mensal efetiva é derivada da SELIC anual de 14,25%:

`TAXA MENSAL = (1 + 0,1425)^(1/12) - 1`

`IMPACTO FINANCEIRO = FRETE SIMULADO × TAXA MENSAL × DIAS / 30`

O horizonte em meses permanece informativo até a criação do BC da simulação.

## Cadastros do MVP

- `db_Usuarios.csv`: usuário, escopo organizacional, perfil, flags de administração e atividade.
- `db_Alcadas_Desconto.csv`: hierarquia e limites máximos de Frete Peso e FV.
- `db_Politicas_Desconto.csv`: descontos por região, UF e faixa de peso.

As senhas locais usam PBKDF2-SHA256 com salt individual. Esse mecanismo atende somente ao MVP. Em produção, a autenticação deve ser delegada ao provedor corporativo (SSO/Identity Platform). O BigQuery deve armazenar metadados de autorização e auditoria, nunca senhas em texto puro.

## Modelo sugerido no BigQuery

### `usuarios`

`id_usuario`, `nome`, `email`, `cod_perfil`, `regiao`, `uf`, `filial`, `admin`, `ativo`, `criado_em`, `atualizado_em`.

### `alcadas_desconto`

`ordem`, `cod_perfil`, `perfil`, `desconto_max_frete_peso`, `desconto_max_ad_valorem`, `pode_aprovar`, `ativo`, `vigencia_inicio`, `vigencia_fim`.

### `politicas_desconto`

`id_politica`, `regiao`, `uf`, `faixa_peso`, `desconto_frete_peso`, `desconto_ad_valorem`, `ativo`, `observacao`, `vigencia_inicio`, `vigencia_fim`, `alterado_por`, `alterado_em`.

### `historico_aprovacoes`

`id_simulacao`, `id_embarque`, `id_solicitante`, `status_alcada`, `desconto_frete_peso`, `desconto_ad_valorem`, `cod_perfil_necessario`, `id_aprovador`, `decisao`, `observacao`, `decidido_em`.

## Generalidades

O próximo componente deve usar a mesma estrutura: valor de tabela, desconto solicitado, limite por perfil, valor líquido e próximo aprovador. Assim, novas generalidades são adicionadas sem alterar a regra já implementada para Frete Peso e FV.
