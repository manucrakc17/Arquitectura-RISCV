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

        # Registros de segmentación (Tuberías inter-etapa)
        self.IF_ID = None
        self.ID_EX = None
        self.EX_MEM = None
        self.MEM_WB = None

    def step(self):
        if not self.running:
            return

        # ---------------------------------------------------------------------
        # ETAPA 5: Write Back (WB)
        # ---------------------------------------------------------------------
        if self.MEM_WB is not None:
            wb = self.MEM_WB
            # Escriben en registro: Tipo-I (0x13), Tipo-R (0x33) y Loads (0x03)
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
            
            mem_result = alu_result # Por defecto pasa el valor de la ALU

            if opcode == 0x03:   # LW (Load Word): Lee de la RAM
                mem_result = self.mem.read_word(alu_result)
            elif opcode == 0x23: # SW (Store Word): Escribe en la RAM
                self.mem.write_word(alu_result, val_rs2)

            next_MEM_WB = {
                "opcode": opcode,
                "rd": rd,
                "mem_result": mem_result
            }

        # ---------------------------------------------------------------------
        # ETAPA 3: Execute (EX) - AQUÍ OPERA EL FORWARDING
        # ---------------------------------------------------------------------
        next_EX_MEM = None
        if self.ID_EX is not None:
            ex = self.ID_EX
            opcode = ex["opcode"]
            
            # Por defecto, usamos los valores que venían desde Decode
            val_a = ex["val_rs1"]
            val_b = ex["val_rs2"]

            # --- BYPASS / FORWARDING ---
            # Caso A: La instrucción de justo adelante (EX_MEM) va a escribir en un registro que necesito usar ya
            if self.EX_MEM is not None and self.EX_MEM["rd"] != 0:
                if self.EX_MEM["rd"] == ex["rs1_num"]:
                    val_a = self.EX_MEM["alu_result"]
                if self.EX_MEM["rd"] == ex["rs2_num"]:
                    val_b = self.EX_MEM["alu_result"]

            # Caso B: La instrucción de dos etapas adelante (MEM_WB) tiene el dato que necesito
            if self.MEM_WB is not None and self.MEM_WB["rd"] != 0:
                if self.MEM_WB["rd"] == ex["rs1_num"]:
                    val_a = self.MEM_WB["mem_result"]
                if self.MEM_WB["rd"] == ex["rs2_num"]:
                    val_b = self.MEM_WB["mem_result"]

            # --- EJECUCIÓN DE LA ALU ---
            alu_out = 0
            if opcode == 0x13:    # ADDI
                alu_out = execute_alu(val_a, ex["imm"], "ADD")
            elif opcode == 0x33:  # Tipo-R (ADD / SUB)
                if ex["funct3"] == 0x00 and ex["funct7"] == 0x00:   # ADD
                    alu_out = execute_alu(val_a, val_b, "ADD")
                elif ex["funct3"] == 0x00 and ex["funct7"] == 0x20: # SUB
                    alu_out = execute_alu(val_a, val_b, "SUB")
            elif opcode in [0x03, 0x23]: # LW / SW (Dirección base + offset)
                alu_out = execute_alu(val_a, ex["imm"], "ADD")

            next_EX_MEM = {
                "opcode": opcode,
                "rd": ex["rd"],
                "alu_result": alu_out,
                "val_rs2": val_b  # Guardamos val_b actualizado por si es un SW
            }

            # Predicción estática
            if opcode == 0x63: # Es una instrucción de Salto (Branch)
                # Imaginemos que es un BEQ (funct3 == 0)
                if ex["funct3"] == 0x00:
                    # Evaluamos la condición con los valores frescos (con forwarding incluido)
                    if val_a == val_b: 
                        # ¡DIABLOS, EL SALTO SÍ SE CUMPLE! (Falló la predicción estática)
                        
                        # 1. Calculamos el PC correcto al que debimos saltar 
                        # (El PC de la instrucción de salto + el valor inmediato de distancia)
                        direccion_salto = ex["PC"] + ex["imm"]
                        self.pc = direccion_salto
                        
                        # 2. FLUSH: Borramos lo que Fetch y Decode alcanzaron a meter por error
                        self.IF_ID = None  # Limpiamos la etapa Decode
                        next_ID_EX = None  # Limpiamos lo que iba a pasar a Execute

        # ---------------------------------------------------------------------
        # ETAPA 2: Decode (ID) - AQUÍ DETECTAMOS EL HAZARD Y METEMOS LA BURBUJA
        # ---------------------------------------------------------------------
        next_ID_EX = None
        hazard_detected = False

        if self.IF_ID is not None:
            d = decode_instruction(self.IF_ID["instruction"])
            
            # Buscamos si hay un hazard con la instruccion siguiente
            if self.ID_EX is not None:
                dest_in_execute = self.ID_EX["rd"]
                opcode_in_execute = self.ID_EX["opcode"]
                
                if dest_in_execute != 0 and opcode_in_execute in [0x13, 0x33, 0x03]:
                    if d["rs1"] == dest_in_execute or d["rs2"] == dest_in_execute:
                        hazard_detected = True 

            if hazard_detected:
                next_ID_EX = None # Inyectamos la BURBUJA (Execute recibirá None en el próximo ciclo)
            else:
                next_ID_EX = {
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
        # ETAPA 1: Fetch (IF) - CONGELAMOS SI HAY HAZARD
        # ---------------------------------------------------------------------
        next_IF_ID = None
        
        if hazard_detected:
            next_IF_ID = self.IF_ID # Congelamos: mantenemos la misma instrucción para el próximo ciclo
        else:
            instruction = self.mem.read_word(self.pc)
            
            if instruction == 0 and self.IF_ID is None and self.ID_EX is None and self.EX_MEM is None and self.MEM_WB is None:
                self.running = False
                return

            if instruction != 0:
                next_IF_ID = {"pc": self.pc, "instruction": instruction}
                self.pc += 4
            else:
                next_IF_ID = None

        # ---------------------------------------------------------------------
        # ACTUALIZACIÓN DE LOS REGISTROS DE SEGMENTACIÓN
        # ---------------------------------------------------------------------
        self.IF_ID = next_IF_ID
        self.ID_EX = next_ID_EX
        self.EX_MEM = next_EX_MEM
        self.MEM_WB = next_MEM_WB

        self.cycle_count += 1