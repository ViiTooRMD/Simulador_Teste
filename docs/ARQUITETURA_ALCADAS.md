# Arquitetura de login, políticas e alçadas

## Regra funcional

- `Frete Peso` e `FV / Ad Valorem` são componentes independentes.
- A alçada é flat: cada desconto solicitado é comparado diretamente ao limite do perfil.
- O desconto ponderado é apenas um indicador da proposta e não substitui as duas validações.
- A política por região, UF e faixa define o desconto a solicitar quando o lote não informa descontos.
- A política não amplia nem reduz a alçada do usuário.
- Quando qualquer componente excede o limite, a proposta fica `BLOQUEADO`, mantém os cálculos para análise e informa o primeiro perfil superior capaz de aprová-la.
- Margens e indicadores usam `FRETE_SIMULADO`; `FRETE_TABELA` permanece disponível para auditoria.

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
