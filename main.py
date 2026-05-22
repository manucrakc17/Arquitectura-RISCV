# main.py
from components import Memory, RegisterFile
from cpu import RISCV_CPU

def main():
    print("=== INICIANDO SIMULADOR RISC-V (MODO PIPELINE) ===")

    # 1. Inicializamos los componentes de hardware simulados
    memoria_ram = Memory()
    banco_registros = RegisterFile()

    # 2. Creamos el procesador y le conectamos el hardware
    cpu = RISCV_CPU(memoria_ram, banco_registros)

    # 3. CARGA DEL PROGRAMA EN LA MEMORIA RAM
    # Vamos a escribir manualmente tres instrucciones en formato hexadecimal/binario
    # empezando desde la dirección de memoria 0.
    
    # Instrucción 1: ADDI x1, x0, 10  (Guarda un 10 en el registro x1)
    # En binario real de RISC-V, esta orden se traduce al número hexadecimal: 0x00A00093
    memoria_ram.write_word(0, 0x00A00093)
    
    # Instrucción 2: ADDI x2, x0, 25  (Guarda un 25 en el registro x2)
    # En binario real de RISC-V, esta orden se traduce a: 0x01900113
    memoria_ram.write_word(4, 0x01900113)
    
    # Instrucción 3: Instrucción de parada (un 0 en la dirección 8)
    # Cuando la CPU lea un 0, sabrá que el programa llegó a su fin.
    memoria_ram.write_word(8, 0x00000000)

    print("\n--- Estado Inicial de los Registros de Interés ---")
    print(f"Registro x1 (Destino 1): {banco_registros.read(1)}")
    print(f"Registro x2 (Destino 2): {banco_registros.read(2)}")
    print(f"Program Counter (PC): {cpu.pc}")

    print("\n--- Ejecutando simulación... ---")
    
    # 4. El bucle del reloj del procesador
    while cpu.running:
        print(f"\n[Ciclo {cpu.cycle_count + 1}] Ejecutando instrucción en PC = {cpu.pc}")
        cpu.step()

    print("\n--- Simulación Terminada con Éxito ---")
    print(f"Ciclos totales de reloj: {cpu.cycle_count}")
    print(f"Valor final en el Registro x1: {banco_registros.read(1)} (Debería ser 10)")
    print(f"Valor final en el Registro x2: {banco_registros.read(2)} (Debería ser 25)")
    print(f"Program Counter (PC) final: {cpu.pc}")

if __name__ == "__main__":
    main()