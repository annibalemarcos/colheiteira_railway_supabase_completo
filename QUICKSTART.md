{
  "url": "https://exemplo.com",
  "inicio": "2025-12-25T02:48:54.034157",
  "plugins": {
    "ortografia": {
      "status": "ok",
      "score": 95.8,
      "peso": 1.5,
      "erro": null,
      "detalhes": {
        "total_erros": 12,
        "total_palavras": 1234,
        "taxa_erro": 0.97,
        "erros_principais": [
          {
            "texto": "Nossa equipe de desemvolvimento trabalha...",
            "erro": "desemvolvimento",
            "sugestao": ["desenvolvimento", "desenvolver"],
            "tipo": "MORFOLOGIK_RULE_PT_BR",
            "mensagem": "Possível erro de ortografia"
          },
          {
            "texto": "O custo exessivo para o projeto...",
            "erro": "exessivo",
            "sugestao": ["excessivo", "executivo"],
            "tipo": "MORFOLOGIK_RULE_PT_BR",
            "mensagem": "Possível erro de ortografia"
          }
        ],
        "concorrentes": [
          {
            "nome": "Amazon Brasil",
            "url": "https://amazon.com.br",
            "taxa_erro": 0.02,
            "motivo": "Usa revisão profissional e ferramentas automatizadas"
          },
          {
            "nome": "Nubank",
            "url": "https://nubank.com.br",
            "taxa_erro": 0.01,
            "motivo": "Time dedicado de content writers e revisores"
          },
          {
            "nome": "Magazine Luiza",
            "url": "https://magazineluiza.com.br",
            "taxa_erro": 0.03,
            "motivo": "Processo rigoroso de QA textual"
          }
        ]
      }
    },
    "links": {
      "status": "ok",
      "score": 78.4,
      "peso": 1.8,
      "erro": null,
      "detalhes": {
        "total_links": 156,
        "links_quebrados": 8,
        "links_lentos": 12,
        "taxa_quebrados": 5.13,
        "problemas": [
          {
            "url": "https://exemplo.com/antiga-pagina",
            "tipo": "a",
            "texto": "Ver produto completo",
            "status": 404,
            "tempo": 0.5
          },
          {
            "url": "https://exemplo.com/blog/2020/noticia",
            "tipo": "a",
            "texto": "Leia mais",
            "status": 404,
            "tempo": 0.3
          }
        ],
        "lentos": [
          {
            "url": "https://cdn.exemplo.com/script.js",
            "tipo": "script",
            "status": 200,
            "tempo": 4.2
          }
        ],
        "concorrentes": [
          {
            "nome": "Apple",
            "url": "https://apple.com",
            "taxa_quebrados": 0,
            "motivo": "Monitoramento 24/7 e testes automatizados continuos"
          },
          {
            "nome": "Google",
            "url": "https://google.com",
            "taxa_quebrados": 0,
            "motivo": "Sistema de CI/CD com validação de links antes do deploy"
          },
          {
            "nome": "Microsoft",
            "url": "https://microsoft.com",
            "taxa_quebrados": 0.1,
            "motivo": "Ferramentas internas de link checking e alertas automáticos"
          }
        ]
      }
    },
    "imagens": {
      "status": "ok",
      "score": 62.3,
      "peso": 1.2,
      "erro": null,
      "detalhes": {
        "total_imagens": 45,
        "sem_alt": 18,
        "baixa_qualidade": 5,
        "muito_grandes": 7,
        "faltando": 2,
        "problemas": {
          "sem_alt": [
            {
              "url": "https://exemplo.com/img/banner.jpg",
              "alt": "",
              "title": ""
            }
          ],
          "baixa_qualidade": [
            {
              "url": "https://exemplo.com/img/produto.png",
              "largura": 640,
              "altura": 480,
              "tamanho": 45000,
              "formato": "PNG",
              "qualidade": "baixa"
            }
          ],
          "muito_grandes": [
            {
              "url": "https://exemplo.com/img/hero.jpg",
              "largura": 4000,
              "altura": 3000,
              "tamanho": 1200000,
              "formato": "JPEG",
              "qualidade": "alta"
            }
          ]
        },
        "concorrentes": [
          {
            "nome": "Unsplash",
            "url": "https://unsplash.com",
            "qualidade": 98,
            "motivo": "Apenas imagens de alta resolução, WebP otimizado, lazy loading"
          },
          {
            "nome": "Adobe Stock",
            "url": "https://stock.adobe.com",
            "qualidade": 97,
            "motivo": "Controle de qualidade rigoroso, múltiplos formatos e tamanhos"
          },
          {
            "nome": "Pexels",
            "url": "https://pexels.com",
            "qualidade": 96,
            "motivo": "Curadoria de imagens, compressão inteligente, CDN global"
          }
        ]
      }
    },
    "social_media": {
      "status": "ok",
      "score": 85.0,
      "peso": 0.3,
      "erro": null,
      "detalhes": {
        "redes_encontradas": 4,
        "redes": {
          "facebook": "https://facebook.com/exemplo",
          "instagram": "https://instagram.com/exemplo",
          "linkedin": "https://linkedin.com/company/exemplo",
          "twitter": "https://twitter.com/exemplo"
        },
        "analises": {
          "facebook": {
            "acessivel": true,
            "imagem_perfil": true,
            "score_atividade": 75,
            "problemas": []
          },
          "instagram": {
            "acessivel": true,
            "imagem_perfil": true,
            "score_atividade": 90,
            "problemas": []
          },
          "linkedin": {
            "acessivel": true,
            "imagem_perfil": true,
            "score_atividade": 65,
            "problemas": ["Última postagem há 3 meses"]
          },
          "twitter": {
            "acessivel": true,
            "imagem_perfil": true,
            "score_atividade": 50,
            "problemas": ["Conta pouco ativa"]
          }
        },
        "concorrentes": [
          {
            "nome": "Nike",
            "redes": 6,
            "score": 98,
            "motivo": "Presença ativa em todas plataformas, conteúdo de alta qualidade, engajamento alto"
          },
          {
            "nome": "Netflix",
            "redes": 6,
            "score": 97,
            "motivo": "Estratégia de conteúdo adaptada por plataforma, posts diários, design consistente"
          },
          {
            "nome": "Coca-Cola",
            "redes": 5,
            "score": 96,
            "motivo": "Campanhas integradas, identidade visual forte, alta frequência de posts"
          }
        ]
      }
    },
    "lighthouse": {
      "status": "ok",
      "score": 87.67,
      "peso": 1.5,
      "erro": null,
      "detalhes": {
        "scores": {
          "performance": 92.0,
          "accessibility": 88.0,
          "best_practices": 85.0,
          "seo": 78.0
        },
        "metricas_performance": {
          "first_contentful_paint": {
            "value": 1200,
            "display": "1.2 s",
            "score": 0.95
          },
          "speed_index": {
            "value": 2100,
            "display": "2.1 s",
            "score": 0.92
          },
          "largest_contentful_paint": {
            "value": 2500,
            "display": "2.5 s",
            "score": 0.90
          },
          "time_to_interactive": {
            "value": 3200,
            "display": "3.2 s",
            "score": 0.88
          },
          "total_blocking_time": {
            "value": 150,
            "display": "150 ms",
            "score": 0.95
          },
          "cumulative_layout_shift": {
            "value": 0.05,
            "display": "0.05",
            "score": 0.98
          }
        },
        "problemas": [
          {
            "categoria": "SEO",
            "severidade": "warning",
            "problema": "Score abaixo do ideal: 78/100",
            "sugestao": "Otimize meta tags, adicione structured data"
          }
        ],
        "oportunidades": [
          {
            "titulo": "Minimize JavaScript não utilizado",
            "descricao": "Reduz o tempo de parse, compile e execution",
            "economia_ms": 850
          },
          {
            "titulo": "Sirva imagens em formatos modernos",
            "descricao": "WebP e AVIF oferecem melhor compressão",
            "economia_ms": 650
          }
        ],
        "concorrentes": [
          {
            "nome": "Google",
            "url": "https://google.com",
            "performance": 99,
            "motivo": "Infraestrutura global, otimização extrema, recursos mínimos"
          },
          {
            "nome": "Vercel",
            "url": "https://vercel.com",
            "performance": 98,
            "motivo": "CDN edge, code splitting, pre-rendering, image optimization"
          },
          {
            "nome": "Cloudflare",
            "url": "https://cloudflare.com",
            "performance": 97,
            "motivo": "Edge computing, automatic optimization, smart caching"
          }
        ]
      }
    },
    "seo": {
      "status": "ok",
      "score": 82.0,
      "peso": 1.0,
      "erro": null,
      "detalhes": {
        "total_problemas": 5,
        "problemas_criticos": 1,
        "problemas_warnings": 3,
        "problemas": [
          {
            "tipo": "warning",
            "elemento": "Title Tag",
            "problema": "Title muito longo (68 caracteres)",
            "impacto": "Médio - Será truncado nos resultados"
          },
          {
            "tipo": "warning",
            "elemento": "Open Graph",
            "problema": "Tags OG faltando: og:image",
            "impacto": "Médio - Importante para redes sociais"
          },
          {
            "tipo": "warning",
            "elemento": "Imagens",
            "problema": "18 de 45 imagens sem alt text",
            "impacto": "Médio - Importante para acessibilidade e SEO"
          }
        ],
        "metricas": {
          "title_length": 68,
          "meta_desc_length": 155,
          "h1_count": 1,
          "images_total": 45,
          "images_sem_alt": 18,
          "links_internos": 87,
          "links_externos": 23,
          "tem_sitemap": true,
          "tem_robots": true
        },
        "concorrentes": [
          {
            "nome": "Moz",
            "url": "https://moz.com",
            "score": 98,
            "motivo": "SEO perfeito: títulos otimizados, rich snippets, schema markup completo"
          },
          {
            "nome": "HubSpot",
            "url": "https://hubspot.com",
            "score": 97,
            "motivo": "Estrutura de headings impecável, meta tags otimizadas, conteúdo semântico"
          },
          {
            "nome": "Neil Patel",
            "url": "https://neilpatel.com",
            "score": 96,
            "motivo": "URLs amigáveis, linking interno estratégico, velocidade otimizada"
          }
        ]
      }
    }
  },
  "score_final": 82.45,
  "ranking": "B (Muito bom)",
  "fim": "2025-12-25T02:52:15.123456"
}

## Dashboard Flask

```bash
python server/app.py
# Windows: run_dashboard.bat
```

Acesse: http://localhost:5840

## Correção Lighthouse no Windows

Se aparecer `Lighthouse não está instalado`, mesmo depois de `npm install -g lighthouse`, normalmente o problema é o PATH do npm global no Windows.

Use:

```bat
npm prefix -g
where lighthouse
where lighthouse.cmd
python scripts\check_lighthouse.py
```

Os arquivos `setup.bat`, `run.bat` e `run_dashboard.bat` já ajustam temporariamente o PATH com `%APPDATA%\npm` e com o resultado de `npm prefix -g`. O plugin também tenta automaticamente `lighthouse`, `lighthouse.cmd`, `lighthouse.exe` e, por último, `npx --yes lighthouse`.

Se quiser forçar um caminho específico:

```bat
set LIGHTHOUSE_BIN=C:\Users\SEU_USUARIO\AppData\Roaming\npm\lighthouse.cmd
run_dashboard.bat
```

## Correção do `check_lighthouse.py`

Se aparecer este erro:

```txt
ImportError: cannot import name 'SocialMediaPlugin' from 'plugins.plugin'
```

Atualize para esta versão do projeto. A causa era um `plugins/__init__.py` antigo tentando importar o plugin de redes sociais pelo arquivo errado. O diagnóstico do Lighthouse agora carrega o plugin diretamente e não depende mais desse import frágil.

## Nota importante: Lighthouse OK no terminal, erro velho no painel

Se `python scripts\check_lighthouse.py` mostrar `[OK] Lighthouse pronto`, mas o dashboard ainda exibir:

```txt
Lighthouse não está instalado. Execute: npm install -g lighthouse
```

quase sempre é **resultado antigo carregado de `output/data.json`**. O ZIP anterior vinha com uma análise de exemplo salva e isso confundia a tela.

Correção rápida:

```bat
python scripts\clear_output.py
run_dashboard.bat
```

Ou, no próprio dashboard, use o botão **Limpar resultado** e rode a análise de novo.

Também existe o botão **Diagnosticar Lighthouse**, que testa o Lighthouse pelo mesmo processo Flask/Python usado pelo dashboard.

## Correção desta versão

Esta versão corrige dois erros vistos no dashboard:

- Lighthouse: proteção para `score=None` retornado pelo Lighthouse 13 em alguns audits/categorias. Antes podia aparecer: `'<'' not supported between instances of 'NoneType' and 'float'`.
- Ortografia: substituição do servidor local `language-tool-python` por `pyspellchecker` em Python puro, sem portas Java concorrentes no Railway.

Depois de atualizar, limpe o resultado antigo pelo botão **Limpar resultado** ou rode `clear_output.bat`, então execute uma nova análise.

## Modo bulk no dashboard

1. Abra `http://localhost:5840`.
2. Ative o toggle **Modo bulk**.
3. Cole vários sites, um por linha, vírgula ou ponto e vírgula.
4. Ajuste as pausas e a **Concorrência do lote** em **Configurações**. O padrão é concorrência 1 e pausas de 8 a 25 segundos entre novos inícios.
5. Clique em **Analisar lote** e acompanhe progresso, logs e resultados individuais.

Exemplo:

```txt
https://example.com
https://www.wikipedia.org
https://credspot.net
```

A análise em lote usa pausas aleatórias entre sites para reduzir rajadas de requisições. Para testes grandes, aumente os intervalos.

