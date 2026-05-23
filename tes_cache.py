from cache import CacheL1

def probar_mi_cache():
    print("=== INICIANDO PRUEBA DE LA CACHÉ ===")
    
    mi_cache = CacheL1(cache_size=32, block_size=16, associativity=1, replacement_policy="LRU", write_policy="write-through", ram_latency=100)
    
    hit, penalizacion = mi_cache.access(0, is_write=False)
    print(f"Acceso a Dirección 0  -> ¿Hit?: {hit} | Penalización: {penalizacion} ciclos (Debería ser False y 100)")

    hit, penalizacion = mi_cache.access(0, is_write=False)
    print(f"Acceso a Dirección 0  -> ¿Hit?: {hit} | Penalización: {penalizacion} ciclos (Debería ser True y 0)")

    hit, penalizacion = mi_cache.access(4, is_write=False)
    print(f"Acceso a Dirección 4  -> ¿Hit?: {hit} | Penalización: {penalizacion} ciclos (Debería ser True y 0)")
    
    hit, penalizacion = mi_cache.access(32, is_write=False)
    print(f"Acceso a Dirección 32 -> ¿Hit?: {hit} | Penalización: {penalizacion} ciclos (Debería ser False y 100)")

    hit, penalizacion = mi_cache.access(0, is_write=False)
    print(f"Acceso a Dirección 0  -> ¿Hit?: {hit} | Penalización: {penalizacion} ciclos (Debería ser False y 100)")

    print("\n=== ESTADÍSTICAS FINALES ===")
    print(f"Total Hits: {mi_cache.hits} | Total Misses: {mi_cache.misses}")

if __name__ == "__main__":
    probar_mi_cache()

    #SOLO SIRVE PARA VER SI FUNCIONA CACHE...
    #SOLO SIRVE PARA VER SI FUNCIONA CACHE...
    #SOLO SIRVE PARA VER SI FUNCIONA CACHE...