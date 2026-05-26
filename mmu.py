# mmu.py

class MMU:
    def __init__(self, tlb_size=4, ram_latency=100):
        """
        Unidad de Manejo de Memoria (MMU) con soporte de TLB y Tabla de Páginas de 2 niveles.
        """
        self.tlb_size = tlb_size
        self.ram_latency = ram_latency
        
        # Métricas obligatorias para el reporte
        self.tlb_hits = 0
        self.tlb_misses = 0
        self.page_faults = 0

        # Estructura de la TLB: Lista de entradas para aplicar LRU fácilmente
        # Cada entrada: {"vpn": int, "ppn": int, "valid": bool}
        self.tlb = []

        # Simulación de la Tabla de Páginas en el sistema (un diccionario para el modelo)
        # En un sistema real esto reside en la RAM física
        self.page_table_level1 = {}

    def translate(self, virtual_address):
        """
        Traduce una dirección virtual a una dirección física.
        Devuelve una tupla: (physical_address: int, penalty_cycles: int)
        """
        # 1. Extraer componentes de la dirección virtual (Páginas de 4KB = 12 bits de offset)
        offset = virtual_address & 0xFFF
        vpn = virtual_address >> 12
        
        # Para la tabla de 2 niveles (SV32): dividimos los 20 bits del VPN en dos partes de 10 bits
        vpn0 = vpn & 0x3FF
        vpn1 = (vpn >> 10) & 0x3FF

        # ---------------------------------------------------------------------
        # CASO 1: BUSCAR EN LA TLB (Translation Lookaside Buffer)
        # ---------------------------------------------------------------------
        for entry in self.tlb:
            if entry["valid"] and entry["vpn"] == vpn:
                self.tlb_hits += 1
                
                # Actualizar LRU: mover al final como la entrada más recientemente usada
                self.tlb.remove(entry)
                self.tlb.append(entry)
                
                # Dirección física = (PPN << 12) | Offset
                physical_address = (entry["ppn"] << 12) | offset
                return physical_address, 0 # TLB Hit no agrega penalización de ciclos

        # ---------------------------------------------------------------------
        # CASO 2: TLB MISS -> RECORRER TABLA DE PÁGINAS DE 2 NIVELES
        # ---------------------------------------------------------------------
        self.tlb_misses += 1
        
        # Simulamos el costo de leer dos niveles de tablas en la RAM principal
        # Cada acceso a la RAM para buscar la traducción cuesta 'ram_latency' ciclos
        tlb_miss_penalty = 2 * self.ram_latency 

        # Verificar Nivel 1
        if vpn1 not in self.page_table_level1:
            self.page_table_level1[vpn1] = {}

        # Verificar Nivel 2
        table_level2 = self.page_table_level1[vpn1]
        if vpn0 not in table_level2:
            # --- PAGE FAULT ---
            # Si la página no existe en las tablas, el OS la crea (Mapeo directo simple para simulación)
            self.page_faults += 1
            allocated_ppn = vpn # Asignamos un número de página física idéntico por simplicidad
            table_level2[vpn0] = allocated_ppn
            
            # Un Page Fault real cuesta miles de ciclos (ir al disco), 
            # contractualmente sumaremos una penalización extra por inicializar el overhead
            tlb_miss_penalty += 50 

        ppn = table_level2[vpn0]
        physical_address = (ppn << 12) | offset

        # ---------------------------------------------------------------------
        # ACTUALIZAR LA TLB (Con política de reemplazo LRU)
        # ---------------------------------------------------------------------
        new_entry = {"vpn": vpn, "ppn": ppn, "valid": True}
        
        if len(self.tlb) >= self.tlb_size:
            # El elemento en el índice 0 es el menos usado recientemente, se desaloja
            self.tlb.pop(0)
            
        self.tlb.append(new_entry)

        return physical_address, tlb_miss_penalty