# Guía de Defensa del TFM: España en escenarios

**Documento oficial de defensa metodológica y justificación teórica para el Tribunal.**

---

## 1. Motores Macro y Arquitectura de Doble Motor

### 1.1 ¿Por qué un port en TypeScript del motor Python?
Para permitir una experiencia interactiva sin latencia de red al mover los 10 deslizadores en el navegador. La ejecución local en TypeScript garantiza una respuesta en tiempo real (<5 ms).

### 1.2 ¿Cómo se garantiza que ambos motores no diverjan?
Mediante un contrato ejecutable basado en fixtures de anclas (`tests/fixtures/engine_anchors.json`). Se ejecutan 8 escenarios predefinidos ($S0$–$S7$) y sondas multi-palanca tanto en Python (`pytest`) como en TypeScript (`vitest`) comprobando que los resultados coinciden dentro de tolerancias estrictas ($\le 10^{-3}$).

---

## 2. Metodología Econométrica y Calibración

### 2.1 Calibración vs. Estimación Econométrica
Las constantes del motor son calibraciones basadas en la literatura académica y la estructura del modelo semiestructural $v16$. No se presentan como datos medidos incondicionales.

### 2.2 Validación Empírica con Datos de Panel
El módulo `research/validate.py` confronta cada parámetro calibrado con estimaciones OLS de datos de panel trimestrales de 20 CCAA (2007–2026). Para la velocidad de reversión del precio de la vivienda ($IPV_{REV}$ = 0,60 anual) y la tendencia a largo plazo ($IPV_{LR}$ = 3,0 %), se calculan bandas de confianza del 90 % separando subperiodos de crisis (2007–2013) y recuperación (2014–2026).

---

## 3. Simulación Estocástica y Monte Carlo

### 3.1 Parámetros de la simulación Monte Carlo
La simulación genera 4.000 trayectorias estocásticas desde 2026 hasta 2070 utilizando perturbaciones AR(1) con un parámetro de persistencia de $\rho = 0,96$ sobre tipos de interés, crecimiento y saldo primario.

### 3.2 Reproducibilidad
Para garantizar que las bandas de incertidumbre $p5$–$p95$ sean exactas y reproducibles en cada ejecución de la defensa, se fija la semilla del generador pseudoaleatorio en 42 (`seed=42`).

---

## 4. Las 10 Palancas y las 9 Líneas Rojas

### 4.1 Selección de Palancas
El motor define 10 palancas empíricamente acotadas: Euríbor ($r$), prima de riesgo ($\sigma$), saldo primario ($sp$), productividad ($\lambda$), precios de importación/energía ($p^m$), cuña fiscal ($\tau$), instituciones laborales ($z$), demanda externa ($Y^*$), demografía ($\beta_{65}$) e indexación ($\iota$).

### 4.2 Evaluación Dinámica de Líneas Rojas
No hay estados cosidos ni semáforos estáticos en la interfaz de usuario. El estado de cada una de las 9 líneas rojas (`safe`, `near`, `crossed`) se calcula dinámicamente sobre la serie temporal proyectada del escenario en cada año.
