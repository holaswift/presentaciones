---
name: holaswift-presentaciones
description: Crea presentaciones de hola Swift (la comunidad de Swift en español) como archivo .pptx editable en Keynote, PowerPoint o Google Slides, con el estilo de la marca, el de una invitación de keynote de Apple con el "hola" en tubo 3D, titulares grandes en Inter Display, fondos claro, oscuro o de color y muy poco texto. Úsala siempre que alguien de hola Swift pida una presentación, unas diapositivas, un deck, unas slides, la charla mensual, la plantilla para un ponente invitado, las pantallas de espera o el programa del encuentro en persona, un recap de una charla, una propuesta para patrocinadores o cualquier presentación con la marca hola Swift, aunque no diga "pptx" ni nombre el skill.
---

# Presentaciones hola Swift

Generas un .pptx de 16:9 con un script que ya sabe maquetar cada tipo de diapositiva con la marca. Tu trabajo es el **guion**: decidir qué diapositivas hay, qué tipo es cada una y qué dice. El script pone tamaños, posiciones, colores, fondos, el tubo y el logo.

## Cómo trabajar

1. **Entiende el encargo.** Qué es (charla mensual, encuentro, patrocinio, comunidad), quién la presenta y cuánto dura. Si el usuario trae material (notas, un documento, un guion de charla), parte de él y resúmelo a una idea por diapositiva. Si falta algo esencial (el tema de la charla, la fecha), pregunta. Si son detalles, escribe `[entre corchetes]` y dilo al final.
2. **Escribe el guion** en un archivo JSON siguiendo `references/guion.md`. Léelo antes de escribir: allí están los tipos de diapositiva, sus campos y cuándo usar cada uno.
3. **Genera el archivo:**
   ```bash
   pip install python-pptx pillow numpy   # si falta
   python3 <ruta-del-skill>/scripts/hacer_presentacion.py guion.json "hola Swift - <nombre>.pptx"
   ```
   Las rutas de `imagen` y `foto` en el guion se buscan junto al JSON. Si el script avisa de algo (un tipo que no existe, por ejemplo), corrígelo y vuelve a generar.
   Guarda el guion junto al .pptx y entrégalos juntos: para cambiar algo luego se edita el guion y se vuelve a generar, en lugar de retocar a mano diapositiva por diapositiva.
4. **Revisa** lo que puedas. En un Mac con Keynote, y si al usuario no le importa que se abra un momento, puedes exportar las diapositivas a imágenes y mirarlas (rutas absolutas; la carpeta de destino tiene que existir):
   ```bash
   osascript -e 'tell application "Keynote"' -e 'open POSIX file "/ruta/absoluta/al.pptx"' -e 'delay 8' -e 'export front document to POSIX file "/ruta/absoluta/carpeta-png" as slide images with properties {image format:PNG}' -e 'close front document saving no' -e 'end tell'
   ```
   Con LibreOffice: `soffice --headless --convert-to pdf archivo.pptx`. Si no tienes ninguno, relee el guion buscando textos más largos de lo que admite su tipo (límites en la referencia) y dilo al entregar.
5. **Entrega** el .pptx (y el guion) donde el usuario pueda descargarlo, y di en pocas líneas qué diapositivas hay y qué datos faltan (los `[corchetes]`).

## Casos de uso

- **Charla mensual:** portada, `hola` con el tema en color, el contenido, `pregunta` para el debate y `cierre`. Si da la charla alguien de fuera, ver el punto siguiente.
- **Plantilla para ponentes invitados:** `assets/plantillas/plantilla-ponentes.pptx` es una presentación de hola Swift con huecos `[entre corchetes]` y notas que explican cada diapositiva. Si un ponente pide la plantilla, entrégala; si te dan su nombre, el tema y la fecha, copia `assets/plantillas/plantilla-ponentes.json`, rellena lo que sepas y genera una personalizada. Recuérdales que las fuentes Inter están en `assets/fonts/`.
- **Pantallas del evento o del directo:** `espera` antes de empezar ("Empezamos a las 19:05"), en las pausas y al terminar; `agenda` con el programa (una copia por bloque con `actual` en la charla en curso); `logos` para dar las gracias a patrocinadores. Suelen ir en un deck aparte, solo de pantallas.
- **Recap de una charla:** 5–7 diapositivas con lo más importante (portada, 3–4 ideas en `frase`, `texto` o `codigo`, y `cierre` con dónde ver la grabación). Para compartirlo en LinkedIn como carrusel o en Discord, se exporta a PDF desde Keynote o PowerPoint (o con LibreOffice).
- **Patrocinio y memoria anual:** `cifras` solo con datos reales, `tarjetas` para lo que se ofrece, `logos` para quien ya apoya y `cierre` con `contacto`. Para un documento largo con tablas y precios, mejor un documento que una presentación.

## El estilo, y por qué

La marca es un saludo escrito a mano: el "hola" en tubo 3D es el protagonista y todo lo demás es sobrio. Las presentaciones siguen el lenguaje de las invitaciones de keynote de Apple: **una idea por diapositiva, titular grande y lo justo de texto**. Si una diapositiva necesita mucho texto, pártela en dos.

- **El "hola + X"** (tipo `hola`) es el gesto de la marca: "hola SwiftUI", "hola Discord", "hola 2027", siempre sin "¡". Úsalo para abrir una charla o un bloque, no en cada diapositiva.
- **Tres temas:** `claro` (papel, el habitual), `oscuro` (para frases y momentos de pausa) y `color` (fondo a sangre del color del contenido, con texto y tubo en blanco). Alterna con intención: claro de base, oscuro para una frase fuerte, color para aperturas y preguntas. Un deck todo en color cansa.
- **Color por contenido:** charla `azul`, encuentro en persona `naranja`, personas y embajadores `verde`, patrocinio `violeta`, comunidad y anuncios `rosa`. Pon `"contenido"` en el guion y el script elige el color.
- **Nada de adornos:** sin iconos inventados, sin emojis, sin sombras, sin degradados propios, sin pies de página con la web ni etiquetas tipo "Swift en español". El script no los pone; no los añadas tú como texto.

## Cómo escribimos

- De **vosotros**, cercano, en español neutro. "Ya no estáis solos" es la frase de la comunidad.
- **Sinceros:** lo bueno, lo malo y lo que viene. Nada de éxito fácil ni frases motivacionales.
- **Frases cortas.** El nombre de la cosa primero: "Charla mensual · 14 de enero", no "Te invitamos a nuestra próxima charla".
- **Estilo de frase:** solo la primera letra en mayúscula ("Próximas charlas", no "Próximas Charlas"). Nada en mayúsculas completas salvo siglas.
- **¡ y ¿ siempre, salvo en la marca.** "hola Swift!" y el "hola" en tubo van sin "¡" (el "!" de cierre recuerda al force unwrap de Swift); el resto del texto, con sus signos de apertura: "¡Gracias!", "¿Preguntas?". El nombre es **hola Swift**: dos palabras, "hola" en minúscula y "Swift" con mayúscula. Nunca "holaSwift" junto.
- No inventes datos, cifras ni citas: si no los tienes, `[corchetes]`.

## Tipografía en el ordenador que la abra

El .pptx usa **Inter Display** (titulares), **Inter** (texto) y **Menlo** (código). Si el equipo que la abre no tiene Inter, Keynote y PowerPoint la sustituyen. Las fuentes están en `assets/fonts/` (licencia libre OFL): recuerda al usuario instalarlas la primera vez si lo ves necesario.

## Recursos

- `scripts/hacer_presentacion.py`: el generador. No hace falta leerlo para usarlo.
- `references/guion.md`: formato del guion, tipos de diapositiva y un ejemplo completo. **Léelo siempre antes de escribir el guion.**
- `assets/tubo/`, `assets/logo/`: el "hola" en tubo (color y blanco) y el logotipo; el script los usa solos.
- `assets/fonts/`: Inter e Inter Display.
- `assets/plantillas/`: la plantilla para ponentes invitados (.pptx y su guion .json).
