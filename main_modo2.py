# main_modo2.py
from components import Memory, RegisterFile
from cpu_modo2 import RISCV_CPU

def main():
    print("=== EJECUTANDO PROCESADOR MODO 2: JERARQUÍA DE MEMORIA ===")

    memoria_ram = Memory()
    banco_registros = RegisterFile()
    cpu = RISCV_CPU(memoria_ram, banco_registros)

    # Carga de instrucciones en RAM
    memoria_ram.write_word(0, 0x00A00093)  # ADDI x1, x0, 10
    memoria_ram.write_word(4, 0x00102823)  # SW x1, 16(x0)
    memoria_ram.write_word(8, 0x01002103)  # LW x2, 16(x0)
    memoria_ram.write_word(12, 0x00000000) # Parada / Halt

    # Bucle principal de simulación
    while cpu.running:
        if cpu.memory_stall_cycles > 0:
            print(f"[Ciclo {cpu.cycle_count + 1}] CPU Congelado... Esperando a la Memoria ({cpu.memory_stall_cycles} ciclos restantes)")
        else:
            print(f"[Ciclo {cpu.cycle_count + 1}] Ejecutando... PC = {cpu.pc}")
            
        cpu.step()

    # Impresión de métricas finales
    print("\n===========================================")
    print("      REPORTE CUANTITATIVO (MODO 2)        ")
    print("===========================================")
    print(f"Ciclos Totales de Ejecución : {cpu.cycle_count}")
    print(f"Registro x1                 : {banco_registros.read(1)}")
    print(f"Registro x2 (Cargado de RAM): {banco_registros.read(2)}")
    print("-------------------------------------------")
    print("ESTADÍSTICAS DE CACHÉ L1:")
    print(f"  Caché Instrucciones (I) -> Hits: {cpu.cache_i.hits} | Misses: {cpu.cache_i.misses}")
    print(f"  Caché Datos (D)         -> Hits: {cpu.cache_d.hits} | Misses: {cpu.cache_d.misses}")
    print("-------------------------------------------")
    print("ESTADÍSTICAS DE MEMORIA VIRTUAL (MMU/TLB):")
    print(f"  TLB Instrucciones       -> Hits: {cpu.mmu_i.tlb_hits} | Misses: {cpu.mmu_i.tlb_misses}")
    print(f"  TLB Datos               -> Hits: {cpu.mmu_d.tlb_hits} | Misses: {cpu.mmu_d.tlb_misses}")
    print(f"  Fallas de Página totales: {cpu.mmu_i.page_faults + cpu.mmu_d.page_faults}")
    print("===========================================")

if __name__ == "__main__":
    main()