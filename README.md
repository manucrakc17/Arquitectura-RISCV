# Arquitectura-RISCV
Modelado de arquitectura de un computador en python, imitando una pipeline de 5 pasos.

Este repositorio contiene la implementación de un simulador funcional para un procesador basado en la arquitectura RISC-V (RV32I), desarrollado de forma modular en Python. El diseño emula fielmente el comportamiento de hardware de una microarquitectura segmentada.

## Arquitectura de Software Modular

El proyecto está estrictamente dividido en módulos independientes para facilitar el desarrollo en paralelo y mitigar conflictos en el control de versiones:

* **`components.py`**: Modelado del estado físico del hardware. Contiene la clase `Memory` (RAM de 1MB administrada en bytes con formato Little-Endian) y `RegisterFile` (banco de 32 registros generales, implementando la restricción por hardware de `x0 = 0`).
* **`decoder.py`**: Unidad de decodificación. Descompone instrucciones binarias de 32 bits y extrae opcodes, registros origen/destino (`rs1`, `rs2`, `rd`) y realiza la reconstrucción y extensión de signo de inmediatos para los formatos Tipo-I, S, B, U, y J.
* **`alu.py`**: Unidad Aritmético Lógica (ALU). Resuelve operaciones lógicas y matemáticas a nivel de bits (`ADD`, `SUB`, `AND`, `OR`, `XOR`, `SLT`) asegurando la consistencia de palabras de 32 bits mediante máscaras lógicas (`0xFFFFFFFF`).
* **`cpu.py`**: Núcleo del procesador que orquesta el Pipeline segmentado.
* **`main.py`**: Punto de entrada encargado de instanciar los módulos, cargar los binarios de prueba en la RAM e iniciar el ciclo de reloj.

---

Características Avanzadas Implementadas (Modo 1)

### 1. Segmentación en 5 Etapas (Pipeline)
El procesador ejecuta en paralelo las cinco etapas clásicas de la arquitectura RISC-V:
1.  **Fetch (IF)**: Lectura de la instrucción desde la RAM utilizando el `Program Counter` (PC).
2.  **Decode (ID)**: Decodificación y lectura del banco de registros.
3.  **Execute (EX)**: Operaciones matemáticas empleando la ALU.
4.  **Memory Access (MEM)**: Lectura y escritura en la memoria RAM para instrucciones Load/Store.
5.  **Write Back (WB)**: Consolidación de resultados en el banco de registros.

*Nota de diseño*: Para emular el comportamiento concurrente del hardware en un entorno secuencial como Python, el método del reloj procesa las etapas en sentido inverso (de la 5 a la 1), asegurando que los registros de segmentación inter-etapa (`IF_ID`, `ID_EX`, `EX_MEM`, `MEM_WB`) no sufran corrupción ni sobreescritura de datos dentro del mismo ciclo.

### 2. Resolución de Hazards de Datos
Para evitar la lectura de datos corruptos o desactualizados (*Data Hazards*), el simulador incorpora dos mecanismos críticos:
* **Detección y Burbujas (Stalls)**: La etapa de decodificación monitoriza si los registros de origen entran en conflicto con el destino de la instrucción en ejecución. De ser así, se inyecta un estado nulo (`None` o burbuja) congelando las etapas previas por un ciclo.
* **Unidad de Forwarding (Adelantamiento)**: Implementa "bypasses" lógicos en la etapa de ejecución. Si los datos requeridos por la ALU ya fueron calculados por instrucciones precedentes pero aún no se consolidan en el banco de registros, la unidad los intercepta directamente desde las tuberías `EX_MEM` o `MEM_WB`, eliminando penalizaciones innecesarias de ciclos de reloj.

### 3. Hazards de Control (Predicción de Saltos)
Para gestionar las instrucciones de salto condicional (`BEQ`), el simulador implementa **Predicción Estática: Siempre No Tomado**. El procesador asume de forma optimista que el salto fallará y continúa cargando instrucciones secuenciales (`PC + 4`). 

En caso de que la predicción falle (el salto efectivamente se cumple en la etapa EX), el procesador activa una rutina de **Pipeline Flush**, invalidando las instrucciones cargadas erróneamente en las etapas de Fetch y Decode (`None`) y redirigiendo el flujo al `PC` destino del salto.

--------------------------------------------------------------------------------------

Características Avanzadas Implementadas (Modo 2)

### 1. Memoria Virtual Avanzada (MMU y TLB)
El sistema emula la traducción y el mapeo de direcciones lógicas a físicas trabajando con páginas estándar de 4KB:
1. **Caché TLB**: Estructura de tamaño reducido para traducciones instantáneas de páginas, administrada bajo la política de reemplazo `LRU`.
2. **Tabla de Páginas de 2 Niveles**: Ante un *TLB Miss*, el hardware simula el recorrido jerárquico indexando descriptores en la RAM, añadiendo una penalización del doble de la latencia base.
3. **Manejo de Page Faults**: El entorno detecta accesos a páginas no inicializadas y emula el overhead de asignación física por parte del sistema operativo.

*Nota de diseño*: La MMU abstrae la dirección virtual dividiendo los bits superiores para simular la estructura de traducción jerárquica de RISC-V, permitiendo evaluar el rendimiento del almacenamiento sin necesidad de cargar un sistema operativo real.

### 2. Jerarquía de Caché L1 Parametrizada
Para evitar el acceso constante a la memoria principal, se incorporan dos estructuras independientes de almacenamiento temporal:
* **Configurabilidad**: Permite modificar dinámicamente parámetros clave de hardware como el tamaño total de la caché, el tamaño de bloque y los niveles de asociatividad (Mapeo Directo y Asociativo por Conjuntos).
* **Políticas de Reemplazo**: Estructuras de control diseñadas para alternar estrategias de desalojo de bloques cuando la caché se llena mediante algoritmos `LRU` o `FIFO`.
* **Políticas de Escritura**: Simulación precisa de estrategias `Write-Through` (escritura directa en RAM) y `Write-Back` (uso de *dirty bits* con penalización doble en desalojo).

### 3. Control de Ciclos por Latencia (Stalls de Memoria)
Para emular de forma empírica el impacto físico del fenómeno del *Memory Wall*, el procesador incorpora un sistema de frenos en el tiempo de ejecución:
* **Freno por Latencia (`memory_stall_cycles`)**: Al detectarse un fallo de caché o de TLB en las etapas de Fetch (`IF`) o Acceso a Memoria (`MEM`), el CPU calcula la penalización correspondiente en ciclos. El simulador congela la marcha completa de todas las etapas del pipeline, sumando el tiempo transcurrido pero deteniendo el avance de las instrucciones hasta que la RAM principal responde.
