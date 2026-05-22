from components import Memory, RegisterFile
from cpu import RISCV_CPU

def main():
    print("=== PROBANDO PIPELINE CON SOPORTE COMPLETO Y HAZARDS ===")

    memoria_ram = Memory()
    banco_registros = RegisterFile()
    cpu = RISCV_CPU(memoria_ram, banco_registros)

    # 1. ADDI x1, x0, 10  (x1 = 10) -> Hex: 0x00A00093
    memoria_ram.write_word(0, 0x00A00093)
    
    # 2. ADD x2, x1, x1   (x2 = x1 + x1 = 20) -> ¡Provoca Hazard de datos!
    # Hexadecimal real de RISC-V para 'add x2, x1, x1': 0x00108133
    memoria_ram.write_word(4, 0x00108133)
    
    # 3. Parada
    memoria_ram.write_word(8, 0x00000000)

    while cpu.running:
        print(f"[Ciclo {cpu.cycle_count + 1}] PC = {cpu.pc}")
        cpu.step()

    print("\n=== Resultados Finales ===")
    print(f"Ciclos totales: {cpu.cycle_count}")
    print(f"Registro x1: {banco_registros.read(1)} (Debería ser 10)")
    print(f"Registro x2: {banco_registros.read(2)} (Debería ser 20)")

if __name__ == "__main__":
    main()