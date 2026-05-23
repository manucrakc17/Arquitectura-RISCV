# cpu_modo2.py
from decoder import decode_instruction
from alu import execute_alu
from cache import CacheL1
from mmu import MMU

class RISCV_CPU:
    def __init__(self, memory, register_file):
        self.mem = memory
        self.regs = register_file
        self.pc = 0
        self.running = True
        self.cycle_count = 0

        # Componentes Modo 2
        self.mmu_i = MMU(tlb_size=4, ram_latency=100)
        self.mmu_d = MMU(tlb_size=4, ram_latency=100)
        self.cache_i = CacheL1(cache_size=1024, block_size=16, associativity=1, ram_latency=100)
        self.cache_d = CacheL1(cache_size=1024, block_size=16, associativity=2, ram_latency=100)
        self.memory_stall_cycles = 0

        # Registros de segmentación
        self.IF_ID = None
        self.ID_EX = None
        self.EX_MEM = None
        self.MEM_WB = None

    def step(self):
        if not self.running:
            return

        # Freno por latencia de memoria
        if self.memory_stall_cycles > 0:
            self.memory_stall_cycles -= 1
            self.cycle_count += 1
            return

        # ---------------------------------------------------------------------
        # ETAPA 5: Write Back (WB)
        # ---------------------------------------------------------------------
        if self.MEM_WB is not None:
            wb = self.MEM_WB
            if wb["opcode"] in [0x13, 0x33, 0x03]: 
                self.regs.write(wb["rd"], wb["mem_result"])

        # ---------------------------------------------------------------------
        # ETAPA 4: Memory Access (MEM)
        # ---------------------------------------------------------------------
        next_MEM_WB = None
        if self.EX_MEM is not None:
            mem = self.EX_MEM
            opcode = mem["opcode"]
            rd = mem["rd"]
            alu_result = mem["alu_result"]
            val_rs2 = mem["val_rs2"]
            
            mem_result = alu_result 

            # Acceso a datos con MMU y Caché
            if opcode == 0x03:   # LW
                p_addr, mmu_penalty = self.mmu_d.translate(alu_result)
                hit, cache_penalty = self.cache_d.access(p_addr, is_write=False)
                self.memory_stall_cycles += (mmu_penalty + cache_penalty)
                mem_result = self.mem.read_word(p_addr)
                
            elif opcode == 0x23: # SW
                p_addr, mmu_penalty = self.mmu_d.translate(alu_result)
                hit, cache_penalty = self.cache_d.access(p_addr, is_write=True)
                self.memory_stall_cycles += (mmu_penalty + cache_penalty)
                self.mem.write_word(p_addr, val_rs2)

            next_MEM_WB = {
                "opcode": opcode,
                "rd": rd,
                "mem_result": mem_result
            }

        # ---------------------------------------------------------------------
        # ETAPA 3: Execute (EX)
        # ---------------------------------------------------------------------
        next_EX_MEM = None
        branch_taken = False
        target_pc = 0

        if self.ID_EX is not None:
            ex = self.ID_EX
            opcode = ex["opcode"]
            val_a = ex["val_rs1"]
            val_b = ex["val_rs2"]

            # Forwarding
            if self.EX_MEM is not None and self.EX_MEM["rd"] != 0:
                if self.EX_MEM["rd"] == ex["rs1_num"]: val_a = self.EX_MEM["alu_result"]
                if self.EX_MEM["rd"] == ex["rs2_num"]: val_b = self.EX_MEM["alu_result"]

            if self.MEM_WB is not None and self.MEM_WB["rd"] != 0:
                if self.MEM_WB["rd"] == ex["rs1_num"]: val_a = self.MEM_WB["mem_result"]
                if self.MEM_WB["rd"] == ex["rs2_num"]: val_b = self.MEM_WB["mem_result"]

            # Operaciones ALU
            alu_out = 0
            if opcode == 0x13:    # ADDI
                alu_out = execute_alu(val_a, ex["imm"], "ADD")
            elif opcode == 0x33:  # Tipo-R
                if ex["funct3"] == 0x00 and ex["funct7"] == 0x00: 
                    alu_out = execute_alu(val_a, val_b, "ADD")
                elif ex["funct3"] == 0x00 and ex["funct7"] == 0x20: 
                    alu_out = execute_alu(val_a, val_b, "SUB")
            elif opcode in [0x03, 0x23]: # LW / SW
                alu_out = execute_alu(val_a, ex["imm"], "ADD")
            elif opcode == 0x63:  # BEQ
                if ex["funct3"] == 0x00: 
                    if val_a == val_b: 
                        branch_taken = True
                        target_pc = ex["pc"] + ex["imm"]

            next_EX_MEM = {
                "opcode": opcode,
                "rd": ex["rd"],
                "alu_result": alu_out,
                "val_rs2": val_b
            }

        # ---------------------------------------------------------------------
        # ETAPA 2: Decode (ID)
        # ---------------------------------------------------------------------
        next_ID_EX = None
        data_hazard = False

        if self.IF_ID is not None:
            d = decode_instruction(self.IF_ID["instruction"])
            
            # Detección de riesgos
            if self.ID_EX is not None:
                dest_in_execute = self.ID_EX["rd"]
                opcode_in_execute = self.ID_EX["opcode"]
                if dest_in_execute != 0 and opcode_in_execute in [0x13, 0x33, 0x03]:
                    if d["rs1"] == dest_in_execute or d["rs2"] == dest_in_execute:
                        data_hazard = True 

            if branch_taken:
                next_ID_EX = None
            elif data_hazard:
                next_ID_EX = None
            else:
                next_ID_EX = {
                    "pc": self.IF_ID["pc"],
                    "opcode": d["opcode"],
                    "rd": d["rd"],
                    "imm": d["imm"],
                    "funct3": d["funct3"],
                    "funct7": d["funct7"],
                    "val_rs1": self.regs.read(d["rs1"]),
                    "val_rs2": self.regs.read(d["rs2"]),
                    "rs1_num": d["rs1"],
                    "rs2_num": d["rs2"]
                }

        # ---------------------------------------------------------------------
        # ETAPA 1: Fetch (IF)
        # ---------------------------------------------------------------------
        next_IF_ID = None
        
        if branch_taken:
            self.pc = target_pc
            p_pc, mmu_penalty = self.mmu_i.translate(self.pc)
            hit, cache_penalty = self.cache_i.access(p_pc, is_write=False)
            self.memory_stall_cycles += (mmu_penalty + cache_penalty)
            
            instruction = self.mem.read_word(p_pc)
            if instruction != 0:
                next_IF_ID = {"pc": self.pc, "instruction": instruction}
                self.pc += 4
            self.IF_ID = None 
        elif data_hazard:
            next_IF_ID = self.IF_ID 
        else:
            p_pc, mmu_penalty = self.mmu_i.translate(self.pc)
            hit, cache_penalty = self.cache_i.access(p_pc, is_write=False)
            self.memory_stall_cycles += (mmu_penalty + cache_penalty)
            
            instruction = self.mem.read_word(p_pc)
            if instruction == 0 and self.IF_ID is None and self.ID_EX is None and self.EX_MEM is None and self.MEM_WB is None:
                self.running = False
                return

            if instruction != 0:
                next_IF_ID = {"pc": self.pc, "instruction": instruction}
                self.pc += 4
            else:
                next_IF_ID = None

        # Actualización de registros inter-etapa
        if not branch_taken:
            self.IF_ID = next_IF_ID
        self.ID_EX = next_ID_EX
        self.EX_MEM = next_EX_MEM
        self.MEM_WB = next_MEM_WB

        self.cycle_count += 1