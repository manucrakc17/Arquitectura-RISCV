# cpu.py
from decoder import decode_instruction
from alu import execute_alu

class RISCV_CPU:
    def __init__(self, memory, register_file):
        self.mem = memory
        self.regs = register_file
        self.pc = 0
        self.running = True
        self.cycle_count = 0

        # Registros de segmentación (cajas inter-etapa)
        self.IF_ID = None
        self.ID_EX = None
        self.EX_MEM = None
        self.MEM_WB = None

    def step(self):
            """Ejecuta UN ciclo de reloj del Pipeline completo de forma correcta"""
            if not self.running:
                return

            # ---------------------------------------------------------------------
            # ETAPA 5: Write Back (WB)
            # ---------------------------------------------------------------------
            if self.MEM_WB is not None:
                wb = self.MEM_WB
                if wb["opcode"] == 0x13: 
                    self.regs.write(wb["rd"], wb["mem_result"])

            # ---------------------------------------------------------------------
            # ETAPA 4: Memory Access (MEM)
            # ---------------------------------------------------------------------
            next_MEM_WB = None
            if self.EX_MEM is not None:
                mem = self.EX_MEM
                next_MEM_WB = {
                    "opcode": mem["opcode"],
                    "rd": mem["rd"],
                    "mem_result": mem["alu_result"] 
                }

            # ---------------------------------------------------------------------
            # ETAPA 3: Execute (EX)
            # ---------------------------------------------------------------------
            next_EX_MEM = None
            if self.ID_EX is not None:
                ex = self.ID_EX
                alu_out = 0
                if ex["opcode"] == 0x13: 
                    alu_out = execute_alu(ex["val_rs1"], ex["imm"], "ADD")
                
                next_EX_MEM = {
                    "opcode": ex["opcode"],
                    "rd": ex["rd"],
                    "alu_result": alu_out
                }

            # ---------------------------------------------------------------------
            # ETAPA 2: Decode (ID)
            # ---------------------------------------------------------------------
            next_ID_EX = None
            if self.IF_ID is not None:
                d = decode_instruction(self.IF_ID["instruction"])
                next_ID_EX = {
                    "opcode": d["opcode"],
                    "rd": d["rd"],
                    "imm": d["imm"],
                    "val_rs1": self.regs.read(d["rs1"]),
                    "val_rs2": self.regs.read(d["rs2"]),
                    "rs1_num": d["rs1"],
                    "rs2_num": d["rs2"]
                }

            # ---------------------------------------------------------------------
            # ETAPA 1: Fetch (IF)
            # ---------------------------------------------------------------------
            next_IF_ID = None
            instruction = self.mem.read_word(self.pc)
            
            # CONDICIÓN DE PARADA DE VERDAD:
            # Si la memoria lee 0 Y todas las tuberías intermedias ya están completamente vacías (en None)
            if instruction == 0 and self.IF_ID is None and self.ID_EX is None and self.EX_MEM is None and self.MEM_WB is None:
                self.running = False
                return

            # Si leímos una instrucción real, armamos el paquete para mandarlo a Decode
            if instruction != 0:
                next_IF_ID = {
                    "pc": self.pc,
                    "instruction": instruction
                }
                self.pc += 4  # Avanzamos el PC normalmente
            else:
                # Si leímos el 0 de parada, Fetch se vuelve None (burbuja de fin de programa)
                next_IF_ID = None

            # ---------------------------------------------------------------------
            # ACTUALIZACIÓN DE LOS REGISTROS DE SEGMENTACIÓN (Flanco de subida)
            # ---------------------------------------------------------------------
            # Al asignar directamente, permitimos que las etapas se limpien volviéndose None
            self.IF_ID = next_IF_ID
            self.ID_EX = next_ID_EX
            self.EX_MEM = next_EX_MEM
            self.MEM_WB = next_MEM_WB

            self.cycle_count += 1