# El guion

Un JSON con datos generales y una lista de diapositivas. Cada diapositiva tiene un `tipo` y sus campos; todo lo demás lo decide el script.

```json
{
  "titulo": "Charla mensual · enero",
  "tema": "claro",
  "contenido": "charla",
  "diapositivas": [ { "tipo": "portada", "titulo": "…" } ]
}
```

| Campo general | Qué hace |
|---|---|
| `titulo` | Nombre del archivo dentro de Keynote/PowerPoint. |
| `tema` | Tema por defecto: `claro` (si no se pone), `oscuro` o `color`. |
| `contenido` | `charla`, `encuentro`, `personas`, `patrocinio` o `comunidad`. Decide el color del tema `color`. |
| `color` | Alternativa a `contenido`: un color del espectro (`azul`, `naranja`, `verde`, `violeta`, `rosa`, `lavanda`, `magenta`, `amarillo`). |

El color general es el del encargo; una diapositiva puede llevar el de lo que enseña. Un deck de patrocinio (violeta) que habla del encuentro en persona puede poner `"color": "naranja"` en las diapositivas del encuentro.

Cualquier diapositiva admite además `tema`, `color` (para cambiar solo esa) y `notas` (notas del orador). Usa las notas para lo que el ponente va a decir: así la diapositiva puede quedarse con una sola idea.

**Código dentro del texto:** en cualquier texto, lo que vaya `entre comillas invertidas` sale en letra de código (`#expect`, `.disabled("motivo")`). Para más de una línea de código, usa el tipo `codigo`.

## Tipos de diapositiva

Los límites de texto son orientativos: por encima, el script reduce el tamaño, y lo grande es lo que hace que se vea bien.

### `portada`
El "hola" en tubo en grande, título abajo a la izquierda y un dato a la derecha.
- `titulo` (hasta ~40 caracteres), `subtitulo` (fecha, lugar).

### `hola`
El gesto de la marca: "hola" en tubo + una palabra enorme debajo, e información abajo. Para abrir una charla ("hola SwiftUI"), un bloque o un evento ("hola 2027"). El "hola" va siempre sin "¡".
- `palabra` (una o dos palabras, ~12 caracteres), `titulo` (una línea), `texto` (fecha, ponente…).
- Queda especialmente bien con `"tema": "color"`.
- La palabra es el *qué*: un tema ("SwiftUI"), un lugar ("Discord"), un año ("2027"). Si no hay una palabra corta que funcione, no uses `hola`: usa `frase`.

### `frase`
Una frase grande que se queda en la cabeza. Para ideas fuertes, cambios de bloque o citas.
- `frase` (hasta ~70 caracteres), `antetitulo` (opcional, pequeño, encima), `texto` (opcional, una línea debajo).
- Suele ir en `oscuro`.

### `texto`
Titular y una lista corta o un par de párrafos.
- `titulo`, y `puntos` (lista, hasta 5; cada uno de unos 55 caracteres como mucho para que quepa en una línea) o `parrafos` (hasta 2 cortos).
- Si te salen más de 5 puntos, parte en dos diapositivas o usa `tarjetas`.

### `tarjetas`
De 2 a 4 ideas paralelas en tarjetas.
- `titulo`, `tarjetas`: lista de `{ "titulo", "texto" }` (título de 1–3 palabras, texto de una o dos frases).

### `cifras`
De 2 a 4 números grandes con su explicación.
- `titulo`, `cifras`: lista de `{ "valor", "texto" }` (valor corto: "120 Hz", "500", "3").
- Solo con números reales que te hayan dado. Con dos cifras basta; si solo tienes una, usa `frase` ("Unas 500 personas.") en lugar de `cifras`.

### `imagen`
Titular y una imagen grande (captura, foto, diagrama).
- `titulo` (opcional), `imagen` (ruta al archivo, relativa al guion), `pie` (opcional), `ajuste`: `cubrir` (rellena y recorta, para fotos; por defecto) o `contener` (entera, para capturas y diagramas).
- Si la imagen no existe, deja un hueco marcado con la ruta: avisa al usuario.

### `codigo`
Una frase arriba y una ventana de Xcode/Mac grande con el código, saliéndose por abajo y la derecha.
- `titulo` (la frase), `codigo` (Swift, hasta 12 líneas y unos 55 caracteres por línea; usa `\n` y 4 espacios para sangrar), `archivo` (opcional, "Tarjeta.swift").
- Enseña el fragmento que importa, no el archivo entero: si una línea es más larga, se sale por la derecha.
- En `oscuro` la ventana es oscura; en `claro`, blanca.

### `pregunta`
Una pregunta grande con el "hola" en macro saliéndose por la esquina. Para abrir debate o cerrar un bloque.
- `pregunta` (con ¿?), `texto` (opcional, una línea).

### `persona`
Para presentar a alguien: un ponente invitado, una embajadora, una persona del equipo nueva. Si quien presenta es quien da la charla y ya sale en la diapositiva `hola`, no hace falta.
- `nombre`, `rol`, `etiqueta` (opcional: "Ponente", "Embajadora"), `frase` (opcional, entre comillas automáticas), `foto` (opcional; sin foto sale su inicial sobre verde).

### `espera`
Pantalla para dejar puesta: antes de empezar, en una pausa o al terminar. El "hola" centrado, un mensaje grande y el logo pequeño abajo.
- `titulo` ("Empezamos a las 19:05", "Volvemos en 10 minutos", "Gracias. Nos vemos el 11 de marzo"), `texto` (opcional: "Mientras, contadnos en el chat desde dónde nos veis.").

### `agenda`
El programa: hora a la izquierda, charla y ponente a la derecha. Hasta 12 filas (más de 6 pasan a dos columnas).
- `titulo` (por defecto "Programa"), `items`: lista de `{ "hora", "titulo", "detalle" }`, `actual` (opcional, número de la fila en curso empezando por 1: la resalta).
- Para el encuentro, haz una copia por bloque con `actual` en la charla que toca y ponla en las pantallas de la sala.

### `logos`
Patrocinadores, colaboradores o comunidades amigas. Los logos ajenos van siempre en tarjetas blancas, sea cual sea el tema.
- `titulo` (por defecto "Gracias a"), y `logos` (lista de rutas a imágenes, PNG con fondo transparente mejor) o `niveles`: lista de `{ "nivel": "Patrocinio principal", "logos": [...] }` (el primer nivel sale más grande).
- Si un logo no está, sale una tarjeta con su nombre entre corchetes: avisa al usuario.

### `cierre`
El logotipo, una frase y, si hace falta, el contacto.
- `frase`: por defecto "Ya no estáis solos.", que es para la comunidad. En decks para empresas o patrocinadores pon una frase que les hable a ellos ("Hagamos comunidad juntos.").
- `contacto` (opcional): texto o lista corta (`["Nombre · rol", "correo", "web"]`), sale en una línea bajo la frase. Así no hace falta una diapositiva aparte de contacto.
- Suele ir en `oscuro`.

## Ejemplo: charla mensual

```json
{
  "titulo": "Charla mensual · enero",
  "tema": "claro",
  "contenido": "charla",
  "diapositivas": [
    {"tipo": "portada", "titulo": "Charla mensual de enero", "subtitulo": "Jueves 14 de enero · 19:00 · Online"},
    {"tipo": "hola", "palabra": "SwiftUI", "titulo": "Animaciones que se sienten nativas", "texto": "Charla 01 · Con [Nombre Apellido], iOS developer", "tema": "color"},
    {"tipo": "frase", "antetitulo": "La idea", "frase": "Una animación buena no se nota: se siente.", "tema": "oscuro"},
    {"tipo": "texto", "titulo": "Lo que vamos a ver", "puntos": ["Curvas de animación y por qué spring() casi siempre gana", "Transiciones entre vistas con matchedGeometryEffect", "Errores típicos que la hacen parecer web"]},
    {"tipo": "tarjetas", "titulo": "Tres reglas", "tarjetas": [
      {"titulo": "Rápida", "texto": "Entre 200 y 400 ms. Más larga se siente lenta."},
      {"titulo": "Interrumpible", "texto": "Si el usuario toca, la animación cede."},
      {"titulo": "Con física", "texto": "Muelles en lugar de curvas fijas."}]},
    {"tipo": "codigo", "titulo": "Un muelle en una línea.", "archivo": "Tarjeta.swift", "codigo": "withAnimation(.spring(duration: 0.35)) {\n    abierta.toggle()\n}"},
    {"tipo": "persona", "etiqueta": "Ponente", "nombre": "[Nombre Apellido]", "rol": "[iOS developer en Empresa]"},
    {"tipo": "pregunta", "pregunta": "¿Qué te gustaría ver en la próxima?", "texto": "Cuéntanoslo en el Discord.", "tema": "color", "color": "rosa"},
    {"tipo": "cierre", "tema": "oscuro", "notas": "Gracias y turno de preguntas."}
  ]
}
```

## Ritmo de un deck

- Abre con `portada` y, si es una charla o un evento, un `hola` en color.
- Alterna: dos o tres diapositivas claras, una `frase` en oscuro, otra vez claras.
- Dos o tres diapositivas en color en todo el deck como mucho (un `hola`, una `pregunta`): si todo es color, nada destaca.
- Cierra con `cierre`.
- 10–15 diapositivas para una charla de 20–30 minutos.
