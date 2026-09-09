Históricos CARP — Canal Martín García
Fase 1: bajar y abrir los ZIP de viento y marea observados (sin
procesar) que publica la Comisión Administradora del Río de la
Plata para 4 estaciones del Canal Martín García (Pilote Norden,
Puerto de Colonia, Puerto de Conchillas, Puerto de Carmelo), y ver
qué formato tienen adentro antes de decidir cómo guardarlos de
forma definitiva.
Cómo ponerlo en marcha (desde el celular, sin PC)
Entrá a github.com con la misma cuenta de siempre.
Creá un repo nuevo llamado `CARP_historicos_martin_garcia`.
Con "Add file → Create new file", creá:
`descubrir_zips.py` — pegá el contenido tal cual.
`.github/workflows/descubrir.yml` — pegá el contenido tal cual.
Pestaña Actions → "Descubrir ZIPs historicos CARP" →
Run workflow.
Cuando termine, avisame y reviso el log (o lo que quedó en
`data/discovery/` del repo).
Por qué en dos pasos
No sabemos todavía si cada ZIP trae un solo archivo con todo el
histórico o algo distinto, ni desde qué fecha hay datos reales. El
script solo mira y guarda una copia de los ZIP tal cual — no
decide todavía cómo estructurar esto en el repo para el uso diario.
