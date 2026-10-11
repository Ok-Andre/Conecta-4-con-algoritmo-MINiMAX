# Conecta-4 con Inteligencia Artificial

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Tkinter](https://img.shields.io/badge/Tkinter-GUI-2C3E50?style=for-the-badge)
![Minimax](https://img.shields.io/badge/Algoritmo-Minimax-FF6F61?style=for-the-badge)
![Alpha-Beta](https://img.shields.io/badge/Poda-Alpha%E2%80%93Beta-00B894?style=for-the-badge)
![Conecta4](https://img.shields.io/badge/Juego-Conecta4-FFD166?style=for-the-badge)

</div>

Este proyecto implementa un juego de Conecta-4 donde una IA juega contra el usuario usando búsqueda adversaria con Minimax y poda alfa-beta.

## 🎯 Objetivo

El objetivo es crear una computadora capaz de decidir la mejor jugada posible en un tablero de 6x7, evaluando futuras ramas del árbol de juego y priorizando movimientos que conduzcan a una victoria o eviten la del oponente.

## 🧠 ¿Cómo funciona la IA?

La lógica principal está en `conecta4.py` y se basa en estos pasos:

### 1. Representación del tablero
- El tablero se modela como una matriz de 6 filas x 7 columnas.
- Cada celda puede contener:
  - `0` = vacío
  - `1` = jugador humano
  - `2` = IA

### 2. Generación de movimientos
- Se consideran solo columnas válidas, es decir, aquellas que no están llenas.
- Las columnas se exploran desde el centro hacia los extremos para mejorar la eficiencia y ganar ventaja estratégica.

### 3. Búsqueda del mejor movimiento: Minimax
La IA evalúa cada movimiento posible y simula las respuestas futuras.

- Si es el turno de la IA, intenta maximizar el valor del estado.
- Si es el turno del jugador humano, intenta minimizarlo.
- Se recorre recursivamente el árbol de juego hasta cierta profundidad.

### 4. Poda alfa-beta
Para evitar revisar todas las ramas posibles, se usa poda alfa-beta:

- `alpha`: mejor valor encontrado para la IA.
- `beta`: mejor valor encontrado para el humano.
- Si una rama ya no puede mejorar el resultado actual, se corta y no se explora más.

Esto acelera la decisión sin perder la calidad de la jugada.

### 5. Heurística de evaluación
Cuando se alcanza la profundidad límite, la IA no puede seguir buscando y usa una función heurística para estimar qué tan bueno es un tablero.

Se evalúan:
- líneas de 4 posibles
- fichas en la columna central
- amenazas de victoria del rival
- oportunidades para ganar

La función favorece a la IA cuando tiene mejor control del tablero y penaliza amenazas del oponente.

## 🕹️ Cómo se juega

El juego se ejecuta con interfaz gráfica en Tkinter.

- El usuario juega con fichas rojas.
- La computadora juega con fichas amarillas.
- Se puede elegir si empieza el humano o la computadora.
- La dificultad depende de la profundidad de búsqueda.

## ▶️ Ejecución

### Juego normal
```bash
python conecta4.py
```

### Benchmark de profundidad
```bash
python conecta4.py --benchmark
```

También puedes especificar una profundidad máxima:
```bash
python conecta4.py --benchmark 7
```

### Partida IA vs IA
```bash
python conecta4.py --match 2 5
```

Esto hace que una IA con profundidad 2 juegue contra otra con profundidad 5.

## 🧪 Archivo de benchmarking

El archivo `benchmark.py` sirve para medir:
- número de nodos explorados
- hojas evaluadas
- podas alfa-beta
- tiempo de cálculo
- rendimiento según la profundidad

Esto ayuda a comparar cómo cambia la fuerza de la IA cuando aumenta la profundidad.

## 📁 Estructura del proyecto

```text
P4/
├── conecta4.py      # lógica del juego, IA y GUI
├── benchmark.py      # pruebas de rendimiento y comparación
├── README.md         # documentación del proyecto
├── Practica04.pdf    # enunciado de la práctica
├── Reporte_Practica4_Conecta4.pdf
└── Archive.zip
```

## 🏷️ Etiquetas principales del proyecto

- `Python`
- `Tkinter`
- `Conecta-4`
- `Minimax`
- `Alpha-Beta`
- `Heurística`
- `IA`
- `Juego`

## ✅ Resumen rápido

La IA funciona así:

1. Genera todos los movimientos legales.
2. Simula cada opción.
3. Evalúa el tablero con Minimax.
4. Usa poda alfa-beta para acelerar la búsqueda.
5. Elige la jugada con mayor valor estimado.
6. Repite el proceso hasta encontrar la mejor decisión posible.

Si quieres, también puedo dejarte una versión del README con estilo más formal, más visual o orientada a entregar la práctica académica.
