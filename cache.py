# cache.py

class CacheL1:
    def __init__(self, cache_size=1024, block_size=16, associativity=1, replacement_policy="LRU", write_policy="write-through", ram_latency=100):
        self.cache_size = cache_size
        self.block_size = block_size
        self.associativity = associativity
        self.replacement_policy = replacement_policy.upper()
        self.write_policy = write_policy.lower()
        self.ram_latency = ram_latency

        # Contadores para el informe técnico
        self.hits = 0
        self.misses = 0

        self.num_lines = cache_size // block_size
        self.num_sets = self.num_lines // associativity
        
        # Cada línea guarda: {"tag": int, "valid": bool, "dirty": bool, "fifo_tick": int}
        self.sets = [[] for _ in range(self.num_sets)]
        self.fifo_counter = 0 

    def access(self, physical_address, is_write=False):
        # Desarmar la dirección física según el tamaño de bloque y conjuntos
        block_address = physical_address // self.block_size
        set_index = block_address % self.num_sets
        tag = block_address // self.num_sets

        target_set = self.sets[set_index]

        # 1. Buscar si el bloque ya está en el conjunto (Hit)
        for line in target_set:
            if line["valid"] and line["tag"] == tag:
                self.hits += 1
                
                # Si es LRU, movemos el bloque al final para marcarlo como usado recientemente
                if self.replacement_policy == "LRU":
                    target_set.remove(line)
                    target_set.append(line)
                
                if is_write and self.write_policy == "write-back":
                    line["dirty"] = True
                
                # Write-through obliga a pagar el costo de RAM inmediatamente en escrituras
                if is_write and self.write_policy == "write-through":
                    return True, self.ram_latency
                
                return True, 0 

        # 2. Si no se encuentra el bloque (Miss)
        self.misses += 1
        penalty = self.ram_latency 

        new_line = {
            "tag": tag,
            "valid": True,
            "dirty": (is_write and self.write_policy == "write-back"),
            "fifo_tick": self.fifo_counter
        }
        self.fifo_counter += 1

        # Insertar bloque si hay espacio libre
        if len(target_set) < self.associativity:
            target_set.append(new_line)
        else:
            # Conjunto lleno: aplicar política de desalojo
            if self.replacement_policy == "LRU":
                victim = target_set.pop(0) 
            elif self.replacement_policy == "FIFO":
                victim = min(target_set, key=lambda x: x["fifo_tick"])
                target_set.remove(victim)
            else:
                victim = target_set.pop(0)

            # Si el bloque desalojado estaba modificado, penaliza el guardado en RAM
            if victim["dirty"] and self.write_policy == "write-back":
                penalty += self.ram_latency 

            target_set.append(new_line)

        return False, penalty