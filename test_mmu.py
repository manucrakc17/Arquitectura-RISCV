from mmu import MMU

def probar_mmu():
    print("=== INICIANDO PRUEBA DE LA MMU Y TLB ===")
    mmu_sistema = MMU(tlb_size=2, ram_latency=100)

    df, ciclos = mmu_sistema.translate(0x1000)
    print(f"Dir Virtual 0x1000 -> Física: {hex(df)} | Penalización: {ciclos} ciclos (TLB Miss + Page Fault)")

    df, ciclos = mmu_sistema.translate(0x1004)
    print(f"Dir Virtual 0x1004 -> Física: {hex(df)} | Penalización: {ciclos} ciclos (Debería ser TLB HIT y 0 ciclos)")

    df, ciclos = mmu_sistema.translate(0x2000)
    print(f"Dir Virtual 0x2000 -> Física: {hex(df)} | Penalización: {ciclos} ciclos (TLB Miss)")

    df, ciclos = mmu_sistema.translate(0x3000)
    print(f"Dir Virtual 0x3000 -> Física: {hex(df)} | Penalización: {ciclos} ciclos (TLB Miss echa a Página 1)")

    df, ciclos = mmu_sistema.translate(0x1000)
    print(f"Dir Virtual 0x1000 -> Física: {hex(df)} | Penalización: {ciclos} ciclos (TLB Miss de nuevo, sin Page Fault)")

    print("\n=== ESTADÍSTICAS DE VIRTUALIZACIÓN ===")
    print(f"TLB Hits: {mmu_sistema.tlb_hits} | TLB Misses: {mmu_sistema.tlb_misses} | Page Faults: {mmu_sistema.page_faults}")

if __name__ == "__main__":
    probar_mmu()
    

    #SOLO SIRVE PARA VER SI FUNCINOA LA MEMORIA...
    #SOLO SIRVE PARA VER SI FUNCINOA LA MEMORIA...
    #SOLO SIRVE PARA VER SI FUNCINOA LA MEMORIA...