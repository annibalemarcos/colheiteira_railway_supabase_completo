"""Pacote de plugins do Colheiteira.

Este arquivo fica propositalmente leve.

Antes ele tentava importar `SocialMediaPlugin` a partir de `plugins.plugin`,
mas `plugins.plugin` é só a classe base. Isso quebrava qualquer importação como:

    from plugins.lighthouse.plugin import LighthousePlugin

Resultado: scripts de diagnóstico morriam antes mesmo de testar o Lighthouse.
Os plugins reais continuam sendo carregados dinamicamente pelo `core.plugin_loader`.
"""

__all__ = []
